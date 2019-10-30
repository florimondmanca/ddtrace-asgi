from typing import Optional

from ddtrace import Tracer, tracer as global_tracer
from ddtrace.constants import ANALYTICS_SAMPLE_RATE_KEY
from ddtrace.ext import http as http_tags
from ddtrace.http import store_request_headers, store_response_headers
from ddtrace.propagation.http import HTTPPropagator
from ddtrace.settings import config
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class TraceMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        tracer: Optional[Tracer] = None,
        service: str = "asgi",
        distributed_tracing: bool = True,
    ) -> None:
        self.app = app
        if tracer is None:
            tracer = global_tracer
        self.tracer = tracer
        self.service = service
        self._distributed_tracing = distributed_tracing

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope=scope, receive=receive)

        if self._distributed_tracing:
            propagator = HTTPPropagator()
            context = propagator.extract(request.headers)
            if context.trace_id:
                self.tracer.context_provider.activate(context)

        resource = "%s %s" % (request.method, request.url.path)
        span = self.tracer.trace(
            name="asgi.request",
            service=self.service,
            resource=resource,
            span_type=http_tags.TYPE,
        )

        span.set_tag(
            ANALYTICS_SAMPLE_RATE_KEY,
            config.asgi.get_analytics_sample_rate(use_global_config=True),
        )
        span.set_tag(http_tags.METHOD, request.method)
        span.set_tag(http_tags.URL, str(request.url))
        if config.asgi.trace_query_string:
            span.set_tag(http_tags.QUERY_STRING, request.url.query)

        # NOTE: any request header set in the future will not be stored in the span.
        store_request_headers(request.headers, span, config.asgi)

        async def send_with_tracing(message: Message) -> None:
            span = self.tracer.current_span()

            if not span:
                # Unexpected.
                await send(message)
                return

            if message["type"] == "http.response.start":
                status_code: int = message["status"]
                response_headers = Headers(raw=message["headers"])
                store_response_headers(response_headers, span, config.asgi)
                span.set_tag(http_tags.STATUS_CODE, str(status_code))

            await send(message)

        try:
            await self.app(scope, receive, send_with_tracing)
        except BaseException as exc:
            span.set_traceback()
            raise exc from None
        finally:
            span.finish()
