import sys

if any(m.startswith("app") for m in sys.modules):
    raise RuntimeError("Illegal runtime: worker importing app")
