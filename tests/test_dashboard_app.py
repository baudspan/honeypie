"""Smoke tests for the Streamlit dashboard (skipped if Streamlit is not installed)."""
import pathlib

import pytest

APP = str(pathlib.Path(__file__).resolve().parent.parent / "app.py")

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest  # noqa: E402

PAGES = ["Overview", "Network Topology", "Attack Path Analysis", "Centrality Analysis",
         "Greedy Algorithm", "Simulated Annealing", "Exhaustive Search", "Algorithm Comparison",
         "Generated Results", "Experiment Runner", "Precinct6 Dataset"]


@pytest.fixture(scope="module")
def app():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    assert not at.exception
    return at


@pytest.mark.parametrize("page", PAGES)
def test_every_page_renders(app, page):
    app.session_state["nav"] = page
    app.run()
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]


def test_runner_updates_active_experiment(app):
    app.session_state["nav"] = "Experiment Runner"
    app.run()
    app.selectbox(key="rn_bench").set_value("A")
    app.number_input(key="rn_k").set_value(3)
    app.number_input(key="rn_m").set_value(20)
    [b for b in app.button if b.label == "Run experiment"][0].click()
    app.run()
    assert not app.exception
    assert app.session_state["params"].benchmark == "A"
    assert app.session_state["result"]["benchmark"] == "A"


def test_report_decoding_utf16(tmp_path):
    from ui import data
    f = tmp_path / "r.txt"
    f.write_bytes("Experiment F — ok\r\nline2\r\n".encode("utf-16"))
    assert data.read_report(f) == "Experiment F — ok\nline2\n"
    g = tmp_path / "u.txt"
    g.write_text("plain ✓", encoding="utf-8")
    assert data.read_report(g) == "plain ✓"
