import importlib
from typing import Any

import pytest
from ddtrace.tracer import Tracer
from starlette.types import ASGIApp

from tests.utils.tracer import DummyTracer

# TIP: use 'pytest -k <id>' to run tests for a given application only.
APPLICATIONS = [
    pytest.param("tests.applications.raw:app", id="raw"),
    pytest.param("tests.applications.starlette:app", id="starlette"),
    pytest.param("tests.applications.fastapi:app", id="fastapi"),
]


@pytest.fixture(name="app", params=APPLICATIONS)
def fixture_app(request: Any) -> ASGIApp:
    module_path, app_name = request.param.split(":")
    module = importlib.import_module(module_path)
    return getattr(module, app_name)


@pytest.fixture
def tracer() -> Tracer:
    return DummyTracer()
