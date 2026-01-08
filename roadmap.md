# HRPO-X Roadmap (Paper -> 100% Production)

This roadmap starts from the current committed baseline and targets full productionization of the paper.

---

## Current Baseline (DONE)

- Clean-room paper primitives (Eq3/Eq4/Eq6)
- Mini pipeline + trainer scaffold
- Tests and documentation

---

## Paper-Ideal Targets for 1-2-3

These are the ideal values explicitly reported in the paper and should be treated as the target defaults.

### 1) Rollout (Hybrid completions per query)
- Group size g: 4 for simpler tasks (knowledge, GSM8k)
- Group size g: 8 for harder tasks (MATH, MMLU-ST, ARC-C)
- Total train batch size: 32 / 64
- Prompt / completion lengths (Table 5):
  - Knowledge tasks: 2048 / 512
  - GSM8k: 512 / 512

### 2) Think Span (Hybrid gating initialization)
- Gating constant c: 8
- Lambda initialization: ac = exp(-c * softplus(Lambda)) sampled uniformly from [rmin, 0.999]
- rmin controls initial hidden ratio (larger rmin -> more token embeddings early)
- Temperature tau in Eq(3): tuned per task (paper notes robustness across a wide range)

### 3) Reward Standardization + HRPO Objective
- HRPO beta: 0.005
- Optimizer: AdamW 8bit
- Weight decay: 0.1
- Max gradient norm: 0.1
- Gradient accumulation: 4
- LR scheduler: cosine with warmup
- Warmup ratio: 0.1
- Precision: BF16-mixed
- LoRA modules: query, key, value, dense
- LoRA rank: 32
- LoRA alpha: 64

---

## Phase 1: Paper-Exact Training Loop (Research Grade)

Goal: 1:1 reproducibility using the paper defaults above.

Tasks:
- Integrate with a real LLM policy/head/embedding
- Implement full hybrid rollout buffer using the paper defaults
- Implement think span boundaries and gating initialization per paper
- Use outcome-based reward with group standardization
- Validate against at least one paper benchmark with comparable metrics

Exit criteria:
- Paper default hyperparameters run end-to-end
- Reproducible training run with documented metrics

---

## Phase 2: Reproducibility & Evaluation

Goal: reproducible results with a fixed protocol.

Tasks:
- Experiment harness (configs, seeds, logs)
- Evaluation pipeline (metrics, plots, regressions)
- Standard report format for paper-vs-implementation deltas

Exit criteria:
- Repeatable results within tolerance
- Automated evaluation reports

---

## Phase 3: Productionization

Goal: 100% productionization of the paper implementation.

Tasks:
- Distributed rollout workers + fault tolerance
- Monitoring, alerting, and drift detection
- Deployment packaging (API/CLI/service)
- Cost, performance, and reliability controls

Exit criteria:
- Production-ready training + inference workflow
- End-to-end stability, observability, and rollback

---

## Notes

- This roadmap assumes paper defaults as the target for 1-2-3.
- Any deviation from the defaults should be explicitly documented.
