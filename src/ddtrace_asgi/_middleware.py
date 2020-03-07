import functools
from typing import Mapping, Optional, Sequence, Union

from ddtrace import Tracer, tracer as global_tracer
from ddtrace.ext import http as http_tags
from ddtrace.propagation.http import HTTPPropagator
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ._backends import TraceBackend
from ._deprecated.utils import parse_tags_from_string
from ._utils import parse_tags_from_list


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
