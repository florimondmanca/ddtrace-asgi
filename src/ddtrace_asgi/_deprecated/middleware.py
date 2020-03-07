import warnings

import deprecation

from .._middleware import TraceMiddleware

__all__ = ["TraceMiddleware"]

warnings.warn(
    deprecation.DeprecatedWarning(
        "Importing from `ddtrace_asgi.middleware`",
        deprecated_in="0.4.0",
        removed_in="0.5.0",
        details=(
            "Import from `ddtrace_asgi` instead: "
            "`from ddtrace_asgi importTraceMiddleware`."
        ),
    ),
    category=DeprecationWarning,
)
