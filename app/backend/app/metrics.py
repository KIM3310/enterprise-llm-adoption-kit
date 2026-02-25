"""Prometheus metric definitions for request, LLM, and policy observability.

All counters and histograms are defined at module scope so they are
registered once and shared across the application.  These feed into the
``/metrics`` endpoint consumed by Prometheus scrapers and the ops
runtime scorecard.
"""

from prometheus_client import Counter, Histogram

REQUEST_COUNTER = Counter(
    "requests_total",
    "Total requests",
    ["endpoint", "use_case", "role", "status"],
)

LATENCY_HIST = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    ["endpoint", "use_case"],
)

TOKENS_IN_COUNTER = Counter(
    "llm_tokens_in_total",
    "Total input tokens",
    ["use_case"],
)

TOKENS_OUT_COUNTER = Counter(
    "llm_tokens_out_total",
    "Total output tokens",
    ["use_case"],
)

COST_COUNTER = Counter(
    "llm_cost_usd_total",
    "Estimated LLM cost in USD",
    ["use_case"],
)

LLM_FAILURE_COUNTER = Counter(
    "llm_failures_total",
    "LLM failures after retry budget exhaustion",
    ["use_case", "provider"],
)

LLM_CIRCUIT_EVENT_COUNTER = Counter(
    "llm_circuit_events_total",
    "LLM circuit breaker events",
    ["provider", "event"],
)

POLICY_EVENT_COUNTER = Counter(
    "policy_events_total",
    "Policy events",
    ["event"],
)
