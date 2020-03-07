import importlib
from typing import Any, Sequence, Tuple

from starlette.types import ASGIApp


def create_app(name: str, middleware: Sequence[Tuple[type, dict]] = ()) -> ASGIApp:
    module_path = f"tests.applications.{name}"
    module: Any = importlib.import_module(module_path)
    return module.create_app(middleware=middleware)
