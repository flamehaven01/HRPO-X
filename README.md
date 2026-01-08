# HRPO-X (Research Prototype)

HRPO-X is a research prototype with:
- prototype utilities in `hrpo_core_v2_2.py`
- clean-room paper primitives (Eq3/Eq4/Eq6) in `hrpo_paper_core.py`
- demo-scale pipelines in `hrpo_paper_pipeline.py` and `hrpo_paper_trainer.py`

This is not production software and does not claim full paper compliance.

---

## Scope

Included:
- importance sampling loss with adaptive epsilon
- adaptive r_min controller
- ghost mode validation
- hash-based coordination (simulated)
- paper-aligned projection, gating, and loss primitives
- mini pipeline + trainer scaffold

Not included:
- production training system
- distributed rollout workers
- monitoring or deployment tooling
- full paper reproduction

---

## Quick Start

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Unix: source venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

Run demos:

```bash
python hrpo_core_v2_2.py
python examples/simple_demo.py
```

---

## Structure

```
hrpo-x/
├── hrpo_core_v2_2.py
├── hrpo_paper_core.py
├── hrpo_paper_pipeline.py
├── hrpo_paper_trainer.py
├── hrpox/
├── tests/
└── docs/
```

---

## Limitations

- demo-scale pipelines only
- simulated distributed coordination
- no production infrastructure
- clean-room alignment for core equations only

---

## License

MIT. See `LICENSE`.
