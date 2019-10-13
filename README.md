# ddtrace-asgi

Unofficial [Datadog tracing][dd-trace-py] integration for ASGI apps and frameworks.

[dd-trace-py]: https://github.com/DataDog/dd-trace-py

> This is a proof of concept and a work in progress.

## Usage

Wrap an ASGI application around `TraceMiddleware` to automatically send tracing information to Datadog on each HTTP request.

```python
from ddtrace import tracer
from ddtrace_asgi.middleware import TraceMiddleware

async def app(scope, receive, send):
    ...

app = TraceMiddleware(app, tracer, service="my-app")
```

For more information on Datadog tracing, please see the official [`dd-trace-py`][dd-trace-py] repository.

## Examples

<details>
<summary>
    <a href="https://www.starlette.io/">Starlette</a>
</summary>

```python
from ddtrace import tracer
from ddtrace_asgi.middleware import TraceMiddleware
from starlette.applications import Starlette

app = Starlette()
app = TraceMiddleware(app, tracer, service="my-starlette-app")
```

</details>
