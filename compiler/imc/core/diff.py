# Placeholder for diff utilities between graph versions


def diff_graph(old, new):
    """Return simple diff of node ids between two graphs."""
    old_set = set(old.keys())
    new_set = set(new.keys())
    added = new_set - old_set
    removed = old_set - new_set
    return {"added": added, "removed": removed}
