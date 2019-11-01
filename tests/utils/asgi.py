from starlette.types import Message, Receive, Scope, Send

mock_http_scope = {
    "type": "http",
    "headers": [],
    "method": "GET",
    "path": "/",
    "query_string": b"",
}


async def mock_receive() -> Message:
    raise NotImplementedError  # pragma: no cover


async def mock_send(message: Message) -> None:
    pass


async def mock_app(scope: Scope, receive: Receive, send: Send) -> None:
    raise NotImplementedError  # pragma: no cover
