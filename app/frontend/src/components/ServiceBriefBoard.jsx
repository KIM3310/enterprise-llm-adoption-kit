import React from "react";

function badgeClass(readiness) {
  const value = String(readiness || "").toLowerCase().trim();
  if (value === "ready") {
    return "readiness-badge ready";
  }
  if (value === "in_progress") {
    return "readiness-badge in-progress";
  }
  return "readiness-badge attention";
}

function healthLabel(health) {
  const value = String(health?.status || "unknown").toLowerCase().trim();
  if (value === "ok") {
    return "Healthy";
  }
  if (value === "degraded") {
    return "Degraded";
  }
  if (value === "offline") {
    return "Offline";
  }
  return "Unknown";
}

export default function ServiceBriefBoard({ brief, schema, health, checkedAt = "", variant = "full" }) {
  if (!brief) {
    return null;
  }

  const runtime = brief.runtime || {};
  const evidence = brief.evidence || {};
  const stages = Array.isArray(brief.stages) ? brief.stages : [];
  const strengths = Array.isArray(brief.strengths) ? brief.strengths : [];
  const watchouts = Array.isArray(brief.watchouts) ? brief.watchouts : [];
  const architectureFlow = Array.isArray(brief.architecture_flow) ? brief.architecture_flow : [];
  const audiences = Array.isArray(brief.audiences) ? brief.audiences : [];
  const runModes = Array.isArray(brief.run_modes) ? brief.run_modes : [];
  const platformTargets = Array.isArray(brief.platform_targets) ? brief.platform_targets : [];
  const rolePaths = Array.isArray(brief.role_paths) ? brief.role_paths : [];
  const proofMap = typeof brief.links?.proof_map === "string" ? brief.links.proof_map : "";
  const requiredFields = Array.isArray(schema?.required_fields) ? schema.required_fields.length : 0;
  const compact = variant === "compact";

  const metrics = [
    ["Tests", evidence.test_files ?? 0],
    ["Blueprints", evidence.blueprint_docs ?? 0],
    ["Modules", evidence.module_packs ?? 0],
    ["Eval Datasets", evidence.eval_datasets ?? 0],
    ["Eval Reports", evidence.eval_reports ?? 0],
    ["App Artifacts", evidence.application_artifacts ?? 0],
  ];

  return (
    <div className={`service-brief-board${compact ? " compact" : ""}`}>
      <div className="service-brief-head">
        <div className="service-brief-copy">
          <p className="eyebrow">Service Brief</p>
          <h3>Executive Readiness Board</h3>
          <p>
            {brief.tagline}. Check governance posture, deployment fit, proof inventory, and rollout stages without
            leaving the product surface.
          </p>
        </div>
        <div className="service-brief-chip-stack">
          <span className="chip">Health: {healthLabel(health)}</span>
          <span className="chip">Maturity: {brief.maturity_stage}</span>
          <span className="chip">
            Runtime: {runtime.llm_provider || "-"} / {runtime.llm_model || "-"}
          </span>
          {checkedAt && <span className="chip">Checked: {checkedAt}</span>}
        </div>
      </div>

      <div className="service-brief-meta">
        <div className="service-brief-card">
          <p className="service-card-label">Service contract</p>
          <strong>{schema?.schema || brief.contract_version}</strong>
          <p>
            Required top-level fields: <strong>{requiredFields || 0}</strong>
          </p>
          <div className="service-chip-row">
            {audiences.map((audience) => (
              <span key={audience} className="tag">
                {audience}
              </span>
            ))}
          </div>
        </div>

        <div className="service-brief-card">
          <p className="service-card-label">Governance + runtime posture</p>
          <ul className="service-brief-list">
            <li>
              auth=<code className="mono-inline">{runtime.auth_mode || "-"}</code> · data=
              <code className="mono-inline">{runtime.data_handling_mode || "-"}</code>
            </li>
            <li>
              storage=<code className="mono-inline">{runtime.storage_backend || "-"}</code> · circuit=
              <code className="mono-inline">{runtime.llm_circuit_state || "-"}</code>
            </li>
            <li>
              login_code=<code className="mono-inline">{runtime.login_code_required ? "required" : "optional"}</code>
              {" "}· integrations_auth=
              <code className="mono-inline">{runtime.integrations_require_auth ? "required" : "optional"}</code>
            </li>
            <li>
              startup=<code className="mono-inline">{runtime.startup_status || "-"}</code> · api_key=
              <code className="mono-inline">{runtime.openai_api_key_configured ? "set" : "unset"}</code>
            </li>
          </ul>
          <p className="service-support-note">
            Deployment modes: {runModes.slice(0, compact ? 2 : 3).join(" · ") || "-"}
          </p>
        </div>
      </div>

      <div className="service-brief-metrics">
        {metrics.map(([label, value]) => (
          <article key={label} className="service-metric-card">
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </div>

      <div className="service-brief-stage-grid">
        {stages.map((stage) => (
          <article key={stage.key} className="service-stage-card">
            <div className="service-stage-head">
              <p>{stage.label}</p>
              <span className={badgeClass(stage.readiness)}>{String(stage.readiness || "attention").replace("_", " ")}</span>
            </div>
            <strong>{stage.artifact_count || 0} proof points</strong>
            <ul className="service-brief-list">
              {(stage.highlights || []).map((artifact) => (
                <li key={`${stage.key}-${artifact.path}`}>
                  <span>{artifact.label}</span>
                  <code className="service-path">{artifact.path}</code>
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>

      <div className="service-brief-columns">
        <div className="service-brief-card">
          <p className="service-card-label">Strengths</p>
          <ul className="service-brief-list">
            {strengths.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <div className="service-chip-row">
            {runModes.map((mode) => (
              <span key={mode} className="tag">
                {mode}
              </span>
            ))}
          </div>
        </div>

        <div className="service-brief-card">
          <p className="service-card-label">Platform targets</p>
          <p className="service-support-note">Platform language for rollout and architecture-readiness conversations.</p>
          <div className="service-chip-row" style={{ marginBottom: 14 }}>
            {platformTargets.map((target) => (
              <span key={target} className="tag">
                {target}
              </span>
            ))}
          </div>
          <p className="service-card-label">Open watchouts</p>
          <ul className="service-brief-list">
            {watchouts.length ? (
              watchouts.map((item) => <li key={item}>{item}</li>)
            ) : (
              <li>No open watchouts. The service brief is currently aligned with the expected runtime posture.</li>
            )}
          </ul>
        </div>
      </div>

      {rolePaths.length > 0 && (
        <article className="service-brief-card">
          <p className="service-card-label">Role-ready paths</p>
          {proofMap ? <code className="service-path">Evidence map: {proofMap}</code> : null}
          <div className="summary-pack-action-list" style={{ marginTop: 14 }}>
            {rolePaths.map((path) => (
              <div key={path.role} className="summary-pack-action-card">
                <strong>{path.role}</strong>
                <p>{path.goal}</p>
                <code className="service-path">Entry: {path.first_surface}</code>
                <code className="service-path">Follow-up: {path.follow_up}</code>
                <div className="service-chip-row">
                  {(Array.isArray(path.proof_assets) ? path.proof_assets : []).map((asset) => (
                    <span key={`${path.role}-${asset}`} className="tag">
                      {asset}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </article>
      )}

      {!compact && architectureFlow.length > 0 && (
        <div className="service-brief-flow">
          {architectureFlow.map((step) => (
            <article key={`${step.order}-${step.title}`} className="service-flow-card">
              <span className="service-flow-index">{String(step.order).padStart(2, "0")}</span>
              <div>
                <h4>{step.title}</h4>
                <p>
                  persona=<code className="mono-inline">{step.persona}</code>
                </p>
                <code className="service-path">{step.endpoint}</code>
                {step.evidence_path && <code className="service-path">{step.evidence_path}</code>}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
