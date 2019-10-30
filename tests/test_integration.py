import typing

import httpx
import pytest
from ddtrace.ext import http as http_ext
from ddtrace.span import Span
from ddtrace.tracer import Tracer
from starlette.types import Receive, Scope, Send

from ddtrace_asgi.middleware import TraceMiddleware


async def hello_world(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope["type"] == "http"
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/plain"]],
        }
    )
    await send({"type": "http.response.body", "body": b"Hello, world!"})


@pytest.fixture
def tracer() -> Tracer:
    from .utils.tracer import DummyTracer

    return DummyTracer()


@pytest.fixture
def client(tracer: Tracer) -> typing.Iterator[httpx.Client]:
    app = TraceMiddleware(hello_world, tracer=tracer, service="test_app")
    with httpx.Client(app=app, base_url="http://testserver") as client:
        yield client


def test_app(client: httpx.Client, tracer: Tracer) -> None:
    r = client.get("/example")
    assert r.status_code == 200
    assert r.text == "Hello, world!"

    traces = tracer.writer.pop_traces()
    assert len(traces) == 1
    assert len(traces[0]) == 1
    span: Span = traces[0][0]
    assert span.name == "asgi.request"
    assert span.service == "test_app"
    assert span.resource == "GET /example"
    assert span.get_tag(http_ext.STATUS_CODE) == "200"
    assert span.get_tag(http_ext.URL) == "http://testserver/example"
    assert http_ext.QUERY_STRING not in span.meta
    assert span.parent_id is None
