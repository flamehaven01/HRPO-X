"""
    HRPO-X v1.0.1 (Research Prototype)
    ==================================
    Status: Research prototype (single-file implementation)

    This module implements a small set of HRPO-inspired components:
    1. [P1] Adaptive Epsilon Scheduling (importance sampling warmup)
    2. [P1] r_min Oscillation Fix (proportional control + momentum)
    3. [P0] Ghost Mode Validation (bootstrap CI)
    4. [P0] Network Partition Handling (simulated hash coordination)
    5. [P2] Task Shift Adaptation (task-aware r_min blending)

    Note: This is not a verified paper implementation and has no distributed training.

    Author: CLI C01
    Date: 2026-01-06
    """




import numpy
import torch
import torch.nn.functional as F
import typing
import logging
import time
import json
import math
from . import paper_core

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HRPO-X-v2.2f")

class HRPOConfig:
    """Configuration for HRPO-X v2.2f"""
    def __init__(self):
        # Eq 6 Constants
        self.beta = 0.005  # KL coefficient
        self.epsilon_clip_base = 0.2
        self.max_kl_reject = 0.01
        
        # Adaptive r_min
        self.target_hidden_ratio = 0.15
        self.r_min_range = (0.90, 0.99)
        self.warmup_steps = 100
        self.adaptation_rate = 0.1
        self.convergence_threshold = 0.001
        self.max_single_change = 0.05
        
        # Ghost Mode
        self.ghost_traffic_percent = 25.0  # Increased from 10%
        self.ghost_min_samples = 250       # Increased from 100
        self.ghost_confidence = 0.99
        self.error_rate_threshold = 0.01
        self.reward_kl_threshold = 0.1
        
        # Network
        self.broadcast_timeout = 5.0
        
        # Task Awareness
        self.default_r_min = {
            'knowledge': 0.98,
            'stem': 0.95,
            'general': 0.96
        }

# ==============================================================================
# 1. [P1] IS Cold Start Stability (Adaptive Epsilon)
# ==============================================================================

def adaptive_epsilon_schedule(step: int, warmup: int = 100) -> float:
    """
    [ENHANCED] Adaptive IS clipping for cold start stability.
    
    Strategy:
        - Warmup (0-100): epsilon = 0.5 (loose clipping)
        - Transition (100-200): epsilon linearly decrease 0.5 -> 0.2
        - Stable (200+): epsilon = 0.2 (PPO default)
    """
    if step < warmup:
        return 0.5  # Loose during warmup
    elif step < warmup * 2:
        # Linear decay
        progress = (step - warmup) / warmup
        return 0.5 - 0.3 * progress  # 0.5 -> 0.2
    else:
        return 0.2  # Standard PPO

def importance_weighted_hrpo_loss(
    policy_logp: torch.Tensor,
    old_policy_logp: torch.Tensor,
    ref_logp: torch.Tensor,
    advantages: torch.Tensor,
    step: int,
    config: HRPOConfig
) -> typing.Tuple[typing.Optional[torch.Tensor], typing.Dict]:
    """
    Computes Eq. 6 with Importance Sampling and Adaptive Clipping.
    """
    epsilon = adaptive_epsilon_schedule(step, config.warmup_steps)
    
    # Compute importance ratios per token
    log_ratio = policy_logp - old_policy_logp
    ratio = torch.exp(log_ratio)

    # [SAFETY] Reject if KL divergence too high
    approx_kl = ((ratio - 1) - log_ratio).mean()
    
    if approx_kl > config.max_kl_reject:
        return None, {
            'status': 'rejected',
            'reason': f'KL {approx_kl:.4f} > {config.max_kl_reject}',
            'approx_kl': approx_kl.item()
        }

    # [EFFICIENCY] Clip importance ratios (PPO-style)
    ratio_clipped = torch.clamp(ratio, 1 - epsilon, 1 + epsilon)

    # Policy gradient with importance weighting
    pg_raw = ratio * advantages.unsqueeze(-1) * policy_logp
    pg_clip = ratio_clipped * advantages.unsqueeze(-1) * policy_logp
    
    # Conservative policy gradient update
    pg_term = torch.min(pg_raw, pg_clip).mean() 
    
    # KL regularization (unchanged from HRPO)
    kl_div = (policy_logp - ref_logp).sum(dim=-1).mean()

    # Combined objective (minimize this)
    total_loss = -pg_term + config.beta * kl_div

    metrics = {
        'status': 'accepted',
        'kl_div': kl_div.item(),
        'approx_kl_old': approx_kl.item(),
        'importance_ratio_mean': ratio.mean().item(),
        'clip_fraction': (ratio != ratio_clipped).float().mean().item(),
        'epsilon': epsilon
    }

    return total_loss, metrics

