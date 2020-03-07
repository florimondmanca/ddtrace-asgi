from typing import Any, List

import httpx
import pytest
from ddtrace import Span, Tracer
from ddtrace.ext import http as http_ext
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ddtrace_asgi import TraceBackend, TraceMiddleware
from tests.utils.fixtures import create_app


@pytest.mark.asyncio
async def test_custom_trace_backend(application: str, tracer: Tracer) -> None:
    class CustomTraceBackend(TraceBackend):
        def on_http_request(self, span: Span, scope: Scope) -> None:
            super().on_http_request(span, scope)
            # Add tags from initial scope data.
            span.set_tags(scope.get("dd_tags", {}))

        def on_http_response(self, span: Span, scope: Scope, message: Message) -> None:
            super().on_http_response(span, scope, message)

            # Set a tag using the ASGI message.
            is_redirect = 300 <= message["status"] < 400
            span.set_tag("is_redirect", "true" if is_redirect else "false")

            # Set tags from scope data, which may have been modified
            # by the underlying ASGI app.
            span.set_tags(scope.get("dd_tags", {}))

    class UpdateScopeMiddleware:
        def __init__(self, app: ASGIApp, **kwargs: Any) -> None:
            self.app = app
            self.kwargs = kwargs

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            scope.update(self.kwargs)
            await self.app(scope, receive, send)

    backend = CustomTraceBackend()
    app = create_app(
        application,
        middleware=[
            (UpdateScopeMiddleware, {"dd_tags": {"session_id": "123abc"}}),
            (
                TraceMiddleware,
                {"tracer": tracer, "service": "test.asgi.service", "backend": backend},
            ),
            (
                UpdateScopeMiddleware,
                {"dd_tags": {"url_pattern": "/tickets/{ticket_id:int}/"}},
            ),
        ],
    )

    async with httpx.AsyncClient(app=app) as client:
        r = await client.get("http://testserver/")
        assert r.status_code == 200

    traces = tracer.writer.pop_traces()
    assert len(traces) == 1
    spans: List[Span] = traces[0]
    assert len(spans) == 1
    span = spans[0]

    # Default behavior should be preserved.
    assert span.span_id
    assert span.trace_id
    assert span.parent_id is None
    assert span.name == "asgi.request"
    assert span.service == "test.asgi.service"
    assert span.resource == "GET /"
    assert span.get_tag(http_ext.STATUS_CODE) == "200"
    assert span.get_tag(http_ext.URL) == "http://testserver/"
    assert span.get_tag(http_ext.QUERY_STRING) is None

    # Custom behavior.
    assert span.get_tag("session_id") == "123abc"
    assert span.get_tag("is_redirect") == "false"
    assert span.get_tag("url_pattern") == "/tickets/{ticket_id:int}/"
