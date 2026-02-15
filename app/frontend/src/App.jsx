import React, { useEffect, useMemo, useRef, useState } from "react";
import heroTower from "./assets/hero-tower.svg";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

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

const SAMPLE_ARCHITECTURE_JSONL = [
  JSON.stringify({
    doc_id: "ACME-0001",
    title: "Payments Production Handover",
    system: "payments",
    env: "prod",
    access_group: "ops",
    owner: { name: "Platform Owner", team: "Payments", contact: "owner@acme.local" },
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
    owner: { name: "Data Lead", team: "Analytics", contact: "data@acme.local" },
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

function getPageFromHash() {
  const hash = window.location.hash.replace("#", "").trim().toLowerCase();
  return pages.includes(hash) ? hash : "home";
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
  const [page, setPage] = useState(() => getPageFromHash());
  const [userId, setUserId] = useState("acme-demo");
  const [role, setRole] = useState("Employee");
  const [token, setToken] = useState("");
  const [activeTab, setActiveTab] = useState("architecture");
  const [status, setStatus] = useState("Ready");
  const [lastRequestId, setLastRequestId] = useState("");
  const [health, setHealth] = useState({ status: "unknown", startup_status: "" });
  const [healthCheckedAt, setHealthCheckedAt] = useState("");
  const [scenarioRun, setScenarioRun] = useState(null);

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
    openai_org: "",
    openai_api_key: ""
  });
  const [isSavingLlmRuntime, setIsSavingLlmRuntime] = useState(false);
  const [architectureCatalog, setArchitectureCatalog] = useState(null);
  const [architectureJsonl, setArchitectureJsonl] = useState("");
  const [architectureError, setArchitectureError] = useState("");
  const [isImportingArchitecture, setIsImportingArchitecture] = useState(false);
  const [isReindexingArchitecture, setIsReindexingArchitecture] = useState(false);

  useEffect(() => {
    const onHashChange = () => setPage(getPageFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [page]);

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(parseApiError(data, "Health check failed"));
        }
        if (cancelled) {
          return;
        }
        setHealth({
          status: String(data.status || "ok"),
          startup_status: String(data.startup_status || "")
        });
        setHealthCheckedAt(new Date().toLocaleTimeString());
      } catch (_error) {
        if (cancelled) {
          return;
        }
        setHealth({ status: "offline", startup_status: "" });
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

  function navigate(nextPage) {
    window.location.hash = nextPage;
    setPage(nextPage);
  }

  async function fetchJson(path, options = {}) {
    const { errorMessage = "Request failed", ...fetchOptions } = options;
    let res;
    try {
      res = await fetch(`${API_BASE}${path}`, fetchOptions);
    } catch (_error) {
      const offline = new Error(
        `Backend offline at ${API_BASE}. Start the backend on :8000 and retry.`
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

  async function login(options = {}) {
    const { silent = false, throwOnError = false } = options;
    if (!silent) {
      setStatus("Authenticating...");
    }
    try {
      const { data, requestId } = await fetchJson("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, role }),
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
    if (!(page === "console" && activeTab === "governance" && runtimeAutoRefresh && token)) {
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
    if (!(page === "console" && activeTab === "governance" && token)) {
      return;
    }
    void loadAdminLlmRuntime({ silent: true });
    void loadArchitectureCatalog({ silent: true });
  }, [page, activeTab, token]);

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

  async function runScenarioRunner() {
    const steps = buildDefaultScenarioSteps();
    const startedAt = new Date().toISOString();

    setScenarioRun({ running: true, startedAt, finishedAt: "", steps });
    setDiagnosisResponse(null);
    setOpsResponse(null);
    setGovernanceSummary(null);
    setGovernanceError("");
    setRuntimeSnapshot(null);
    setRuntimeError("");
    setStatus("Running end-to-end scenario...");

    const runStep = async (stepKey, runner) => {
      updateScenarioStep(stepKey, { status: "running", startedAt: new Date().toISOString(), error: "" });
      const result = await runner();
      const requestId = result?.requestId || "";
      updateScenarioStep(stepKey, {
        status: "ok",
        requestId,
        finishedAt: new Date().toISOString()
      });
      return result;
    };

    try {
      await runStep("auth", async () => login({ silent: true, throwOnError: true }));
      await runStep("architecture", async () =>
        runArchitectureDiagnosis({ silent: true, throwOnError: true })
      );
      await runStep("ops", async () => runOpsRiskAnalysis({ silent: true, throwOnError: true }));
      await runStep("governance", async () =>
        loadGovernanceSummary({ silent: true, throwOnError: true })
      );

      const isOpsEligible = role === "Ops" || role === "Admin";
      if (isOpsEligible) {
        await runStep("runtime", async () =>
          loadRuntimeSnapshot({ silent: true, throwOnError: true })
        );
      }

      setScenarioRun((prev) =>
        prev ? { ...prev, running: false, finishedAt: new Date().toISOString() } : prev
      );
      setStatus("Scenario complete");
    } catch (error) {
      const message = error?.message || "Scenario failed";
      setScenarioRun((prev) =>
        prev ? { ...prev, running: false, finishedAt: new Date().toISOString() } : prev
      );
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
          finishedAt: new Date().toISOString()
        };
        return { ...prev, steps: stepsNext };
      });
    }
  }

  function exportScenarioReport() {
    if (!scenarioRun || scenarioRun.running) {
      return;
    }

    const stamp = new Date().toISOString();
    const lines = [];
    lines.push(`# ${APP_NAME} - End-to-End Validation Report`);
    lines.push("");
    lines.push(`- generated_at_utc: ${stamp}`);
    lines.push(`- api_base: ${API_BASE}`);
    lines.push(`- user_id: ${userId}`);
    lines.push(`- role: ${role}`);
    if (scenarioRun.startedAt) {
      lines.push(`- started_at_utc: ${scenarioRun.startedAt}`);
    }
    if (scenarioRun.finishedAt) {
      lines.push(`- finished_at_utc: ${scenarioRun.finishedAt}`);
    }
    lines.push("");

    lines.push("## Execution Timeline");
    lines.push("| Step | Status | Request ID | Endpoint |");
    lines.push("| --- | --- | --- | --- |");
    scenarioRun.steps.forEach((step) => {
      const status = String(step.status || "idle").toUpperCase();
      const requestId = step.requestId ? `\`${step.requestId}\`` : "-";
      const endpoint = step.endpoint ? `\`${step.endpoint}\`` : "-";
      lines.push(`| ${step.title} | ${status} | ${requestId} | ${endpoint} |`);
    });
    lines.push("");

    lines.push("## UC1 - Architecture Risk Diagnosis");
    lines.push("### Prompt");
    lines.push("```");
    lines.push(String(diagnosisQuery || "").trim());
    lines.push("```");
    lines.push("");
    lines.push("### Answer");
    lines.push(diagnosisResponse?.answer ? String(diagnosisResponse.answer) : "_Not available_");
    lines.push("");
    if (Array.isArray(diagnosisResponse?.citations) && diagnosisResponse.citations.length > 0) {
      lines.push("### Citations");
      diagnosisResponse.citations.forEach((citation) => {
        lines.push(`- ${citation.doc_id} :: ${citation.field_path}`);
      });
      lines.push("");
    }

    lines.push("## UC2 - Operations Log Risk Analysis");
    lines.push("### Input logs");
    lines.push("```");
    lines.push(String(opsLogs || "").trim());
    lines.push("```");
    lines.push("");
    lines.push("### Summary");
    lines.push(opsResponse?.summary ? String(opsResponse.summary) : "_Not available_");
    lines.push("");
    if (Array.isArray(opsResponse?.root_causes) && opsResponse.root_causes.length > 0) {
      lines.push("### Root Causes");
      opsResponse.root_causes.forEach((cause) => lines.push(`- ${cause}`));
      lines.push("");
    }
    if (Array.isArray(opsResponse?.runbook_steps) && opsResponse.runbook_steps.length > 0) {
      lines.push("### Runbook Steps");
      opsResponse.runbook_steps.forEach((step) => lines.push(`- ${step}`));
      lines.push("");
    }

    lines.push("## Governance Summary");
    if (governanceSummary) {
      lines.push(`- requests: ${governanceSummary.requests ?? "-"}`);
      lines.push(`- total_cost_usd: ${governanceSummary.total_cost ?? "-"}`);
      lines.push(`- policy_events: ${Array.isArray(governanceSummary.policy_events) ? governanceSummary.policy_events.length : 0}`);
      lines.push(`- tools_used: ${Array.isArray(governanceSummary.tools_used) ? governanceSummary.tools_used.length : 0}`);
    } else {
      lines.push("_Not available_");
    }
    lines.push("");

    lines.push("## Ops Control Tower Snapshot");
    if (runtimeSnapshot) {
      lines.push(`- startup_status: ${runtimeSnapshot.startup_status ?? "-"}`);
      lines.push(`- requests: ${runtimeSnapshot.audit_summary?.requests ?? "-"}`);
      lines.push(`- daily_cost_usd: ${runtimeSnapshot.daily_cost_usd ?? "-"}`);
      lines.push(`- alerts: ${Array.isArray(runtimeSnapshot.alerts) ? runtimeSnapshot.alerts.length : 0}`);
      lines.push(`- service_events: ${Array.isArray(runtimeSnapshot.service_events) ? runtimeSnapshot.service_events.length : 0}`);
      lines.push(`- recent_decisions: ${Array.isArray(runtimeSnapshot.recent_decisions) ? runtimeSnapshot.recent_decisions.length : 0}`);
    } else {
      lines.push("_Not available (requires Ops/Admin role)_");
    }
    lines.push("");

    const safeStamp = stamp.replace(/[:.]/g, "-");
    exportTextFile(`atelier-validation-report-${safeStamp}.md`, lines.join("\n"), "text/markdown;charset=utf-8");
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
                      <button className="cta-primary" onClick={runScenarioRunner} disabled={scenarioRun?.running}>
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
                    {String(health.status || "")
                      .toLowerCase()
                      .trim() === "offline" && (
                      <li>
                        Start local demo:{" "}
                        <code className="mono-inline">bash scripts/start_demo_local.sh</code>
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
                        >
                          <option value="stub">stub</option>
                          <option value="openai">openai</option>
                          <option value="openai_compatible">openai_compatible</option>
                        </select>
                      </label>
                      <label>
                        Model
                        <input
                          value={llmRuntimeForm.model}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, model: event.target.value }))
                          }
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
                        />
                      </label>
                      <label>
                        OpenAI Base URL
                        <input
                          value={llmRuntimeForm.openai_base_url}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, openai_base_url: event.target.value }))
                          }
                        />
                      </label>
                      <label>
                        OpenAI Org
                        <input
                          value={llmRuntimeForm.openai_org}
                          onChange={(event) =>
                            setLlmRuntimeForm((prev) => ({ ...prev, openai_org: event.target.value }))
                          }
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
                        />
                      </label>
                    </div>
                    <div className="action-row">
                      <button className="cta-ghost" onClick={() => loadAdminLlmRuntime()} disabled={!token}>
                        Reload Runtime
                      </button>
                      <button
                        className="cta-primary"
                        onClick={() => saveAdminLlmRuntime(false)}
                        disabled={!token || isSavingLlmRuntime}
                      >
                        {isSavingLlmRuntime ? "Saving..." : "Save Runtime Settings"}
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={() => saveAdminLlmRuntime(true)}
                        disabled={!token || isSavingLlmRuntime}
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
                    <div className="action-row">
                      <button className="cta-ghost" onClick={loadSampleArchitectureDataset}>
                        Load Sample JSONL
                      </button>
                      <label className="file-btn">
                        Choose JSONL File
                        <input type="file" accept=".jsonl,.txt,application/json" onChange={onArchitectureFileSelected} />
                      </label>
                    </div>
                    <label>
                      JSONL Payload
                      <textarea
                        className="admin-jsonl"
                        placeholder='{"doc_id":"ACME-0001","system":"payments","env":"prod","access_group":"ops",...}'
                        value={architectureJsonl}
                        onChange={(event) => setArchitectureJsonl(event.target.value)}
                      />
                    </label>
                    <div className="action-row">
                      <button
                        className="cta-primary"
                        onClick={importArchitectureDataset}
                        disabled={!token || isImportingArchitecture}
                      >
                        {isImportingArchitecture ? "Importing..." : "Import + Reindex"}
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={reindexArchitectureDataset}
                        disabled={!token || isReindexingArchitecture}
                      >
                        {isReindexingArchitecture ? "Reindexing..." : "Reindex Existing Dataset"}
                      </button>
                      <button className="cta-ghost" onClick={() => loadArchitectureCatalog()} disabled={!token}>
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
                      <button className="cta-primary" onClick={loadRuntimeSnapshot} disabled={!token}>
                        Load Runtime Snapshot
                      </button>
                      <button
                        className="cta-ghost"
                        onClick={refreshDiagnostics}
                        disabled={!token || isRefreshingDiagnostics}
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
            </section>
          </div>
        )}
      </main>

      <footer className="site-footer">
        <p>Observability: /metrics</p>
        <p>Audit logs: app/backend/data/audit.log (runtime)</p>
      </footer>
    </div>
  );
}
