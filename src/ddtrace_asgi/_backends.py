from ddtrace import Span
from ddtrace.constants import ANALYTICS_SAMPLE_RATE_KEY, MANUAL_DROP_KEY
from ddtrace.ext import http as http_tags
from ddtrace.http import store_request_headers, store_response_headers
from ddtrace.settings import config as global_config
from ddtrace.settings.config import IntegrationConfig
from starlette.datastructures import URL, Headers
from starlette.types import Message, Scope


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
