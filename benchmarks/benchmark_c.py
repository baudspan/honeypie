"""Benchmark C: hybrid attack graph on real Precinct6 hosts.

Hosts, IPs, roles, and chain edges are real, from WitFoo Precinct6
(100 incidents merged by IP). Bypass edges are synthesized to model
alternate lateral-movement routes that skip an intermediate hop.
Full disclosure: see scripts/build_hybrid_c.py and report §Benchmark C.
"""
from __future__ import annotations
import networkx as nx

PATH = "data/precinct6_hybrid.graphml"
SOURCE = "100.64.36.183"
TARGET = "100.64.111.159"


def build():
    G = nx.read_graphml(PATH)
    for u, v, d in G.edges(data=True):
        if "weight" not in d:
            d["weight"] = 1.0
    return G, SOURCE, TARGET


def eligible(G, s, t):
    return set(G.nodes) - {s, t}