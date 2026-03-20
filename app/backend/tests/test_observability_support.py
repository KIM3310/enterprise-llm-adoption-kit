import importlib
import json
import logging
import runpy
import sys
import types
from types import SimpleNamespace

import app.logging_config as logging_config
import app.telemetry as telemetry


class _FakeSpan:
    def __init__(self) -> None:
        self.attributes = {}

    def set_attribute(self, key: str, value) -> None:
        self.attributes[key] = value


class _FakeSpanContext:
    def __init__(self, span: _FakeSpan) -> None:
        self._span = span

    def __enter__(self) -> _FakeSpan:
        return self._span

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeTracer:
    def __init__(self) -> None:
        self.started = []

    def start_as_current_span(self, name: str) -> _FakeSpanContext:
        span = _FakeSpan()
        self.started.append((name, span))
        return _FakeSpanContext(span)


class _FakeTraceNamespace:
    def __init__(self) -> None:
        self.providers = []
        self.tracer = _FakeTracer()

    def set_tracer_provider(self, provider) -> None:
        self.providers.append(provider)

    def get_tracer(self, name: str) -> _FakeTracer:
        assert name == telemetry.SERVICE_NAME
        return self.tracer


class _FakeBatchSpanProcessor:
    def __init__(self, exporter) -> None:
        self.exporter = exporter


class _FakeTracerProvider:
    def __init__(self, resource) -> None:
        self.resource = resource
        self.processors = []
        self.shutdown_called = 0

    def add_span_processor(self, processor) -> None:
        self.processors.append(processor)

    def shutdown(self) -> None:
        self.shutdown_called += 1


class _FakeResource:
    def __init__(self, *, attributes) -> None:
        self.attributes = attributes


class _FakeExporter:
    def __init__(self, *, endpoint: str) -> None:
        self.endpoint = endpoint


def _install_fake_otel(monkeypatch, exporter_cls=_FakeExporter):
    fake_trace = _FakeTraceNamespace()
    fake_opentelemetry = types.ModuleType("opentelemetry")
    fake_opentelemetry.trace = fake_trace

    fake_sdk_trace = types.ModuleType("opentelemetry.sdk.trace")
    fake_sdk_trace.TracerProvider = _FakeTracerProvider

    fake_sdk_trace_export = types.ModuleType("opentelemetry.sdk.trace.export")
    fake_sdk_trace_export.BatchSpanProcessor = _FakeBatchSpanProcessor

    fake_exporter_module = types.ModuleType(
        "opentelemetry.exporter.otlp.proto.grpc.trace_exporter"
    )
    fake_exporter_module.OTLPSpanExporter = exporter_cls

    fake_resources = types.ModuleType("opentelemetry.sdk.resources")
    fake_resources.Resource = _FakeResource
    fake_resources.SERVICE_NAME = "service.name"

    monkeypatch.setitem(sys.modules, "opentelemetry", fake_opentelemetry)
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.trace", fake_sdk_trace)
    monkeypatch.setitem(
        sys.modules,
        "opentelemetry.sdk.trace.export",
        fake_sdk_trace_export,
    )
    monkeypatch.setitem(
        sys.modules,
        "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
        fake_exporter_module,
    )
    monkeypatch.setitem(sys.modules, "opentelemetry.sdk.resources", fake_resources)
    return fake_trace


def test_generate_correlation_id_has_traceable_shape() -> None:
    correlation_id = logging_config.generate_correlation_id()
    assert len(correlation_id) == 16
    int(correlation_id, 16)


def test_structured_json_formatter_includes_context_and_exception() -> None:
    formatter = logging_config.StructuredJSONFormatter()
    token = logging_config.correlation_id_ctx.set("cid-123")
    try:
        try:
            raise ValueError("boom")
        except ValueError:
            record = logging.LogRecord(
                name="ops.logger",
                level=logging.ERROR,
                pathname=__file__,
                lineno=10,
                msg="something failed",
                args=(),
                exc_info=sys.exc_info(),
            )
        body = json.loads(formatter.format(record))
    finally:
        logging_config.correlation_id_ctx.reset(token)

    assert body["logger"] == "ops.logger"
    assert body["message"] == "something failed"
    assert body["correlation_id"] == "cid-123"
    assert "ValueError: boom" in body["exception"]


def test_configure_logging_replaces_root_handlers() -> None:
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    try:
        root.handlers[:] = [logging.StreamHandler(sys.stderr)]
        logging_config.configure_logging(level=logging.DEBUG)
        assert root.level == logging.DEBUG
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, logging_config.StructuredJSONFormatter)
    finally:
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        for handler in original_handlers:
            root.addHandler(handler)
        root.setLevel(original_level)