# ==============================================================================
# 2. [P1] & [P2] Adaptive r_min Controller (Proportional Control + Task Aware)
# ==============================================================================

class TaskAwareAdaptiveRminController:
    """
    [ENHANCED] Task-conditioned r_min adaptation with oscillation control.
    Integrates Patch #2 (Proportional Control) and Patch #5 (Task Awareness).
    """

    def __init__(self, config: HRPOConfig):
        self.config = config
        
        # [Patch #5] Per-task r_min tracking
        self.r_min_per_task = config.default_r_min.copy()
        
        self.task_history: typing.List[typing.Dict] = []
        self.step_count = 0
        
        # [Patch #2] Momentum state
        self.momentum = 0.0
        self.convergence_count = 0
        self.converged = False

    def step(
        self,
        observed_hidden_ratio: float,
        current_query: str
    ) -> typing.Optional[float]:
        """
        Executes one adaptation step.
        """
        self.step_count += 1
        task_type = self._detect_task(current_query)
        
        self.task_history.append({
            'step': self.step_count,
            'task': task_type,
            'hidden_ratio': observed_hidden_ratio
        })

        if self.step_count < self.config.warmup_steps:
            return None

        # [Patch #2] Convergence check
        recent_error = abs(observed_hidden_ratio - self.config.target_hidden_ratio)
        if recent_error < self.config.convergence_threshold:
            self.convergence_count += 1
            if self.convergence_count >= 3:
                self.converged = True
        else:
            self.convergence_count = 0
            self.converged = False

        # Compute per-task statistics (recent window)
        recent = self.task_history[-100:]
        
        # Current task distribution
        recent_tasks = [h['task'] for h in recent]
        if not recent_tasks:
            return None
            
        task_dist = {
            task: recent_tasks.count(task) / len(recent_tasks)
            for task in self.r_min_per_task.keys()
        }

        # Update specific task r_min if we have enough samples
        current_task_samples = [h for h in recent if h['task'] == task_type]
        if len(current_task_samples) >= 5:
             mean_ratio = numpy.mean([h['hidden_ratio'] for h in current_task_samples])
             error = mean_ratio - self.config.target_hidden_ratio
             
             # [Patch #2] Proportional Control
             proportional_delta = -self.config.adaptation_rate * error
             
             # [Patch #2] Momentum
             momentum_delta = 0.9 * self.momentum
             total_delta = 0.7 * proportional_delta + 0.3 * momentum_delta
             self.momentum = total_delta
             
             # Apply bounds
             delta = numpy.clip(total_delta, -self.config.max_single_change, self.config.max_single_change)
             
             # Update
             self.r_min_per_task[task_type] += delta
             self.r_min_per_task[task_type] = numpy.clip(
                 self.r_min_per_task[task_type],
                 *self.config.r_min_range
             )

        # Blend r_min values according to current distribution
        blended_r_min = sum(
            self.r_min_per_task[t] * task_dist.get(t, 0)
            for t in self.r_min_per_task.keys()
        )
        
        # Safe clip just in case
        blended_r_min = numpy.clip(blended_r_min, *self.config.r_min_range)

        return blended_r_min

    def _detect_task(self, query: str) -> str:
        """Heuristic task detection."""
        q = query.lower()
        if any(kw in q for kw in ['who', 'what', 'when', 'where', 'history', 'explain']):
            return 'knowledge'
        elif any(kw in q for kw in ['calculate', 'solve', 'prove', 'math', 'code', 'python']):
            return 'stem'
        else:
            return 'general'

# ==============================================================================
# 3. [P0] Distributional Ghost Mode (Adaptive Sampling + Bootstrap CI)
# ==============================================================================

