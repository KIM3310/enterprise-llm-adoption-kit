"""
OpenTelemetry instrumentation for enterprise-llm-adoption-kit.

Opt-in: telemetry is only active when OTEL_EXPORTER_OTLP_ENDPOINT is set.

Usage:
    from app.telemetry import init_telemetry, tracer
    init_telemetry()  # call once at startup
    with tracer.start_as_current_span("my-op"):
        ...
"""

from __future__ import annotations

import os
import logging
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)

_initialized = False
_tracer_provider = None

SERVICE_NAME = "enterprise-llm-adoption-kit"


def _read_env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def _resolve_otlp_trace_endpoint(raw_value: str | None = None) -> str | None:
    """Resolve the OTLP traces endpoint from standard env vars."""
    candidate = raw_value or _read_env("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or _read_env(
        "OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    if not candidate:
        return None

    normalized = candidate.rstrip("/")
    if normalized.endswith("/v1/traces"):
        return normalized
    return f"{normalized}/v1/traces"


def _parse_otlp_headers(raw_value: str | None = None) -> dict[str, str]:
    """Parse OTLP headers from a comma-separated env var."""
    header_value = raw_value if raw_value is not None else os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
    headers: dict[str, str] = {}
    for part in header_value.split(","):
        token = part.strip()
        if not token or "=" not in token:
            continue
        key, value = token.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            headers[key] = value
    return headers


def is_otel_enabled() -> bool:
    """Return True when the OTLP endpoint is configured."""
    return bool(_resolve_otlp_trace_endpoint())


def init_telemetry() -> None:
    """
    Initialize the OpenTelemetry SDK.  No-op when OTEL_EXPORTER_OTLP_ENDPOINT
    is not set so telemetry stays opt-in.
    """
    global _initialized, _tracer_provider
    if _initialized or not is_otel_enabled():
        return
    _initialized = True

    endpoint = _resolve_otlp_trace_endpoint()
    if not endpoint:
        _initialized = False
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME as RES_SVC

        resource = Resource(attributes={RES_SVC: SERVICE_NAME})
        provider = TracerProvider(resource=resource)
        headers = _parse_otlp_headers()

        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=headers or None,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _tracer_provider = provider
        logger.info("OpenTelemetry tracing initialized (service=%s)", SERVICE_NAME)
    except Exception:
        logger.exception("Failed to initialize OpenTelemetry; tracing disabled")
        _initialized = False


def shutdown_telemetry() -> None:
    """Flush and shut down the tracer provider."""
    global _tracer_provider, _initialized
    if _tracer_provider is not None:
        _tracer_provider.shutdown()
        _tracer_provider = None
        _initialized = False


def _get_tracer():
    """Return a tracer (real or no-op depending on init state)."""
    from opentelemetry import trace
    return trace.get_tracer(SERVICE_NAME)


# ---------------------------------------------------------------------------
# Convenience span helpers
# ---------------------------------------------------------------------------

@contextmanager
def llm_call_span(provider: str, model: str) -> Generator:
    """Span wrapping an LLM provider call."""
    tracer = _get_tracer()
    with tracer.start_as_current_span("llm.call") as span:
        span.set_attribute("llm.provider", provider)
        span.set_attribute("llm.model", model)
        yield span


@contextmanager
def safety_check_span() -> Generator:
    """Span wrapping a safety / injection check."""
    tracer = _get_tracer()
    with tracer.start_as_current_span("safety.check") as span:
        yield span


@contextmanager
def rbac_evaluation_span(role: str, resource: str) -> Generator:
    """Span wrapping an RBAC evaluation."""
    tracer = _get_tracer()
    with tracer.start_as_current_span("rbac.evaluate") as span:
        span.set_attribute("rbac.role", role)
        span.set_attribute("rbac.resource", resource)
        yield span


@contextmanager
def rag_retrieval_span(query_length: int = 0) -> Generator:
    """Span wrapping a RAG retrieval operation."""
    tracer = _get_tracer()
    with tracer.start_as_current_span("rag.retrieve") as span:
        span.set_attribute("rag.query_length", query_length)
        yield span
