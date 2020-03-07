import typing

from ddtrace import Tracer
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route


async def home(request: Request) -> Response:
    return PlainTextResponse("Hello, world!")


async def child(request: Request) -> Response:
    tracer: Tracer = request["ddtrace_asgi.tracer"]
    with tracer.trace("asgi.request.child", resource="child") as span:
        span.set_tag("hello", "world")
        return PlainTextResponse("Hello, child!")


async def exception(request: Request) -> typing.NoReturn:
    raise RuntimeError("Oops")


routes = [Route("/", home), Route("/child", child), Route("/exception", exception)]
app = Starlette(routes=routes)
