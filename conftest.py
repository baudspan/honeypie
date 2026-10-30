"""Pytest bootstrap: ensure repo root is on sys.path so `import src` works."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)