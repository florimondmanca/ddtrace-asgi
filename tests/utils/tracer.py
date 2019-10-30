"""
Copied from:
https://github.com/DataDog/dd-trace-py/blob/master/tests/utils/tracer.py

Changes:
- Add type annotations.
- Make flake8-compliant.
"""

import typing

from ddtrace.encoding import JSONEncoder, MsgpackEncoder
from ddtrace.internal.writer import AgentWriter
from ddtrace.tracer import Tracer

Span = typing.Any
Trace = typing.Any
Service = typing.Any


class DummyWriter(AgentWriter):
    """DummyWriter is a small fake writer used for tests. not thread-safe."""

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

        # Dummy components.
        self.spans: typing.List[Span] = []
        self.traces: typing.List[Trace] = []
        self.services: typing.Dict[str, Service] = {}
        self.json_encoder = JSONEncoder()
        self.msgpack_encoder = MsgpackEncoder()

    def write(
        self, spans: typing.List[Span] = None, services: typing.List[Service] = None
    ) -> None:
        if spans:
            # The traces encoding expect a list of traces so we
            # put spans in a list like we do in the real execution path
            # with both encoders.
            trace = [spans]
            self.json_encoder.encode_traces(trace)
            self.msgpack_encoder.encode_traces(trace)
            self.spans += spans
            self.traces += trace

        if services:
            self.json_encoder.encode_services(services)
            self.msgpack_encoder.encode_services(services)
            self.services.update(services)

    def pop(self) -> typing.List[Span]:
        # Dummy method.
        spans = self.spans
        self.spans = []
        return spans

    def pop_traces(self) -> typing.List[Trace]:
        # Dummy method.
        traces = self.traces
        self.traces = []
        return traces

    def pop_services(self) -> typing.Dict[str, Service]:
        # Dummy method.
        # Setting service info has been deprecated,
        # we want to make sure nothing ever gets written here.
        assert self.services == {}
        services = self.services
        self.services = {}
        return services


class DummyTracer(Tracer):
    """
    DummyTracer is a tracer which uses the DummyWriter by default
    """

    writer: DummyWriter

    def __init__(self) -> None:
        super().__init__()
        self._update_writer()

    def _update_writer(self) -> None:
        self.writer = DummyWriter(
            hostname=self.writer.api.hostname,
            port=self.writer.api.port,
            filters=self.writer._filters,
            priority_sampler=self.writer._priority_sampler,
        )

    def configure(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().configure(*args, **kwargs)
        # `.configure()` may reset the writer.
        self._update_writer()
