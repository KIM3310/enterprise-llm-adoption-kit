import React, { useEffect, useMemo, useRef, useState } from "react";
import heroTower from "./assets/hero-tower.svg";
import ExecutiveReviewPack from "./components/ExecutiveReviewPack.jsx";
import ServiceBriefBoard from "./components/ServiceBriefBoard.jsx";
import {
  buildReviewerShareUrl,
  parseReviewerUrlState,
  replaceReviewerUrlState,
} from "./urlState.js";

const API_BASE = String(import.meta.env.VITE_API_BASE || "").trim();
const FORMSPREE_ENDPOINT = String(import.meta.env.VITE_FORMSPREE_ENDPOINT || "").trim();
const DISQUS_SHORTNAME = String(import.meta.env.VITE_DISQUS_SHORTNAME || "").trim();
const DISQUS_IDENTIFIER = String(import.meta.env.VITE_DISQUS_IDENTIFIER || "atelier-home").trim();
const GISCUS_REPO = String(import.meta.env.VITE_GISCUS_REPO || "").trim();
const GISCUS_REPO_ID = String(import.meta.env.VITE_GISCUS_REPO_ID || "").trim();
const GISCUS_CATEGORY = String(import.meta.env.VITE_GISCUS_CATEGORY || "").trim();
const GISCUS_CATEGORY_ID = String(import.meta.env.VITE_GISCUS_CATEGORY_ID || "").trim();
const ADSENSE_CLIENT = "ca-pub-4973160293737562";
const DEFAULT_ADSENSE_SLOT = String(import.meta.env.VITE_ADSENSE_SLOT || "").trim();

const APP_NAME = "LLM Adoption Atelier";
const APP_TAGLINE = "Enterprise LLM Readiness Control Tower";

const roles = ["Employee", "Ops", "Admin"];
const pages = ["home", "capabilities", "validation", "scenario", "console"];

const navItems = [
  { key: "home", label: "Overview" },
  { key: "capabilities", label: "Capabilities" },
  { key: "validation", label: "Readiness" },
  { key: "scenario", label: "Scenario Runner" },
  { key: "console", label: "Console" }
];

const capabilityCards = [
  {
    title: "Role-Based Access Control",
    body: "Enforce least-privilege access by filtering retrieval to each role (Employee/Ops/Admin)."
  },
  {
    title: "RAG Retrieval with Citations",
    body: "Return grounded answers with field-level citations so reviewers can verify provenance fast."
  },
  {
    title: "Architecture Risk Diagnosis",
    body: "Diagnose security and reliability risks from architecture prompts, then justify with evidence."
  },
  {
    title: "Operations Log Risk Analysis",
    body: "Turn noisy incident logs into a structured summary, hypotheses, and actionable runbook steps."
  },
  {
    title: "Safety Guardrails",
    body: "Detect prompt injection patterns and apply refusal policies before model calls."
  },
  {
    title: "PII Redaction and Audit",
    body: "Mask sensitive content and emit audit events for accountability and compliance reviews."
  },
  {
    title: "Governance Summary",
    body: "Review requests, policy events, tool usage, and daily cost in a single decision-ready view."
  },
  {
    title: "Metrics and Eval Readiness",
    body: "Expose latency/token/cost/policy metrics and keep the system eval-ready for regression checks."
  }
];

const validationActs = [
  {
    title: "Act 1 - Discovery to Scope",
    text: "Define outcomes, roles, and data sensitivity to lock the real adoption scope."
  },
  {
    title: "Act 2 - Security and Evals",
    text: "Validate RBAC, redaction, injection defenses, and measurable eval criteria."
  },
  {
    title: "Act 3 - Operations Proof",
    text: "Verify audit and metrics end-to-end so operations can trust what ships to production."
  }
];

const scenarioSteps = [
  {
    title: "Identity and Role Check",
    text: "Issue a JWT and confirm least-privilege access behavior.",
    endpoint: "/auth/login"
  },
  {
    title: "Architecture Risk Diagnosis",
    text: "Run the architecture advisor and verify citations are consistent and relevant.",
    endpoint: "/uc1/architecture"
  },
  {
    title: "Operations Log Risk Analysis",
    text: "Generate incident hypotheses and runbook steps from raw operational logs.",
    endpoint: "/uc2/log-intel"
  },
  {
    title: "Governance and Observability",
    text: "Review audit + cost metrics to decide if the system is production-ready.",
    endpoint: "/audit/summary · /metrics"
  }
];

function buildStaticServiceBrief() {
  return {
    service: "Enterprise LLM Adoption Kit (Korea)",
    contract_version: "enterprise-adoption-service-brief-v1",
    tagline: "Discovery -> Secure Architecture -> Evals -> Deployment/LLMOps",
    maturity_stage: "pre-production validation system",
    audiences: [
      "Solutions Architect",
      "Platform Engineering",
      "Security Review",
      "Customer Success",
      "Executive Sponsor",
    ],
    runtime: {
      auth_mode: "local_jwt",
      data_handling_mode: "demo",
      storage_backend: "sqlite",
      llm_provider: "stub",
      llm_model: "stub-llm",
      openai_api_key_configured: false,
      login_code_required: false,
      integrations_require_auth: true,
      startup_status: "portfolio-static",
      startup_ready: true,
      llm_circuit_state: "closed",
    },
    evidence: {
      test_files: 22,
      blueprint_docs: 9,
      module_packs: 4,
      eval_datasets: 5,
      eval_reports: 9,
      application_artifacts: 9,
    },
    run_modes: ["local-jwt demo", "docker compose", "ollama local", "openai compatible"],
    platform_targets: ["aws", "databricks", "mariadb", "palantir", "snowflake"],
    strengths: [
      "One repo ties discovery, governance, evals, runtime diagnostics, and executive review together.",
      "Scenario Runner and ops surfaces make the portfolio feel like a working service instead of a static deck.",
      "Platform mapping speaks directly to AWS, Snowflake, and Palantir-flavored deployment conversations.",
      "Static fallback keeps the review surface readable even when the backend is not running.",
    ],
    watchouts: [
      "Static mode is active until the backend serves /ops/service-brief.",
      "Default portfolio runtime stays in stub mode; switch to Ollama or OpenAI for live reviewer demos.",
      "Enable enterprise data handling mode and a shared login code before regulated workshop sessions.",
    ],
    stages: [
      {
        key: "discovery",
        label: "Discovery to Scope",
        readiness: "ready",
        artifact_count: 3,
        highlights: [
          {
            label: "Discovery questionnaire",
            path: "docs/sales/discovery_questionnaire.md",
            kind: "doc",
          },
          {
            label: "Customer journey blueprint",
            path: "docs/blueprint/09_customer_journey.md",
            kind: "doc",
          },
          {
            label: "Role alignment",
            path: "docs/application/role_alignment.md",
            kind: "doc",
          },
        ],
      },
      {
        key: "security",
        label: "Security and Governance",
        readiness: "ready",
        artifact_count: 4,
        highlights: [
          {
            label: "Security threat model",
            path: "docs/blueprint/03_security_threat_model.md",
            kind: "doc",
          },
          {
            label: "Security governance",
            path: "docs/architecture/security_governance.md",
            kind: "doc",
          },
          {
            label: "Redaction test",
            path: "tests/test_redaction.py",
            kind: "test",
          },
          {
            label: "Injection test",
            path: "tests/test_injection.py",
            kind: "test",
          },
        ],
      },
      {
        key: "evals",
        label: "Evaluation and Regression",
        readiness: "ready",
        artifact_count: 4,
        highlights: [
          {
            label: "Eval plan",
            path: "docs/blueprint/04_evals_plan.md",
            kind: "doc",
          },
          {
            label: "Latest eval report",
            path: "evals/reports/latest_report.md",
            kind: "report",
          },
          {
            label: "Eval gate",
            path: "docs/evals/eval_gate.md",
            kind: "doc",
          },
          {
            label: "Eval runner test",
            path: "tests/test_eval_runner.py",
            kind: "test",
          },
        ],
      },
      {
        key: "deployment",
        label: "Deployment and Integration",
        readiness: "ready",
        artifact_count: 4,
        highlights: [
          {
            label: "Deployment options",
            path: "docs/architecture/llm_deployment_options.md",
            kind: "doc",
          },
          {
            label: "AWS reference architecture",
            path: "docs/architecture/aws_openai_reference_architecture.md",
            kind: "doc",
          },
          {
            label: "Integration pack",
            path: "docs/modules/integration-pack/README.md",
            kind: "doc",
          },
          {
            label: "Docker compose",
            path: "infra/docker-compose.yml",
            kind: "doc",
          },
        ],
      },
      {
        key: "operations",
        label: "Operations and Executive Review",
        readiness: "ready",
        artifact_count: 4,
        highlights: [
          {
            label: "Ops runtime endpoint",
            path: "app/backend/app/main.py",
            kind: "endpoint",
          },
          {
            label: "Exec value dashboard",
            path: "docs/sales/exec_value_dashboard/latest.md",
            kind: "doc",
          },
          {
            label: "Audit viewer guide",
            path: "docs/ops/audit_viewer.md",
            kind: "doc",
          },
          {
            label: "Executive dashboard test",
            path: "tests/test_exec_dashboard.py",
            kind: "test",
          },
        ],
      },
    ],
    review_flow: [
      {
        order: 1,
        title: "Issue a role-aware token",
        endpoint: "/auth/login",
        evidence_path: "docs/blueprint/06_acceptance_tests.md",
        persona: "operator",
      },
      {
        order: 2,
        title: "Run architecture diagnosis with citations",
        endpoint: "/uc1/architecture",
        evidence_path: "docs/sales/demo_script_exec.md",
        persona: "buyer",
      },
      {
        order: 3,
        title: "Run log-intel and inspect actionability",
        endpoint: "/uc2/log-intel",
        evidence_path: "docs/ops/eval_report_ko.md",
        persona: "platform",
      },
      {
        order: 4,
        title: "Verify audit, metrics, and ops runtime",
        endpoint: "/audit/summary -> /ops/runtime -> /metrics",
        evidence_path: "docs/sales/exec_value_dashboard/latest.md",
        persona: "exec",
      },
    ],
    links: {
      health: "/health",
      service_brief: "/ops/service-brief",
      service_brief_schema: "/ops/service-brief/schema",
      review_pack: "/ops/review-pack",
      metrics: "/metrics",
      audit_summary: "/audit/summary",
      ops_runtime: "/ops/runtime",
      control_tower_spec: "/v1/control-tower/spec",
      customer_journey: "docs/blueprint/09_customer_journey.md",
      role_alignment: "docs/application/role_alignment.md",
    },
  };
}

function buildStaticServiceBriefSchema() {
  return {
    schema: "enterprise-adoption-service-brief-v1",
    required_fields: [
      "service",
      "contract_version",
      "tagline",
      "maturity_stage",
      "audiences",
      "runtime",
      "evidence",
      "run_modes",
      "platform_targets",
      "stages",
      "review_flow",
      "links",
    ],
    runtime_required_fields: [
      "auth_mode",
      "data_handling_mode",
      "storage_backend",
      "llm_provider",
      "llm_model",
      "openai_api_key_configured",
      "login_code_required",
      "integrations_require_auth",
      "startup_status",
      "startup_ready",
      "llm_circuit_state",
    ],
    evidence_required_fields: [
      "test_files",
      "blueprint_docs",
      "module_packs",
      "eval_datasets",
      "eval_reports",
      "application_artifacts",
    ],
    stage_keys: ["discovery", "security", "evals", "deployment", "operations"],
  };
}

function buildStaticReviewPack() {
  return {
    service: "Enterprise LLM Adoption Kit (Korea)",
    generated_at: new Date().toISOString(),
    contract_version: "enterprise-adoption-review-pack-v1",
    headline:
      "Executive review pack that ties buyer thesis, governance proof, and rollout tracks to one validation story.",
    buyer_promises: [
      "Show a secure adoption path before rollout by grounding every claim in tests, docs, or runtime endpoints.",
      "Keep the architecture conversation concrete across AWS, Snowflake, Palantir, Databricks, and MariaDB-flavored decisions.",
      "Move from discovery to proof with a runnable system, not a static deck.",
    ],
    runtime_summary: {
      auth_mode: "local_jwt",
      llm_provider: "stub",
      llm_model: "stub-llm",
      startup_status: "portfolio-static",
      startup_ready: true,
      llm_circuit_state: "closed",
    },
    proof_bundle: {
      tests: 22,
      blueprints: 9,
      module_packs: 4,
      eval_assets: 14,
      application_artifacts: 9,
      review_assets_count: 5,
      review_assets: [
        {
          label: "Executive dashboard markdown",
          path: "docs/sales/exec_value_dashboard/latest.md",
          kind: "doc",
        },
        {
          label: "Executive dashboard snapshot",
          path: "docs/sales/exec_value_dashboard/snapshot.svg",
          kind: "doc",
        },
        {
          label: "Security compliance packet",
          path: "docs/sales/security_compliance_packet.md",
          kind: "doc",
        },
        {
          label: "Latest eval report",
          path: "evals/reports/latest_report.md",
          kind: "report",
        },
        {
          label: "Customer journey blueprint",
          path: "docs/blueprint/09_customer_journey.md",
          kind: "doc",
        },
      ],
      platform_targets: ["aws", "databricks", "mariadb", "palantir", "snowflake"],
      runtime_surfaces: [
        "/health",
        "/ops/service-brief",
        "/ops/review-pack",
        "/ops/review-pack/schema",
        "/ops/runtime",
        "/metrics",
      ],
      review_endpoints: [
        "/health",
        "/ops/service-brief",
        "/ops/review-pack",
        "/ops/review-pack/schema",
        "/audit/summary",
        "/metrics",
      ],
    },
    review_actions: [
      {
        label: "Check buyer-ready runtime posture",
        surface: "/ops/service-brief",
        proof: "Review maturity stage, runtime posture, and stage evidence before the demo.",
      },
      {
        label: "Inspect executive overview",
        surface: "/ops/review-pack",
        proof: "Use the review pack to walk buyer promises, rollout tracks, and platform dialogue.",
      },
      {
        label: "Verify governance signals",
        surface: "/audit/summary -> /metrics",
        proof: "Confirm auditability, policy events, and cost/latency visibility.",
      },
      {
        label: "Map the deployment path",
        surface: "docs/architecture/llm_deployment_options.md",
        proof: "Choose API-first, workspace-first, or hybrid rollout with evidence-backed tradeoffs.",
      },
    ],
    two_minute_review: [
      {
        step: "1. Runtime posture",
        surface: "/ops/service-brief",
        proof: "Confirm maturity stage, startup readiness, runtime mode, and evidence counts before the walkthrough.",
      },
      {
        step: "2. Executive overview",
        surface: "/ops/review-pack",
        proof: "Use buyer promises, proof assets, and rollout tracks to frame the system in one pass.",
      },
      {
        step: "3. Governance path",
        surface: "/audit/summary -> /metrics",
        proof: "Show auditability, policy events, and cost/latency visibility without leaving the runtime surface.",
      },
      {
        step: "4. Deployment decision",
        surface: "docs/architecture/llm_deployment_options.md -> docs/blueprint/09_customer_journey.md",
        proof: "Tie runtime evidence back to rollout strategy and customer journey in one review path.",
      },
    ],
    rollout_tracks: [
      {
        track: "api-first validation",
        fit_for: ["solution architecture review", "security pilot", "ops workshop"],
        evidence: "docs/architecture/llm_deployment_options.md",
      },
      {
        track: "workspace-first enablement",
        fit_for: ["business user pilot", "low-code adoption", "change management"],
        evidence: "docs/sales/llm_workspace_checklist.md",
      },
      {
        track: "hybrid control tower",
        fit_for: ["platform governance", "evaluation gate", "quarterly business review"],
        evidence: "docs/sales/qbr_template.md",
      },
    ],
    platform_dialogues: [
      "aws: map discovery, governance, and deployment decisions into the customer's preferred platform language.",
      "databricks: map discovery, governance, and deployment decisions into the customer's preferred platform language.",
      "mariadb: map discovery, governance, and deployment decisions into the customer's preferred platform language.",
      "palantir: map discovery, governance, and deployment decisions into the customer's preferred platform language.",
      "snowflake: map discovery, governance, and deployment decisions into the customer's preferred platform language.",
    ],
    review_sequence: [
      "1. Issue a role-aware token -> /auth/login",
      "2. Run architecture diagnosis with citations -> /uc1/architecture",
      "3. Run log-intel and inspect actionability -> /uc2/log-intel",
      "4. Verify audit, metrics, and ops runtime -> /audit/summary -> /ops/runtime -> /metrics",
    ],
    stage_map: [
      "Discovery to Scope",
      "Security and Governance",
      "Evaluation and Regression",
      "Deployment and Integration",
      "Operations and Executive Review",
    ],
    watchouts: [
      "Static mode is active until the backend serves /ops/review-pack.",
      "Default portfolio runtime stays in stub mode; switch to Ollama or OpenAI for live reviewer demos.",
      "Enable enterprise data handling mode and a shared login code before regulated workshop sessions.",
    ],
    links: {
      health: "/health",
      service_brief: "/ops/service-brief",
      review_pack: "/ops/review-pack",
      review_pack_schema: "/ops/review-pack/schema",
      metrics: "/metrics",
      audit_summary: "/audit/summary",
      customer_journey: "docs/blueprint/09_customer_journey.md",
      deployment_options: "docs/architecture/llm_deployment_options.md",
      exec_summary_template: "docs/sales/executive_summary_template.md",
      qbr_template: "docs/sales/qbr_template.md",
    },
  };
}

