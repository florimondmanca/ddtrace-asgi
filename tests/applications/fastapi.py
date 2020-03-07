from typing import NoReturn, Sequence, Tuple

from ddtrace import Tracer
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp


def create_app(middleware: Sequence[Tuple[type, dict]]) -> ASGIApp:
    app = FastAPI()

    @app.get("/", response_class=PlainTextResponse)
    async def home() -> str:
        return "Hello, world!"

    @app.get("/child/", response_class=PlainTextResponse)
    async def child(request: Request) -> str:
        tracer: Tracer = request["ddtrace_asgi.tracer"]
        with tracer.trace("asgi.request.child", resource="child") as span:
            span.set_tag("hello", "world")
            return "Hello, child!"

    @app.get("/exception/")
    async def exception() -> NoReturn:
        raise RuntimeError("Oops")

    for cls, options in middleware:
        app.add_middleware(cls, **options)

    return app
