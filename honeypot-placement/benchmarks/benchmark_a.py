"""Benchmark A: ~15-node corporate network with multiple routes to a DB.

Weights = simulated traversal cost (lower = cheaper route to compute).
Non-negative. Dijkstra/Yen minimize total accumulated cost — this is a
route-selection model, not a probability of compromise.
"""
from __future__ import annotations
import networkx as nx


def build() -> tuple[nx.DiGraph, str, str]:
    G = nx.DiGraph()
    G.add_nodes_from([
        "s", "gw", "fw", "vpn",
        "dmz_web", "dmz_mail",
        "app1", "app2",
        "admin", "ws1", "ws2",
        "backup", "router", "log",
        "db",
    ])
    edges = [
        ("s", "gw", 1), ("s", "vpn", 3),
        ("gw", "fw", 1),
        ("fw", "dmz_web", 2), ("fw", "dmz_mail", 2),
        ("dmz_web", "app1", 2), ("dmz_web", "app2", 2),
        ("dmz_mail", "app2", 3), ("dmz_mail", "admin", 3),
        ("vpn", "admin", 2), ("vpn", "ws1", 3),
        ("app1", "db", 3), ("app2", "db", 3),
        ("app1", "backup", 2), ("app2", "backup", 2),
        ("admin", "ws1", 1), ("admin", "ws2", 1), ("admin", "backup", 2),
        ("ws1", "log", 2), ("ws2", "log", 2),
        ("backup", "router", 2), ("backup", "log", 1),
        ("router", "app1", 2), ("router", "app2", 2),
        ("log", "db", 4),
    ]
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
    return G, "s", "db"