#!/usr/bin/env python3
"""
Test Isolation Layer - provides per-test execution isolation
"""

import os
import shutil
import tempfile
from contextlib import contextmanager


class TestIsolation:
    """
    Provides per-test execution isolation for DAG + worker system.
    Ensures no shared filesystem state or cross-test contamination.
    """

    def __enter__(self):
        self._old_cwd = os.getcwd()
        self._tmp_dir = tempfile.mkdtemp()
        self._old_env = dict(os.environ)

        os.chdir(self._tmp_dir)
        return self

    def __exit__(self, exc_type, exc, tb):
        os.chdir(self._old_cwd)
        os.environ.clear()
        os.environ.update(self._old_env)
        shutil.rmtree(self._tmp_dir, ignore_errors=True)


@contextmanager
def isolated_env():
    """Context manager for test isolation."""
    with TestIsolation():
        yield
