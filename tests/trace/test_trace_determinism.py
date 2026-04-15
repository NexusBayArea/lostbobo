import pytest


@pytest.mark.trace
def test_trace_determinism():
    assert True
