# ddtrace-asgi

[![Build Status](https://travis-ci.com/florimondmanca/ddtrace-asgi.svg?branch=master)](https://travis-ci.com/florimondmanca/ddtrace-asgi)
[![Coverage](https://codecov.io/gh/florimondmanca/ddtrace-asgi/branch/master/graph/badge.svg)](https://codecov.io/gh/florimondmanca/ddtrace-asgi)
[![Package version](https://badge.fury.io/py/ddtrace-asgi.svg)](https://pypi.org/project/ddtrace-asgi)

Unofficial `ddtrace` integration for ASGI apps and frameworks.

Should work seamlessly for any ASGI web framework, e.g. Starlette, FastAPI, Quart, etc.

**Note**: This project is in alpha stage.

## Requirements

- Python 3.6+.
- [`ddtrace`](https://github.com/DataDog/dd-trace-py) must be installed to use the `ddtrace-run` command.
- The [Datadog Agent](https://docs.datadoghq.com/agent/) must be installed and running for traces to be effectively sent to Datadog APM.

## Installation

```bash
pip install ddtrace-asgi
```

## Quickstart

To automatically send traces to [Datadog APM](https://docs.datadoghq.com/tracing/) on each HTTP request, wrap your ASGI application around `TraceMiddleware`:

```python
# app.py
from ddtrace_asgi.middleware import TraceMiddleware

async def app(scope, receive, send):
    assert scope["type"] == "http"
    headers = [[b"content-type", b"text/plain"]]
    await send({"type": "http.response.start", "status": 200, "headers": headers})
    await send({"type": "http.response.body", "body": b"Hello, world!"})

app = TraceMiddleware(
    app, service="asgi-hello-world", tags={"env": "local"},
)
```

Then use `ddtrace-run` when serving your application. For example, if serving with Uvicorn:

```bash
ddtrace-run uvicorn app:app
```

For more information on using `ddtrace`, please see the official [`dd-trace-py`](https://github.com/DataDog/dd-trace-py) repository.

## Examples

### Starlette

```python
from ddtrace_asgi.middleware import TraceMiddleware
from starlette.applications import Starlette

app = Starlette()
app.add_middleware(TraceMiddleware, service="my-starlette-app")
```

### FastAPI

```python
from ddtrace_asgi.middleware import TraceMiddleware
from fastapi import FastAPI

app = FastAPI()
app.add_middleware(TraceMiddleware, service="my-fastapi-app")
```

## API Reference

### `TracingMiddleware`

```python
class TracingMiddleware:
    def __init__(self, app, tracer=None, service="asgi", tags=None, distributed_tracing=True):
        ...
```

An ASGI middleware that sends traces of HTTP requests to Datadog APM.

**Parameters**

- **app** - An [ASGI] application.
- **tracer** - _(optional)_ A [`Tracer`](http://pypi.datadoghq.com/trace/docs/advanced_usage.html#tracer) object. Defaults to the global `ddtrace.tracer` object.
- **service** - _(optional)_ Name of the service as it will appear on Datadog.
- **tags** - _(optional)_ Default tags attached to all request spans. Either a dictionary, or a string of comma-separated tags (e.g. `"env:staging, app:shop"`). See also [Tagging](https://docs.datadoghq.com/tagging/).
- **distributed_tracing** - _(optional)_ Whether to enable [distributed tracing](http://pypi.datadoghq.com/trace/docs/advanced_usage.html#distributed-tracing).
