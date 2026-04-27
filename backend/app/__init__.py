import sys

if any(m.startswith("worker") for m in sys.modules):
    raise RuntimeError("Illegal runtime: app importing worker")
