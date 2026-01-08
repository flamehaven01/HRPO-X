"""
HRPO-X Simple Demo
==================
Demonstrates actual usage without buzzwords.
"""

import pathlib
import sys

# Add parent directory to path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import numpy
import torch

import hrpox


def demo_1_adaptive_epsilon():
    """Demo: Adaptive epsilon scheduling for importance sampling"""
    print("\n=== Demo 1: Adaptive Epsilon Scheduling ===")

    for step in [0, 50, 100, 150, 200, 250]:
        epsilon = hrpox.adaptive_epsilon_schedule(step, warmup=100)
        print(f"Step {step:3d}: epsilon = {epsilon:.3f}")

    print("\nExplanation:")
    print("- Steps 0-100:   epsilon = 0.5 (loose clipping for cold start)")
    print("- Steps 100-200: epsilon decreases linearly 0.5 -> 0.2")
    print("- Steps 200+:    epsilon = 0.2 (standard PPO)")


def demo_2_importance_sampling():
    """Demo: Importance sampling with KL rejection"""
    print("\n=== Demo 2: Importance Sampling Loss ===")

    config = hrpox.HRPOConfig()
    batch_size, seq_len = 4, 10

    # Simulate policy outputs
    policy_logp = torch.randn(batch_size, seq_len) * 0.1
    old_policy_logp = policy_logp + torch.randn(batch_size, seq_len) * 0.05
    ref_logp = torch.randn(batch_size, seq_len) * 0.1
    advantages = torch.randn(batch_size)

    loss, metrics = hrpox.importance_weighted_hrpo_loss(
        policy_logp, old_policy_logp, ref_logp, advantages,
        step=150, config=config
    )

    if loss is not None:
        print(f"Loss: {loss.item():.4f}")
        print(f"Metrics:")
        for k, v in metrics.items():
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
    else:
        print(f"REJECTED: {metrics['reason']}")

    print("\nExplanation:")
    print("- Computes importance ratio: rho = pi_new / pi_old")
    print("- Clips ratio for stability (PPO-style)")
    print("- Rejects if KL divergence too high (safety)")


def demo_3_adaptive_controller():
    """Demo: Task-aware adaptive r_min controller"""
    print("\n=== Demo 3: Adaptive r_min Controller ===")

    config = hrpox.HRPOConfig()
    controller = hrpox.TaskAwareAdaptiveRminController(config)

    # Simulate warmup
    print("Warmup phase (returns None):")
    for i in range(5):
        r_min = controller.step(0.15, "test query")
        print(f"  Step {i}: r_min = {r_min}")

    # Fast-forward past warmup
    for _ in range(95):
        controller.step(0.15, "dummy")

    # Simulate different task types
    print("\nAfter warmup (adapts based on task):")
    tasks = [
        ("What is Python?", "knowledge", 0.12),
        ("Calculate 2+2", "stem", 0.18),
        ("Hello world", "general", 0.15),
    ]

    for query, expected_type, ratio in tasks:
        r_min = controller.step(ratio, query)
        detected = controller._detect_task(query)
        print(f"  '{query}'")
        print(f"    Detected: {detected}, r_min: {r_min:.4f}")

    print("\nExplanation:")
    print("- Detects task type from query keywords")
    print("- Maintains separate r_min for each task type")
    print("- Adapts threshold based on observed latent usage")


def demo_4_ghost_mode():
    """Demo: Statistical validation with bootstrap CI"""
    print("\n=== Demo 4: Ghost Mode Validation ===")

    config = hrpox.HRPOConfig()
    ghost = hrpox.DistributionalGhostMode(config)

    print(f"Collecting {config.ghost_min_samples} samples...")

    # Simulate baseline and candidate metrics
    numpy.random.seed(42)
    for i in range(260):
        baseline = {
            'reward': numpy.random.normal(0.5, 0.05),
            'length': 100,
            'error': False
        }
        candidate = {
            'reward': numpy.random.normal(0.51, 0.05),  # Slightly better
            'length': 102,
            'error': False
        }
        ghost.add_sample(baseline, candidate)

    passed, results = ghost.run_test()

    print(f"\nValidation Result: {'PASS' if passed else 'FAIL'}")
    print(f"Metrics:")
    for k, v in results.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

    print("\nExplanation:")
    print("- Compares candidate vs baseline with 4 metrics")
    print("- Uses bootstrap for confidence intervals")
    print("- Ensures statistical safety before deployment")


def demo_5_realistic_workflow():
    """Demo: Realistic training workflow simulation"""
    print("\n=== Demo 5: Realistic Workflow ===")

    config = hrpox.HRPOConfig()
    controller = hrpox.TaskAwareAdaptiveRminController(config)

    # Warmup
    for _ in range(100):
        controller.step(0.15, "warmup")

    print("Simulating 10 training steps:\n")

    for step in range(10):
        # 1. Get epsilon for this step
        epsilon = hrpox.adaptive_epsilon_schedule(step + 100)

        # 2. Simulate policy outputs
        policy_logp = torch.randn(2, 5) * 0.1
        old_policy_logp = policy_logp + torch.randn(2, 5) * 0.02
        ref_logp = torch.randn(2, 5) * 0.1
        advantages = torch.randn(2)

        # 3. Compute loss with IS
        loss, metrics = hrpox.importance_weighted_hrpo_loss(
            policy_logp, old_policy_logp, ref_logp, advantages,
            step=step + 100, config=config
        )

        # 4. Update r_min based on observation
        observed_ratio = numpy.random.uniform(0.12, 0.18)
        r_min = controller.step(observed_ratio, "Calculate the derivative")

        # 5. Log
        if loss is not None:
            print(f"Step {step:2d}: loss={loss.item():.4f}, "
                  f"epsilon={epsilon:.3f}, r_min={r_min:.4f}, "
                  f"ratio={metrics['importance_ratio_mean']:.3f}")
        else:
            print(f"Step {step:2d}: REJECTED (KL too high)")

    print("\nExplanation:")
    print("- This is what actual usage looks like")
    print("- No K8s, no Byzantine FT, just algorithm components")
    print("- Can be integrated into any PyTorch training loop")


if __name__ == "__main__":
    print("=" * 60)
    print("HRPO-X Simple Demonstrations")
    print("No buzzwords, just working code")
    print("=" * 60)

    demo_1_adaptive_epsilon()
    demo_2_importance_sampling()
    demo_3_adaptive_controller()
    demo_4_ghost_mode()
    demo_5_realistic_workflow()

    print("\n" + "=" * 60)
    print("All demos complete!")
    print("See hrpo_core_v2_2.py for implementation details")
    print("=" * 60)
