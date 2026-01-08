# PAPER_TO_CODE_MAP (HRPO-X)

## Source
- Paper notes: local file (hlr.txt) in the Flamehaven research library (path contains non-ASCII)
- Codebase: D:\Sanctum\HRPO-X
- Mode: Offline, clean-room mapping (no external code reuse)

## Scope
This document maps paper requirements to HRPO-X and identifies gaps. It does not
copy external code. It is a planning and verification artifact only.

## Paper -> HRPO-X Mapping

### Eq(3): Hidden state projection to embedding space
Paper (hlr.txt):
- p_{t+1} = softmax(Head(h_hat_t) / tau)
- h_{t+1} = W_e^T p_{t+1} / ||p_{t+1}||

HRPO-X:
- Status: IMPLEMENTED (core + mini + full trainer scaffold)
- Location: hrpox/paper_core.py::project_hidden_to_embedding
- Pipelines:
  - hrpox/paper_pipeline.py::MiniHRPOTrainer.rollout_group uses the projection.
  - hrpox/paper_trainer.py::PaperHRPOTrainer._rollout_group uses the projection.

### Eq(4): Hybrid gating mechanism (think span only)
Paper (hlr.txt):
- r_t = sigmoid(W_a e_hat_{t+1} + b_a)
- i_t = sigmoid(W_x e_hat_{t+1} + b_x)
- a_t = exp(-c * softplus(Lambda) * r_t)
- e_{t+1} = a_t * e_hat_{t+1} + (1 - a_t^2) * (i_t * h_{t+1}) for think span
- e_{t+1} = e_hat_{t+1} outside think span

HRPO-X:
- Status: IMPLEMENTED (core + mini + full trainer scaffold)
- Location: hrpox/paper_core.py::hybrid_gating_step
- Pipelines:
  - hrpox/paper_pipeline.py::MiniHRPOTrainer.rollout_group applies think-span masking.
  - hrpox/paper_trainer.py::PaperHRPOTrainer._rollout_group applies think-span masking.

### Eq(6): HRPO objective (on-policy, group-standardized rewards)
Paper (hlr.txt):
- Group rollouts per input; standardize rewards within group
- Use KL(pi_theta || pi_ref) regularization
- Explicitly avoid importance sampling / ratio clipping (on-policy)

HRPO-X:
- Status: IMPLEMENTED (mini + full trainer scaffold)
- Current: hrpox/paper_core.py::hrpo_loss implements the paper-style objective
  without ratio/IS.
- Pipelines:
  - hrpox/paper_pipeline.py::MiniHRPOTrainer.train_step uses hrpo_loss with a token mask.
  - hrpox/paper_trainer.py::PaperHRPOTrainer.train_step uses hrpo_loss with a token mask.

### Rollout design
Paper (hlr.txt):
- Hybrid rollouts combine discrete tokens + latent features via gating
- Outcome-based reward in answer span

HRPO-X:
- Status: IMPLEMENTED (mini + full trainer scaffold)
- Locations:
  - hrpox/paper_pipeline.py::MiniHRPOTrainer.rollout_group
  - hrpox/paper_trainer.py::PaperHRPOTrainer._rollout_group
- Notes: ToyPolicy and small vocab; demo-scale only.

## HRPO-X Existing Components (Non-paper additions)
- Adaptive epsilon schedule
- r_min controller
- Ghost mode validation
- Hash manager

These are not part of the paper core and should be treated as optional extensions.

## Minimum Steps for Paper Alignment (Clean-room)
1) Implement Eq(3) projection module - DONE (core + mini + full trainer scaffold)
2) Implement Eq(4) gating module with think span control - DONE (core + mini + full trainer scaffold)
3) Replace IS loss with paper-style HRPO loss (no ratio) - DONE (core + mini + full trainer scaffold)
4) Add group rollout + standardized reward computation - DONE (mini + full trainer scaffold)
5) Add tests for Eq(3), Eq(4), Eq(6) - DONE (tests/test_paper_core.py,
   tests/test_paper_pipeline.py, tests/test_paper_trainer.py)

## Validation Checklist
- Eq(3): projection output shape, normalization, tau parameter (tests/test_paper_core.py)
- Eq(4): gating value ranges and think span behavior (tests/test_paper_core.py)
- Eq(6): no ratio usage, KL term present, reward standardization
  (tests/test_paper_core.py, tests/test_paper_pipeline.py, tests/test_paper_trainer.py)
- End-to-end: hybrid rollouts used in loss computation
  (tests/test_paper_pipeline.py, tests/test_paper_trainer.py)

## Status
- Paper alignment: PARTIAL (full trainer scaffold is demo-scale)
- Prototype alignment: OK