const SAMPLE_ARCHITECTURE_JSONL = [
  JSON.stringify({
    doc_id: "ACME-0001",
    title: "Payments Production Handover",
    system: "payments",
    env: "prod",
    access_group: "ops",
    owner: { name: "Platform Owner", team: "Payments", contact: "owner@acme-ops.ai" },
    summary: "Payments service architecture with external gateway dependency.",
    handover_notes: "Monitor timeout spikes and queue depth after deployment.",
    runbook_steps: [
      "Check API latency dashboard.",
      "Validate recent deployment diff.",
      "Rollback if p95 exceeds threshold."
    ],
    dependencies: ["postgres", "redis", "gateway"],
    risks: ["traffic spike", "upstream timeout"],
    last_updated: "2026-02-12"
  }),
  JSON.stringify({
    doc_id: "ACME-0002",
    title: "Analytics Staging Handover",
    system: "analytics",
    env: "staging",
    access_group: "admin",
    owner: { name: "Data Lead", team: "Analytics", contact: "data@acme-ops.ai" },
    summary: "Analytics pipeline architecture for staged model validation.",
    handover_notes: "Validate schema drift alerts before production sync.",
    runbook_steps: [
      "Run drift diagnostics.",
      "Check staging job failures.",
      "Approve sync window with ops."
    ],
    dependencies: ["spark", "object-storage"],
    risks: ["schema drift", "job backlog"],
    last_updated: "2026-02-12"
  })
].join("\n");

function isValidAdSenseSlot(value) {
  return /^\d{8,20}$/.test(String(value || "").trim()) && String(value || "").trim() !== "1234567890";
}

function AdSenseSlot({ slot = "" }) {
  const pushedRef = useRef(false);
  const activeSlot = String(slot || "").trim();
  const adsReady = isValidAdSenseSlot(activeSlot);

  useEffect(() => {
    if (!adsReady || pushedRef.current) {
      return;
    }
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
      pushedRef.current = true;
    } catch (_err) {
      // no-op
    }
  }, [adsReady, activeSlot]);

  if (!adsReady) {
    return (
      <div className="adsense-placeholder">
        Sponsored slot is in standby mode. Set a valid AdSense slot ID in the Sponsored panel or{" "}
        <code>VITE_ADSENSE_SLOT</code>.
      </div>
    );
  }

  return (
    <ins
      className="adsbygoogle adsense-box"
      style={{ display: "block" }}
      data-ad-client={ADSENSE_CLIENT}
      data-ad-slot={activeSlot}
      data-ad-format="auto"
      data-full-width-responsive="true"
    />
  );
}

function getPageFromHash() {
  const hash = window.location.hash.replace("#", "").trim().toLowerCase();
  return pages.includes(hash) ? hash : "home";
}

const STORAGE_KEYS = {
  userId: "atelier.user_id",
  role: "atelier.role",
  loginCode: "atelier.login_code",
  scenarioHistory: "atelier.scenario_history.v1",
  adsenseSlot: "atelier.adsense_slot.v1"
};

function safeStorageGet(key, fallback = "") {
  try {
    const value = window.localStorage.getItem(key);
    return value == null ? fallback : value;
  } catch (_err) {
    return fallback;
  }
}

function safeStorageSet(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch (_err) {
    // ignore
  }
}

function safeJsonParse(raw, fallback) {
  if (!raw) {
    return fallback;
  }
  try {
    return JSON.parse(raw);
  } catch (_err) {
    return fallback;
  }
}

function safeJsonStringify(value, fallback = "") {
  try {
    return JSON.stringify(value);
  } catch (_err) {
    return fallback;
  }
}

function readJsonStorage(key, fallback) {
  return safeJsonParse(safeStorageGet(key, ""), fallback);
}

function writeJsonStorage(key, value) {
  safeStorageSet(key, safeJsonStringify(value, ""));
}

async function copyTextToClipboard(text) {
  const payload = String(text ?? "");
  try {
    await navigator.clipboard.writeText(payload);
    return true;
  } catch (_err) {
    // Fallback for older browsers / permissions.
    try {
      const textarea = document.createElement("textarea");
      textarea.value = payload;
      textarea.style.position = "fixed";
      textarea.style.top = "-1000px";
      textarea.style.left = "-1000px";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      const ok = document.execCommand("copy");
      textarea.remove();
      return ok;
    } catch (_err2) {
      return false;
    }
  }
}

function parseApiError(payload, fallback) {
  const detail = payload?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail.trim();
  }
  if (detail && typeof detail === "object") {
    if (typeof detail.message === "string" && detail.message.trim()) {
      return detail.message.trim();
    }
    if (typeof detail.error === "string" && detail.error.trim()) {
      return detail.error.trim();
    }
  }
  if (typeof payload?.error === "string" && payload.error.trim()) {
    return payload.error.trim();
  }
  return fallback;
}

function withRequestId(message, requestId) {
  return requestId ? `${message} (${requestId})` : message;
}

function csvCell(value) {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, "\"\"")}"`;
}

function exportCsvFile(filename, columns, rows, metadata = []) {
  const lines = [];
  if (Array.isArray(metadata) && metadata.length > 0) {
    lines.push([csvCell("__meta__"), csvCell("key"), csvCell("value")].join(","));
    metadata.forEach(([key, value]) => {
      lines.push([csvCell("__meta__"), csvCell(key), csvCell(value)].join(","));
    });
    lines.push("");
  }
  lines.push(columns.map((column) => csvCell(column)).join(","));
  rows.forEach((row) => {
    lines.push(row.map((item) => csvCell(item)).join(","));
  });
  const csv = `\uFEFF${lines.join("\n")}`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function exportTextFile(filename, content, mime = "text/plain;charset=utf-8") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

const SEVERITY_ORDER = {
  critical: 3,
  warning: 2,
  info: 1
};

function parseIsoTime(value) {
  const parsed = Date.parse(String(value || ""));
  return Number.isNaN(parsed) ? 0 : parsed;
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 20000) {
  const safeTimeoutMs = Math.max(1000, Math.min(120000, Number(timeoutMs) || 20000));
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), safeTimeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(`Request timed out after ${Math.round(safeTimeoutMs / 1000)}s`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function formatRuntimeTime(value) {
  const parsed = parseIsoTime(value);
  return parsed ? new Date(parsed).toLocaleString() : String(value || "-");
}

function severityBadgeClass(value) {
  const severity = String(value || "info").trim().toLowerCase();
  if (severity === "critical" || severity === "blocked") {
    return "pill pill-critical";
  }
  if (severity === "warning" || severity === "high") {
    return "pill pill-warning";
  }
  return "pill pill-info";
}

function levelBadgeClass(value) {
  const level = String(value || "INFO").trim().toUpperCase();
  if (level === "ERROR") {
    return "pill pill-critical";
  }
  if (level === "WARN" || level === "WARNING") {
    return "pill pill-warning";
  }
  return "pill pill-info";
}

function Reveal({ children, className = "", delay = 0 }) {
  const ref = useRef(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) {
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            node.classList.add("is-visible");
            observer.unobserve(node);
          }
        });
      },
      { threshold: 0.2, rootMargin: "0px 0px -8% 0px" }
    );

    observer.observe(node);

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className={`reveal ${className}`} style={{ "--delay": `${delay}ms` }}>
      {children}
    </div>
  );
}

function Icon({ name = "default" }) {
  const common = {
    width: 22,
    height: 22,
    viewBox: "0 0 24 24",
    fill: "none",
    xmlns: "http://www.w3.org/2000/svg"
  };

  const stroke = {
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round"
  };

  if (name === "architecture") {
    return (
      <svg {...common}>
        <path {...stroke} d="M12 7V5" />
        <path {...stroke} d="M12 19v-2" />
        <path {...stroke} d="M7.2 9.2L5.8 7.8" />
        <path {...stroke} d="M18.2 16.2l-1.4-1.4" />
        <path {...stroke} d="M16.8 9.2l1.4-1.4" />
        <path {...stroke} d="M5.8 16.2l1.4-1.4" />
        <circle cx="12" cy="12" r="2.5" {...stroke} />
        <circle cx="12" cy="5" r="1.6" {...stroke} />
        <circle cx="12" cy="19" r="1.6" {...stroke} />
        <circle cx="5" cy="12" r="1.6" {...stroke} />
        <circle cx="19" cy="12" r="1.6" {...stroke} />
        <path {...stroke} d="M9.7 10.7L6.6 11.6" />
        <path {...stroke} d="M14.3 10.7l3.1.9" />
        <path {...stroke} d="M9.7 13.3L6.6 12.4" />
        <path {...stroke} d="M14.3 13.3l3.1-.9" />
      </svg>
    );
  }

  if (name === "ops") {
    return (
      <svg {...common}>
        <path {...stroke} d="M3 12h4l2-6 4 14 2-6h6" />
        <path {...stroke} d="M4 19h16" opacity="0.35" />
        <path {...stroke} d="M4 5h16" opacity="0.35" />
      </svg>
    );
  }

  if (name === "governance") {
    return (
      <svg {...common}>
        <path
          {...stroke}
          d="M12 3l7 4v6c0 5-3.2 8.2-7 9-3.8-.8-7-4-7-9V7l7-4z"
        />
        <path {...stroke} d="M8.5 12.5l2.2 2.2L15.8 9.6" />
      </svg>
    );
  }

  return (
    <svg {...common}>
      <path {...stroke} d="M12 2v20" opacity="0.15" />
      <path {...stroke} d="M2 12h20" opacity="0.15" />
      <circle cx="12" cy="12" r="5" {...stroke} />
    </svg>
  );
}

