import functools
import typing

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

    def init_span(self, span: Span, scope: Scope) -> None:
        try:
            raw_headers = scope["headers"]
            method = scope["method"]
            url = URL(scope=scope)
        except KeyError:
            # Invalid ASGI.
            span.set_tag(MANUAL_DROP_KEY)
            return

        headers = Headers(raw=raw_headers)

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

    def on_http_response_start(self, span: Span, message: Message) -> None:
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
        tracer: typing.Optional[Tracer] = None,
        service: str = "asgi",
        tags: typing.Union[str, typing.Dict[str, str]] = None,
        distributed_tracing: bool = True,
        backend: TraceBackend = None,
    ) -> None:
        if tracer is None:
            tracer = global_tracer

        if tags is None:
            tags = {}
        if isinstance(tags, str):
            tags = parse_tags(tags)

        assert isinstance(tags, dict)

        if backend is None:
            backend = TraceBackend()

        self.app = app
        self.tracer = tracer
        self.service = service
        self.tags = tags
        self._distributed_tracing = distributed_tracing
        self.backend = backend

    async def send_with_tracing(self, send: Send, message: Message) -> None:
        span = self.tracer.current_span()
        if span is not None and message.get("type") == "http.response.start":
            self.backend.on_http_response_start(span, message)
        await send(message)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["ddtrace_asgi.tracer"] = self.tracer

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_headers = Headers(raw=scope.get("headers", []))

        if self._distributed_tracing:
            propagator = HTTPPropagator()
            context = propagator.extract(request_headers)
            if context.trace_id:
                self.tracer.context_provider.activate(context)

        span = self.tracer.trace(
            name="asgi.request", service=self.service, span_type=http_tags.TYPE,
        )

        self.backend.init_span(span, scope)

        for key, value in self.tags.items():
            span.set_tag(key, value)

        send = functools.partial(self.send_with_tracing, send)

        try:
            await self.app(scope, receive, send)
        except BaseException as exc:
            span.set_traceback()
            raise exc from None
        finally:
            span.finish()


def parse_tags(value: str) -> typing.Dict[str, str]:
    tags = {}
    for tag in CommaSeparatedStrings(value):
        key, sep, val = tag.partition(":")
        if not sep:
            raise ValueError(f"Invalid tag format: {tag!r}")
        assert sep
        tags[key] = val
    return tags
