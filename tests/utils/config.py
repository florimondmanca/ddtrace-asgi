import contextlib
import typing

import ddtrace


@contextlib.contextmanager
def override_config(integration: str, **values: typing.Any) -> typing.Iterator[None]:
    options: dict = getattr(ddtrace.config, integration)
    original = {key: options.get(key) for key in values.keys()}
    options.update(values)
    try:
        yield
    finally:
        options.update(original)
