# ddtrace-asgi

[![Build Status](https://travis-ci.com/florimondmanca/ddtrace-asgi.svg?branch=master)](https://travis-ci.com/florimondmanca/ddtrace-asgi)
[![Coverage](https://codecov.io/gh/florimondmanca/ddtrace-asgi/branch/master/graph/badge.svg)](https://codecov.io/gh/florimondmanca/ddtrace-asgi)
[![Package version](https://badge.fury.io/py/ddtrace-asgi.svg)](https://pypi.org/project/ddtrace-asgi)

Unofficial [`ddtrace`] integration for ASGI apps and frameworks.

Use `ddtrace-asgi` to automatically send traces to [Datadog APM](https://docs.datadoghq.com/tracing/), which allows you to visualize traffic and detailed traces of requests.

Should work seamlessly for any ASGI web framework, e.g. Starlette, FastAPI, Quart, etc.

[`ddtrace`]: https://github.com/DataDog/dd-trace-py

**Note**: This project is in alpha stage.

## Installation

```bash
pip install ddtrace-asgi
```

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