export default function App() {
  const initialReviewerUrlState =
    typeof window === "undefined"
      ? {}
      : parseReviewerUrlState(window.location.search, window.location.hash);
  const [page, setPage] = useState(() => initialReviewerUrlState.page || getPageFromHash());
  const [userId, setUserId] = useState(() => safeStorageGet(STORAGE_KEYS.userId, "acme-demo"));
  const [role, setRole] = useState(() => {
    if (initialReviewerUrlState.role && roles.includes(initialReviewerUrlState.role)) {
      return initialReviewerUrlState.role;
    }
    const stored = safeStorageGet(STORAGE_KEYS.role, "Employee");
    return roles.includes(stored) ? stored : "Employee";
  });
  const [loginCode, setLoginCode] = useState(() => safeStorageGet(STORAGE_KEYS.loginCode, ""));
  const [token, setToken] = useState("");
  const [activeTab, setActiveTab] = useState(() => initialReviewerUrlState.tab || "architecture");
  const [status, setStatus] = useState("Ready");
  const [lastRequestId, setLastRequestId] = useState("");
  const [health, setHealth] = useState({
    status: "unknown",
    startup_status: "",
    auth_mode: "",
    login_code_required: false,
    data_handling_mode: "",
    storage_backend: "",
    integrations_require_auth: false,
    llm_fallback_to_stub_on_error: true,
    llm_circuit_state: "closed",
    llm_circuit_open_seconds_remaining: 0,
    llm_circuit_consecutive_failures: 0,
    request_max_body_bytes: 0,
    llm_provider: "",
    llm_model: "",
    openai_api_key_configured: false
  });
  const [healthCheckedAt, setHealthCheckedAt] = useState("");
  const [serviceBrief, setServiceBrief] = useState(() => buildStaticServiceBrief());
  const [serviceBriefSchema, setServiceBriefSchema] = useState(() => buildStaticServiceBriefSchema());
  const [reviewPack, setReviewPack] = useState(() => buildStaticReviewPack());
  const [scenarioRun, setScenarioRun] = useState(null);
  const [scenarioHistory, setScenarioHistory] = useState(() => {
    const stored = readJsonStorage(STORAGE_KEYS.scenarioHistory, []);
    return Array.isArray(stored) ? stored : [];
  });
  const [adsenseSlotInput, setAdsenseSlotInput] = useState(() =>
    safeStorageGet(STORAGE_KEYS.adsenseSlot, DEFAULT_ADSENSE_SLOT)
  );
  const activeAdSenseSlot = String(adsenseSlotInput || "").trim();
  const adSenseSlotReady = isValidAdSenseSlot(activeAdSenseSlot);

  useEffect(() => {
    safeStorageSet(STORAGE_KEYS.userId, userId);
  }, [userId]);

  useEffect(() => {
    safeStorageSet(STORAGE_KEYS.role, role);
  }, [role]);

  useEffect(() => {
    safeStorageSet(STORAGE_KEYS.loginCode, loginCode);
  }, [loginCode]);

  useEffect(() => {
    writeJsonStorage(STORAGE_KEYS.scenarioHistory, scenarioHistory);
  }, [scenarioHistory]);

  useEffect(() => {
    safeStorageSet(STORAGE_KEYS.adsenseSlot, activeAdSenseSlot);
  }, [activeAdSenseSlot]);

  const [diagnosisQuery, setDiagnosisQuery] = useState(
    "Prioritize the top security and reliability risks in our LLM adoption architecture. Provide evidence-backed mitigation steps."
  );
  const [diagnosisCitationOnly, setDiagnosisCitationOnly] = useState(false);
  const [targetSystem, setTargetSystem] = useState("");
  const [targetEnv, setTargetEnv] = useState("");
  const [diagnosisResponse, setDiagnosisResponse] = useState(null);

  const [opsLogs, setOpsLogs] = useState("ERROR Timeout while calling payments API");
  const [opsResponse, setOpsResponse] = useState(null);

  const [governanceSummary, setGovernanceSummary] = useState(null);
  const [governanceError, setGovernanceError] = useState("");
  const [runtimeSnapshot, setRuntimeSnapshot] = useState(null);
  const [runtimeError, setRuntimeError] = useState("");
  const [isRefreshingDiagnostics, setIsRefreshingDiagnostics] = useState(false);
  const [runtimeEventsLimit, setRuntimeEventsLimit] = useState(20);
  const [runtimeDecisionsLimit, setRuntimeDecisionsLimit] = useState(10);
  const [runtimeWindowMinutes, setRuntimeWindowMinutes] = useState(60);
  const [runtimeLevelFilter, setRuntimeLevelFilter] = useState("");
  const [runtimeComponentFilter, setRuntimeComponentFilter] = useState("");
  const [runtimeAutoRefresh, setRuntimeAutoRefresh] = useState(false);
  const [runtimeAutoRefreshSec, setRuntimeAutoRefreshSec] = useState(15);
  const [runtimeLastLoadedAt, setRuntimeLastLoadedAt] = useState("");
  const [runtimeSnapshotRequestId, setRuntimeSnapshotRequestId] = useState("");
  const [runtimeSearchTerm, setRuntimeSearchTerm] = useState("");
  const [runtimeAlertSeverity, setRuntimeAlertSeverity] = useState("all");
  const [runtimeSortOrder, setRuntimeSortOrder] = useState("desc");
  const [runtimeOnlyErrors, setRuntimeOnlyErrors] = useState(false);
  const [llmRuntime, setLlmRuntime] = useState(null);
  const [llmRuntimeError, setLlmRuntimeError] = useState("");
  const [llmRuntimeForm, setLlmRuntimeForm] = useState({
    provider: "stub",
    model: "stub-llm",
    temperature: "0.2",
    max_tokens: "512",
    timeout_sec: "30",
    openai_base_url: "https://api.openai.com/v1",
    ollama_base_url: "http://127.0.0.1:11434",
    openai_org: "",
    openai_api_key: ""
  });
  const [isSavingLlmRuntime, setIsSavingLlmRuntime] = useState(false);
  const [userApiKeyInput, setUserApiKeyInput] = useState("");
  const [userApiKeyView, setUserApiKeyView] = useState(null);
  const [userApiKeyError, setUserApiKeyError] = useState("");
  const [isSavingUserApiKey, setIsSavingUserApiKey] = useState(false);
  const [architectureCatalog, setArchitectureCatalog] = useState(null);
  const [architectureJsonl, setArchitectureJsonl] = useState("");
  const [architectureError, setArchitectureError] = useState("");
  const [isImportingArchitecture, setIsImportingArchitecture] = useState(false);
  const [isReindexingArchitecture, setIsReindexingArchitecture] = useState(false);
  const [slackText, setSlackText] = useState("/uc2 ERROR Timeout while calling payments API");
  const [slackChannel, setSlackChannel] = useState("ops-incidents");
  const [slackResponse, setSlackResponse] = useState(null);
  const [slackError, setSlackError] = useState("");
  const [jiraTicketId, setJiraTicketId] = useState("INC-1001");
  const [jiraTitle, setJiraTitle] = useState("Payments API timeout spikes");
  const [jiraDescription, setJiraDescription] = useState("ERROR Timeout while calling payments API");
  const [jiraPriority, setJiraPriority] = useState("High");
  const [jiraResponse, setJiraResponse] = useState(null);
  const [jiraError, setJiraError] = useState("");
  const [communityName, setCommunityName] = useState("");
  const [communityEmail, setCommunityEmail] = useState("");
  const [communityMessage, setCommunityMessage] = useState("");
  const [communitySubmitStatus, setCommunitySubmitStatus] = useState("idle");
  const [communityNotice, setCommunityNotice] = useState("");
  const disqusLoadedRef = useRef(false);
  const giscusContainerRef = useRef(null);

  useEffect(() => {
    const onHashChange = () => setPage(getPageFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [page]);

  useEffect(() => {
    replaceReviewerUrlState({ page, tab: activeTab, role });
  }, [activeTab, page, role]);

  useEffect(() => {
    if (!DISQUS_SHORTNAME || typeof document === "undefined" || disqusLoadedRef.current) {
      return;
    }
    const script = document.createElement("script");
    script.id = "atelier-disqus-script";
    script.src = `https://${DISQUS_SHORTNAME}.disqus.com/embed.js`;
    script.async = true;
    script.setAttribute("data-timestamp", String(Date.now()));
    script.setAttribute("data-identifier", DISQUS_IDENTIFIER);
    document.body.appendChild(script);
    disqusLoadedRef.current = true;
  }, []);

  useEffect(() => {
    const node = giscusContainerRef.current;
    if (!node || !GISCUS_REPO || !GISCUS_REPO_ID || !GISCUS_CATEGORY || !GISCUS_CATEGORY_ID) {
      return;
    }
    if (node.querySelector("script[data-giscus]")) {
      return;
    }
    const script = document.createElement("script");
    script.src = "https://giscus.app/client.js";
    script.async = true;
    script.setAttribute("data-giscus", "1");
    script.setAttribute("data-repo", GISCUS_REPO);
    script.setAttribute("data-repo-id", GISCUS_REPO_ID);
    script.setAttribute("data-category", GISCUS_CATEGORY);
    script.setAttribute("data-category-id", GISCUS_CATEGORY_ID);
    script.setAttribute("data-mapping", "pathname");
    script.setAttribute("data-strict", "0");
    script.setAttribute("data-reactions-enabled", "1");
    script.setAttribute("data-emit-metadata", "0");
    script.setAttribute("data-input-position", "top");
    script.setAttribute("data-theme", "light");
    script.setAttribute("data-lang", "en");
    script.crossOrigin = "anonymous";
    node.appendChild(script);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const res = await fetchWithTimeout(`${API_BASE}/health`, { cache: "no-store" }, 8000);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(parseApiError(data, "Health check failed"));
        }
        if (cancelled) {
          return;
        }
        setHealth({
          status: String(data.status || "ok"),
          startup_status: String(data.startup_status || ""),
          auth_mode: String(data.auth_mode || ""),
          login_code_required: Boolean(data.login_code_required),
          data_handling_mode: String(data.data_handling_mode || ""),
          storage_backend: String(data.storage_backend || ""),
          integrations_require_auth: Boolean(data.integrations_require_auth),
          llm_fallback_to_stub_on_error: Boolean(data.llm_fallback_to_stub_on_error),
          llm_circuit_state: String(data.llm_circuit_state || "closed"),
          llm_circuit_open_seconds_remaining: Number(data.llm_circuit_open_seconds_remaining || 0),
          llm_circuit_consecutive_failures: Number(data.llm_circuit_consecutive_failures || 0),
          request_max_body_bytes: Number(data.request_max_body_bytes || 0),
          llm_provider: String(data.llm_provider || ""),
          llm_model: String(data.llm_model || ""),
          openai_api_key_configured: Boolean(data.openai_api_key_configured)
        });
        setHealthCheckedAt(new Date().toLocaleTimeString());
      } catch (_error) {
        if (cancelled) {
          return;
        }
        setHealth({
          status: "offline",
          startup_status: "",
          auth_mode: "",
          login_code_required: false,
          data_handling_mode: "",
          storage_backend: "",
          integrations_require_auth: false,
          llm_fallback_to_stub_on_error: true,
          llm_circuit_state: "closed",
          llm_circuit_open_seconds_remaining: 0,
          llm_circuit_consecutive_failures: 0,
          request_max_body_bytes: 0,
          llm_provider: "",
          llm_model: "",
          openai_api_key_configured: false
        });
        setHealthCheckedAt(new Date().toLocaleTimeString());
      }
    }

    void loadHealth();
    const timerId = window.setInterval(() => void loadHealth(), 12000);
    return () => {
      cancelled = true;
      window.clearInterval(timerId);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadServiceBrief() {
      try {
        const response = await fetchWithTimeout(`${API_BASE}/ops/service-brief`, { cache: "no-store" }, 8000);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(parseApiError(data, "Service brief request failed"));
        }
        if (!cancelled) {
          setServiceBrief(data);
        }
      } catch (_error) {
        if (!cancelled) {
          setServiceBrief(buildStaticServiceBrief());
        }
      }

      try {
        const response = await fetchWithTimeout(`${API_BASE}/ops/service-brief/schema`, { cache: "no-store" }, 8000);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(parseApiError(data, "Service brief schema request failed"));
        }
        if (!cancelled) {
          setServiceBriefSchema(data);
        }
      } catch (_error) {
        if (!cancelled) {
          setServiceBriefSchema(buildStaticServiceBriefSchema());
        }
      }

      try {
        const response = await fetchWithTimeout(`${API_BASE}/ops/review-pack`, { cache: "no-store" }, 8000);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(parseApiError(data, "Review pack request failed"));
        }
        if (!cancelled) {
          setReviewPack(data);
        }
      } catch (_error) {
        if (!cancelled) {
          setReviewPack(buildStaticReviewPack());
        }
      }
    }

    void loadServiceBrief();
    const timerId = window.setInterval(() => void loadServiceBrief(), 30000);
    return () => {
      cancelled = true;
      window.clearInterval(timerId);
    };
  }, []);

  const healthStatus = String(health.status || "").toLowerCase().trim();
  // "unknown" is treated as online so the UI isn't blocked before the first health poll finishes.
  const backendOnline = healthStatus !== "offline";
  const isAdmin = role === "Admin";
  const isOpsEligible = role === "Ops" || role === "Admin";
  const loginCodeRequired = Boolean(health.login_code_required);
  const integrationAuthRequired = Boolean(health.integrations_require_auth);

  function navigate(nextPage) {
    window.location.hash = nextPage;
    setPage(nextPage);
  }

  async function copyCurrentReviewLink() {
    const url = buildReviewerShareUrl({ page, tab: activeTab, role });
    const ok = await copyTextToClipboard(url);
    setStatus(ok ? "Current review link copied" : "Failed to copy current review link");
  }

  async function fetchJson(path, options = {}) {
    const { errorMessage = "Request failed", timeoutMs = 20000, ...fetchOptions } = options;
    let res;
    try {
      res = await fetchWithTimeout(`${API_BASE}${path}`, fetchOptions, timeoutMs);
    } catch (rawError) {
      const reason =
        rawError instanceof Error && rawError.message.includes("timed out")
          ? rawError.message
          : `Backend offline at ${API_BASE}. Start the backend on :8000 and retry.`;
      const offline = new Error(
        reason
      );
      offline.status = 0;
      offline.requestId = "";
      throw offline;
    }
    const data = await res.json().catch(() => ({}));
    const requestId = res.headers.get("x-request-id") || data.request_id || "";
    if (requestId) {
      setLastRequestId(requestId);
    }
    if (!res.ok) {
      const error = new Error(parseApiError(data, errorMessage));
      error.status = res.status;
      error.requestId = requestId;
      throw error;
    }
    return { data, requestId };
  }

  async function submitCommunityFeedback(event) {
    event.preventDefault();
    if (!FORMSPREE_ENDPOINT) {
      setCommunitySubmitStatus("error");
      setCommunityNotice("Set VITE_FORMSPREE_ENDPOINT to enable feedback submission.");
      return;
    }

    setCommunitySubmitStatus("submitting");
    setCommunityNotice("");
    try {
      const response = await fetchWithTimeout(
        FORMSPREE_ENDPOINT,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json"
          },
          body: JSON.stringify({
            name: communityName.trim(),
            email: communityEmail.trim(),
            message: communityMessage.trim(),
            source: "enterprise-llm-adoption-kit",
            page_url: window.location.href
          })
        },
        12000
      );
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiError(payload, "Feedback request failed."));
      }

      setCommunitySubmitStatus("success");
      setCommunityMessage("");
      setCommunityNotice("Feedback submitted. We'll include it in the next validation cycle.");
    } catch (error) {
      setCommunitySubmitStatus("error");
      setCommunityNotice(error instanceof Error ? error.message : "Feedback request failed.");
    }
  }

  async function login(options = {}) {
    const { silent = false, throwOnError = false } = options;
    const trimmedUserId = String(userId || "").trim();
    const trimmedLoginCode = String(loginCode || "").trim();

    if (!trimmedUserId) {
      const message = "user_id is required";
      if (!silent) {
        setStatus(message);
      }
      if (throwOnError) {
        throw new Error(message);
      }
      return null;
    }
    if (loginCodeRequired && !trimmedLoginCode) {
      const message = "Login code required. Enter the shared code and retry.";
      if (!silent) {
        setStatus(message);
      }
      if (throwOnError) {
        throw new Error(message);
      }
      return null;
    }

    if (!silent) {
      setStatus("Authenticating...");
    }
    try {
      const { data, requestId } = await fetchJson("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: trimmedUserId,
          role,
          login_code: trimmedLoginCode || null
        }),
        errorMessage: "Login failed"
      });
      setToken(data.access_token);
      if (!silent) {
        setStatus(withRequestId("Authentication complete", requestId));
      }
      return { data, requestId };
    } catch (error) {
      if (!silent) {
        setStatus(withRequestId(error.message || "Login failed", error.requestId));
      }
      if (throwOnError) {
        throw error;
      }
      return null;
    }
  }

  async function runArchitectureDiagnosis(options = {}) {
    const { silent = false, throwOnError = false } = options;
    if (!silent) {
      setStatus("Running architecture diagnosis...");
    }
    try {
      const body = JSON.stringify({
        query: diagnosisQuery,
        citation_only: diagnosisCitationOnly,
        system: targetSystem || null,
        env: targetEnv || null
      });

      const requestOptions = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body,
        errorMessage: "Architecture diagnosis failed"
      };

      let result;
      try {
        result = await fetchJson("/uc1/architecture", requestOptions);
      } catch (error) {
        // Backward compatibility for older backend route names.
        if (error.status === 404) {
          result = await fetchJson("/uc1/handover", requestOptions);
        } else {
          throw error;
        }
      }

      setDiagnosisResponse(result.data);
      if (!silent) {
        setStatus(withRequestId("Architecture diagnosis complete", result.requestId));
      }
      return result;
    } catch (error) {
      if (!silent) {
        setStatus(withRequestId(error.message || "Architecture diagnosis failed", error.requestId));
      }
      if (throwOnError) {
        throw error;
      }
      return null;
    }
  }

  async function runOpsRiskAnalysis(options = {}) {
    const { silent = false, throwOnError = false } = options;
    if (!silent) {
      setStatus("Running operations risk analysis...");
    }
    try {
      const { data, requestId } = await fetchJson("/uc2/log-intel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ logs: opsLogs }),
        errorMessage: "Operations risk analysis failed"
      });

      setOpsResponse(data);
      if (!silent) {
        setStatus(withRequestId("Operations risk analysis complete", requestId));
      }
      return { data, requestId };
    } catch (error) {
      if (!silent) {
        setStatus(withRequestId(error.message || "Operations risk analysis failed", error.requestId));
      }
      if (throwOnError) {
        throw error;
      }
      return null;
    }
  }

  async function loadGovernanceSummary(options = {}) {
    const { silent = false, throwOnError = false } = options;
    if (!silent) {
      setStatus("Loading governance summary...");
    }
    setGovernanceError("");

    try {
      const { data, requestId } = await fetchJson("/audit/summary", {
        errorMessage: "Governance summary failed"
      });
      setGovernanceSummary(data);
      if (!silent) {
        setStatus(withRequestId("Governance summary loaded", requestId));
      }
      return { data, requestId };
    } catch (error) {
      setGovernanceError(error.message || "Governance summary failed");
      if (!silent) {
        setStatus(withRequestId("Governance summary error", error.requestId));
      }
      if (throwOnError) {
        throw error;
      }
      return null;
    }
  }

  async function sendSlackEvent(options = {}) {
    const { silent = false } = options;
    setSlackError("");
    setSlackResponse(null);
    if (!silent) {
      setStatus("Sending Slack event...");
    }

    if (integrationAuthRequired && !token) {
      const msg = "Bearer token required. Issue a token in Access Control first.";
      setSlackError(msg);
      if (!silent) {
        setStatus(msg);
      }
      return null;
    }

    const text = String(slackText || "").trim();
    if (!text) {
      const msg = "Slack message cannot be empty";
      setSlackError(msg);
      if (!silent) {
        setStatus(msg);
      }
      return null;
    }

    try {
      const headers = { "Content-Type": "application/json" };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      const { data, requestId } = await fetchJson("/integrations/slack/events", {
        method: "POST",
        headers,
        body: JSON.stringify({
          user_id: userId || "slack-user",
          role,
          channel: slackChannel || null,
          text
        }),
        errorMessage: "Slack integration failed"
      });
      setSlackResponse(data);
      if (!silent) {
        setStatus(withRequestId("Slack reply generated", requestId));
      }
      return { data, requestId };
    } catch (error) {
      setSlackError(error.message || "Slack integration failed");
      if (!silent) {
        setStatus(withRequestId("Slack integration error", error.requestId));
      }
      return null;
    }
  }

  async function generateJiraComment(options = {}) {
    const { silent = false } = options;
    setJiraError("");
    setJiraResponse(null);
    if (!silent) {
      setStatus("Generating Jira comment...");
    }

    if (integrationAuthRequired && !token) {
      const msg = "Bearer token required. Issue a token in Access Control first.";
      setJiraError(msg);
      if (!silent) {
        setStatus(msg);
      }
      return null;
    }

    const ticketId = String(jiraTicketId || "").trim();
    const title = String(jiraTitle || "").trim();
    const description = String(jiraDescription || "").trim();
    if (!ticketId || !title || !description) {
      const msg = "Jira ticket_id/title/description are required";
      setJiraError(msg);
      if (!silent) {
        setStatus(msg);
      }
      return null;
    }

    try {
      const headers = { "Content-Type": "application/json" };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      const { data, requestId } = await fetchJson("/integrations/jira/ticket", {
        method: "POST",
        headers,
        body: JSON.stringify({
          ticket_id: ticketId,
          title,
          description,
          priority: String(jiraPriority || "Medium"),
          reporter: userId || null,
          role
        }),
        errorMessage: "Jira integration failed"
      });
      setJiraResponse(data);
      if (!silent) {
        setStatus(withRequestId("Jira comment generated", requestId));
      }
      return { data, requestId };
    } catch (error) {
      setJiraError(error.message || "Jira integration failed");
      if (!silent) {
        setStatus(withRequestId("Jira integration error", error.requestId));
      }
      return null;
    }
  }

  function applyLlmRuntimeToForm(data) {
    if (!data) {
      return;
    }
    setLlmRuntimeForm({
      provider: String(data.provider || "stub"),
      model: String(data.model || "stub-llm"),
      temperature: String(data.temperature ?? "0.2"),
      max_tokens: String(data.max_tokens ?? "512"),
      timeout_sec: String(data.timeout_sec ?? "30"),
      openai_base_url: String(data.openai_base_url || "https://api.openai.com/v1"),
      ollama_base_url: String(data.ollama_base_url || "http://127.0.0.1:11434"),
      openai_org: String(data.openai_org || ""),
      openai_api_key: ""
    });
  }

  async function loadAdminLlmRuntime(options = {}) {
    const { silent = false } = options;
    if (!token) {
      setLlmRuntimeError("JWT required. Issue an Admin token first.");
      return;
    }
    if (!silent) {
      setStatus("Loading LLM runtime settings...");
    }
    setLlmRuntimeError("");
    try {
      const { data, requestId } = await fetchJson("/admin/runtime/llm", {
        headers: {
          Authorization: `Bearer ${token}`
        },
        errorMessage: "LLM runtime load failed"
      });
      setLlmRuntime(data);
      applyLlmRuntimeToForm(data);
      if (!silent) {
        setStatus(withRequestId("LLM runtime settings loaded", requestId));
      }
    } catch (error) {
      setLlmRuntimeError(error.message || "LLM runtime load failed");
      if (!silent) {
        setStatus(withRequestId("LLM runtime load error", error.requestId));
      }
    }
  }

  async function saveAdminLlmRuntime(resetToEnv = false) {
    if (!token) {
      setLlmRuntimeError("JWT required. Issue an Admin token first.");
      return;
    }
    setIsSavingLlmRuntime(true);
    setLlmRuntimeError("");
    setStatus(resetToEnv ? "Resetting LLM runtime..." : "Saving LLM runtime settings...");

    try {
      const payload = resetToEnv
        ? { reset_to_env: true }
        : {
            provider: llmRuntimeForm.provider,
            model: llmRuntimeForm.model.trim(),
            temperature: Number(llmRuntimeForm.temperature),
            max_tokens: Number(llmRuntimeForm.max_tokens),
            timeout_sec: Number(llmRuntimeForm.timeout_sec),
            openai_base_url: llmRuntimeForm.openai_base_url.trim(),
            ollama_base_url: llmRuntimeForm.ollama_base_url.trim(),
            openai_org: llmRuntimeForm.openai_org.trim(),
            openai_api_key: llmRuntimeForm.openai_api_key.trim() || null
          };

      const { data, requestId } = await fetchJson("/admin/runtime/llm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload),
        errorMessage: "LLM runtime update failed"
      });
      setLlmRuntime(data);
      applyLlmRuntimeToForm(data);
      setStatus(
        withRequestId(
          resetToEnv ? "LLM runtime reset to environment defaults" : "LLM runtime settings updated",
          requestId
        )
      );
    } catch (error) {
      setLlmRuntimeError(error.message || "LLM runtime update failed");
      setStatus(withRequestId("LLM runtime update error", error.requestId));
    } finally {
      setIsSavingLlmRuntime(false);
    }
  }

  async function loadUserApiKeyStatus(options = {}) {
    const { silent = false } = options;
    if (!token) {
      setUserApiKeyView(null);
      if (!silent) {
        setUserApiKeyError("JWT required. Issue a token in Access Control first.");
      }
      return null;
    }
    if (!silent) {
      setStatus("Loading personal API key status...");
    }
    setUserApiKeyError("");
    try {
      const { data, requestId } = await fetchJson("/runtime/user-api-key", {
        headers: {
          Authorization: `Bearer ${token}`
        },
        errorMessage: "Personal API key status load failed"
      });
      setUserApiKeyView(data);
      if (!silent) {
        setStatus(withRequestId("Personal API key status loaded", requestId));
      }
      return { data, requestId };
    } catch (error) {
      setUserApiKeyError(error.message || "Personal API key status load failed");
      if (!silent) {
        setStatus(withRequestId("Personal API key status load error", error.requestId));
      }
      return null;
    }
  }

  async function saveUserApiKey() {
    if (!token) {
      setUserApiKeyError("JWT required. Issue a token in Access Control first.");
      return;
    }
    const apiKey = String(userApiKeyInput || "").trim();
    if (!apiKey) {
      setUserApiKeyError("Enter an API key first.");
      return;
    }
    setIsSavingUserApiKey(true);
    setUserApiKeyError("");
    setStatus("Saving personal API key...");
    try {
      const { data, requestId } = await fetchJson("/runtime/user-api-key", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ openai_api_key: apiKey }),
        errorMessage: "Personal API key save failed"
      });
      setUserApiKeyView(data);
      setUserApiKeyInput("");
      setStatus(withRequestId("Personal API key saved", requestId));
    } catch (error) {
      setUserApiKeyError(error.message || "Personal API key save failed");
      setStatus(withRequestId("Personal API key save error", error.requestId));
    } finally {
      setIsSavingUserApiKey(false);
    }
  }

  async function clearUserApiKey() {
    if (!token) {
      setUserApiKeyError("JWT required. Issue a token in Access Control first.");
      return;
    }
    setIsSavingUserApiKey(true);
    setUserApiKeyError("");
    setStatus("Removing personal API key...");
    try {
      const { data, requestId } = await fetchJson("/runtime/user-api-key", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`
        },
        errorMessage: "Personal API key remove failed"
      });
      setUserApiKeyView(data);
      setUserApiKeyInput("");
      setStatus(withRequestId("Personal API key removed", requestId));
    } catch (error) {
      setUserApiKeyError(error.message || "Personal API key remove failed");
      setStatus(withRequestId("Personal API key remove error", error.requestId));
    } finally {
      setIsSavingUserApiKey(false);
    }
  }

  function onArchitectureFileSelected(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setArchitectureJsonl(String(reader.result || ""));
    };
    reader.onerror = () => {
      setArchitectureError("Could not read the file.");
    };
    reader.readAsText(file, "utf-8");
  }

  async function loadArchitectureCatalog(options = {}) {
    const { silent = false } = options;
    if (!token) {
      setArchitectureError("JWT required. Issue an Admin token first.");
      return;
    }
    if (!silent) {
      setStatus("Loading architecture catalog...");
    }
    setArchitectureError("");

    try {
      const { data, requestId } = await fetchJson("/admin/architecture/catalog", {
        headers: {
          Authorization: `Bearer ${token}`
        },
        errorMessage: "Architecture catalog load failed"
      });
      setArchitectureCatalog(data);
      if (!silent) {
        setStatus(withRequestId("Architecture catalog loaded", requestId));
      }
    } catch (error) {
      setArchitectureError(error.message || "Architecture catalog load failed");
      if (!silent) {
        setStatus(withRequestId("Architecture catalog load error", error.requestId));
      }
    }
  }

  async function importArchitectureDataset() {
    if (!token) {
      setArchitectureError("JWT required. Issue an Admin token first.");
      return;
    }
    if (!architectureJsonl.trim()) {
      setArchitectureError("Provide a JSONL payload or select a file.");
      return;
    }
    setIsImportingArchitecture(true);
    setArchitectureError("");
    setStatus("Importing architecture dataset...");

    try {
      const { data, requestId } = await fetchJson("/admin/architecture/import", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ jsonl: architectureJsonl }),
        errorMessage: "Architecture import failed"
      });
      setArchitectureCatalog(data);
      setStatus(withRequestId("Architecture dataset imported and indexed", requestId));
      await loadRuntimeSnapshot({ silent: true });
    } catch (error) {
      setArchitectureError(error.message || "Architecture import failed");
      setStatus(withRequestId("Architecture import error", error.requestId));
    } finally {
      setIsImportingArchitecture(false);
    }
  }

  async function reindexArchitectureDataset() {
    if (!token) {
      setArchitectureError("JWT required. Issue an Admin token first.");
      return;
    }
    setIsReindexingArchitecture(true);
    setArchitectureError("");
    setStatus("Reindexing architecture dataset...");

    try {
      const { data, requestId } = await fetchJson("/admin/architecture/reindex", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        errorMessage: "Architecture reindex failed"
      });
      setArchitectureCatalog(data);
      setStatus(withRequestId("Architecture dataset reindexed", requestId));
      await loadRuntimeSnapshot({ silent: true });
    } catch (error) {
      setArchitectureError(error.message || "Architecture reindex failed");
      setStatus(withRequestId("Architecture reindex error", error.requestId));
    } finally {
      setIsReindexingArchitecture(false);
    }
  }

  function loadSampleArchitectureDataset() {
    setArchitectureJsonl(SAMPLE_ARCHITECTURE_JSONL);
    setArchitectureError("");
  }

  function buildRuntimeQuery() {
    const params = new URLSearchParams();
    const safeEvents = Math.max(1, Number(runtimeEventsLimit) || 20);
    const safeDecisions = Math.max(1, Number(runtimeDecisionsLimit) || 10);
    const safeWindow = Math.max(0, Number(runtimeWindowMinutes) || 0);
    params.set("events_limit", String(safeEvents));
    params.set("decisions_limit", String(safeDecisions));
    if (safeWindow > 0) {
      params.set("events_since_minutes", String(safeWindow));
      params.set("decisions_since_minutes", String(safeWindow));
    }
    if (runtimeLevelFilter.trim()) {
      params.set("level", runtimeLevelFilter.trim());
    }
    if (runtimeComponentFilter.trim()) {
      params.set("component", runtimeComponentFilter.trim());
    }
    if (runtimeSearchTerm.trim()) {
      params.set("search", runtimeSearchTerm.trim());
    }
    params.set("sort", runtimeSortOrder);
    return `?${params.toString()}`;
  }

  async function loadRuntimeSnapshot(options = {}) {
    const { silent = false, throwOnError = false } = options;
    if (!token) {
      const error = new Error("JWT required. Issue a token in Access Control first.");
      setRuntimeError(error.message);
      if (throwOnError) {
        throw error;
      }
      return null;
    }
    if (!silent) {
      setStatus("Loading runtime debug snapshot...");
    }
    setRuntimeError("");

    try {
      const { data, requestId } = await fetchJson(`/ops/runtime${buildRuntimeQuery()}`, {
        headers: {
          Authorization: `Bearer ${token}`
        },
        errorMessage: "Runtime snapshot failed"
      });
      setRuntimeSnapshot(data);
      setRuntimeLastLoadedAt(new Date().toLocaleString());
      setRuntimeSnapshotRequestId(requestId || "");
      if (!silent) {
        setStatus(withRequestId("Runtime snapshot loaded", requestId));
      }
      return { data, requestId };
    } catch (error) {
      setRuntimeError(error.message || "Runtime snapshot failed");
      if (!silent) {
        setStatus(withRequestId("Runtime snapshot error", error.requestId));
      }
      if (throwOnError) {
        throw error;
      }
      return null;
    }
  }

  async function refreshDiagnostics() {
    if (!token) {
      setRuntimeError("JWT required. Issue a token in Access Control first.");
      return;
    }
    setIsRefreshingDiagnostics(true);
    setStatus("Refreshing diagnostics...");
    setRuntimeError("");
    try {
      const { requestId } = await fetchJson("/ops/diagnostics/refresh", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        errorMessage: "Diagnostics refresh failed"
      });
      setStatus(withRequestId("Diagnostics refreshed", requestId));
      await loadRuntimeSnapshot();
    } catch (error) {
      setRuntimeError(error.message || "Diagnostics refresh failed");
      setStatus(withRequestId("Diagnostics refresh error", error.requestId));
    } finally {
      setIsRefreshingDiagnostics(false);
    }
  }

  useEffect(() => {
    if (!(page === "console" && activeTab === "governance" && runtimeAutoRefresh && token && isOpsEligible)) {
      return undefined;
    }
    const intervalSec = Math.max(5, Number(runtimeAutoRefreshSec) || 15);
    const timerId = window.setInterval(() => {
      void loadRuntimeSnapshot({ silent: true });
    }, intervalSec * 1000);
    return () => window.clearInterval(timerId);
  }, [
    page,
    activeTab,
    runtimeAutoRefresh,
    runtimeAutoRefreshSec,
    role,
    token,
    runtimeEventsLimit,
    runtimeDecisionsLimit,
    runtimeWindowMinutes,
    runtimeLevelFilter,
    runtimeComponentFilter,
    runtimeSearchTerm,
    runtimeSortOrder
  ]);

  useEffect(() => {
    if (!(page === "console" && activeTab === "governance" && token && isAdmin)) {
      return;
    }
    void loadAdminLlmRuntime({ silent: true });
    void loadArchitectureCatalog({ silent: true });
  }, [page, activeTab, token, role]);

  useEffect(() => {
    if (!token) {
      setUserApiKeyView(null);
      setUserApiKeyError("");
      setUserApiKeyInput("");
      return;
    }
    void loadUserApiKeyStatus({ silent: true });
  }, [token]);

  const runtimeView = useMemo(() => {
    const snapshot = runtimeSnapshot || {};
    const search = runtimeSearchTerm.trim().toLowerCase();

    const matchesSearch = (parts) => {
      if (!search) {
        return true;
      }
      const blob = parts
        .map((part) => String(part || "").toLowerCase())
        .join(" ");
      return blob.includes(search);
    };

    const sortDirection = runtimeSortOrder === "asc" ? 1 : -1;
    const byTime = (a, b) => {
      const left = parseIsoTime(a.created_at);
      const right = parseIsoTime(b.created_at);
      return (left - right) * sortDirection;
    };

    const baseAlerts = Array.isArray(snapshot.alerts) ? snapshot.alerts : [];
    const baseEvents = Array.isArray(snapshot.service_events) ? snapshot.service_events : [];
    const baseDecisions = Array.isArray(snapshot.recent_decisions) ? snapshot.recent_decisions : [];

    const alerts = baseAlerts
      .filter((alert) => {
        if (runtimeAlertSeverity === "all") {
          return true;
        }
        return String(alert.severity || "").toLowerCase() === runtimeAlertSeverity;
      })
      .filter((alert) => matchesSearch([alert.code, alert.message, alert.severity]))
      .filter((alert) => {
        if (!runtimeOnlyErrors) {
          return true;
        }
        const severity = String(alert.severity || "").toLowerCase();
        return severity === "critical";
      })
      .sort((a, b) => {
        const left = SEVERITY_ORDER[String(a.severity || "").toLowerCase()] || 0;
        const right = SEVERITY_ORDER[String(b.severity || "").toLowerCase()] || 0;
        if (left !== right) {
          return right - left;
        }
        return String(a.code || "").localeCompare(String(b.code || ""));
      });

    const events = baseEvents
      .filter((event) =>
        matchesSearch([event.created_at, event.level, event.component, event.message])
      )
      .filter((event) => {
        if (!runtimeOnlyErrors) {
          return true;
        }
        return String(event.level || "").toUpperCase() === "ERROR";
      })
      .sort(byTime);

    const decisions = baseDecisions
      .filter((decision) =>
        matchesSearch([
          decision.created_at,
          decision.decision_id,
          decision.scenario_id,
          decision.risk_level,
          decision.user_id
        ])
      )
      .filter((decision) => {
        if (!runtimeOnlyErrors) {
          return true;
        }
        const risk = String(decision.risk_level || "").toLowerCase();
        return risk === "critical" || risk === "blocked";
      })
      .sort(byTime);

    return {
      baseAlerts,
      baseEvents,
      baseDecisions,
      alerts,
      events,
      decisions
    };
  }, [
    runtimeSnapshot,
    runtimeSearchTerm,
    runtimeAlertSeverity,
    runtimeSortOrder,
    runtimeOnlyErrors
  ]);

  function runtimeCsvRows(type = "all") {
    const rows = [];
    const includeAlerts = type === "all" || type === "alerts";
    const includeEvents = type === "all" || type === "events";
    const includeDecisions = type === "all" || type === "decisions";

    if (includeAlerts) {
      runtimeView.alerts.forEach((alert) => {
        rows.push([
          "alert",
          "",
          String(alert.severity || ""),
          String(alert.code || ""),
          "",
          String(alert.message || ""),
          String(alert.value ?? ""),
          String(alert.threshold ?? "")
        ]);
      });
    }

    if (includeEvents) {
      runtimeView.events.forEach((event) => {
        rows.push([
          "service_event",
          String(event.created_at || ""),
          String(event.level || ""),
          String(event.id ?? ""),
          String(event.component || ""),
          String(event.message || ""),
          "",
          ""
        ]);
      });
    }

    if (includeDecisions) {
      runtimeView.decisions.forEach((decision) => {
        rows.push([
          "control_tower_decision",
          String(decision.created_at || ""),
          String(decision.risk_level || ""),
          String(decision.decision_id || ""),
          String(decision.scenario_id || ""),
          "",
          String(decision.risk_score ?? ""),
          String(decision.spec_version ?? "")
        ]);
      });
    }

    return rows;
  }

  function runtimeCsvMetadata(type, rowCount) {
    const exportType =
      type === "alerts"
        ? "alerts"
        : type === "events"
          ? "events"
          : type === "decisions"
            ? "decisions"
            : "snapshot";
    return [
      ["exported_at_utc", new Date().toISOString()],
      ["export_type", exportType],
      ["rows_exported", rowCount],
      ["api_base", API_BASE],
      ["auth_role", role || ""],
      ["request_id", runtimeSnapshotRequestId || lastRequestId || ""],
      ["startup_status", runtimeSnapshot?.startup_status || ""],
      ["daily_cost_usd", runtimeSnapshot?.daily_cost_usd ?? ""],
      ["requests", runtimeSnapshot?.audit_summary?.requests ?? ""],
      ["last_refresh_local", runtimeLastLoadedAt || ""],
      ["filter_events_limit", runtimeEventsLimit],
      ["filter_decisions_limit", runtimeDecisionsLimit],
      ["filter_window_minutes", runtimeWindowMinutes],
      ["filter_level", runtimeLevelFilter || "all"],
      ["filter_component", runtimeComponentFilter || "all"],
      ["filter_search", runtimeSearchTerm || ""],
      ["filter_alert_severity", runtimeAlertSeverity || "all"],
      ["filter_sort", runtimeSortOrder || "desc"],
      ["filter_only_errors", runtimeOnlyErrors ? "true" : "false"],
      ["visible_alerts", `${runtimeView.alerts.length}/${runtimeView.baseAlerts.length}`],
      ["visible_events", `${runtimeView.events.length}/${runtimeView.baseEvents.length}`],
      ["visible_decisions", `${runtimeView.decisions.length}/${runtimeView.baseDecisions.length}`]
    ];
  }

  function exportRuntimeSnapshotCsv(type = "all") {
    const rows = runtimeCsvRows(type);
    if (rows.length === 0) {
      setRuntimeError("No data available to export.");
      return;
    }

    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const suffix =
      type === "alerts"
        ? "alerts"
        : type === "events"
          ? "events"
          : type === "decisions"
            ? "decisions"
            : "snapshot";

    exportCsvFile(
      `runtime-${suffix}-${stamp}.csv`,
      ["record_type", "time", "severity_or_level", "id_or_code", "scope", "message", "value", "meta"],
      rows,
      runtimeCsvMetadata(type, rows.length)
    );
    setStatus(
      type === "all"
        ? "Runtime snapshot CSV exported"
        : `Runtime ${suffix} CSV exported`
    );
  }

  function buildDefaultScenarioSteps() {
    const isOpsEligible = role === "Ops" || role === "Admin";
    const base = [
      {
        key: "auth",
        title: "Identity and Role Check",
        text: "Issue a JWT and confirm least-privilege access behavior.",
        endpoint: "/auth/login",
        status: "idle"
      },
      {
        key: "architecture",
        title: "Architecture Risk Diagnosis",
        text: "Run the architecture advisor and verify citations are consistent and relevant.",
        endpoint: "/uc1/architecture",
        status: "idle"
      },
      {
        key: "ops",
        title: "Operations Log Risk Analysis",
        text: "Generate incident hypotheses and runbook steps from raw operational logs.",
        endpoint: "/uc2/log-intel",
        status: "idle"
      },
      {
        key: "governance",
        title: "Governance and Observability",
        text: "Review audit + cost signals to decide if the system is production-ready.",
        endpoint: "/audit/summary",
        status: "idle"
      },
      {
        key: "runtime",
        title: "Ops Control Tower Snapshot (Optional)",
        text: "Load /ops/runtime for alerts, recent events, and recent control tower decisions (Ops/Admin only).",
        endpoint: "/ops/runtime",
        status: isOpsEligible ? "idle" : "skipped",
        skippedReason: isOpsEligible ? "" : "Requires Ops/Admin role."
      }
    ];
    return base.map((step) => ({
      ...step,
      requestId: "",
      error: "",
      startedAt: "",
      finishedAt: ""
    }));
  }

  function updateScenarioStep(stepKey, patch) {
    setScenarioRun((prev) => {
      if (!prev) {
        return prev;
      }
      const steps = prev.steps.map((step) =>
        step.key === stepKey ? { ...step, ...patch } : step
      );
      return { ...prev, steps };
    });
  }

  function scenarioPillClass(statusValue) {
    const status = String(statusValue || "idle").toLowerCase();
    if (status === "running") {
      return "pill pill-warning";
    }
    if (status === "error") {
      return "pill pill-critical";
    }
    if (status === "skipped") {
      return "pill pill-warning";
    }
    if (status === "ok") {
      return "pill pill-info";
    }
    return "pill pill-info";
  }

  function addScenarioHistoryEntry(entry) {
    const next = {
      id: String(entry?.id || `run-${Date.now()}`),
      generated_at_utc: String(entry?.generated_at_utc || new Date().toISOString()),
      status: String(entry?.status || "ok"),
      api_base: String(entry?.api_base || API_BASE),
      user_id: String(entry?.user_id || userId),
      role: String(entry?.role || role),
      report_md: String(entry?.report_md || "")
    };

    setScenarioHistory((prev) => {
      const existing = Array.isArray(prev) ? prev : [];
      const deduped = existing.filter((item) => item?.id !== next.id);
      return [next, ...deduped].slice(0, 12);
    });
  }

  function clearScenarioHistory() {
    setScenarioHistory([]);
    setStatus("Scenario history cleared");
  }

  function downloadScenarioHistoryEntry(entry) {
    const stamp = String(entry?.generated_at_utc || new Date().toISOString());
    const report = String(entry?.report_md || "");
    if (!report.trim()) {
      setStatus("No report content available");
      return;
    }
    const safeStamp = stamp.replace(/[:.]/g, "-");
    exportTextFile(`atelier-validation-report-${safeStamp}.md`, report, "text/markdown;charset=utf-8");
    setStatus("Scenario report exported");
  }

  async function copyScenarioHistoryEntry(entry) {
    const report = String(entry?.report_md || "");
    if (!report.trim()) {
      setStatus("No report content available");
      return;
    }
    const ok = await copyTextToClipboard(report);
    setStatus(ok ? "Scenario report copied" : "Failed to copy scenario report");
  }

  function buildScenarioReportMarkdown(options = {}) {
    const stamp = String(options.stamp || new Date().toISOString());
    const scenario = options.scenario || scenarioRun;
    const reportUserId = String(options.userId ?? userId);
    const reportRole = String(options.role ?? role);
    const reportApiBase = String(options.apiBase ?? API_BASE);

    const diagnosisPrompt = String(options.diagnosisQuery ?? diagnosisQuery);
    const opsInputLogs = String(options.opsLogs ?? opsLogs);
    const diagnosisData = options.diagnosisData ?? diagnosisResponse;
    const opsData = options.opsData ?? opsResponse;
    const governanceData = options.governanceData ?? governanceSummary;
    const runtimeData = options.runtimeData ?? runtimeSnapshot;

    const steps = Array.isArray(scenario?.steps) ? scenario.steps : [];

    const lines = [];
    lines.push(`# ${APP_NAME} - End-to-End Validation Report`);
    lines.push("");
    lines.push(`- generated_at_utc: ${stamp}`);
    lines.push(`- api_base: ${reportApiBase}`);
    lines.push(`- user_id: ${reportUserId}`);
    lines.push(`- role: ${reportRole}`);
    if (scenario?.startedAt) {
      lines.push(`- started_at_utc: ${scenario.startedAt}`);
    }
    if (scenario?.finishedAt) {
      lines.push(`- finished_at_utc: ${scenario.finishedAt}`);
    }
    lines.push("");

    lines.push("## Execution Timeline");
    lines.push("| Step | Status | Request ID | Endpoint |");
    lines.push("| --- | --- | --- | --- |");
    steps.forEach((step) => {
      const status = String(step.status || "idle").toUpperCase();
      const requestId = step.requestId ? `\`${step.requestId}\`` : "-";
      const endpoint = step.endpoint ? `\`${step.endpoint}\`` : "-";
      lines.push(`| ${step.title} | ${status} | ${requestId} | ${endpoint} |`);
    });
    lines.push("");

    lines.push("## UC1 - Architecture Risk Diagnosis");
    lines.push("### Prompt");
    lines.push("```");
    lines.push(String(diagnosisPrompt || "").trim());
    lines.push("```");
    lines.push("");
    lines.push("### Answer");
    lines.push(diagnosisData?.answer ? String(diagnosisData.answer) : "_Not available_");
    lines.push("");
    if (Array.isArray(diagnosisData?.citations) && diagnosisData.citations.length > 0) {
      lines.push("### Citations");
      diagnosisData.citations.forEach((citation) => {
        lines.push(`- ${citation.doc_id} :: ${citation.field_path}`);
      });
      lines.push("");
    }

    lines.push("## UC2 - Operations Log Risk Analysis");
    lines.push("### Input logs");
    lines.push("```");
    lines.push(String(opsInputLogs || "").trim());
    lines.push("```");
    lines.push("");
    lines.push("### Summary");
    lines.push(opsData?.summary ? String(opsData.summary) : "_Not available_");
    lines.push("");
    if (Array.isArray(opsData?.root_causes) && opsData.root_causes.length > 0) {
      lines.push("### Root Causes");
      opsData.root_causes.forEach((cause) => lines.push(`- ${cause}`));
      lines.push("");
    }
    if (Array.isArray(opsData?.runbook_steps) && opsData.runbook_steps.length > 0) {
      lines.push("### Runbook Steps");
      opsData.runbook_steps.forEach((step) => lines.push(`- ${step}`));
      lines.push("");
    }

    lines.push("## Governance Summary");
    if (governanceData) {
      lines.push(`- requests: ${governanceData.requests ?? "-"}`);
      lines.push(`- total_cost_usd: ${governanceData.total_cost ?? "-"}`);
      lines.push(
        `- policy_events: ${
          Array.isArray(governanceData.policy_events) ? governanceData.policy_events.length : 0
        }`
      );
      lines.push(
        `- tools_used: ${
          Array.isArray(governanceData.tools_used) ? governanceData.tools_used.length : 0
        }`
      );
    } else {
      lines.push("_Not available_");
    }
    lines.push("");

    lines.push("## Ops Control Tower Snapshot");
    if (runtimeData) {
      lines.push(`- startup_status: ${runtimeData.startup_status ?? "-"}`);
      lines.push(`- requests: ${runtimeData.audit_summary?.requests ?? "-"}`);
      lines.push(`- daily_cost_usd: ${runtimeData.daily_cost_usd ?? "-"}`);
      lines.push(`- alerts: ${Array.isArray(runtimeData.alerts) ? runtimeData.alerts.length : 0}`);
      lines.push(
        `- service_events: ${
          Array.isArray(runtimeData.service_events) ? runtimeData.service_events.length : 0
        }`
      );
      lines.push(
        `- recent_decisions: ${
          Array.isArray(runtimeData.recent_decisions) ? runtimeData.recent_decisions.length : 0
        }`
      );
    } else {
      lines.push("_Not available (requires Ops/Admin role)_");
    }
    lines.push("");

    lines.push("## Runtime Metadata");
    lines.push(`- auth_mode: ${String(health.auth_mode || "-")}`);
    lines.push(`- data_handling_mode: ${String(health.data_handling_mode || "-")}`);
    lines.push(`- storage_backend: ${String(health.storage_backend || "-")}`);
    lines.push(
      `- llm_provider: ${String(health.llm_provider || "-")} (${String(health.llm_model || "-")})`
    );
    lines.push(`- openai_api_key_configured: ${health.openai_api_key_configured ? "true" : "false"}`);
    lines.push(`- llm_circuit_state: ${String(health.llm_circuit_state || "closed")}`);
    lines.push(
      `- llm_circuit_open_seconds_remaining: ${Number(health.llm_circuit_open_seconds_remaining || 0)}`
    );
    lines.push(
      `- llm_circuit_consecutive_failures: ${Number(health.llm_circuit_consecutive_failures || 0)}`
    );
    lines.push(`- request_max_body_bytes: ${Number(health.request_max_body_bytes || 0)}`);
    lines.push("");

    return lines.join("\n");
  }

  async function copyScenarioReportToClipboard() {
    if (!scenarioRun || scenarioRun.running) {
      return;
    }
    const stamp = new Date().toISOString();
    const report = buildScenarioReportMarkdown({ stamp });
    const ok = await copyTextToClipboard(report);
    setStatus(ok ? "Scenario report copied" : "Failed to copy scenario report");
  }

  async function runScenarioRunner() {
    const steps = buildDefaultScenarioSteps();
    const runId = `run-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
    const startedAt = new Date().toISOString();

    setScenarioRun({ id: runId, running: true, startedAt, finishedAt: "", steps });
    setDiagnosisResponse(null);
    setOpsResponse(null);
    setGovernanceSummary(null);
    setGovernanceError("");
    setRuntimeSnapshot(null);
    setRuntimeError("");
    setStatus("Running end-to-end scenario...");

    const updateLocalStep = (stepKey, patch) => {
      const idx = steps.findIndex((item) => item.key === stepKey);
      if (idx >= 0) {
        steps[idx] = { ...steps[idx], ...patch };
      }
      updateScenarioStep(stepKey, patch);
    };

    const runStep = async (stepKey, runner) => {
      updateLocalStep(stepKey, { status: "running", startedAt: new Date().toISOString(), error: "" });
      const result = await runner();
      const requestId = result?.requestId || "";
      updateLocalStep(stepKey, {
        status: "ok",
        requestId,
        finishedAt: new Date().toISOString()
      });
      return result;
    };

    try {
      const authResult = await runStep("auth", async () => login({ silent: true, throwOnError: true }));
      const uc1Result = await runStep("architecture", async () =>
        runArchitectureDiagnosis({ silent: true, throwOnError: true })
      );
      const uc2Result = await runStep("ops", async () =>
        runOpsRiskAnalysis({ silent: true, throwOnError: true })
      );
      const governanceResult = await runStep("governance", async () =>
        loadGovernanceSummary({ silent: true, throwOnError: true })
      );

      const isOpsEligible = role === "Ops" || role === "Admin";
      let runtimeResult = null;
      if (isOpsEligible) {
        runtimeResult = await runStep("runtime", async () =>
          loadRuntimeSnapshot({ silent: true, throwOnError: true })
        );
      }

      const finishedAt = new Date().toISOString();
      setScenarioRun((prev) => (prev ? { ...prev, running: false, finishedAt } : prev));
      setStatus("Scenario complete");

      addScenarioHistoryEntry({
        id: runId,
        generated_at_utc: finishedAt,
        status: "ok",
        api_base: API_BASE,
        user_id: userId,
        role,
        report_md: buildScenarioReportMarkdown({
          stamp: finishedAt,
          scenario: { id: runId, startedAt, finishedAt, steps },
          userId,
          role,
          apiBase: API_BASE,
          diagnosisData: uc1Result?.data,
          opsData: uc2Result?.data,
          governanceData: governanceResult?.data,
          runtimeData: runtimeResult?.data
        })
      });

      void authResult;
    } catch (error) {
      const message = error?.message || "Scenario failed";
      const finishedAt = new Date().toISOString();
      setScenarioRun((prev) => (prev ? { ...prev, running: false, finishedAt } : prev));
      setStatus(message);

      // Mark the first running step as failed if any.
      setScenarioRun((prev) => {
        if (!prev) {
          return prev;
        }
        const idx = prev.steps.findIndex((step) => step.status === "running");
        if (idx === -1) {
          return prev;
        }
        const stepsNext = prev.steps.slice();
        stepsNext[idx] = {
          ...stepsNext[idx],
          status: "error",
          error: message,
          finishedAt
        };
        return { ...prev, steps: stepsNext };
      });

      // Keep local copy consistent for report/history.
      const idx = steps.findIndex((step) => step.status === "running");
      if (idx >= 0) {
        steps[idx] = { ...steps[idx], status: "error", error: message, finishedAt };
      }

      addScenarioHistoryEntry({
        id: runId,
        generated_at_utc: finishedAt,
        status: "error",
        api_base: API_BASE,
        user_id: userId,
        role,
        report_md: buildScenarioReportMarkdown({
          stamp: finishedAt,
          scenario: { id: runId, startedAt, finishedAt, steps },
          userId,
          role,
          apiBase: API_BASE
        })
      });
    }
  }

  function exportScenarioReport() {
    if (!scenarioRun || scenarioRun.running) {
      return;
    }

    const stamp = new Date().toISOString();
    const report = buildScenarioReportMarkdown({ stamp });
    const safeStamp = stamp.replace(/[:.]/g, "-");
    exportTextFile(`atelier-validation-report-${safeStamp}.md`, report, "text/markdown;charset=utf-8");
    setStatus("Scenario report exported");
  }

  return (
    <div className="site-shell">
      <header className="top-nav">
        <button className="brand" onClick={() => navigate("home")}>
          <span className="brand-mark">A</span>
          <span className="brand-text">
            <strong>{APP_NAME}</strong>
            <span>{APP_TAGLINE}</span>
          </span>
        </button>

        <nav className="nav-links">
          {navItems.map((item) => (
            <button
              key={item.key}
              className={page === item.key ? "nav-btn active" : "nav-btn"}
              onClick={() => navigate(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="nav-right">
          <span
            className="chip"
            title={[
              `API_BASE: ${API_BASE}`,
              health.startup_status ? `startup_status: ${health.startup_status}` : "",
              healthCheckedAt ? `checked: ${healthCheckedAt}` : ""
            ]
              .filter(Boolean)
              .join("\n")}
          >
            <span
              className={
                String(health.status || "")
                  .toLowerCase()
                  .trim() === "ok"
                  ? "dot ok"
                  : String(health.status || "")
                        .toLowerCase()
                        .trim() === "degraded"
                    ? "dot degraded"
                    : "dot offline"
              }
            />
            Backend:{" "}
            {String(health.status || "")
              .toLowerCase()
              .trim() === "ok"
              ? "OK"
              : String(health.status || "")
                    .toLowerCase()
                    .trim() === "degraded"
                ? "Degraded"
                : "Offline"}
          </span>
          <span className="chip">Role: {role}</span>
          <span className="chip">
            {page === "console" ? `Tab: ${activeTab}` : `Page: ${page}`}
          </span>
          <button className="cta-light" onClick={() => void copyCurrentReviewLink()}>
            Copy Review Link
          </button>
          <button className="cta-light" onClick={() => navigate("console")}>
            Open Console
          </button>
        </div>
      </header>

      <main className="main-content">
        {page === "home" && (
          <div className="page-view">
            <section className="hero-grid">
              <Reveal className="hero-copy">
                <p className="eyebrow">Enterprise Adoption Sandbox</p>
                <h1>{APP_NAME}</h1>
                <p className="lead">
                  A production-minded validation kit for enterprise LLM adoption. Use it to test governance,
                  grounded answers, and operational signals before you ship into sensitive environments.
                </p>
                <div className="hero-actions">
                  <button className="cta-primary" onClick={() => navigate("capabilities")}>
                    Explore Capabilities
                  </button>
                  <button className="cta-ghost" onClick={() => navigate("scenario")}>
                    Run End-to-End Scenario
                  </button>
                </div>
                <div className="kpi-grid">
                  <article className="kpi-item">
                    <p>03</p>
                    <span>Roles (Employee/Ops/Admin)</span>
                  </article>
                  <article className="kpi-item">
                    <p>02</p>
                    <span>Use Cases (UC1/UC2)</span>
                  </article>
                  <article className="kpi-item">
                    <p>01</p>
                    <span>Control Tower Snapshot</span>
                  </article>
                </div>
              </Reveal>

              <Reveal className="hero-media" delay={120}>
                <div className="media-frame">
                  <img src={heroTower} alt="Control tower visualization" />
                  <div className="media-tag">CONTROL TOWER</div>
                </div>
              </Reveal>
            </section>

            <section className="section-block">
              <Reveal delay={80}>
                <ServiceBriefBoard
                  brief={serviceBrief}
                  schema={serviceBriefSchema}
                  health={health}
                  checkedAt={healthCheckedAt}
                />
              </Reveal>
            </section>

            <section className="section-block">
              <Reveal delay={90}>
                <ExecutiveReviewPack reviewPack={reviewPack} />
              </Reveal>
            </section>

            <section className="section-block sponsored-section">
              <Reveal className="sponsored-card" delay={90}>
                <p className="eyebrow">Sponsored</p>
                <h3>AdSense Slot</h3>
                <p>
                  Ad placement area. Configure the slot ID in Console and this slot will render automatically.
                </p>
                <AdSenseSlot key={activeAdSenseSlot || "home-empty-slot"} slot={activeAdSenseSlot} />
              </Reveal>
            </section>

            <section className="section-block">
              <Reveal className="section-head">
                <p className="eyebrow">What You Can Validate</p>
                <h2>Service-aligned validation surfaces</h2>
                <p>
                  This UI maps directly to the platform's core endpoints: architecture diagnosis, incident log
                  analysis, and governance/ops signals.
                </p>
              </Reveal>

              <div className="gallery-grid">
                <Reveal className="gallery-card" delay={60}>
                  <div className="icon-badge">
                    <Icon name="architecture" />
                  </div>
                  <h3>Architecture Risk Diagnosis</h3>
                  <p>Turn architecture questions into prioritized risks with evidence-linked citations.</p>
                  <div className="card-meta">
                    <span className="tag">
                      <strong>RAG</strong> citations
                    </span>
                    <span className="tag">
                      <strong>RBAC</strong> enforced
                    </span>
                  </div>
                </Reveal>

                <Reveal className="gallery-card" delay={120}>
                  <div className="icon-badge">
                    <Icon name="ops" />
                  </div>
                  <h3>Operations Log Risk Analysis</h3>
                  <p>Summarize noisy logs into hypotheses and runbook steps you can execute immediately.</p>
                  <div className="card-meta">
                    <span className="tag">
                      <strong>RCA</strong> hypotheses
                    </span>
                    <span className="tag">
                      <strong>MTTR</strong> focus
                    </span>
                  </div>
                </Reveal>

                <Reveal className="gallery-card" delay={180}>
                  <div className="icon-badge">
                    <Icon name="governance" />
                  </div>
                  <h3>Governance and Audit Flow</h3>
                  <p>Review policy events, tool usage, and daily cost to make adoption decisions defensible.</p>
                  <div className="card-meta">
                    <span className="tag">
                      <strong>AUDIT</strong> events
                    </span>
                    <span className="tag">
                      <strong>COST</strong> control
                    </span>
                  </div>
                </Reveal>
              </div>
            </section>

            <section className="section-block">
              <Reveal className="section-head">
                <p className="eyebrow">Community Integrations</p>
                <h2>Open-source feedback and discussion channels</h2>
                <p>
                  Formspree handles structured feedback intake, while Disqus/Giscus keep threaded discussions
                  attached to each page revision.
                </p>
              </Reveal>

              <div className="community-grid">
                <Reveal className="result-card" delay={90}>
                  <h4>Feedback Intake (Formspree)</h4>
                  <form onSubmit={submitCommunityFeedback} className="community-form">
                    <input
                      required
                      value={communityName}
                      onChange={(event) => setCommunityName(event.target.value)}
                      placeholder="Name"
                    />
                    <input
                      required
                      type="email"
                      value={communityEmail}
                      onChange={(event) => setCommunityEmail(event.target.value)}
                      placeholder="Email"
                    />
                    <textarea
                      required
                      value={communityMessage}
                      onChange={(event) => setCommunityMessage(event.target.value)}
                      placeholder="What should this validation kit improve next?"
                    />
                    <button className="cta-primary" disabled={communitySubmitStatus === "submitting"}>
                      {communitySubmitStatus === "submitting" ? "Sending..." : "Send Feedback"}
                    </button>
                  </form>
                  {communityNotice && (
                    <p className={communitySubmitStatus === "error" ? "feedback-status error" : "feedback-status"}>
                      {communityNotice}
                    </p>
                  )}
                </Reveal>

                <Reveal className="result-card" delay={130}>
                  <h4>Threaded Discussion (Disqus + Giscus)</h4>
                  <div className="discussion-card">
                    <p>Disqus</p>
                    {DISQUS_SHORTNAME ? (
                      <div id="disqus_thread" className="discussion-frame" />
                    ) : (
                      <p className="admin-note">Set VITE_DISQUS_SHORTNAME to enable Disqus thread.</p>
                    )}
                  </div>
                  <div className="discussion-card">
                    <p>Giscus (GitHub Discussions)</p>
                    {GISCUS_REPO && GISCUS_REPO_ID && GISCUS_CATEGORY && GISCUS_CATEGORY_ID ? (
                      <div ref={giscusContainerRef} className="discussion-frame" />
                    ) : (
                      <p className="admin-note">Set VITE_GISCUS_* variables to enable Giscus.</p>
                    )}
                  </div>
                </Reveal>
              </div>
            </section>
          </div>
        )}

        {page === "capabilities" && (
          <div className="page-view">
            <section className="section-block">
              <Reveal className="section-head">
                <p className="eyebrow">Core Capabilities</p>
                <h2>Capabilities aligned to real adoption decisions</h2>
                <p>
                  This platform focuses on the questions that matter before rollout: access control, grounded
                  answers, incident readiness, and governance signals.
                </p>
              </Reveal>

              <div className="capability-grid">
                {capabilityCards.map((card, index) => (
                  <Reveal key={card.title} className="capability-card" delay={50 + index * 40}>
                    <span className="cap-index">{String(index + 1).padStart(2, "0")}</span>
                    <h3>{card.title}</h3>
                    <p>{card.body}</p>
                  </Reveal>
                ))}
              </div>
            </section>
          </div>
        )}

        {page === "validation" && (
          <div className="page-view">
            <section className="section-block">
              <Reveal className="section-head">
                <p className="eyebrow">Readiness Flow</p>
                <h2>A structured validation order (before you deploy)</h2>
              </Reveal>

              <Reveal delay={70}>
                <ServiceBriefBoard
                  brief={serviceBrief}
                  schema={serviceBriefSchema}
                  health={health}
                  checkedAt={healthCheckedAt}
                  variant="compact"
                />
              </Reveal>

              <Reveal delay={90}>
                <ExecutiveReviewPack reviewPack={reviewPack} variant="compact" />
              </Reveal>

              <div className="validation-layout">
                <div className="validation-timeline">
                  {validationActs.map((act, index) => (
                    <Reveal key={act.title} className="validation-step" delay={70 + index * 55}>
                      <span>{`Act ${index + 1}`}</span>
                      <h3>{act.title}</h3>
                      <p>{act.text}</p>
                    </Reveal>
                  ))}
                </div>

                <Reveal className="validation-visual" delay={120}>
                  <h3>Readiness Checklist</h3>
                  <ul>
                    <li>RBAC and policy event consistency</li>
                    <li>Citation reliability for architecture diagnosis</li>
                    <li>Operations risk output actionability</li>
                    <li>Governance metrics traceability</li>
                    <li>Cost and latency boundaries (pre-budget)</li>
                  </ul>
                  <p className="lead" style={{ marginTop: 0 }}>
                    The goal is not a pretty demo, but a repeatable validation loop that produces evidence you can
                    share with reviewers.
                  </p>
                </Reveal>
              </div>
            </section>
          </div>
        )}

        {page === "scenario" && (
          <div className="page-view">
            <section className="section-block">
              <Reveal className="section-head">
                <p className="eyebrow">Scenario Runner</p>
                <h2>Run a repeatable end-to-end validation</h2>
                <p>
                  Issue a token, execute UC1/UC2, review governance signals, and export a report you can share with
                  reviewers.
                </p>
              </Reveal>

              <div className="scenario-layout">
                <Reveal className="scenario-window" delay={70}>
                  <div className="window-bar">
                    <p>End-to-End Runbook</p>
                    <div className="window-actions">
                      <button className="cta-ghost" onClick={() => navigate("console")}>
                        Open Console
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={exportScenarioReport}
                        disabled={!scenarioRun || scenarioRun.running}
                      >
                        Download Report
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={copyScenarioReportToClipboard}
                        disabled={!scenarioRun || scenarioRun.running}
                      >
                        Copy Report
                      </button>
                      <button
                        className="cta-primary"
                        onClick={runScenarioRunner}
                        disabled={scenarioRun?.running || !backendOnline}
                        title={
                          backendOnline
                            ? ""
                            : `Backend offline. Start it first (e.g., make demo-local). API_BASE=${API_BASE}`
                        }
                      >
                        {scenarioRun?.running ? "Running..." : "Run Scenario"}
                      </button>
                    </div>
                  </div>

                  <div className="window-body">
                    {(scenarioRun?.steps || buildDefaultScenarioSteps()).map((step) => (
                      <article key={step.key} className="scenario-step">
                        <div className="step-head">
                          <h3>{step.title}</h3>
                          <span className={scenarioPillClass(step.status)}>
                            {String(step.status || "idle").toUpperCase()}
                          </span>
                        </div>
                        <p>{step.text}</p>
                        <code>{step.endpoint}</code>
                        {step.requestId && (
                          <code className="mono-inline">request_id: {step.requestId}</code>
                        )}
                        {step.status === "skipped" && step.skippedReason && (
                          <p className="error-text">{step.skippedReason}</p>
                        )}
                        {step.status === "error" && step.error && <p className="error-text">{step.error}</p>}
                      </article>
                    ))}
                  </div>
                </Reveal>

                <Reveal className="validation-visual" delay={130}>
                  <h3>Preflight</h3>
                  <ul>
                    <li>
                      API base: <code className="mono-inline">{API_BASE}</code>
                    </li>
                    <li>
                      Health:{" "}
                      <code className="mono-inline">
                        {String(health.status || "unknown")}
                        {health.startup_status ? ` / ${health.startup_status}` : ""}
                      </code>
                    </li>
                    <li>
                      LLM:{" "}
                      <code className="mono-inline">
                        {health.llm_provider || "-"} / {health.llm_model || "-"}
                      </code>{" "}
                      <code className="mono-inline">
                        api_key={health.openai_api_key_configured ? "set" : "unset"}
                      </code>{" "}
                      <code className="mono-inline">
                        circuit={String(health.llm_circuit_state || "closed")}
                      </code>{" "}
                      <code className="mono-inline">
                        circuit_failures={Number(health.llm_circuit_consecutive_failures || 0)}
                      </code>
                    </li>
                    <li>
                      Modes:{" "}
                      <code className="mono-inline">{health.auth_mode || "-"}</code>{" "}
                      <code className="mono-inline">{health.data_handling_mode || "-"}</code>{" "}
                      <code className="mono-inline">{health.storage_backend || "-"}</code>{" "}
                      <code className="mono-inline">
                        login_code={health.login_code_required ? "required" : "optional"}
                      </code>{" "}
                      <code className="mono-inline">
                        integrations_auth={integrationAuthRequired ? "required" : "optional"}
                      </code>{" "}
                      <code className="mono-inline">
                        max_body={Number(health.request_max_body_bytes || 0)}
                      </code>
                    </li>
                    {String(health.status || "")
                      .toLowerCase()
                      .trim() === "offline" && (
                      <li>
                        Start local demo:{" "}
                        <code className="mono-inline">bash scripts/start_demo_local.sh</code>
                        {" "}or{" "}
                        <code className="mono-inline">bash scripts/start_demo_ollama_local.sh</code>
                      </li>
                    )}
                    <li>Ops snapshot requires Ops/Admin role.</li>
                  </ul>

                  <div className="panel" style={{ padding: 0, background: "transparent", boxShadow: "none" }}>
                    <h4 style={{ margin: "0 0 10px" }}>Identity</h4>
                    <div className="form-grid">
                      <label>
                        User ID
                        <input value={userId} onChange={(event) => setUserId(event.target.value)} />
                      </label>
                      <label>
                        Role
                        <select value={role} onChange={(event) => setRole(event.target.value)}>
                          {roles.map((item) => (
                            <option key={item} value={item}>
                              {item}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label>
                        Login Code {loginCodeRequired ? "(required)" : "(optional)"}
                        <input
                          type="password"
                          value={loginCode}
                          onChange={(event) => setLoginCode(event.target.value)}
                          placeholder={loginCodeRequired ? "Enter demo login code" : "Optional"}
                        />
                      </label>
                      <button className="cta-primary" onClick={() => login()} disabled={scenarioRun?.running}>
                        Issue JWT
                      </button>
                    </div>
                    <div className="token-row">
                      <span>Token</span>
                      <code>{token ? `${token.slice(0, 72)}...` : "Not issued"}</code>
                    </div>
                  </div>

                  <div className="result-card" style={{ minHeight: 0 }}>
                    <h4>Latest Outputs (Preview)</h4>
                    <p>
                      <strong>UC1:</strong>{" "}
                      {diagnosisResponse?.answer ? `${String(diagnosisResponse.answer).slice(0, 140)}...` : "—"}
                    </p>
                    <p>
                      <strong>UC2:</strong>{" "}
                      {opsResponse?.summary ? `${String(opsResponse.summary).slice(0, 140)}...` : "—"}
                    </p>
                    <p>
                      <strong>Governance:</strong>{" "}
                      {governanceSummary
                        ? `requests=${governanceSummary.requests}, cost=$${governanceSummary.total_cost}`
                        : "—"}
                    </p>
                  </div>

                  {Array.isArray(scenarioHistory) && scenarioHistory.length > 0 && (
                    <div className="result-card" style={{ minHeight: 0 }}>
                      <div className="card-head">
                        <h4>Run History (local)</h4>
                        <button className="cta-ghost" onClick={clearScenarioHistory}>
                          Clear
                        </button>
                      </div>
                      <p className="admin-note" style={{ marginTop: 0 }}>
                        Stored in browser localStorage. Avoid real secrets or proprietary data.
                      </p>
                      <ul className="history-list">
                        {scenarioHistory.map((entry) => (
                          <li key={entry.id} className="history-item">
                            <div className="history-row">
                              <div className="history-meta">
                                <strong>{String(entry.status || "ok").toUpperCase()}</strong>
                                <span>
                                  {entry.generated_at_utc
                                    ? new Date(entry.generated_at_utc).toLocaleString()
                                    : "-"}{" "}
                                  · {entry.role || "-"}
                                </span>
                              </div>
                              <div className="history-actions">
                                <button
                                  className="cta-ghost"
                                  onClick={() => downloadScenarioHistoryEntry(entry)}
                                  disabled={!entry.report_md}
                                >
                                  Download
                                </button>
                                <button
                                  className="cta-ghost"
                                  onClick={() => void copyScenarioHistoryEntry(entry)}
                                  disabled={!entry.report_md}
                                >
                                  Copy
                                </button>
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Reveal>
              </div>
            </section>
          </div>
        )}

        {page === "console" && (
          <div className="page-view console-view">
            <section className="section-block console-header">
              <Reveal className="section-head">
                <p className="eyebrow">Console</p>
                <h2>Run live validation against the backend</h2>
                <p>
                  Issue JWTs, execute UC1/UC2, and inspect governance + ops signals. Use Admin panels only when
                  required (role-gated).
                </p>
              </Reveal>

              <Reveal className="signal-card" delay={120}>
                <p className="signal-title">System Status</p>
                <div className="signal-main">
                  <span
                    className="chip"
                    title={[
                      `API_BASE: ${API_BASE}`,
                      health.startup_status ? `startup_status: ${health.startup_status}` : "",
                      healthCheckedAt ? `checked: ${healthCheckedAt}` : ""
                    ]
                      .filter(Boolean)
                      .join("\n")}
                  >
                    <span
                      className={
                        String(health.status || "")
                          .toLowerCase()
                          .trim() === "ok"
                          ? "dot ok"
                          : String(health.status || "")
                                .toLowerCase()
                                .trim() === "degraded"
                            ? "dot degraded"
                            : "dot offline"
                      }
                    />
                    {String(health.status || "")
                      .toLowerCase()
                      .trim() === "ok"
                      ? "Healthy"
                      : String(health.status || "")
                            .toLowerCase()
                            .trim() === "degraded"
                        ? "Degraded"
                        : "Offline"}
                  </span>
                  <strong>{status || "Ready"}</strong>
                  {lastRequestId && <code className="signal-request-id">request_id: {lastRequestId}</code>}
                </div>

                <div className="signal-grid">
                  <div className="signal-metric">
                    <span>Role</span>
                    <strong>{role}</strong>
                  </div>
                  <div className="signal-metric">
                    <span>Token</span>
                    <strong>{token ? "Issued" : "None"}</strong>
                  </div>
                  <div className="signal-metric">
                    <span>Requests</span>
                    <strong>{runtimeSnapshot?.audit_summary?.requests ?? governanceSummary?.requests ?? "-"}</strong>
                  </div>
                  <div className="signal-metric">
                    <span>Daily Cost</span>
                    <strong>
                      {runtimeSnapshot?.daily_cost_usd != null
                        ? `$${runtimeSnapshot.daily_cost_usd}`
                        : governanceSummary?.total_cost != null
                          ? `$${governanceSummary.total_cost}`
                          : "-"}
                    </strong>
                  </div>
                </div>
              </Reveal>
            </section>

            <section className="panel access-panel">
              <h3 className="panel-title">Access Control</h3>
              <div className="form-grid">
                <label>
                  User ID
                  <input value={userId} onChange={(event) => setUserId(event.target.value)} />
                </label>
                <label>
                  Role
                  <select value={role} onChange={(event) => setRole(event.target.value)}>
                    {roles.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </label>
                <button className="cta-primary" onClick={login}>
                  Issue JWT
                </button>
              </div>
              <div className="token-row">
                <span>Token</span>
                <code>{token ? `${token.slice(0, 72)}...` : "Not issued"}</code>
              </div>
            </section>

            <section className="panel byok-panel">
              <h3 className="panel-title">Personal OpenAI API Key (BYOK)</h3>
              <p>
                Enter your own API key. The backend keeps it in memory per user and resets it when the server restarts.
              </p>
              <div className="form-grid byok-grid">
                <label>
                  OpenAI API Key
                  <input
                    type="password"
                    placeholder="sk-..."
                    value={userApiKeyInput}
                    onChange={(event) => setUserApiKeyInput(event.target.value)}
                    disabled={!token || isSavingUserApiKey}
                  />
                </label>
              </div>
              <div className="action-row">
                <button
                  className="cta-primary"
                  onClick={saveUserApiKey}
                  disabled={!token || isSavingUserApiKey || !String(userApiKeyInput || "").trim()}
                >
                  {isSavingUserApiKey ? "Saving..." : "Save My API Key"}
                </button>
                <button className="cta-ghost" onClick={clearUserApiKey} disabled={!token || isSavingUserApiKey}>
                  Remove My API Key
                </button>
                <button
                  className="cta-ghost"
                  onClick={() => loadUserApiKeyStatus()}
                  disabled={!token || isSavingUserApiKey}
                >
                  Refresh Status
                </button>
              </div>
              {userApiKeyError && <p className="error-text">{userApiKeyError}</p>}
              {userApiKeyView && (
                <div className="admin-meta">
                  <p>User: {userApiKeyView.user_id}</p>
                  <p>API key configured: {userApiKeyView.openai_api_key_configured ? "yes" : "no"}</p>
                  <p>
                    Effective model: {userApiKeyView.effective_provider} / {userApiKeyView.effective_model}
                  </p>
                </div>
              )}
            </section>

            <section className="panel sponsored-panel">
              <h3 className="panel-title">Sponsored</h3>
              <p className="admin-note">
                Set your AdSense slot ID here. Values are stored in local browser storage for this device.
              </p>
              <div className="form-grid byok-grid">
                <label>
                  AdSense Slot ID
                  <input
                    placeholder="1234567890"
                    value={adsenseSlotInput}
                    onChange={(event) => setAdsenseSlotInput(event.target.value)}
                  />
                </label>
              </div>
              <p className="admin-note">Slot status: {adSenseSlotReady ? "valid" : "invalid or missing"}</p>
              <AdSenseSlot key={activeAdSenseSlot || "console-empty-slot"} slot={activeAdSenseSlot} />
            </section>

            <section className="panel workbench-panel">
              <div className="tab-strip">
                <button
                  className={activeTab === "architecture" ? "tab-btn active" : "tab-btn"}
                  onClick={() => setActiveTab("architecture")}
                >
                  Architecture Risk Diagnosis
                </button>
                <button
                  className={activeTab === "ops" ? "tab-btn active" : "tab-btn"}
                  onClick={() => setActiveTab("ops")}
                >
                  Operations Log Risk Analysis
                </button>
                <button
                  className={activeTab === "governance" ? "tab-btn active" : "tab-btn"}
                  onClick={() => setActiveTab("governance")}
                >
                  Adoption Design and Governance
                </button>
                <button
                  className={activeTab === "integrations" ? "tab-btn active" : "tab-btn"}
                  onClick={() => setActiveTab("integrations")}
                >
                  Integrations Simulator
                </button>
              </div>

              {activeTab === "architecture" && (
                <div className="tab-content tab-architecture">
                  <label>
                    Diagnostic Prompt
                    <textarea
                      value={diagnosisQuery}
                      onChange={(event) => setDiagnosisQuery(event.target.value)}
                    />
                  </label>

                  <div className="inline-grid">
                    <label>
                      Target System
                      <input
                        value={targetSystem}
                        onChange={(event) => setTargetSystem(event.target.value)}
                      />
                    </label>
                    <label>
                      Environment
                      <input value={targetEnv} onChange={(event) => setTargetEnv(event.target.value)} />
                    </label>
                    <label className="toggle">
                      <input
                        type="checkbox"
                        checked={diagnosisCitationOnly}
                        onChange={(event) => setDiagnosisCitationOnly(event.target.checked)}
                      />
                      Citation-Priority Mode
                    </label>
                  </div>

                  <button className="cta-primary" onClick={runArchitectureDiagnosis} disabled={!token}>
                    Run Architecture Diagnosis
                  </button>

                  {diagnosisResponse && (
                    <div className="result-card">
                      <h4>Diagnosis Result</h4>
                      <p>{diagnosisResponse.answer}</p>
                      <h5>Evidence Sources</h5>
                      <ul>
                        {diagnosisResponse.citations?.map((citation, index) => (
                          <li key={`${citation.doc_id}-${index}`}>
                            {citation.doc_id} | {citation.field_path}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "ops" && (
                <div className="tab-content tab-ops">
                  <label>
                    Operations Logs
                    <textarea value={opsLogs} onChange={(event) => setOpsLogs(event.target.value)} />
                  </label>
                  <button className="cta-primary" onClick={runOpsRiskAnalysis} disabled={!token}>
                    Run Log Risk Analysis
                  </button>

                  {opsResponse && (
                    <div className="result-card">
                      <h4>Summary</h4>
                      <p>{opsResponse.summary}</p>
                      <h5>Root Causes</h5>
                      <ul>
                        {opsResponse.root_causes?.map((cause, index) => (
                          <li key={index}>{cause}</li>
                        ))}
                      </ul>
                      <h5>Runbook Steps</h5>
                      <ul>
                        {opsResponse.runbook_steps?.map((step, index) => (
                          <li key={index}>{step}</li>
                        ))}
                      </ul>
                      <h5>Tool Calls</h5>
                      <ul>
                        {opsResponse.tool_calls?.map((tool, index) => (
                          <li key={index}>
                            {tool.name} | {tool.status}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {activeTab === "governance" && (
                <div className="tab-content tab-governance">
                  <div className="result-card">
                    <h4>Discovery Wizard (CLI)</h4>
                    <p>Generate an adoption brief, risk notes, and an eval plan as a repeatable artifact.</p>
                    <code className="mono-inline">
                      python3 app/backend/scripts/discovery_wizard.py --company "ACME Korea"
                    </code>
                    <p>Output: docs/samples/discovery_output/&lt;timestamp&gt;_brief.md</p>
                  </div>

                  <div className="result-card">
                    <h4>Governance Summary</h4>
                    <p>Aggregate requests, policy events, tool usage, and cost signals into one summary.</p>
                    <button className="cta-primary" onClick={loadGovernanceSummary}>
                      Load Governance Summary
                    </button>
                    {governanceError && <p className="error-text">{governanceError}</p>}
                    {governanceSummary && (
                      <div>
                        <p>Requests: {governanceSummary.requests}</p>
                        <p>Total cost (USD): {governanceSummary.total_cost}</p>
                        <h5>Top Users</h5>
                        <ul>
                          {governanceSummary.top_users?.map((user, index) => (
                            <li key={index}>
                              {user[0]} | {user[1]}
                            </li>
                          ))}
                        </ul>
                        <h5>Tools Used</h5>
                        <ul>
                          {governanceSummary.tools_used?.map((tool, index) => (
                            <li key={index}>
                              {tool[0]} | {tool[1]}
                            </li>
                          ))}
                        </ul>
                        <h5>Policy Events</h5>
                        <ul>
                          {governanceSummary.policy_events?.map((event, index) => (
                            <li key={index}>
                              {event[0]} | {event[1]}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="result-card admin-card">
                    <h4>Admin Runtime LLM Settings</h4>
                    <p>
                      Update provider/model/runtime parameters from the browser. In production, wire secrets through
                      a Secret Manager instead of pasting keys into the UI.
                    </p>
                    <p className="admin-note">
                      Current role: <strong>{role}</strong> (Admin required)
                    </p>
                    <div className="admin-grid">
                      <label>
                        Provider
                        <select
                          value={llmRuntimeForm.provider}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, provider: event.target.value }))
                          }
                          disabled={!isAdmin}
                        >
                          <option value="stub">stub</option>
                          <option value="openai">openai</option>
                          <option value="openai_compatible">openai_compatible</option>
                          <option value="ollama">ollama</option>
                        </select>
                      </label>
                      <label>
                        Model
                        <input
                          value={llmRuntimeForm.model}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, model: event.target.value }))
                          }
                          disabled={!isAdmin}
                        />
                      </label>
                      <label>
                        Temperature
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="2"
                          value={llmRuntimeForm.temperature}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, temperature: event.target.value }))
                          }
                          disabled={!isAdmin}
                        />
                      </label>
                      <label>
                        Max Tokens
                        <input
                          type="number"
                          min="1"
                          max="8192"
                          value={llmRuntimeForm.max_tokens}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, max_tokens: event.target.value }))
                          }
                          disabled={!isAdmin}
                        />
                      </label>
                      <label>
                        Timeout (sec)
                        <input
                          type="number"
                          min="1"
                          max="600"
                          value={llmRuntimeForm.timeout_sec}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, timeout_sec: event.target.value }))
                          }
                          disabled={!isAdmin}
                        />
                      </label>
                      <label>
                        OpenAI Base URL
                        <input
                          value={llmRuntimeForm.openai_base_url}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, openai_base_url: event.target.value }))
                          }
                          disabled={!isAdmin}
                        />
                      </label>
                      <label>
                        Ollama Base URL
                        <input
                          value={llmRuntimeForm.ollama_base_url}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, ollama_base_url: event.target.value }))
                          }
                          disabled={!isAdmin}
                        />
                      </label>
                      <label>
                        OpenAI Org
                        <input
                          value={llmRuntimeForm.openai_org}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, openai_org: event.target.value }))
                          }
                          disabled={!isAdmin}
                        />
                      </label>
                      <label>
                        OpenAI API Key (Optional)
                        <input
                          type="password"
                          placeholder="sk-..."
                          value={llmRuntimeForm.openai_api_key}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, openai_api_key: event.target.value }))
                          }
                          disabled={!isAdmin}
                        />
                      </label>
                    </div>
                    <div className="action-row">
                      <button className="cta-ghost" onClick={() => loadAdminLlmRuntime()} disabled={!token || !isAdmin}>
                        Reload Runtime
                      </button>
                      <button
                        className="cta-primary"
                        onClick={() => saveAdminLlmRuntime(false)}
                        disabled={!token || !isAdmin || isSavingLlmRuntime}
                      >
                        {isSavingLlmRuntime ? "Saving..." : "Save Runtime Settings"}
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={() => saveAdminLlmRuntime(true)}
                        disabled={!token || !isAdmin || isSavingLlmRuntime}
                      >
                        Reset To Env Defaults
                      </button>
                    </div>
                    {llmRuntimeError && <p className="error-text">{llmRuntimeError}</p>}
                    {llmRuntime && (
                      <div className="admin-meta">
                        <p>
                          Active: {llmRuntime.provider} / {llmRuntime.model}
                        </p>
                        <p>
                          API key configured: {llmRuntime.openai_api_key_configured ? "yes" : "no"}
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="result-card admin-card">
                    <h4>Architecture Dataset Manager</h4>
                    <p>
                      Hot-swap the architecture JSONL dataset and reindex without redeploy. The fields{" "}
                      <code className="mono-inline">system</code>, <code className="mono-inline">env</code>, and{" "}
                      <code className="mono-inline">access_group</code> are required.
                    </p>
                    <p className="admin-note">
                      Current role: <strong>{role}</strong> (Admin required)
                    </p>
                    <div className="action-row">
                      <button className="cta-ghost" onClick={loadSampleArchitectureDataset} disabled={!isAdmin}>
                        Load Sample JSONL
                      </button>
                      <label className={isAdmin ? "file-btn" : "file-btn disabled"} aria-disabled={!isAdmin}>
                        Choose JSONL File
                        <input
                          type="file"
                          accept=".jsonl,.txt,application/json"
                          onChange={onArchitectureFileSelected}
                          disabled={!isAdmin}
                        />
                      </label>
                    </div>
                    <label>
                      JSONL Payload
                      <textarea
                        className="admin-jsonl"
                        placeholder='{"doc_id":"ACME-0001","system":"payments","env":"prod","access_group":"ops",...}'
                        value={architectureJsonl}
                        onChange={(event) => setArchitectureJsonl(event.target.value)}
                        disabled={!isAdmin}
                      />
                    </label>
                    <div className="action-row">
                      <button
                        className="cta-primary"
                        onClick={importArchitectureDataset}
                        disabled={!token || !isAdmin || isImportingArchitecture}
                      >
                        {isImportingArchitecture ? "Importing..." : "Import + Reindex"}
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={reindexArchitectureDataset}
                        disabled={!token || !isAdmin || isReindexingArchitecture}
                      >
                        {isReindexingArchitecture ? "Reindexing..." : "Reindex Existing Dataset"}
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={() => loadArchitectureCatalog()}
                        disabled={!token || !isAdmin}
                      >
                        Reload Catalog
                      </button>
                    </div>
                    {architectureError && <p className="error-text">{architectureError}</p>}
                    {architectureCatalog && (
                      <div className="admin-meta">
                        <p>Docs: {architectureCatalog.doc_count}</p>
                        <p>Indexed chunks: {architectureCatalog.chunk_count}</p>
                        <p>Systems: {architectureCatalog.systems?.join(", ") || "-"}</p>
                        <p>Envs: {architectureCatalog.envs?.join(", ") || "-"}</p>
                        <p>Access groups: {architectureCatalog.access_groups?.join(", ") || "-"}</p>
                        <code className="mono-inline">{architectureCatalog.source_path}</code>
                      </div>
                    )}
                  </div>

                  <div className="result-card runtime-card">
                    <h4>Runtime Debug Snapshot</h4>
                    <p>
                      Ops debugging snapshot. Inspect alerts, recent service events, and recent Control Tower decisions
                      in one view.
                    </p>
                    <p className="admin-note">
                      Current role: <strong>{role}</strong> (Ops/Admin required)
                    </p>
                    <div className="runtime-filters">
                      <label>
                        Event Limit
                        <input
                          type="number"
                          min="1"
                          max="500"
                          value={runtimeEventsLimit}
                          onChange={(event) => setRuntimeEventsLimit(event.target.value)}
                        />
                      </label>
                      <label>
                        Decision Limit
                        <input
                          type="number"
                          min="1"
                          max="200"
                          value={runtimeDecisionsLimit}
                          onChange={(event) => setRuntimeDecisionsLimit(event.target.value)}
                        />
                      </label>
                      <label>
                        Window (min)
                        <input
                          type="number"
                          min="0"
                          max="10080"
                          value={runtimeWindowMinutes}
                          onChange={(event) => setRuntimeWindowMinutes(event.target.value)}
                        />
                      </label>
                      <label>
                        Level
                        <select
                          value={runtimeLevelFilter}
                          onChange={(event) => setRuntimeLevelFilter(event.target.value)}
                        >
                          <option value="">All</option>
                          <option value="INFO">INFO</option>
                          <option value="WARN">WARN</option>
                          <option value="ERROR">ERROR</option>
                        </select>
                      </label>
                      <label>
                        Component
                        <input
                          placeholder="startup | alerts | diagnostics"
                          value={runtimeComponentFilter}
                          onChange={(event) => setRuntimeComponentFilter(event.target.value)}
                        />
                      </label>
                      <label className="toggle runtime-auto-toggle">
                        <input
                          type="checkbox"
                          checked={runtimeAutoRefresh}
                          onChange={(event) => setRuntimeAutoRefresh(event.target.checked)}
                          disabled={!token || !isOpsEligible}
                        />
                        Auto Refresh
                      </label>
                      <label>
                        Interval (sec)
                        <input
                          type="number"
                          min="5"
                          max="600"
                          value={runtimeAutoRefreshSec}
                          onChange={(event) => setRuntimeAutoRefreshSec(event.target.value)}
                        />
                      </label>
                      <label>
                        Search
                        <input
                          placeholder="message, component, scenario..."
                          value={runtimeSearchTerm}
                          onChange={(event) => setRuntimeSearchTerm(event.target.value)}
                        />
                      </label>
                      <label>
                        Alert Severity
                        <select
                          value={runtimeAlertSeverity}
                          onChange={(event) => setRuntimeAlertSeverity(event.target.value)}
                        >
                          <option value="all">All</option>
                          <option value="critical">Critical</option>
                          <option value="warning">Warning</option>
                          <option value="info">Info</option>
                        </select>
                      </label>
                      <label>
                        Sort Time
                        <select
                          value={runtimeSortOrder}
                          onChange={(event) => setRuntimeSortOrder(event.target.value)}
                        >
                          <option value="desc">Newest first</option>
                          <option value="asc">Oldest first</option>
                        </select>
                      </label>
                      <label className="toggle runtime-auto-toggle">
                        <input
                          type="checkbox"
                          checked={runtimeOnlyErrors}
                          onChange={(event) => setRuntimeOnlyErrors(event.target.checked)}
                        />
                        Only Errors
                      </label>
                    </div>
                    <div className="action-row">
                      <button
                        className="cta-primary"
                        onClick={loadRuntimeSnapshot}
                        disabled={!token || !isOpsEligible}
                        title={isOpsEligible ? "" : "Requires Ops/Admin role"}
                      >
                        Load Runtime Snapshot
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={refreshDiagnostics}
                        disabled={!token || !isOpsEligible || isRefreshingDiagnostics}
                        title={isOpsEligible ? "" : "Requires Ops/Admin role"}
                      >
                        {isRefreshingDiagnostics ? "Refreshing..." : "Refresh Diagnostics"}
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={exportRuntimeSnapshotCsv}
                        disabled={
                          !runtimeSnapshot ||
                          (runtimeView.alerts.length === 0 &&
                            runtimeView.events.length === 0 &&
                            runtimeView.decisions.length === 0)
                        }
                      >
                        Export Visible CSV
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={() => exportRuntimeSnapshotCsv("alerts")}
                        disabled={runtimeView.alerts.length === 0}
                      >
                        Export Alerts CSV
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={() => exportRuntimeSnapshotCsv("events")}
                        disabled={runtimeView.events.length === 0}
                      >
                        Export Events CSV
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={() => exportRuntimeSnapshotCsv("decisions")}
                        disabled={runtimeView.decisions.length === 0}
                      >
                        Export Decisions CSV
                      </button>
                    </div>

                    {runtimeError && <p className="error-text">{runtimeError}</p>}

                    {runtimeSnapshot && (
                      <div className="runtime-stack">
                        <p>Startup status: {runtimeSnapshot.startup_status}</p>
                        <p>Requests: {runtimeSnapshot.audit_summary?.requests ?? 0}</p>
                        <p>Daily cost (USD): {runtimeSnapshot.daily_cost_usd}</p>
                        {runtimeLastLoadedAt && <p>Last refresh: {runtimeLastLoadedAt}</p>}
                        <p>
                          Visible: alerts {runtimeView.alerts.length}/{runtimeView.baseAlerts.length} | events{" "}
                          {runtimeView.events.length}/{runtimeView.baseEvents.length} | decisions{" "}
                          {runtimeView.decisions.length}/{runtimeView.baseDecisions.length}
                        </p>

                        <h5>Alerts</h5>
                        {runtimeView.alerts.length ? (
                          <div className="runtime-alert-grid">
                            {runtimeView.alerts.map((alert, index) => (
                              <article key={`${alert.code}-${index}`} className="runtime-alert-item">
                                <div className="runtime-alert-head">
                                  <span className={severityBadgeClass(alert.severity)}>
                                    {String(alert.severity || "info").toUpperCase()}
                                  </span>
                                  <strong>{alert.code}</strong>
                                </div>
                                <p>{alert.message}</p>
                                <p>
                                  value: {alert.value ?? "-"} | threshold: {alert.threshold ?? "-"}
                                </p>
                              </article>
                            ))}
                          </div>
                        ) : (
                          <p>No matched alerts</p>
                        )}

                        <h5>Recent Service Events</h5>
                        {runtimeView.events.length ? (
                          <div className="runtime-table-wrap">
                            <table className="runtime-table">
                              <thead>
                                <tr>
                                  <th>Time</th>
                                  <th>Level</th>
                                  <th>Component</th>
                                  <th>Message</th>
                                </tr>
                              </thead>
                              <tbody>
                                {runtimeView.events.map((event, index) => (
                                  <tr key={`${event.id}-${index}`}>
                                    <td>{formatRuntimeTime(event.created_at)}</td>
                                    <td>
                                      <span className={levelBadgeClass(event.level)}>
                                        {String(event.level || "INFO").toUpperCase()}
                                      </span>
                                    </td>
                                    <td className="runtime-mono">{event.component}</td>
                                    <td>{event.message}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <p>No matched service events</p>
                        )}

                        <h5>Recent Control Tower Decisions</h5>
                        {runtimeView.decisions.length ? (
                          <div className="runtime-table-wrap">
                            <table className="runtime-table">
                              <thead>
                                <tr>
                                  <th>Time</th>
                                  <th>Risk</th>
                                  <th>Score</th>
                                  <th>Scenario</th>
                                  <th>Decision ID</th>
                                </tr>
                              </thead>
                              <tbody>
                                {runtimeView.decisions.map((decision, index) => (
                                  <tr key={`${decision.decision_id}-${index}`}>
                                    <td>{formatRuntimeTime(decision.created_at)}</td>
                                    <td>
                                      <span className={severityBadgeClass(decision.risk_level)}>
                                        {String(decision.risk_level || "").toUpperCase()}
                                      </span>
                                    </td>
                                    <td>{decision.risk_score}</td>
                                    <td>{decision.scenario_id}</td>
                                    <td className="runtime-mono">{decision.decision_id}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <p>No matched decisions</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === "integrations" && (
                <div className="tab-content tab-integrations">
                  <div className="result-card">
                    <h4>Slack Event Simulator</h4>
                    <p>
                      Simulate a Slack command payload. Use <code className="mono-inline">/uc1</code> or{" "}
                      <code className="mono-inline">/uc2</code> prefixes to trigger the corresponding workflow.
                    </p>
                    {integrationAuthRequired && (
                      <p className="muted-note">
                        Integration auth is enabled. Send requests with the JWT issued in Access Control.
                      </p>
                    )}
                    <div className="inline-grid">
                      <label>
                        Channel
                        <input
                          value={slackChannel}
                          onChange={(event) => setSlackChannel(event.target.value)}
                        />
                      </label>
                      <label>
                        Role (payload)
                        <input value={role} readOnly />
                      </label>
                      <label>
                        User ID (payload)
                        <input value={userId} readOnly />
                      </label>
                    </div>
                    <label>
                      Slack Message
                      <textarea value={slackText} onChange={(event) => setSlackText(event.target.value)} />
                    </label>
                    <button
                      className="cta-primary"
                      onClick={sendSlackEvent}
                      disabled={integrationAuthRequired && !token}
                    >
                      Send Slack Event
                    </button>
                    {slackError && <p className="error-text">{slackError}</p>}
                    {slackResponse?.text && (
                      <label>
                        Bot Reply
                        <textarea value={String(slackResponse.text)} readOnly />
                      </label>
                    )}
                  </div>

                  <div className="result-card">
                    <h4>Jira Ticket Simulator</h4>
                    <p>
                      Simulate generating an incident triage comment for a Jira ticket using the UC2 log analysis
                      workflow.
                    </p>
                    <div className="inline-grid">
                      <label>
                        Ticket ID
                        <input
                          value={jiraTicketId}
                          onChange={(event) => setJiraTicketId(event.target.value)}
                        />
                      </label>
                      <label>
                        Priority
                        <select
                          value={jiraPriority}
                          onChange={(event) => setJiraPriority(event.target.value)}
                        >
                          <option value="Low">Low</option>
                          <option value="Medium">Medium</option>
                          <option value="High">High</option>
                          <option value="Critical">Critical</option>
                        </select>
                      </label>
                      <label>
                        Role (payload)
                        <input value={role} readOnly />
                      </label>
                    </div>
                    <label>
                      Title
                      <input value={jiraTitle} onChange={(event) => setJiraTitle(event.target.value)} />
                    </label>
                    <label>
                      Description
                      <textarea
                        value={jiraDescription}
                        onChange={(event) => setJiraDescription(event.target.value)}
                      />
                    </label>
                    <button
                      className="cta-primary"
                      onClick={generateJiraComment}
                      disabled={integrationAuthRequired && !token}
                    >
                      Generate Jira Comment
                    </button>
                    {jiraError && <p className="error-text">{jiraError}</p>}
                    {jiraResponse?.comment && (
                      <label>
                        Generated Comment
                        <textarea value={String(jiraResponse.comment)} readOnly />
                      </label>
                    )}
                  </div>
                </div>
              )}
            </section>
          </div>
        )}
      </main>

      <footer className="site-footer">
        <div className="footer-meta">
          <p>Observability: /metrics</p>
          <p>Audit logs: app/backend/data/audit.log (runtime)</p>
          <p>
            Contact:{" "}
            <a href="https://github.com/KIM3310/enterprise-llm-adoption-kit/issues">GitHub Issues</a>
          </p>
          <p>Privacy: only operational telemetry required for governance workflows.</p>
          <p>Terms: guidance output must be reviewed by human operators before production decisions.</p>
          <p>
            Links: <a href="/about.html">About</a> · <a href="/privacy.html">Privacy</a> · <a href="/terms.html">Terms</a> ·{" "}
            <a href="/contact.html">Contact</a> · <a href="/compliance.html">Compliance</a>
          </p>
        </div>
        <div className="footer-ad">
          <p>Sponsored</p>
          <AdSenseSlot key={activeAdSenseSlot || "footer-empty-slot"} slot={activeAdSenseSlot} />
        </div>
      </footer>
    </div>
  );
}
