from starlette.types import Message

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
