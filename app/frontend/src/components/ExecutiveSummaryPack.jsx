import React from "react";

async function copyTextToClipboard(text) {
  const payload = typeof text === "string" ? text.trim() : "";
  if (!payload) return false;

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(payload);
      return true;
    }
  } catch {
    // Fallback below.
  }

  try {
    const helper = document.createElement("textarea");
    helper.value = payload;
    helper.setAttribute("readonly", "true");
    helper.style.position = "absolute";
    helper.style.left = "-9999px";
    document.body.appendChild(helper);
    helper.select();
    const ok = document.execCommand("copy");
    helper.remove();
    return Boolean(ok);
  } catch {
    return false;
  }
}

export default function ExecutiveSummaryPack({ summaryPack, variant = "full" }) {
  const [copyStatus, setCopyStatus] = React.useState("");

  if (!summaryPack) {
    return null;
  }

  const compact = variant === "compact";
  const stakeholderPromises = Array.isArray(summaryPack.stakeholder_promises) ? summaryPack.stakeholder_promises : [];
  const rolloutTracks = Array.isArray(summaryPack.rollout_tracks) ? summaryPack.rollout_tracks : [];
  const platformDialogues = Array.isArray(summaryPack.platform_dialogues) ? summaryPack.platform_dialogues : [];
  const architectureSequence = Array.isArray(summaryPack.architecture_sequence) ? summaryPack.architecture_sequence : [];
  const stageMap = Array.isArray(summaryPack.stage_map) ? summaryPack.stage_map : [];
  const watchouts = Array.isArray(summaryPack.watchouts) ? summaryPack.watchouts : [];
  const architectureActions = Array.isArray(summaryPack.architecture_actions) ? summaryPack.architecture_actions : [];
  const twoMinuteArchitecture = Array.isArray(summaryPack.two_minute_architecture) ? summaryPack.two_minute_architecture : [];
  const rolePaths = Array.isArray(summaryPack.role_paths) ? summaryPack.role_paths : [];
  const architectureGate = summaryPack.architecture_gate || {};
  const evidenceBundle = summaryPack.evidence_bundle || {};
  const architectureAssets = Array.isArray(evidenceBundle.architecture_assets) ? evidenceBundle.architecture_assets : [];
  const runtimeSurfaces = Array.isArray(evidenceBundle.runtime_surfaces) ? evidenceBundle.runtime_surfaces : [];
  const runtimeSummary = summaryPack.runtime_summary || {};
  const fastArchitectureSurfaces = Object.entries(summaryPack.links || {}).filter(([, surface]) => typeof surface === "string" && surface).slice(0, compact ? 4 : 6);
  const describePlatformDialogue = (item) => {
    if (typeof item === "string") {
      return item;
    }
    const surface = item?.surface || item?.platform || "platform";
    const fitFor = Array.isArray(item?.fit_for) && item.fit_for.length > 0 ? item.fit_for.join(", ") : "architecture fit";
    return `${surface}: ${fitFor}`;
  };
  const platformDialogueKey = (item, index) => {
    if (typeof item === "string") {
      return item;
    }
    return item?.surface || item?.platform || `platform-${index}`;
  };
  const surfaceHints = {
    health: "Confirm startup posture and runtime state before discussing rollout.",
    service_brief: "Anchor the walkthrough in maturity stage, evidence counts, and operator posture.",
    summary_pack: "Open the executive overview for stakeholder promises and rollout tracks.",
    summary_pack_schema: "Lock the explicit contract for architecture actions and test assets.",
    metrics: "Show runtime cost and latency visibility without leaving the evaluation path.",
    audit_summary: "Surface audit and governance signals before making enterprise-readiness claims.",
    customer_journey: "Tie the technical proof back to adoption sequence.",
    deployment_options: "Map API-first, workspace-first, and hybrid rollout options.",
    exec_summary_template: "Keep the narrative anchored in stakeholder language.",
    qbr_template: "Show how proof rolls forward into executive cadence.",
    proof_map: "Open the role-based evidence map when the user needs the shortest evidence path.",
  };
  const fastArchitectureRouteText = [
    "Enterprise architecture routes",
    ...fastArchitectureSurfaces.map(([label, surface]) => `- ${label}: ${surface}`),
  ].join("\n");
  const twoMinuteArchitectureText = [
    "Enterprise architecture flow",
    ...twoMinuteArchitecture.map((item) => `- ${item.step}: ${item.surface} (${item.proof})`),
  ].join("\n");
  const supportingEvidenceText = [
    "Enterprise executive overview",
    `Tests: ${evidenceBundle.tests || 0}`,
    `Blueprints: ${evidenceBundle.blueprints || 0}`,
    `Eval Assets: ${evidenceBundle.eval_assets || 0}`,
    `Architecture assets: ${evidenceBundle.architecture_assets_count || architectureAssets.length || 0}`,
    ...(architectureAssets.length
      ? ["", "Supporting assets", ...architectureAssets.map((item) => `- ${item}`)]
      : []),
    ...(runtimeSurfaces.length
      ? ["", "Runtime surfaces", ...runtimeSurfaces.map((item) => `- ${item}`)]
      : []),
  ].join("\n");
  const rolloutSnapshotText = [
    "Enterprise rollout snapshot",
    `Headline: ${summaryPack.headline}`,
    `Runtime: ${runtimeSummary.llm_provider || "-"} / ${runtimeSummary.startup_status || "-"}`,
    "",
    "Stakeholder promises",
    ...stakeholderPromises.slice(0, 4).map((item) => `- ${item}`),
    "",
    "Rollout tracks",
    ...rolloutTracks.slice(0, 4).map((track) => `- ${track.track}: ${track.milestone}`),
    "",
    "Platform dialogues",
    ...platformDialogues.slice(0, 3).map((item) => `- ${describePlatformDialogue(item)}`),
  ].join("\n");
  const stakeholderThesisText = [
    "Enterprise stakeholder thesis snapshot",
    `Headline: ${summaryPack.headline}`,
    `Runtime: ${runtimeSummary.llm_provider || "-"} / ${runtimeSummary.startup_status || "-"}`,
    `Architecture assets: ${evidenceBundle.architecture_assets_count || architectureAssets.length || 0}`,
    `Endpoints: ${Array.isArray(evidenceBundle.architecture_endpoints) ? evidenceBundle.architecture_endpoints.length : 0}`,
    "",
    "Stakeholder promises",
    ...stakeholderPromises.slice(0, 3).map((item) => `- ${item}`),
    "",
    "Fast architecture surfaces",
    ...fastArchitectureSurfaces.slice(0, 4).map(([label, surface]) => `- ${label}: ${surface}`),
  ].join("\n");
  const rolloutDecisionBriefText = [
    "Enterprise rollout decision brief",
    `Headline: ${summaryPack.headline}`,
    `Runtime: ${runtimeSummary.llm_provider || "-"} / ${runtimeSummary.startup_status || "-"}`,
    `Circuit: ${runtimeSummary.llm_circuit_state || "-"}`,
    `Architecture assets: ${evidenceBundle.architecture_assets_count || architectureAssets.length || 0}`,
    `Endpoints: ${Array.isArray(evidenceBundle.architecture_endpoints) ? evidenceBundle.architecture_endpoints.length : 0}`,
    "",
    "Recommended rollout tracks",
    ...(rolloutTracks.length > 0
      ? rolloutTracks.slice(0, 2).map(
          (track, index) =>
            `${index + 1}. ${track.track}: ${track.milestone} (${Array.isArray(track.fit_for) ? track.fit_for.join(", ") : "fit readout"})`
        )
      : ["1. Summary pack unavailable. Start with /ops/service-brief and /ops/rollout-board."]),
    "",
    "Platform dialogue",
    ...(platformDialogues.length > 0
      ? platformDialogues.slice(0, 3).map(
          (item) =>
            `- ${item.surface}: ${Array.isArray(item.fit_for) ? item.fit_for.join(", ") : "architecture fit"}`
        )
      : ["- Platform dialogue unavailable."]),
    "",
    "Watchouts",
    ...(watchouts.length > 0 ? watchouts.slice(0, 3).map((item) => `- ${item}`) : ["- No active watchouts."]),
    "",
    "Fast architecture surfaces",
    ...fastArchitectureSurfaces.slice(0, 4).map(([label, surface]) => `- ${label}: ${surface}`),
  ].join("\n");

  const handleCopyRoutes = async () => {
    const ok = await copyTextToClipboard(fastArchitectureRouteText);
    setCopyStatus(ok ? "Copied executive architecture routes." : "Failed to copy executive architecture routes.");
  };

  const handleCopyTwoMinuteArchitecture = async () => {
    const ok = await copyTextToClipboard(twoMinuteArchitectureText);
    setCopyStatus(ok ? "Copied executive architecture flow." : "Failed to copy executive architecture flow.");
  };

  const handleCopySupportingEvidence = async () => {
    const ok = await copyTextToClipboard(supportingEvidenceText);
    setCopyStatus(ok ? "Copied supporting evidence." : "Failed to copy supporting evidence.");
  };

  const handleCopyRolloutSnapshot = async () => {
    const ok = await copyTextToClipboard(rolloutSnapshotText);
    setCopyStatus(ok ? "Copied rollout snapshot." : "Failed to copy rollout snapshot.");
  };

  const handleCopyStakeholderThesis = async () => {
    const ok = await copyTextToClipboard(stakeholderThesisText);
    setCopyStatus(ok ? "Copied stakeholder thesis snapshot." : "Failed to copy stakeholder thesis snapshot.");
  };

  const handleCopyRolloutDecisionBrief = async () => {
    const ok = await copyTextToClipboard(rolloutDecisionBriefText);
    setCopyStatus(ok ? "Copied rollout decision brief." : "Failed to copy rollout decision brief.");
  };

  return (
    <section className={`executive-summary-pack${compact ? " compact" : ""}`}>
      <div className="service-brief-head">
        <div className="service-brief-copy">
          <p className="eyebrow">Executive Summary Pack</p>
          <h3>Stakeholder thesis, governance proof, and deployment narrative</h3>
          <p>{summaryPack.headline}</p>
        </div>
        <div className="service-chip-row">
          <span className="chip">{summaryPack.contract_version}</span>
          <span className="chip">runtime {runtimeSummary.llm_provider || "-"}</span>
          <span className="chip">startup {runtimeSummary.startup_status || "-"}</span>
          <span className="chip">circuit {runtimeSummary.llm_circuit_state || "-"}</span>
        </div>
      </div>

      <div className="summary-pack-metrics">
        <article className="service-metric-card">
          <span>Tests</span>
          <strong>{evidenceBundle.tests || 0}</strong>
        </article>
        <article className="service-metric-card">
          <span>Blueprints</span>
          <strong>{evidenceBundle.blueprints || 0}</strong>
        </article>
        <article className="service-metric-card">
          <span>Eval Assets</span>
          <strong>{evidenceBundle.eval_assets || 0}</strong>
        </article>
        <article className="service-metric-card">
          <span>Endpoints</span>
          <strong>{Array.isArray(evidenceBundle.architecture_endpoints) ? evidenceBundle.architecture_endpoints.length : 0}</strong>
        </article>
        <article className="service-metric-card">
          <span>Architecture Assets</span>
          <strong>{evidenceBundle.architecture_assets_count || architectureAssets.length || 0}</strong>
        </article>
      </div>

      <div className="summary-pack-grid">
        <article className="service-brief-card">
          <p className="service-card-label">Quality gate</p>
          <strong>{architectureGate.status || "unknown"}</strong>
          <p>{architectureGate.blocker || "No explicit blocker recorded."}</p>
          <p className="meta-text">{architectureGate.next_step || "Open the summary pack before moving into runtime-specific claims."}</p>
        </article>
        <article className="service-brief-card">
          <p className="service-card-label">Fallback posture</p>
          <strong>{runtimeSummary.startup_status || "-"}</strong>
          <p>{architectureGate.fallback_posture || "Keep the walkthrough grounded in checked-in test assets if runtime evidence is degraded."}</p>
        </article>
      </div>

      <div className="summary-pack-toolbar">
        <button type="button" onClick={() => void handleCopyRoutes()}>
          Copy Architecture Routes
        </button>
        <button type="button" onClick={() => void handleCopyTwoMinuteArchitecture()}>
          Copy Architecture Flow
        </button>
        <button type="button" onClick={() => void handleCopySupportingEvidence()}>
          Copy Supporting Evidence
        </button>
        <button type="button" onClick={() => void handleCopyRolloutSnapshot()}>
          Copy Rollout Snapshot
        </button>
        <button type="button" onClick={() => void handleCopyStakeholderThesis()}>
          Copy Stakeholder Thesis
        </button>
        <button type="button" onClick={() => void handleCopyRolloutDecisionBrief()}>
          Copy Rollout Decision Brief
        </button>
        {copyStatus ? <span className="summary-pack-toolbar-status">{copyStatus}</span> : null}
      </div>

      <article className="service-brief-card">
        <p className="service-card-label">Fast architecture surfaces</p>
        <p className="service-support-note">Keep governance and deployment evidence visible in the same evaluation path.</p>
        <div className="summary-pack-action-list">
          {fastArchitectureSurfaces.map(([label, surface]) => (
            <div key={`${label}-${surface}`} className="summary-pack-action-card">
              <strong>{label.replaceAll("_", " ")}</strong>
              <code className="service-path">{surface}</code>
              <p>{surfaceHints[label] || "Visible route or doc for the executive walkthrough."}</p>
            </div>
          ))}
        </div>
      </article>

      <div className="summary-pack-grid">
        <article className="service-brief-card">
          <p className="service-card-label">Stakeholder promises</p>
          <ul className="service-brief-list">
            {stakeholderPromises.slice(0, compact ? 2 : 3).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="service-brief-card">
          <p className="service-card-label">Architecture sequence</p>
          <ul className="service-brief-list">
            {architectureSequence.slice(0, compact ? 3 : 4).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>

      <article className="service-brief-card">
        <p className="service-card-label">2-minute evidence path</p>
        <div className="summary-pack-action-list">
          {twoMinuteArchitecture.slice(0, compact ? 2 : 4).map((item) => (
            <div key={`${item.step}-${item.surface}`} className="summary-pack-action-card">
              <strong>{item.step}</strong>
              <code className="service-path">{item.surface}</code>
              <p>{item.proof}</p>
            </div>
          ))}
        </div>
      </article>

      {rolePaths.length > 0 && (
        <article className="service-brief-card">
          <p className="service-card-label">Architecture lanes</p>
          <div className="summary-pack-action-list">
            {rolePaths.map((path) => (
              <div key={path.role} className="summary-pack-action-card">
                <strong>{path.role}</strong>
                <p>{path.goal}</p>
                <code className="service-path">Entry: {path.first_surface}</code>
                <code className="service-path">Follow-up: {path.follow_up}</code>
              </div>
            ))}
          </div>
        </article>
      )}

      <div className="summary-pack-columns">
        <article className="service-brief-card">
          <p className="service-card-label">Rollout tracks</p>
          <div className="summary-pack-track-list">
            {rolloutTracks.slice(0, compact ? 2 : 3).map((track) => (
              <div key={track.track} className="summary-pack-track-card">
                <strong>{track.track}</strong>
                <p>{Array.isArray(track.fit_for) ? track.fit_for.join(" · ") : ""}</p>
                <code className="service-path">{track.evidence}</code>
              </div>
            ))}
          </div>
        </article>

        <article className="service-brief-card">
          <p className="service-card-label">Platform dialogues</p>
          <ul className="service-brief-list">
            {platformDialogues.slice(0, compact ? 3 : 5).map((item, index) => (
              <li key={platformDialogueKey(item, index)}>{describePlatformDialogue(item)}</li>
            ))}
          </ul>
          {!compact && stageMap.length > 0 && (
            <>
              <p className="service-card-label" style={{ marginTop: 16 }}>Stage map</p>
              <div className="service-chip-row">
                {stageMap.map((item) => (
                  <span key={item} className="tag">
                    {item}
                  </span>
                ))}
              </div>
            </>
          )}
        </article>
      </div>

      <div className="summary-pack-columns">
        <article className="service-brief-card">
          <p className="service-card-label">Architecture actions</p>
          <div className="summary-pack-action-list">
            {architectureActions.slice(0, compact ? 2 : 4).map((item) => (
              <div key={`${item.label}-${item.surface}`} className="summary-pack-action-card">
                <strong>{item.label}</strong>
                <code className="service-path">{item.surface}</code>
                <p>{item.proof}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="service-brief-card">
          <p className="service-card-label">Proof assets</p>
          <div className="summary-pack-asset-list">
            {architectureAssets.slice(0, compact ? 3 : 5).map((item) => (
              <div key={`${item.label}-${item.path}`} className="summary-pack-asset-card">
                <strong>{item.label}</strong>
                <p>{item.kind}</p>
                <code className="service-path">{item.path}</code>
              </div>
            ))}
          </div>
          {runtimeSurfaces.length > 0 && (
            <>
              <p className="service-card-label" style={{ marginTop: 16 }}>Runtime surfaces</p>
              <div className="service-chip-row">
                {runtimeSurfaces.map((item) => (
                  <span key={item} className="tag">
                    {item}
                  </span>
                ))}
              </div>
            </>
          )}
        </article>
      </div>

      {!compact && (
        <article className="service-brief-card">
          <p className="service-card-label">Open watchouts</p>
          <ul className="service-brief-list">
            {watchouts.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      )}
    </section>
  );
}
