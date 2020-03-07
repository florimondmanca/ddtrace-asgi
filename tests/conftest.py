from typing import Any

import pytest
from ddtrace.tracer import Tracer

from tests.utils.tracer import DummyTracer

# TIP: use 'pytest -k <id>' to run tests for a given application only.
APPLICATIONS = [
    pytest.param("raw", id="raw"),
    pytest.param("starlette", id="starlette"),
    pytest.param("fastapi", id="fastapi"),
]


@pytest.fixture(name="application", params=APPLICATIONS)
def fixture_application(request: Any) -> str:
    return request.param


@pytest.fixture
def tracer() -> Tracer:
    return DummyTracer()
