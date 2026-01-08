# HRPO-X Architecture (Research Prototype)

## Summary
HRPO-X is a research prototype that implements a small set of HRPO-inspired
components plus a clean-room paper alignment scaffold. It is not a production
system and does not include distributed training, monitoring, or deployment
tooling.

## Actual Structure

```
hrpo-x/
|-- hrpo_core_v2_2.py        # Core implementation (prototype utilities)
|-- hrpo_paper_core.py       # Clean-room paper primitives (Eq3, Eq4, Eq6)
|-- hrpo_paper_pipeline.py   # Mini pipeline demo
|-- hrpo_paper_trainer.py    # Full trainer scaffold (rollouts, rewards, buffer)
|-- hrpox/
|   `-- __init__.py          # Convenience re-exports
|-- examples/
|   `-- simple_demo.py       # Runnable demos
|-- tests/
|   |-- test_core.py         # Prototype unit tests
|   |-- test_paper_core.py   # Paper primitive tests
|   |-- test_paper_pipeline.py
|   `-- test_paper_trainer.py
|-- core/
|   |-- integrity.py         # Optional numerical checks
|   `-- validators.py        # Optional equation validators
|-- extensions/
|   `-- validators.py        # Optional patch validators
`-- docs/
    `-- ARCHITECTURE.md
```

## Components

1. adaptive_epsilon_schedule
   - Warmup schedule for PPO-style clipping (0.5 -> 0.2)
2. importance_weighted_hrpo_loss
   - Importance sampling with KL rejection
3. TaskAwareAdaptiveRminController
   - Simple task detection + proportional control
4. DistributionalGhostMode
   - Bootstrap CI checks for candidate vs baseline
5. PolicyHashManager
   - Simulated, in-memory hash coordination (no networking)
6. Paper primitives (Eq3/Eq4/Eq6)
   - Hidden projection, hybrid gating, HRPO loss
7. Paper trainer scaffold
   - Rollout buffer, reward evaluators, on-policy updates

## Typical Flow (Single Process)

1. Compute epsilon for the current step
2. Compute the IS-weighted loss
3. Update r_min based on observed hidden ratio
4. Optionally run ghost-mode validation on samples
5. Optional paper-aligned rollouts and HRPO updates (toy scale)

## Not Implemented

- Distributed rollout workers
- Real network coordination or Byzantine fault tolerance
- Monitoring pipelines (Prometheus/Grafana)
- Deployment artifacts (Docker/K8s)
