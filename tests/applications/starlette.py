from typing import NoReturn, Sequence, Tuple

from ddtrace import Tracer
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Route
from starlette.types import ASGIApp


async def home(request: Request) -> Response:
    return PlainTextResponse("Hello, world!")


async def child(request: Request) -> Response:
    tracer: Tracer = request["ddtrace_asgi.tracer"]
    with tracer.trace("asgi.request.child", resource="child") as span:
        span.set_tag("hello", "world")
        return PlainTextResponse("Hello, child!")


async def get_show(request: Request) -> Response:
    pk = request.path_params["pk"]
    return JSONResponse({"id": pk, "title": "PyCon"})


async def exception(request: Request) -> NoReturn:
    raise RuntimeError("Oops")


routes = [
    Route("/", home),
    Route("/child/", child),
    Route("/shows/{pk:int}/", get_show),
    Route("/exception/", exception),
]


def create_app(middleware: Sequence[Tuple[type, dict]]) -> ASGIApp:
    return Starlette(
        routes=routes,
        middleware=[Middleware(cls, **options) for cls, options in middleware],
    )
