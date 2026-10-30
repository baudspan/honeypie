"""Thin wrappers so the dashboard runs on both older and newer Streamlit.

Newer Streamlit deprecates `use_container_width` in favour of `width="stretch"`.
"""
from __future__ import annotations
import streamlit as st

try:
    _V = tuple(int(x) for x in st.__version__.split(".")[:2])
except Exception:  # pragma: no cover
    _V = (1, 0)
_NEW_WIDTH_API = _V >= (1, 49)

PLOT_CONFIG = {"displaylogo": False,
               "modeBarButtonsToRemove": ["lasso2d", "select2d"]}


def plot(fig, key=None):
    """Render a Plotly figure full-width with our own (dark) styling."""
    if _NEW_WIDTH_API:
        return st.plotly_chart(fig, width="stretch", theme=None, key=key,
                               config=PLOT_CONFIG)
    return st.plotly_chart(fig, use_container_width=True, theme=None, key=key,
                           config=PLOT_CONFIG)


def table(data, **kw):
    """Full-width dataframe without the index column."""
    if _NEW_WIDTH_API:
        return st.dataframe(data, width="stretch", hide_index=True, **kw)
    return st.dataframe(data, use_container_width=True, hide_index=True, **kw)


def image(path, caption=None):
    if _NEW_WIDTH_API:
        return st.image(str(path), caption=caption, width="stretch")
    return st.image(str(path), caption=caption, use_container_width=True)
