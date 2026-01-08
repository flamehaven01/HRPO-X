from hrpox.core_v2_2 import paper_alignment_demo


def test_paper_alignment_demo_metrics():
    metrics = paper_alignment_demo()
    required = {
        "loss",
        "pg_loss",
        "kl",
        "reward_mean",
        "reward_std",
        "beta",
        "gate_a_mean",
        "gate_r_mean",
        "gate_i_mean",
        "e_next_mean",
    }
    assert required.issubset(metrics.keys())