class DistributionalGhostMode:
    """
    [ENHANCED] Ghost Mode with adaptive sampling and statistical guarantees.
    """
    def __init__(self, config: HRPOConfig):
        self.config = config
        self.baseline_metrics: typing.List[typing.Dict] = []
        self.candidate_metrics: typing.List[typing.Dict] = []

    def add_sample(self, baseline_m: Dict, candidate_m: Dict):
        self.baseline_metrics.append(baseline_m)
        self.candidate_metrics.append(candidate_m)

    def run_test(self) -> typing.Tuple[bool, typing.Dict]:
        """
        Runs the ghost mode validation.
        """
        if len(self.candidate_metrics) < self.config.ghost_min_samples:
            return False, {'status': 'insufficient_samples', 'count': len(self.candidate_metrics)}

        # [Patch #3] Bootstrap Confidence Interval for KL
        kl_stats = self._bootstrap_kl_confidence()
        
        # Check 1: Error Rate
        errors = sum(1 for m in self.candidate_metrics if m.get('error', False))
        error_rate = errors / len(self.candidate_metrics)
        pass_error = error_rate < self.config.error_rate_threshold

        # Check 2: Reward KL (using CI upper bound)
        pass_kl = kl_stats['ci_high'] < self.config.reward_kl_threshold

        # Check 3: Length Variance
        b_len = [m['length'] for m in self.baseline_metrics]
        c_len = [m['length'] for m in self.candidate_metrics]
        ratio = numpy.std(c_len) / (numpy.std(b_len) + 1e-8)
        pass_var = 0.5 <= ratio <= 2.0

        # Overall
        passed = pass_error and pass_kl and pass_var
        
        return passed, {
            'error_rate': float(error_rate),
            'reward_kl_mean': float(kl_stats['mean']),
            'reward_kl_ci_high': float(kl_stats['ci_high']),
            'len_var_ratio': float(ratio),
            'passed': bool(passed)
        }

    def _bootstrap_kl_confidence(self, n_bootstrap: int = 1000) -> Dict:
        """Bootstrap confidence interval for KL divergence."""
        baseline_rewards = [m['reward'] for m in self.baseline_metrics]
        candidate_rewards = [m['reward'] for m in self.candidate_metrics]
        
        if not baseline_rewards or not candidate_rewards:
             return {'mean': 1.0, 'ci_high': 1.0}

        kl_samples = []
        for _ in range(n_bootstrap):
            # Resample with replacement
            b_boot = numpy.random.choice(baseline_rewards, size=len(baseline_rewards))
            c_boot = numpy.random.choice(candidate_rewards, size=len(candidate_rewards))
            
            kl = self._compute_kl_divergence(b_boot, c_boot)
            kl_samples.append(kl)

        ci_high = numpy.percentile(kl_samples, 99.5)
        return {
            'mean': numpy.mean(kl_samples),
            'ci_high': ci_high
        }

    def _compute_kl_divergence(self, p_samples, q_samples, bins=20) -> float:
        """Simple histogram-based KL divergence."""
        min_val = min(min(p_samples), min(q_samples))
        max_val = max(max(p_samples), max(q_samples))
        
        p_hist, _ = numpy.histogram(p_samples, bins=bins, range=(min_val, max_val), density=True)
        q_hist, _ = numpy.histogram(q_samples, bins=bins, range=(min_val, max_val), density=True)
        
        # Smooth to avoid inf
        p_hist = p_hist + 1e-8
        q_hist = q_hist + 1e-8
        
        # Normalize again
        p_hist /= p_hist.sum()
        q_hist /= q_hist.sum()
        
        return numpy.sum(p_hist * numpy.log(p_hist / q_hist))

# ==============================================================================
# 4. [P0] Network Partition Handling (simulated hash coordination)
# ==============================================================================

class PolicyHashManager:
    """
    [ENHANCED] Simulated hash coordination (single-process).
    Simulated implementation (Redis replaced with internal state for demo).
    """

    def __init__(self, broadcast_timeout: float = 5.0):
        self.broadcast_timeout = broadcast_timeout
        self.current_hash = "GENESIS_HASH"
        self.history = ["GENESIS_HASH"]
        self.stale_workers = set()
        
        # Simulated worker state
        self.worker_acks = {}

    def update_hash(self, new_hash: str):
        self.history.append(new_hash)
        self.current_hash = new_hash
        self.worker_acks = {} # Reset ACKs

    def receive_ack(self, worker_id: str, hash_val: str):
        self.worker_acks[worker_id] = hash_val

    def check_partition_health(self, active_workers: typing.List[str]) -> typing.List[str]:
        """
        Identify workers that haven't ACKed the current hash.
        """
        failed = []
        for w in active_workers:
            if self.worker_acks.get(w) != self.current_hash:
                failed.append(w)
                self.stale_workers.add(w)
        
        if failed:
            logger.warning(f"Workers failed to ACK hash {self.current_hash[:8]}: {failed}")
        return failed

    def validate_trajectory(self, trajectory_hash: str, worker_id: str) -> typing.Tuple[bool, str]:
        """
        Validate trajectory with grace period for stale workers.
        """
        # [Grace Period]
        if worker_id in self.stale_workers:
            self.stale_workers.remove(worker_id)
            logger.warning(f"Worker {worker_id} grace period: accepting trajectory")
            return True, "grace_period"

        if trajectory_hash == self.current_hash:
            return True, "current"
        
        # Check lag
        try:
            lag = len(self.history) - 1 - self.history.index(trajectory_hash)
        except ValueError:
            return False, "unknown_hash"

        if lag <= 3:
            return True, f"lagged_k={lag}"
        else:
            return False, f"too_stale_k={lag}"

# ==============================================================================
# 5. Paper Alignment Demo (clean-room)
# ==============================================================================

