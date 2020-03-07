from typing import Dict, Mapping, Optional, Sequence, Union

import deprecation
from ddtrace import Tracer, tracer as global_tracer
from ddtrace.constants import ANALYTICS_SAMPLE_RATE_KEY
from ddtrace.ext import http as http_tags
from ddtrace.http import store_request_headers, store_response_headers
from ddtrace.propagation.http import HTTPPropagator
from ddtrace.settings import config
from starlette.datastructures import CommaSeparatedStrings, Headers
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class TraceMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        tracer: Optional[Tracer] = None,
        service: str = "asgi",
        tags: Union[Mapping[str, str], Sequence[str]] = None,
        distributed_tracing: bool = True,
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

        self.app = app
        self.tracer = tracer
        self.service = service
        self.tags = tags
        self._distributed_tracing = distributed_tracing

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope["ddtrace_asgi.tracer"] = self.tracer

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope=scope, receive=receive)
        try:
            request_headers = request.headers
            method = request.method
            url = request.url
        except KeyError:
            # ASGI message is invalid - most likely missing the 'headers' or 'method'
            # fields.
            await self.app(scope, receive, send)
            return

        # Make sure we don't use potentially unsafe request attributes after this point.
        del request

        if self._distributed_tracing:
            propagator = HTTPPropagator()
            context = propagator.extract(request_headers)
            if context.trace_id:
                self.tracer.context_provider.activate(context)

        resource = "%s %s" % (method, url.path)
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
        span.set_tag(http_tags.METHOD, method)
        span.set_tag(http_tags.URL, str(url))
        if config.asgi.get("trace_query_string"):
            span.set_tag(http_tags.QUERY_STRING, url.query)

        span.set_tags(self.tags)

        # NOTE: any request header set in the future will not be stored in the span.
        store_request_headers(request_headers, span, config.asgi)

        async def send_with_tracing(message: Message) -> None:
            span = self.tracer.current_span()

            if span and message.get("type") == "http.response.start":
                if "status" in message:
                    status_code: int = message["status"]
                    span.set_tag(http_tags.STATUS_CODE, str(status_code))
                if "headers" in message:
                    response_headers = Headers(raw=message["headers"])
                    store_response_headers(response_headers, span, config.asgi)

            await send(message)

        try:
            await self.app(scope, receive, send_with_tracing)
        except BaseException as exc:
            span.set_traceback()
            raise exc from None
        finally:
            span.finish()


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
