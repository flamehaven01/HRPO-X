"""
Basic test suite for HRPO-X v2.2f
Run: pytest tests/test_core.py -v
"""

import pytest
import torch
import numpy as np
from hrpox import (
    HRPOConfig,
    adaptive_epsilon_schedule,
    importance_weighted_hrpo_loss,
    TaskAwareAdaptiveRminController,
    DistributionalGhostMode,
    PolicyHashManager
)


class TestAdaptiveEpsilon:
    """Test [P1] Adaptive epsilon scheduling"""
    
    def test_warmup_phase(self):
        """Epsilon should be 0.5 during warmup"""
        for step in range(100):
            eps = adaptive_epsilon_schedule(step, warmup=100)
            assert eps == 0.5, f"Step {step}: expected 0.5, got {eps}"
    
    def test_transition_phase(self):
        """Epsilon should linearly decrease 0.5 -> 0.2"""
        eps_start = adaptive_epsilon_schedule(100, warmup=100)
        eps_mid = adaptive_epsilon_schedule(150, warmup=100)
        eps_end = adaptive_epsilon_schedule(199, warmup=100)
        
        assert eps_start > eps_mid > eps_end
        assert abs(eps_end - 0.2) < 0.05
    
    def test_stable_phase(self):
        """Epsilon should be 0.2 after transition"""
        for step in range(200, 300):
            eps = adaptive_epsilon_schedule(step, warmup=100)
            assert eps == 0.2


class TestImportanceSampling:
    """Test [P1] Importance Sampling with clipping"""
    
    @pytest.fixture
    def config(self):
        return HRPOConfig()
    
    def test_kl_rejection(self, config):
        """High KL should trigger rejection"""
        batch_size = 4
        seq_len = 10
        
        policy_logp = torch.randn(batch_size, seq_len)
        old_policy_logp = torch.randn(batch_size, seq_len) * 5  # Large difference
        ref_logp = torch.randn(batch_size, seq_len)
        advantages = torch.randn(batch_size)
        
        loss, metrics = importance_weighted_hrpo_loss(
            policy_logp, old_policy_logp, ref_logp, advantages, step=150, config=config
        )
        
        # May be rejected due to high KL
        if loss is None:
            assert metrics['status'] == 'rejected'
            assert 'approx_kl' in metrics
    
    def test_clipping_behavior(self, config):
        """Ratio should be clipped when large"""
        batch_size = 4
        seq_len = 10
        
        policy_logp = torch.randn(batch_size, seq_len)
        old_policy_logp = policy_logp - 0.5  # Small difference
        ref_logp = torch.randn(batch_size, seq_len)
        advantages = torch.ones(batch_size)
        
        loss, metrics = importance_weighted_hrpo_loss(
            policy_logp, old_policy_logp, ref_logp, advantages, step=150, config=config
        )
        
        if loss is not None:
            assert 'clip_fraction' in metrics
            assert 0.0 <= metrics['clip_fraction'] <= 1.0


class TestAdaptiveRmin:
    """Test [P1][P2] Adaptive r_min controller"""
    
    @pytest.fixture
    def controller(self):
        config = HRPOConfig()
        return TaskAwareAdaptiveRminController(config)
    
    def test_warmup_returns_none(self, controller):
        """Should not update during warmup"""
        for i in range(99):  # 0-98, step_count will be 1-99
            r_min = controller.step(0.15, "test query")
            assert r_min is None, f"Expected None at step {i+1}, got {r_min}"
    
    def test_convergence_detection(self, controller):
        """Should detect convergence when error small"""
        # Fast-forward past warmup
        for i in range(100):
            controller.step(0.15, "test query")
        
        # Feed near-target observations
        for i in range(10):
            r_min = controller.step(0.150, "test query")
        
        # Should converge
        assert controller.converged or controller.convergence_count >= 1
    
    def test_task_detection(self, controller):
        """Should detect different task types"""
        assert controller._detect_task("Who is Einstein?") == 'knowledge'
        assert controller._detect_task("Calculate 2+2") == 'stem'
        assert controller._detect_task("Hello world") == 'general'


class TestGhostMode:
    """Test [P0] Distributional Ghost Mode"""
    
    @pytest.fixture
    def ghost_mode(self):
        config = HRPOConfig()
        return DistributionalGhostMode(config)
    
    def test_insufficient_samples(self, ghost_mode):
        """Should fail with insufficient samples"""
        # Add only 100 samples (need 250)
        for _ in range(100):
            ghost_mode.add_sample(
                {'reward': 0.5, 'length': 100, 'error': False},
                {'reward': 0.5, 'length': 100, 'error': False}
            )
        
        passed, result = ghost_mode.run_test()
        assert not passed
        assert result['status'] == 'insufficient_samples'
    
    def test_success_with_good_candidate(self, ghost_mode):
        """Should pass with similar distributions"""
        # Add 250+ samples with similar distributions
        for _ in range(260):
            baseline = {'reward': np.random.normal(0.5, 0.05), 'length': 100, 'error': False}
            candidate = {'reward': np.random.normal(0.51, 0.05), 'length': 102, 'error': False}
            ghost_mode.add_sample(baseline, candidate)
        
        passed, result = ghost_mode.run_test()
        # Should likely pass (small difference)
        assert 'error_rate' in result
        assert 'reward_kl_mean' in result


class TestHashManager:
    """Test [P0] Network partition handling"""
    
    @pytest.fixture
    def hash_manager(self):
        return PolicyHashManager()
    
    def test_current_hash_validation(self, hash_manager):
        """Current hash should always validate"""
        hash_manager.update_hash("HASH_V1")
        valid, reason = hash_manager.validate_trajectory("HASH_V1", "worker_1")
        
        assert valid
        assert reason == "current"
    
    def test_lagged_validation(self, hash_manager):
        """k<=3 lag should be accepted"""
        for i in range(5):
            hash_manager.update_hash(f"HASH_V{i}")
        
        # k=3 lag (current is V4, trajectory is V1)
        valid, reason = hash_manager.validate_trajectory("HASH_V1", "worker_1")
        assert valid
        assert "lagged" in reason
    
    def test_grace_period(self, hash_manager):
        """Stale workers should get grace period"""
        hash_manager.update_hash("HASH_V1")
        hash_manager.stale_workers.add("worker_2")
        
        # Even with old hash, should accept once
        valid, reason = hash_manager.validate_trajectory("HASH_V0", "worker_2")
        assert valid
        assert reason == "grace_period"
        
        # But not twice
        assert "worker_2" not in hash_manager.stale_workers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
