import React, { useEffect, useRef, useState } from "react";

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

function getPageFromHash() {
  const hash = window.location.hash.replace("#", "").trim().toLowerCase();
  return pages.includes(hash) ? hash : "home";
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

  async function login() {
    setStatus("Authenticating...");
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, role })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Login failed");
      }
      setToken(data.access_token);
      setStatus("Authentication complete");
    } catch (error) {
      setStatus(error.message || "Login failed");
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

      let res = await fetch(`${API_BASE}/uc1/architecture`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body
      });

      // Backward compatibility for older backend route names.
      if (res.status === 404) {
        res = await fetch(`${API_BASE}/uc1/handover`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body
        });
      }

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Architecture diagnosis failed");
      }

      setDiagnosisResponse(data);
      setStatus("Architecture diagnosis complete");
    } catch (error) {
      setStatus(error.message || "Architecture diagnosis failed");
    }
  }

  async function runOpsRiskAnalysis() {
    setStatus("Running operations risk analysis...");
    try {
      const res = await fetch(`${API_BASE}/uc2/log-intel`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ logs: opsLogs })
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Operations risk analysis failed");
      }

      setOpsResponse(data);
      setStatus("Operations risk analysis complete");
    } catch (error) {
      setStatus(error.message || "Operations risk analysis failed");
    }
  }

  async function loadGovernanceSummary() {
    setStatus("Loading governance summary...");
    setGovernanceError("");

    try {
      const res = await fetch(`${API_BASE}/audit/summary`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Governance summary failed");
      }
      setGovernanceSummary(data);
      setStatus("Governance summary loaded");
    } catch (error) {
      setGovernanceError(error.message || "Governance summary failed");
      setStatus("Governance summary error");
    }
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
          <div className="page-view">
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
              </Reveal>
            </section>

            <section className="panel">
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

            <section className="panel">
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
                <div className="tab-content">
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
                <div className="tab-content">
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
                <div className="tab-content">
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
                    {governanceError && <p>{governanceError}</p>}
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
