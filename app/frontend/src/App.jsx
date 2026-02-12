import React, { useEffect, useMemo, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const IMG_HERO =
  "https://upload.wikimedia.org/wikipedia/commons/9/9f/Blacksmith%27s_workshop_2.jpg";
const IMG_ARCHITECTURE =
  "https://upload.wikimedia.org/wikipedia/commons/c/c6/The_Blacksmith%27s_Studio.jpg";
const IMG_OPERATIONS =
  "https://upload.wikimedia.org/wikipedia/commons/e/e9/Blacksmith_S_Workshop_%2860845456%29.jpeg";
const IMG_GOVERNANCE =
  "https://upload.wikimedia.org/wikipedia/commons/f/f0/Charlemont%E2%80%93A_Blacksmith_in_his_Workshop%2C_1882.jpg";
const IMG_VALIDATION =
  "https://upload.wikimedia.org/wikipedia/commons/2/28/A_Blacksmith%27s_Shop_%28by_Joseph_Wright_of_Derby%29.jpg";
const IMG_SCENARIO =
  "https://upload.wikimedia.org/wikipedia/commons/1/16/The_Blacksmith_%28Interior_of_a_Workshop_with_Figures%29.jpg";
const IMG_SIGNAL =
  "https://upload.wikimedia.org/wikipedia/commons/3/3e/Blacksmith_at_work.jpg";

const roles = ["Employee", "Ops", "Admin"];
const pages = ["home", "capabilities", "validation", "scenario", "console"];

const navItems = [
  { key: "home", label: "Home" },
  { key: "capabilities", label: "Capabilities" },
  { key: "validation", label: "Validation" },
  { key: "scenario", label: "Scenarios" },
  { key: "console", label: "Live Console" }
];

const capabilityCards = [
  {
    title: "Role-Based Access Control",
    body: "직무별(Employee/Ops/Admin)로 볼 수 있는 문서 범위를 분리해 권한 누수를 방지합니다."
  },
  {
    title: "RAG Retrieval with Citations",
    body: "질문에 맞는 문서를 검색하고, 답변 근거 문서 ID와 필드를 함께 제시합니다."
  },
  {
    title: "Architecture Risk Diagnosis",
    body: "아키텍처 질문을 기반으로 보안/운영 리스크를 진단하고 근거 소스를 함께 제시합니다."
  },
  {
    title: "Operations Log Risk Analysis",
    body: "장애 로그를 요약하고 원인 가설, 우선 대응 런북 단계를 정리합니다."
  },
  {
    title: "Safety Guardrails",
    body: "Prompt injection 탐지와 안전 거절 규칙으로 위험한 요청을 차단합니다."
  },
  {
    title: "PII Redaction and Audit",
    body: "민감정보를 자동 마스킹하고 모든 요청/응답 이벤트를 감사 로그로 기록합니다."
  },
  {
    title: "Governance Summary",
    body: "요청 수, 정책 이벤트, 툴 사용, 비용 지표를 하나의 요약 리포트로 확인합니다."
  },
  {
    title: "Metrics and Eval Readiness",
    body: "latency/token/cost/policy 이벤트 지표와 평가 흐름을 묶어 운영 준비 상태를 점검합니다."
  }
];

const validationActs = [
  {
    title: "Act 1 - Discovery to Scope",
    text: "업무 목표, 사용자 역할, 데이터 민감도를 정리해 도입 범위를 확정합니다."
  },
  {
    title: "Act 2 - Security and Evals",
    text: "RBAC, redaction, injection 방어, 평가 기준을 검증해 안전성과 품질 기준을 맞춥니다."
  },
  {
    title: "Act 3 - Operations Proof",
    text: "기능 실행 결과를 audit/metrics로 확인해 운영 가시성과 확장성을 점검합니다."
  }
];

const scenarioSteps = [
  {
    title: "Identity and Role Check",
    text: "JWT 발급 후 역할별 접근 범위를 점검합니다.",
    endpoint: "/auth/login"
  },
  {
    title: "Architecture Risk Diagnosis",
    text: "아키텍처 리스크 진단 결과와 근거(citation) 일관성을 검증합니다.",
    endpoint: "/uc1/architecture"
  },
  {
    title: "Operations Log Risk Analysis",
    text: "로그 요약, 원인 가설, 런북 단계를 점검합니다.",
    endpoint: "/uc2/log-intel"
  },
  {
    title: "Governance and Observability",
    text: "정책 이벤트, 비용, 요청량 지표를 확인해 운영 준비도를 판단합니다.",
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

export default function App() {
  const [page, setPage] = useState(() => getPageFromHash());
  const [userId, setUserId] = useState("aeak-demo");
  const [role, setRole] = useState("Employee");
  const [token, setToken] = useState("");
  const [activeTab, setActiveTab] = useState("architecture");
  const [status, setStatus] = useState("Atelier console ready");
  const [lastRequestId, setLastRequestId] = useState("");

  const [diagnosisQuery, setDiagnosisQuery] = useState(
    "우리 조직의 LLM 도입 아키텍처에서 보안/운영 리스크를 우선순위로 정리해줘"
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

  function navigate(nextPage) {
    window.location.hash = nextPage;
    setPage(nextPage);
  }

  async function fetchJson(path, options = {}) {
    const { errorMessage = "Request failed", ...fetchOptions } = options;
    const res = await fetch(`${API_BASE}${path}`, fetchOptions);
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

  async function login() {
    setStatus("Authenticating...");
    try {
      const { data, requestId } = await fetchJson("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, role }),
        errorMessage: "Login failed"
      });
      setToken(data.access_token);
      setStatus(withRequestId("Authentication complete", requestId));
    } catch (error) {
      setStatus(withRequestId(error.message || "Login failed", error.requestId));
    }
  }

  async function runArchitectureDiagnosis() {
    setStatus("Running architecture diagnosis...");
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
      setStatus(withRequestId("Architecture diagnosis complete", result.requestId));
    } catch (error) {
      setStatus(withRequestId(error.message || "Architecture diagnosis failed", error.requestId));
    }
  }

  async function runOpsRiskAnalysis() {
    setStatus("Running operations risk analysis...");
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
      setStatus(withRequestId("Operations risk analysis complete", requestId));
    } catch (error) {
      setStatus(withRequestId(error.message || "Operations risk analysis failed", error.requestId));
    }
  }

  async function loadGovernanceSummary() {
    setStatus("Loading governance summary...");
    setGovernanceError("");

    try {
      const { data, requestId } = await fetchJson("/audit/summary", {
        errorMessage: "Governance summary failed"
      });
      setGovernanceSummary(data);
      setStatus(withRequestId("Governance summary loaded", requestId));
    } catch (error) {
      setGovernanceError(error.message || "Governance summary failed");
      setStatus(withRequestId("Governance summary error", error.requestId));
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
      setLlmRuntimeError("JWT가 필요합니다. Admin 토큰을 먼저 발급하세요.");
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
      setLlmRuntimeError("JWT가 필요합니다. Admin 토큰을 먼저 발급하세요.");
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
      setArchitectureError("파일을 읽지 못했습니다.");
    };
    reader.readAsText(file, "utf-8");
  }

  async function loadArchitectureCatalog(options = {}) {
    const { silent = false } = options;
    if (!token) {
      setArchitectureError("JWT가 필요합니다. Admin 토큰을 먼저 발급하세요.");
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
      setArchitectureError("JWT가 필요합니다. Admin 토큰을 먼저 발급하세요.");
      return;
    }
    if (!architectureJsonl.trim()) {
      setArchitectureError("JSONL 데이터를 입력하거나 파일을 선택하세요.");
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
      setArchitectureError("JWT가 필요합니다. Admin 토큰을 먼저 발급하세요.");
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
    const { silent = false } = options;
    if (!token) {
      setRuntimeError("JWT가 필요합니다. 먼저 Access Control에서 토큰을 발급하세요.");
      return;
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
    } catch (error) {
      setRuntimeError(error.message || "Runtime snapshot failed");
      if (!silent) {
        setStatus(withRequestId("Runtime snapshot error", error.requestId));
      }
    }
  }

  async function refreshDiagnostics() {
    if (!token) {
      setRuntimeError("JWT가 필요합니다. 먼저 Access Control에서 토큰을 발급하세요.");
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
      setRuntimeError("CSV로 내보낼 데이터가 없습니다.");
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

  return (
    <div className="site-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />

      <header className="top-nav">
        <button className="brand" onClick={() => navigate("home")}>
          <span className="brand-mark">A</span>
          <span className="brand-text">LLM Adoption Atelier</span>
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

        <button className="cta-light" onClick={() => navigate("console")}>
          Open Console
        </button>
      </header>

      <main className="main-content">
        {page === "home" && (
          <div className="page-view">
            <section className="hero-grid">
              <Reveal className="hero-copy">
                <p className="eyebrow">Medieval Craft x Modern AI</p>
                <h1>LLM Adoption Atelier</h1>
                <p className="lead">
                  중세 공방의 정교함과 현대 AI 운영 원칙을 결합해, 엔터프라이즈 LLM 도입 전에 필요한 검증을
                  실제 콘솔 흐름으로 제공합니다.
                </p>
                <div className="hero-actions">
                  <button className="cta-primary" onClick={() => navigate("capabilities")}>
                    Explore Capabilities
                  </button>
                  <button className="cta-ghost" onClick={() => navigate("console")}>
                    Run Live Validation
                  </button>
                </div>
                <div className="kpi-grid">
                  <article className="kpi-item">
                    <p>08</p>
                    <span>Core Features</span>
                  </article>
                  <article className="kpi-item">
                    <p>99.9%</p>
                    <span>Observability Coverage-Oriented</span>
                  </article>
                  <article className="kpi-item">
                    <p>05</p>
                    <span>Scenario Pages</span>
                  </article>
                </div>
              </Reveal>

              <Reveal className="hero-media" delay={120}>
                <div className="media-frame">
                  <img src={IMG_HERO} alt="European medieval artisan workshop" />
                  <div className="media-tag">Atelier Motion</div>
                </div>
              </Reveal>
            </section>

            <section className="section-block">
              <Reveal className="section-head">
                <p className="eyebrow">Core Service Surfaces</p>
                <h2>Service-Aligned Validation Scenes</h2>
                <p>
                  홈 카드 3개를 실제 코어 기능과 직접 연결했습니다. 아키텍처 리스크 진단, 운영 로그 분석,
                  거버넌스 점검 흐름을 한 번에 이해할 수 있도록 구성했습니다.
                </p>
              </Reveal>

              <div className="gallery-grid">
                <Reveal className="gallery-card" delay={60}>
                  <img src={IMG_ARCHITECTURE} alt="Architecture risk diagnosis scene" />
                  <h3>Architecture Risk Diagnosis</h3>
                  <p>도입 아키텍처 질문을 기준으로 보안/운영 리스크를 진단하는 핵심 기능입니다.</p>
                </Reveal>

                <Reveal className="gallery-card" delay={120}>
                  <img src={IMG_OPERATIONS} alt="Operations log analysis scene" />
                  <h3>Operations Log Risk Analysis</h3>
                  <p>장애 로그를 요약하고 원인 가설과 실행 가능한 런북 단계를 제공하는 기능입니다.</p>
                </Reveal>

                <Reveal className="gallery-card" delay={180}>
                  <img src={IMG_GOVERNANCE} alt="Governance and audit review scene" />
                  <h3>Governance and Audit Flow</h3>
                  <p>요청량, 정책 이벤트, 비용 지표를 모아 도입 의사결정 품질을 높이는 기능입니다.</p>
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
                <h2>코어 서비스와 정확히 맞물린 검증 기능</h2>
                <p>
                  이 플랫폼은 아키텍처 진단, 운영 로그 분석, 거버넌스 요약을 중심으로 엔터프라이즈 LLM 도입의
                  핵심 의사결정 질문에 답하도록 설계되었습니다.
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

              <div className="gif-ribbon">
                <Reveal className="ribbon-item" delay={80}>
                  <img src={IMG_ARCHITECTURE} alt="Architecture risk ribbon" />
                  <span>Architecture Discipline</span>
                </Reveal>
                <Reveal className="ribbon-item" delay={130}>
                  <img src={IMG_OPERATIONS} alt="Operations risk ribbon" />
                  <span>Operations Discipline</span>
                </Reveal>
              </div>
            </section>
          </div>
        )}

        {page === "validation" && (
          <div className="page-view">
            <section className="section-block">
              <Reveal className="section-head">
                <p className="eyebrow">Validation Flow</p>
                <h2>도입 전 검증 순서를 명확히 고정한 흐름</h2>
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
                  <img src={IMG_VALIDATION} alt="Validation workshop checklist visual" />
                  <h3>Validation Checklist</h3>
                  <ul>
                    <li>RBAC and policy event consistency</li>
                    <li>Citation reliability for architecture diagnosis</li>
                    <li>Operations risk output actionability</li>
                    <li>Governance metrics traceability</li>
                  </ul>
                </Reveal>
              </div>
            </section>
          </div>
        )}

        {page === "scenario" && (
          <div className="page-view">
            <section className="section-block">
              <Reveal className="section-head">
                <p className="eyebrow">Scenario Viewer</p>
                <h2>서비스 검증 시나리오를 화면 단위로 재현</h2>
              </Reveal>

              <div className="scenario-layout">
                <Reveal className="scenario-window" delay={70}>
                  <div className="window-bar">
                    <span className="window-dot red" />
                    <span className="window-dot amber" />
                    <span className="window-dot green" />
                    <p>Scenario Runtime Window</p>
                  </div>

                  <div className="window-body">
                    {scenarioSteps.map((step) => (
                      <article key={step.title} className="scenario-step">
                        <h3>{step.title}</h3>
                        <p>{step.text}</p>
                        <code>{step.endpoint}</code>
                      </article>
                    ))}
                  </div>
                </Reveal>

                <Reveal className="scenario-visual" delay={130}>
                  <img src={IMG_SCENARIO} alt="Scenario execution workshop visual" />
                  <h3>Scenario Alignment</h3>
                  <ul>
                    <li>도입 아키텍처 질문 중심</li>
                    <li>운영 로그 기반 리스크 분석</li>
                    <li>거버넌스 지표 기반 판단</li>
                    <li>실행 가능한 콘솔 검증 흐름</li>
                  </ul>
                  <button className="cta-primary" onClick={() => navigate("console")}>
                    Move To Live Console
                  </button>
                </Reveal>
              </div>
            </section>
          </div>
        )}

        {page === "console" && (
          <div className="page-view console-view">
            <section className="section-block console-header">
              <Reveal className="section-head">
                <p className="eyebrow">Live Console</p>
                <h2>코어 서비스 검증을 실행하는 메인 워크벤치</h2>
                <p>
                  이 콘솔은 아키텍처 리스크 진단, 운영 로그 분석, 거버넌스 요약을 실제 API 호출로 검증하도록
                  구성되어 있습니다.
                </p>
              </Reveal>

              <Reveal className="signal-card" delay={120}>
                <img src={IMG_SIGNAL} alt="Live validation signal visual" />
                <span>System Status</span>
                <strong>{status || "Ready"}</strong>
                {lastRequestId && <code className="signal-request-id">request_id: {lastRequestId}</code>}
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
                    <p>도입 브리프, 리스크 노트, 평가 계획을 자동 생성합니다.</p>
                    <code className="mono-inline">
                      python3 app/backend/scripts/discovery_wizard.py --company "ACME Korea"
                    </code>
                    <p>Output: docs/samples/discovery_output/&lt;timestamp&gt;_brief.md</p>
                  </div>

                  <div className="result-card">
                    <h4>Governance Summary</h4>
                    <p>요청량, 정책 이벤트, 툴 사용, 비용 지표를 통합 요약합니다.</p>
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
                      브라우저에서 LLM provider/model/runtime 파라미터를 변경할 수 있습니다. 실제 운영에서는
                      Secret Manager 연동이 필요합니다.
                    </p>
                    <p className="admin-note">
                      현재 선택 Role: <strong>{role}</strong> (Admin 권한 필요)
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
                      운영 중에도 아키텍처 JSONL 데이터를 교체하고 즉시 재인덱싱할 수 있습니다. `system/env/access_group`
                      필드는 필수입니다.
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
                      운영 디버깅용 스냅샷입니다. 최근 서비스 이벤트, 최근 Control Tower 결정, 현재 경보 상태를
                      한 번에 확인할 수 있습니다.
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
        <p>Audit logs: data/audit.log</p>
      </footer>
    </div>
  );
}
