from typing import List, Optional

import httpx
import pytest
from ddtrace import Span, Tracer
from ddtrace.ext import http as http_ext
from starlette.applications import Starlette
from starlette.routing import Match, Route, Router
from starlette.types import Message, Scope

from ddtrace_asgi.middleware import TraceBackend, TraceMiddleware
from tests.utils.fixtures import create_app


@pytest.mark.asyncio
async def test_custom_trace_backend(application: str, tracer: Tracer) -> None:
    class CustomTraceBackend(TraceBackend):
        def init_span(self, span: Span, scope: Scope) -> None:
            super().init_span(span, scope)
            span.set_tag("env", "prod")

        def on_http_response_start(self, span: Span, message: Message) -> None:
            super().on_http_response_start(span, message)
            status = message["status"]
            span.set_tag("status_reversed", str(status)[::-1])

    backend = CustomTraceBackend()
    app = create_app(
        application,
        middleware=[
            (
                TraceMiddleware,
                {"tracer": tracer, "service": "test.asgi.service", "backend": backend},
            )
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
    assert span.get_tag("env") == "prod"
    assert span.get_tag("status_reversed") == "002"


@pytest.mark.asyncio
async def test_usecase_route_path_as_resource(application: str, tracer: Tracer) -> None:
    class RoutePathAsResourceTraceBackend(TraceBackend):
        def _find_matching_route(self, scope: Scope, router: Router) -> Optional[Route]:
            for route in router.routes:
                assert isinstance(route, Route)
                match, child_scope = route.matches(scope)
                if match == Match.FULL or match == Match.PARTIAL:
                    return route
            raise RuntimeError  # pragma: no cover

        def init_span(self, span: Span, scope: Scope) -> None:
            super().init_span(span, scope)

            app: Starlette = scope["app"]
            route = self._find_matching_route(scope, router=app.router)
            assert route is not None

            method = scope["method"]
            span.resource = f"{method} {route.path}"

    backend = RoutePathAsResourceTraceBackend()
    app = create_app(
        application,
        middleware=[
            (
                TraceMiddleware,
                {"tracer": tracer, "service": "test.asgi.service", "backend": backend},
            )
        ],
    )

    if not isinstance(app, Starlette):
        pytest.skip(f"Not a Starlette instance: {app}")

    async with httpx.AsyncClient(app=app) as client:
        r = await client.get("http://testserver/shows/42/")
        assert r.status_code == 200
        assert r.json() == {"id": 42, "title": "PyCon"}

    traces = tracer.writer.pop_traces()
    assert len(traces) == 1
    spans: List[Span] = traces[0]
    assert len(spans) == 1
    span = spans[0]

    assert span.name == "asgi.request"
    assert span.service == "test.asgi.service"
    assert span.resource == "GET /shows/{pk:int}/"
