# ddtrace-asgi

[![Build Status](https://travis-ci.com/florimondmanca/ddtrace-asgi.svg?branch=master)](https://travis-ci.com/florimondmanca/ddtrace-asgi)
[![Coverage](https://codecov.io/gh/florimondmanca/ddtrace-asgi/branch/master/graph/badge.svg)](https://codecov.io/gh/florimondmanca/ddtrace-asgi)
[![Package version](https://badge.fury.io/py/ddtrace-asgi.svg)](https://pypi.org/project/ddtrace-asgi)

Unofficial [`ddtrace`] integration for ASGI apps and frameworks.

Should work seamlessly for any ASGI web framework, e.g. Starlette, FastAPI, Quart, etc.

[`ddtrace`]: https://github.com/DataDog/dd-trace-py

**Note**: This project is in alpha stage.

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

app = TraceMiddleware(app, service="asgi-hello-world")
```

Then use `ddtrace-run` when serving your application. For example, if serving with Uvicorn:

```bash
ddtrace-run uvicorn app:app
```

For more information on using `ddtrace`, please see the official [`ddtrace`] repository.

## Examples

<details>
<summary>
    <a href="https://www.starlette.io/">Starlette</a>
</summary>

```python
from ddtrace_asgi.middleware import TraceMiddleware
from starlette.applications import Starlette

app = Starlette()
app.add_middleware(TraceMiddleware, service="my-starlette-app")
```

</details>

## API Reference

### `TracingMiddleware`

```python
class TracingMiddleware:
    def __init__(self, app, tracer=tracer, service="asgi", distributed_tracing=True):
        ...
```

An ASGI middleware that sends traces of HTTP requests to Datadog APM.

**Parameters**

- **app** - An [ASGI] application.
- **tracer** - _(optional)_ A [`Tracer`] object. Defaults to the global `ddtrace.tracer` object.
- **service** - _(optional)_ Name of the service as it will appear on Datadog.
- **distributed_tracing** - _(optional)_ Whether to enable [distributed tracing].

[asgi]: https://asgi.readthedocs.io
[`tracer`]: http://pypi.datadoghq.com/trace/docs/advanced_usage.html#tracer
[distributed tracing]: http://pypi.datadoghq.com/trace/docs/advanced_usage.html#distributed-tracing
