import typing

from ddtrace import Tracer
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import PlainTextResponse

application = FastAPI()


@application.get("/example", response_class=PlainTextResponse)
async def example() -> str:
    return "Hello, world!"


@application.get("/child", response_class=PlainTextResponse)
async def child(request: Request) -> str:
    tracer: Tracer = request["ddtrace_asgi.tracer"]
    with tracer.trace("asgi.request.child", resource="child") as span:
        span.set_tag("hello", "world")
        return "Hello, child!"


@application.get("/exception")
async def exception() -> typing.NoReturn:
    raise RuntimeError("Oops")
