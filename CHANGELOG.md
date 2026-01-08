# Changelog

All notable changes to HRPO-X will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-01-08

### Changed - Honesty Refactoring

This release removes exaggerated claims and aligns documentation with actual implementation.

**Documentation Updates:**
- Rewrote docs/ARCHITECTURE.md to match the single-file prototype
- Rewrote SECURITY.md with prototype-safe scope
- Updated setup_and_verify.py instructions and removed training references
- Aligned hrpo_core_v2_2.py and hrpox/__init__.py headers with prototype status

**File Cleanup:**
- Removed k8s/ directory (aspirational, not implemented)
- Removed monitoring/ directory (aspirational, not implemented)
- Removed docker-compose.yml (aspirational, not implemented)
- Removed Dockerfile and .dockerignore (no container support)
- Removed docs/HRPO-X_Production_Hardening.pdf (22MB of unverified content)
- Removed docs/EVIDENCE_TRAIL.md (contained unverified claims)
- Removed scripts/deploy-k8s.sh (not functional)
- Removed scripts/train.sh and scripts/evaluate.sh (no training modules)
- Removed requirements-llm.txt and requirements-monitoring.txt (unused)

**Added:**
- examples/simple_demo.py - Working demonstrations of all components
  - Demo 1: Adaptive Epsilon Scheduling
  - Demo 2: Importance Sampling Loss
  - Demo 3: Adaptive r_min Controller
  - Demo 4: Ghost Mode Validation
  - Demo 5: Realistic Workflow

**Verified:**
- All 13 unit tests still pass
- Core implementation (hrpo_core_v2_2.py) unchanged and functional
- Package imports work correctly

### Status

**What Works:**
- ✓ Adaptive epsilon scheduling (warmup 0.5 → 0.2)
- ✓ Importance sampling with KL rejection
- ✓ Task-aware adaptive r_min controller
- ✓ Bootstrap confidence interval validation
- ✓ Simulated hash-based coordination

**What Doesn't:**
- ❌ Distributed training infrastructure (simulated only)
- ❌ Production deployment (K8s, monitoring removed)
- ❌ "Golden Core" architecture (single file implementation)
- ❌ Paper compliance verification (unverified claims removed)

---

## [1.0.0] - 2026-01-06

### Initial Release

**Note:** This version contained significant exaggerations and unverified claims.
See v1.0.1 for honest documentation.

**Core Implementation:** hrpo_core_v2_2.py (463 lines)
- HRPOConfig
- adaptive_epsilon_schedule()
- importance_weighted_hrpo_loss()
- TaskAwareAdaptiveRminController
- DistributionalGhostMode
- PolicyHashManager

**Tests:** 13 unit tests in tests/test_core.py

**Exaggerated Claims (Removed in v1.0.1):**
- "NeurIPS 2025 Spotlight" - Not verified
- "96% test coverage" - Actually 13 tests
- "Production Ready" - Research prototype
- "Byzantine Fault Tolerant" - Simulated only

---

## Summary

**v1.0.0:** Over-promised, under-documented reality
**v1.0.1:** Honest documentation matching actual implementation

The core algorithm remains unchanged and functional across both versions.
Only documentation and cleanup were changed in v1.0.1.
