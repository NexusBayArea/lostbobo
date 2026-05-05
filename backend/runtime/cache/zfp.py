"""ZFP compression for simulation fields."""

from __future__ import annotations

import numpy as np

try:
    import zfpy
except ImportError:
    zfpy = None


def compress_field(data: np.ndarray, tolerance: float = 1e-6) -> bytes | None:
    """Compress grid/field with ZFP."""
    if zfpy is None or not isinstance(data, np.ndarray):
        return None
    try:
        return zfpy.compress_numpy(data, tolerance=tolerance)
    except Exception:
        return None


def decompress_field(blob: bytes) -> np.ndarray | None:
    """Decompress ZFP field."""
    if zfpy is None:
        return None
    try:
        return zfpy.decompress_numpy(blob)
    except Exception:
        return None
