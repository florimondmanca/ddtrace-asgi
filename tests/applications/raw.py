from ddtrace import Tracer
from starlette.types import Receive, Scope, Send


async def home(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope["type"] == "http"
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/plain"]],
        }
    )
    await send({"type": "http.response.body", "body": b"Hello, world!"})


async def child(scope: Scope, receive: Receive, send: Send) -> None:
    assert scope["type"] == "http"
    tracer: Tracer = scope["ddtrace_asgi.tracer"]
    with tracer.trace("asgi.request.child", resource="child") as span:
        span.set_tag("hello", "world")
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"text/plain"]],
            }
        )
        await send({"type": "http.response.body", "body": b"Hello, child!"})


async def exception(scope: Scope, receive: Receive, send: Send) -> None:
    exc = RuntimeError("Oops")
    await send(
        {
            "type": "http.response.start",
            "status": 500,
            "headers": [[b"content-type", b"text/plain"]],
        }
    )
    await send({"type": "http.response.body", "body": str(exc).encode()})
    raise exc


async def app(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["path"] == "/child":
        await child(scope, receive, send)
    elif scope["path"] == "/exception":
        await exception(scope, receive, send)
    else:
        await home(scope, receive, send)
