# HRPO-X (Research Prototype)

HRPO-X is a research prototype with:
- prototype utilities in `hrpox/core_v2_2.py`
- clean-room paper primitives (Eq3/Eq4/Eq6) in `hrpox/paper_core.py`
- demo-scale pipelines in `hrpox/paper_pipeline.py` and `hrpox/paper_trainer.py`

This is not production software and does not claim full paper compliance.

Roadmap: see `roadmap.md`.

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
python -m hrpox
python examples/simple_demo.py
```

---

## Structure

```
hrpo-x/
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
