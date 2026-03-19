"""
OpenTelemetry metrics for enterprise-llm-adoption-kit.

Opt-in: instruments are created unconditionally but produce no-op recordings
when the SDK has not been initialized (i.e. OTEL_EXPORTER_OTLP_ENDPOINT unset).

These complement the existing Prometheus metrics in metrics.py; use the OTEL
metrics when shipping to an OTLP-compatible collector.
"""

from __future__ import annotations

from opentelemetry import metrics

meter = metrics.get_meter("enterprise-llm-adoption-kit")

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

llm_requests_total = meter.create_counter(
    name="llm_requests_total",
    description="Total LLM requests",
    unit="1",
)

safety_blocks_total = meter.create_counter(
    name="safety_blocks_total",
    description="Total safety-blocked requests",
    unit="1",
)

rbac_denials_total = meter.create_counter(
    name="rbac_denials_total",
    description="Total RBAC denials",
    unit="1",
)

# ---------------------------------------------------------------------------
# Histograms
# ---------------------------------------------------------------------------

llm_request_duration = meter.create_histogram(
    name="llm_request_duration_seconds",
    description="LLM request duration in seconds",
    unit="s",
)

rag_retrieval_duration = meter.create_histogram(
    name="rag_retrieval_duration_seconds",
    description="RAG retrieval duration in seconds",
    unit="s",
)
