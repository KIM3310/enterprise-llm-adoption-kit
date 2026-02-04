import React, { useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const roles = ["Employee", "Ops", "Admin"];

export default function App() {
  const [userId, setUserId] = useState("aeak-demo");
  const [role, setRole] = useState("Employee");
  const [token, setToken] = useState("");
  const [activeTab, setActiveTab] = useState("uc1");
  const [status, setStatus] = useState("");

  const [uc1Query, setUc1Query] = useState("Summarize handover risks for payments prod");
  const [uc1CitationOnly, setUc1CitationOnly] = useState(false);
  const [uc1System, setUc1System] = useState("");
  const [uc1Env, setUc1Env] = useState("");
  const [uc1Response, setUc1Response] = useState(null);

  const [uc2Logs, setUc2Logs] = useState("ERROR Timeout while calling payments API");
  const [uc2Response, setUc2Response] = useState(null);
  const [auditSummary, setAuditSummary] = useState(null);
  const [auditError, setAuditError] = useState("");

  async function login() {
    setStatus("Authenticating...");
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, role })
    });
    if (!res.ok) {
      setStatus("Login failed");
      return;
    }
    const data = await res.json();
    setToken(data.access_token);
    setStatus("Authenticated");
  }

  async function runUc1() {
    setStatus("Running UC1...");
    const res = await fetch(`${API_BASE}/uc1/handover`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        query: uc1Query,
        citation_only: uc1CitationOnly,
        system: uc1System || null,
        env: uc1Env || null
      })
    });
    const data = await res.json();
    setUc1Response(data);
    setStatus("UC1 complete");
  }

  async function runUc2() {
    setStatus("Running UC2...");
    const res = await fetch(`${API_BASE}/uc2/log-intel`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ logs: uc2Logs })
    });
    const data = await res.json();
    setUc2Response(data);
    setStatus("UC2 complete");
  }

  async function loadAuditSummary() {
    setStatus("Loading audit summary...");
    setAuditError("");
    const res = await fetch(`${API_BASE}/audit/summary`);
    if (!res.ok) {
      setAuditError("Failed to load audit summary");
      setStatus("Audit summary error");
      return;
    }
    const data = await res.json();
    setAuditSummary(data);
    setStatus("Audit summary loaded");
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <div className="badge">Enterprise LLM Adoption Kit</div>
          <h1>Discovery -> Secure Architecture -> Evals -> Deployment/LLMOps</h1>
          <p>
            Flagship pre-sales demo for Applied AI (Korea). Minimal UI, maximum enterprise controls.
          </p>
        </div>
        <div className="status">{status || "Ready"}</div>
      </header>

      <section className="panel">
        <h2>Login</h2>
        <div className="grid">
          <label>
            User ID
            <input value={userId} onChange={(e) => setUserId(e.target.value)} />
          </label>
          <label>
            Role
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              {roles.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          <button onClick={login}>Issue JWT</button>
        </div>
        <div className="token">
          <span>Token:</span>
          <code>{token ? token.slice(0, 56) + "..." : "Not issued"}</code>
        </div>
      </section>

      <section className="panel">
        <div className="tabs">
          <button
            className={activeTab === "uc1" ? "active" : ""}
            onClick={() => setActiveTab("uc1")}
          >
            UC1 - Handover Copilot
          </button>
          <button
            className={activeTab === "uc2" ? "active" : ""}
            onClick={() => setActiveTab("uc2")}
          >
            UC2 - Log Intelligence
          </button>
          <button
            className={activeTab === "discovery" ? "active" : ""}
            onClick={() => setActiveTab("discovery")}
          >
            Discovery & Audit
          </button>
        </div>

        {activeTab === "uc1" ? (
          <div className="tab-content">
            <label>
              Query
              <textarea value={uc1Query} onChange={(e) => setUc1Query(e.target.value)} />
            </label>
            <div className="row">
              <label>
                System
                <input value={uc1System} onChange={(e) => setUc1System(e.target.value)} />
              </label>
              <label>
                Env
                <input value={uc1Env} onChange={(e) => setUc1Env(e.target.value)} />
              </label>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={uc1CitationOnly}
                  onChange={(e) => setUc1CitationOnly(e.target.checked)}
                />
                Citation-only mode
              </label>
            </div>
            <button onClick={runUc1} disabled={!token}>Run UC1</button>
            {uc1Response && (
              <div className="response">
                <h3>Response</h3>
                <p>{uc1Response.answer}</p>
                <h4>Citations</h4>
                <ul>
                  {uc1Response.citations?.map((c, idx) => (
                    <li key={`${c.doc_id}-${idx}`}>
                      {c.doc_id} - {c.field_path}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : activeTab === "uc2" ? (
          <div className="tab-content">
            <label>
              Logs
              <textarea value={uc2Logs} onChange={(e) => setUc2Logs(e.target.value)} />
            </label>
            <button onClick={runUc2} disabled={!token}>Run UC2</button>
            {uc2Response && (
              <div className="response">
                <h3>Summary</h3>
                <p>{uc2Response.summary}</p>
                <h4>Root Causes</h4>
                <ul>
                  {uc2Response.root_causes?.map((c, idx) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
                <h4>Runbook Steps</h4>
                <ul>
                  {uc2Response.runbook_steps?.map((c, idx) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
                <h4>Tool Calls</h4>
                <ul>
                  {uc2Response.tool_calls?.map((c, idx) => (
                    <li key={idx}>{c.name} - {c.status}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="tab-content">
            <div className="response">
              <h3>Discovery Wizard (CLI)</h3>
              <p>Generate a use-case brief, risk notes, and eval plan.</p>
              <code>
                python3 app/backend/scripts/discovery_wizard.py --company "ACME Korea"
              </code>
              <p>Output: docs/samples/discovery_output/&lt;timestamp&gt;_brief.md</p>
            </div>
            <div className="response">
              <h3>Audit Viewer</h3>
              <p>Summarizes requests, policy events, tools, and cost.</p>
              <button onClick={loadAuditSummary}>Load Audit Summary</button>
              {auditError && <p>{auditError}</p>}
              {auditSummary && (
                <div>
                  <p>Requests: {auditSummary.requests}</p>
                  <p>Total cost (USD): {auditSummary.total_cost}</p>
                  <h4>Top Users</h4>
                  <ul>
                    {auditSummary.top_users?.map((u, idx) => (
                      <li key={idx}>{u[0]} - {u[1]}</li>
                    ))}
                  </ul>
                  <h4>Tools Used</h4>
                  <ul>
                    {auditSummary.tools_used?.map((t, idx) => (
                      <li key={idx}>{t[0]} - {t[1]}</li>
                    ))}
                  </ul>
                  <h4>Policy Events</h4>
                  <ul>
                    {auditSummary.policy_events?.map((p, idx) => (
                      <li key={idx}>{p[0]} - {p[1]}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      <footer className="footer">
        <div>Observability: /metrics | Audit logs: data/audit.log</div>
      </footer>
    </div>
  );
}
