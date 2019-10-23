# ddtrace-asgi

Unofficial [`ddtrace`] integration for ASGI apps and frameworks.

Use `ddtrace-asgi` to automatically send traces to [Datadog APM](https://docs.datadoghq.com/tracing/), which allows you to visualize traffic and detailed traces of requests.

[`ddtrace`]: https://github.com/DataDog/dd-trace-py

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

For more information on using `ddtrace`, please see the official [`ddtrace`] repository.

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
