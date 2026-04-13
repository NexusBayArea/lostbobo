#!/usr/bin/env python3
"""Cache check and update utilities."""

import json
import sys

CACHE_PATH = "ci/cache_state.json"


def load_cache() -> dict:
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_cache(cache: dict):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def should_skip(module: str, new_hash: str) -> bool:
    cache = load_cache()
    return cache.get(module) == new_hash


def update_cache(module: str, new_hash: str):
    cache = load_cache()
    cache[module] = new_hash
    save_cache(cache)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: cache_check.py <module> <hash>")
        sys.exit(1)

    module = sys.argv[1]
    new_hash = sys.argv[2]

    if should_skip(module, new_hash):
        print("skip")
    else:
        print("run")
        update_cache(module, new_hash)