def test_init_telemetry_noops_without_endpoint(monkeypatch) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.setattr(telemetry, "_initialized", False)
    monkeypatch.setattr(telemetry, "_tracer_provider", None)
    telemetry.init_telemetry()
    assert telemetry._initialized is False
    assert telemetry._tracer_provider is None


def test_init_telemetry_success_and_shutdown(monkeypatch) -> None:
    fake_trace = _install_fake_otel(monkeypatch)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4317")
    monkeypatch.setattr(telemetry, "_initialized", False)
    monkeypatch.setattr(telemetry, "_tracer_provider", None)

    telemetry.init_telemetry()

    assert telemetry._initialized is True
    assert isinstance(telemetry._tracer_provider, _FakeTracerProvider)
    provider = telemetry._tracer_provider
    assert provider.resource.attributes["service.name"] == telemetry.SERVICE_NAME
    assert provider.processors[0].exporter.endpoint == "http://collector:4317"
    assert telemetry._get_tracer() is fake_trace.tracer

    telemetry.shutdown_telemetry()
    assert provider.shutdown_called == 1
    assert telemetry._tracer_provider is None
    assert telemetry._initialized is False


def test_init_telemetry_failure_logs_and_resets(monkeypatch, caplog) -> None:
    class _ExplodingExporter:
        def __init__(self, *, endpoint: str) -> None:
            raise RuntimeError(f"bad endpoint: {endpoint}")

    _install_fake_otel(monkeypatch, exporter_cls=_ExplodingExporter)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://broken:4317")
    monkeypatch.setattr(telemetry, "_initialized", False)
    monkeypatch.setattr(telemetry, "_tracer_provider", None)

    with caplog.at_level(logging.ERROR):
        telemetry.init_telemetry()

    assert telemetry._initialized is False
    assert telemetry._tracer_provider is None
    assert "Failed to initialize OpenTelemetry" in caplog.text


def test_span_helpers_attach_expected_attributes(monkeypatch) -> None:
    fake_tracer = _FakeTracer()
    monkeypatch.setattr(telemetry, "_get_tracer", lambda: fake_tracer)

    with telemetry.llm_call_span("openai", "gpt-4.1") as llm_span:
        assert isinstance(llm_span, _FakeSpan)
    with telemetry.safety_check_span() as safety_span:
        assert isinstance(safety_span, _FakeSpan)
    with telemetry.rbac_evaluation_span("Admin", "/reports") as rbac_span:
        assert isinstance(rbac_span, _FakeSpan)
    with telemetry.rag_retrieval_span(42) as rag_span:
        assert isinstance(rag_span, _FakeSpan)

    names = [name for name, _ in fake_tracer.started]
    assert names == [
        "llm.call",
        "safety.check",
        "rbac.evaluate",
        "rag.retrieve",
    ]
    assert fake_tracer.started[0][1].attributes == {
        "llm.provider": "openai",
        "llm.model": "gpt-4.1",
    }
    assert fake_tracer.started[2][1].attributes == {
        "rbac.role": "Admin",
        "rbac.resource": "/reports",
    }
    assert fake_tracer.started[3][1].attributes == {"rag.query_length": 42}


def test_otel_metrics_registers_expected_instruments(monkeypatch) -> None:
    class _FakeMeter:
        def __init__(self) -> None:
            self.counters = []
            self.histograms = []

        def create_counter(self, **kwargs):
            self.counters.append(kwargs)
            return kwargs

        def create_histogram(self, **kwargs):
            self.histograms.append(kwargs)
            return kwargs

    fake_meter = _FakeMeter()
    fake_metrics = types.ModuleType("opentelemetry.metrics")
    fake_metrics.get_meter = lambda name: fake_meter
    fake_opentelemetry = types.ModuleType("opentelemetry")
    fake_opentelemetry.metrics = fake_metrics

    monkeypatch.setitem(sys.modules, "opentelemetry", fake_opentelemetry)
    monkeypatch.setitem(sys.modules, "opentelemetry.metrics", fake_metrics)

    sys.modules.pop("app.otel_metrics", None)
    otel_metrics = importlib.import_module("app.otel_metrics")

    assert otel_metrics.meter is fake_meter
    assert [counter["name"] for counter in fake_meter.counters] == [
        "llm_requests_total",
        "safety_blocks_total",
        "rbac_denials_total",
    ]
    assert [histogram["name"] for histogram in fake_meter.histograms] == [
        "llm_request_duration_seconds",
        "rag_retrieval_duration_seconds",
    ]


def test_module_entrypoint_runs_uvicorn(monkeypatch) -> None:
    import uvicorn

    calls = {}

    def _fake_run(app, host, port, reload) -> None:
        calls.update(
            {"app": app, "host": host, "port": port, "reload": reload}
        )

    monkeypatch.setattr(uvicorn, "run", _fake_run)
    runpy.run_module("app.__main__", run_name="__main__")

    assert calls == {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": False,
    }
