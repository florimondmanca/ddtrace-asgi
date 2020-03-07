import pytest

import ddtrace_asgi

from .utils.fixtures import create_app


@pytest.mark.parametrize(
    "tags", ["", "env:testing"],
)
def test_deprecated_string_tags(tags: str) -> None:
    app = create_app("raw")
    with pytest.deprecated_call():
        ddtrace_asgi.TraceMiddleware(app, tags=tags)


def test_deprecated_middleware_module() -> None:
    with pytest.deprecated_call():
        from ddtrace_asgi.middleware import TraceMiddleware  # noqa