def paper_alignment_demo(
    config: typing.Optional[paper_core.PaperHRPOConfig] = None,
    group_size: int = 3,
    seq_len: int = 5,
    vocab: int = 16,
    dim: int = 8,
) -> typing.Dict[str, float]:
    """
    Demonstrate paper-aligned primitives (Eq.3/4/6) in a clean-room way.
    This is a demo only and does not implement a full training pipeline.
    """
    torch.manual_seed(0)
    cfg = config or paper_core.PaperHRPOConfig()

    embedding = torch.randn(vocab, dim)
    logits = torch.randn(group_size, seq_len, vocab)
    probs = F.softmax(logits, dim=-1)
    token_ids = torch.argmax(probs, dim=-1)
    e_hat = embedding[token_ids]

    h_proj, _ = paper_core.project_hidden_to_embedding(logits, embedding, tau=cfg.tau, eps=cfg.eps)

    w_a = torch.randn(dim, dim)
    b_a = torch.randn(dim)
    w_x = torch.randn(dim, dim)
    b_x = torch.randn(dim)
    lambda_vec = torch.randn(dim)

    think_mask = torch.zeros(group_size, seq_len, dtype=torch.bool)
    think_mask[:, :-1] = True

    e_next, gates = paper_core.hybrid_gating_step(
        e_hat,
        h_proj,
        w_a,
        b_a,
        w_x,
        b_x,
        lambda_vec,
        c=cfg.c,
        think_mask=think_mask,
    )

    logp = F.log_softmax(logits, dim=-1).gather(-1, token_ids.unsqueeze(-1)).squeeze(-1)
    ref_logits = torch.randn(group_size, seq_len, vocab)
    ref_logp = F.log_softmax(ref_logits, dim=-1).gather(-1, token_ids.unsqueeze(-1)).squeeze(-1)

    rewards = torch.linspace(0.0, 1.0, steps=group_size)
    token_mask = torch.zeros(group_size, seq_len, dtype=torch.bool)
    token_mask[:, -2:] = True

    loss, metrics = paper_core.hrpo_loss(
        logp,
        rewards,
        ref_logp,
        beta=cfg.beta,
        eps=cfg.eps,
        token_mask=token_mask,
    )

    metrics.update(
        {
            "gate_a_mean": float(gates["a_t"].mean().item()),
            "gate_r_mean": float(gates["r_t"].mean().item()),
            "gate_i_mean": float(gates["i_t"].mean().item()),
            "e_next_mean": float(e_next.mean().item()),
            "loss": float(loss.item()),
        }
    )
    return metrics

# ==============================================================================
# Main Execution / Demo
# ==============================================================================

def main():
    logger.info("Initializing HRPO-X v1.0.0 Core...")
    config = HRPOConfig()
    
    # 1. Controller Demo
    rmin_controller = TaskAwareAdaptiveRminController(config)
    
    logger.info("--- Testing Adaptive r_min Controller ---")
    # Simulate Knowledge Task (needs high r_min)
    for i in range(110):
        # Warmup phase
        obs_ratio = 0.12 # Low latent usage
        new_rmin = rmin_controller.step(obs_ratio, "Who is the president?")
        if i % 20 == 0:
            logger.info(f"Step {i}: r_min = {new_rmin}")

    # 2. Ghost Mode Demo
    ghost = DistributionalGhostMode(config)
    logger.info("\n--- Testing Ghost Mode ---")
    
    # Simulate some data
    for _ in range(300):
        b_m = {'reward': numpy.random.normal(0.5, 0.1), 'length': 100, 'error': False}
        c_m = {'reward': numpy.random.normal(0.55, 0.1), 'length': 105, 'error': False}
        ghost.add_sample(b_m, c_m)
        
    passed, res = ghost.run_test()
    logger.info(f"Ghost Mode Result: {passed}")
    logger.info(json.dumps(res, indent=2))

    # 3. Hash Manager Demo
    hash_mgr = PolicyHashManager()
    logger.info("\n--- Testing Hash Coordination (simulated) ---")
    
    hash_mgr.update_hash("HASH_V1")
    hash_mgr.receive_ack("worker_1", "HASH_V1")
    # worker_2 fails to ACK
    
    failed = hash_mgr.check_partition_health(["worker_1", "worker_2"])
    logger.info(f"Failed workers: {failed}")
    
    # Worker 2 sends trajectory with old hash (simulated)
    valid, reason = hash_mgr.validate_trajectory("GENESIS_HASH", "worker_2")
    logger.info(f"Worker 2 Trajectory Validation: {valid} ({reason})")

    # 4. Paper Alignment Demo (clean-room)
    logger.info("\n--- Paper Alignment Demo (clean-room) ---")
    paper_metrics = paper_alignment_demo()
    logger.info(json.dumps(paper_metrics, indent=2))

    logger.info("\nHRPO-X v1.0.0 System Ready.")

if __name__ == "__main__":
    main()
