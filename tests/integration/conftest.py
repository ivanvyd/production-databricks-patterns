"""Fixtures for the integration suite.

`workspace` and `operation_store` are where this template meets a real platform:
one wraps a client pointed at a disposable environment, the other whatever table
records your operations. Supply them and the tests below become real.

Stubs rather than nothing, because a missing fixture is a collection error and
not a skip, which makes a bare `pytest` at the repository root red.
"""

import pytest

REASON = "integration fixture not supplied; see tests/integration/conftest.py"


@pytest.fixture
def workspace():
    pytest.skip(REASON)


@pytest.fixture
def operation_store():
    pytest.skip(REASON)
