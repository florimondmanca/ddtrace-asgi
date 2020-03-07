import functools
from typing import Dict, Mapping, Optional, Sequence, Union

import deprecation
from ddtrace import Span, Tracer, tracer as global_tracer
from ddtrace.constants import ANALYTICS_SAMPLE_RATE_KEY, MANUAL_DROP_KEY
from ddtrace.ext import http as http_tags
from ddtrace.http import store_request_headers, store_response_headers
from ddtrace.propagation.http import HTTPPropagator
from ddtrace.settings import IntegrationConfig, config as global_config
from starlette.datastructures import URL, CommaSeparatedStrings, Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class TraceBackend:
    config: IntegrationConfig = global_config.asgi

    def on_http_request(self, span: Span, scope: Scope) -> None:
        """
        Called just before dispatching an incoming HTTP request to the underlying
        ASGI app.
        """
        assert scope["type"] == "http"

        try:
            method = scope["method"]
            url = URL(scope=scope)
        except KeyError:
            # Invalid ASGI.
            span.set_tag(MANUAL_DROP_KEY)
            return

        headers = Headers(raw=scope.get("headers", []))

        # NOTE: any header set in the future will not be stored in the span.
        store_request_headers(headers, span, self.config)

        span.resource = f"{method} {url.path}"

        span.set_tag(http_tags.METHOD, method)
        span.set_tag(http_tags.URL, str(url))
        if self.config.get("trace_query_string", False):
            span.set_tag(http_tags.QUERY_STRING, url.query)

        span.set_tag(
            ANALYTICS_SAMPLE_RATE_KEY,
            self.config.get_analytics_sample_rate(use_global_config=True),
        )

    def on_http_response(self, span: Span, scope: Scope, message: Message) -> None:
        """
        Called just before sending the HTTP response returned by the underlying
        ASGI app.
        """
        assert message["type"] == "http.response.start"

        if "status" in message:
            status_code: int = message["status"]
            span.set_tag(http_tags.STATUS_CODE, str(status_code))

        if "headers" in message:
            response_headers = Headers(raw=message["headers"])
            # NOTE: any header set in the future will not be stored in the span.
            store_response_headers(response_headers, span, self.config)


class TraceMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        tracer: Optional[Tracer] = None,
        service: str = "asgi",
        tags: Union[Mapping[str, str], Sequence[str]] = None,
        distributed_tracing: bool = True,
        backend: TraceBackend = None,
    ) -> None:
        if tracer is None:
            tracer = global_tracer

        if tags is None:
            tags = []
        if isinstance(tags, str):
            tags = parse_tags_from_string(tags)
        elif isinstance(tags, list):
            tags = parse_tags_from_list(tags)

        assert isinstance(tags, dict)

        if backend is None:
            backend = TraceBackend()

        self.app = app
        self.tracer = tracer
        self.service = service
        self.tags = tags
        self._distributed_tracing = distributed_tracing
        self.backend = backend

    async def send_with_tracing(
        self, send: Send, scope: Scope, message: Message
    ) -> None:
        span = self.tracer.current_span()

        if span is not None and message.get("type") == "http.response.start":
            self.backend.on_http_response(span, scope, message)

        await send(message)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["ddtrace_asgi.tracer"] = self.tracer

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if "headers" in scope and self._distributed_tracing:
            propagator = HTTPPropagator()
            headers = Headers(raw=scope["headers"])
            context = propagator.extract(headers)
            if context.trace_id:
                self.tracer.context_provider.activate(context)

        with self.tracer.trace(
            name="asgi.request", service=self.service, span_type=http_tags.TYPE,
        ) as span:
            span.set_tags(self.tags)
            self.backend.on_http_request(span, scope)

            send = functools.partial(self.send_with_tracing, send, scope)
            await self.app(scope, receive, send)


def parse_tags_from_list(tags: Sequence[str]) -> Dict[str, str]:
    parsed: Dict[str, str] = {}

    for tag in tags:
        name, _, value = tag.partition(":")
        parsed[name] = value

    return parsed


@deprecation.deprecated(
    deprecated_in="0.4.0",
    removed_in="0.5.0",
    details=(
        "Pass a list or dict instead. "
        "You can use starlette.datastructures.CommaSeparatedStrings for parsing."
    ),
)
def parse_tags_from_string(value: str) -> Dict[str, str]:
    return parse_tags_from_list(CommaSeparatedStrings(value))
