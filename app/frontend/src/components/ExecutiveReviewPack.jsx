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

export default function ExecutiveReviewPack({ reviewPack, variant = "full" }) {
  const [copyStatus, setCopyStatus] = React.useState("");

  if (!reviewPack) {
    return null;
  }

  const compact = variant === "compact";
  const buyerPromises = Array.isArray(reviewPack.buyer_promises) ? reviewPack.buyer_promises : [];
  const rolloutTracks = Array.isArray(reviewPack.rollout_tracks) ? reviewPack.rollout_tracks : [];
  const platformDialogues = Array.isArray(reviewPack.platform_dialogues) ? reviewPack.platform_dialogues : [];
  const reviewSequence = Array.isArray(reviewPack.review_sequence) ? reviewPack.review_sequence : [];
  const stageMap = Array.isArray(reviewPack.stage_map) ? reviewPack.stage_map : [];
  const watchouts = Array.isArray(reviewPack.watchouts) ? reviewPack.watchouts : [];
  const reviewActions = Array.isArray(reviewPack.review_actions) ? reviewPack.review_actions : [];
  const twoMinuteReview = Array.isArray(reviewPack.two_minute_review) ? reviewPack.two_minute_review : [];
  const rolePaths = Array.isArray(reviewPack.role_paths) ? reviewPack.role_paths : [];
  const reviewGate = reviewPack.review_gate || {};
  const proofBundle = reviewPack.proof_bundle || {};
  const reviewAssets = Array.isArray(proofBundle.review_assets) ? proofBundle.review_assets : [];
  const runtimeSurfaces = Array.isArray(proofBundle.runtime_surfaces) ? proofBundle.runtime_surfaces : [];
  const runtimeSummary = reviewPack.runtime_summary || {};
  const fastReviewSurfaces = Object.entries(reviewPack.links || {}).filter(([, surface]) => typeof surface === "string" && surface).slice(0, compact ? 4 : 6);
  const describePlatformDialogue = (item) => {
    if (typeof item === "string") {
      return item;
    }
    const surface = item?.surface || item?.platform || "platform";
    const fitFor = Array.isArray(item?.fit_for) && item.fit_for.length > 0 ? item.fit_for.join(", ") : "review fit";
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
    review_pack: "Open the executive overview for buyer promises and rollout tracks.",
    review_pack_schema: "Lock the explicit contract for review actions and proof assets.",
    metrics: "Show runtime cost and latency visibility without leaving the reviewer path.",
    audit_summary: "Surface audit and governance signals before making enterprise-readiness claims.",
    customer_journey: "Tie the technical proof back to adoption sequence.",
    deployment_options: "Map API-first, workspace-first, and hybrid rollout options.",
    exec_summary_template: "Keep the narrative anchored in buyer language.",
    qbr_template: "Show how proof rolls forward into executive cadence.",
    proof_map: "Open the role-based proof map when the reviewer needs the shortest evidence path.",
  };
  const fastReviewRouteText = [
    "Enterprise review routes",
    ...fastReviewSurfaces.map(([label, surface]) => `- ${label}: ${surface}`),
  ].join("\n");
  const twoMinuteReviewText = [
    "Enterprise review flow",
    ...twoMinuteReview.map((item) => `- ${item.step}: ${item.surface} (${item.proof})`),
  ].join("\n");
  const supportingEvidenceText = [
    "Enterprise executive overview",
    `Tests: ${proofBundle.tests || 0}`,
    `Blueprints: ${proofBundle.blueprints || 0}`,
    `Eval Assets: ${proofBundle.eval_assets || 0}`,
    `Review Assets: ${proofBundle.review_assets_count || reviewAssets.length || 0}`,
    ...(reviewAssets.length
      ? ["", "Supporting assets", ...reviewAssets.map((item) => `- ${item}`)]
      : []),
    ...(runtimeSurfaces.length
      ? ["", "Runtime surfaces", ...runtimeSurfaces.map((item) => `- ${item}`)]
      : []),
  ].join("\n");
  const rolloutSnapshotText = [
    "Enterprise rollout snapshot",
    `Headline: ${reviewPack.headline}`,
    `Runtime: ${runtimeSummary.llm_provider || "-"} / ${runtimeSummary.startup_status || "-"}`,
    "",
    "Buyer promises",
    ...buyerPromises.slice(0, 4).map((item) => `- ${item}`),
    "",
    "Rollout tracks",
    ...rolloutTracks.slice(0, 4).map((track) => `- ${track.track}: ${track.milestone}`),
    "",
    "Platform dialogues",
    ...platformDialogues.slice(0, 3).map((item) => `- ${describePlatformDialogue(item)}`),
  ].join("\n");
  const buyerThesisText = [
    "Enterprise buyer thesis snapshot",
    `Headline: ${reviewPack.headline}`,
    `Runtime: ${runtimeSummary.llm_provider || "-"} / ${runtimeSummary.startup_status || "-"}`,
    `Review assets: ${proofBundle.review_assets_count || reviewAssets.length || 0}`,
    `Endpoints: ${Array.isArray(proofBundle.review_endpoints) ? proofBundle.review_endpoints.length : 0}`,
    "",
    "Buyer promises",
    ...buyerPromises.slice(0, 3).map((item) => `- ${item}`),
    "",
    "Fast review surfaces",
    ...fastReviewSurfaces.slice(0, 4).map(([label, surface]) => `- ${label}: ${surface}`),
  ].join("\n");
  const rolloutDecisionBriefText = [
    "Enterprise rollout decision brief",
    `Headline: ${reviewPack.headline}`,
    `Runtime: ${runtimeSummary.llm_provider || "-"} / ${runtimeSummary.startup_status || "-"}`,
    `Circuit: ${runtimeSummary.llm_circuit_state || "-"}`,
    `Review assets: ${proofBundle.review_assets_count || reviewAssets.length || 0}`,
    `Endpoints: ${Array.isArray(proofBundle.review_endpoints) ? proofBundle.review_endpoints.length : 0}`,
    "",
    "Recommended rollout tracks",
    ...(rolloutTracks.length > 0
      ? rolloutTracks.slice(0, 2).map(
          (track, index) =>
            `${index + 1}. ${track.track}: ${track.milestone} (${Array.isArray(track.fit_for) ? track.fit_for.join(", ") : "fit review"})`
        )
      : ["1. Review pack unavailable. Start with /ops/service-brief and /ops/rollout-board."]),
    "",
    "Platform dialogue",
    ...(platformDialogues.length > 0
      ? platformDialogues.slice(0, 3).map(
          (item) =>
            `- ${item.surface}: ${Array.isArray(item.fit_for) ? item.fit_for.join(", ") : "review fit"}`
        )
      : ["- Platform dialogue unavailable."]),
    "",
    "Watchouts",
    ...(watchouts.length > 0 ? watchouts.slice(0, 3).map((item) => `- ${item}`) : ["- No active watchouts."]),
    "",
    "Fast review surfaces",
    ...fastReviewSurfaces.slice(0, 4).map(([label, surface]) => `- ${label}: ${surface}`),
  ].join("\n");

  const handleCopyRoutes = async () => {
    const ok = await copyTextToClipboard(fastReviewRouteText);
    setCopyStatus(ok ? "Copied executive review routes." : "Failed to copy executive review routes.");
  };

  const handleCopyTwoMinuteReview = async () => {
    const ok = await copyTextToClipboard(twoMinuteReviewText);
    setCopyStatus(ok ? "Copied executive review flow." : "Failed to copy executive review flow.");
  };

  const handleCopySupportingEvidence = async () => {
    const ok = await copyTextToClipboard(supportingEvidenceText);
    setCopyStatus(ok ? "Copied supporting evidence." : "Failed to copy supporting evidence.");
  };

  const handleCopyRolloutSnapshot = async () => {
    const ok = await copyTextToClipboard(rolloutSnapshotText);
    setCopyStatus(ok ? "Copied rollout snapshot." : "Failed to copy rollout snapshot.");
  };

  const handleCopyBuyerThesis = async () => {
    const ok = await copyTextToClipboard(buyerThesisText);
    setCopyStatus(ok ? "Copied buyer thesis snapshot." : "Failed to copy buyer thesis snapshot.");
  };

  const handleCopyRolloutDecisionBrief = async () => {
    const ok = await copyTextToClipboard(rolloutDecisionBriefText);
    setCopyStatus(ok ? "Copied rollout decision brief." : "Failed to copy rollout decision brief.");
  };

  return (
    <section className={`executive-review-pack${compact ? " compact" : ""}`}>
      <div className="service-brief-head">
        <div className="service-brief-copy">
          <p className="eyebrow">Executive Review Pack</p>
          <h3>Buyer thesis, governance proof, and deployment narrative</h3>
          <p>{reviewPack.headline}</p>
        </div>
        <div className="service-chip-row">
          <span className="chip">{reviewPack.contract_version}</span>
          <span className="chip">runtime {runtimeSummary.llm_provider || "-"}</span>
          <span className="chip">startup {runtimeSummary.startup_status || "-"}</span>
          <span className="chip">circuit {runtimeSummary.llm_circuit_state || "-"}</span>
        </div>
      </div>

      <div className="review-pack-metrics">
        <article className="service-metric-card">
          <span>Tests</span>
          <strong>{proofBundle.tests || 0}</strong>
        </article>
        <article className="service-metric-card">
          <span>Blueprints</span>
          <strong>{proofBundle.blueprints || 0}</strong>
        </article>
        <article className="service-metric-card">
          <span>Eval Assets</span>
          <strong>{proofBundle.eval_assets || 0}</strong>
        </article>
        <article className="service-metric-card">
          <span>Endpoints</span>
          <strong>{Array.isArray(proofBundle.review_endpoints) ? proofBundle.review_endpoints.length : 0}</strong>
        </article>
        <article className="service-metric-card">
          <span>Review Assets</span>
          <strong>{proofBundle.review_assets_count || reviewAssets.length || 0}</strong>
        </article>
      </div>

      <div className="review-pack-grid">
        <article className="service-brief-card">
          <p className="service-card-label">Review gate</p>
          <strong>{reviewGate.status || "unknown"}</strong>
          <p>{reviewGate.blocker || "No explicit blocker recorded."}</p>
          <p className="meta-text">{reviewGate.next_step || "Open the review pack before moving into runtime-specific claims."}</p>
        </article>
        <article className="service-brief-card">
          <p className="service-card-label">Fallback posture</p>
          <strong>{runtimeSummary.startup_status || "-"}</strong>
          <p>{reviewGate.fallback_posture || "Keep the walkthrough grounded in checked-in proof assets if runtime evidence is degraded."}</p>
        </article>
      </div>

      <div className="review-pack-toolbar">
        <button type="button" onClick={() => void handleCopyRoutes()}>
          Copy Review Routes
        </button>
        <button type="button" onClick={() => void handleCopyTwoMinuteReview()}>
          Copy Review Flow
        </button>
        <button type="button" onClick={() => void handleCopySupportingEvidence()}>
          Copy Supporting Evidence
        </button>
        <button type="button" onClick={() => void handleCopyRolloutSnapshot()}>
          Copy Rollout Snapshot
        </button>
        <button type="button" onClick={() => void handleCopyBuyerThesis()}>
          Copy Buyer Thesis
        </button>
        <button type="button" onClick={() => void handleCopyRolloutDecisionBrief()}>
          Copy Rollout Decision Brief
        </button>
        {copyStatus ? <span className="review-pack-toolbar-status">{copyStatus}</span> : null}
      </div>

      <article className="service-brief-card">
        <p className="service-card-label">Fast review surfaces</p>
        <p className="service-support-note">Keep governance and deployment evidence visible in the same reviewer path.</p>
        <div className="review-pack-action-list">
          {fastReviewSurfaces.map(([label, surface]) => (
            <div key={`${label}-${surface}`} className="review-pack-action-card">
              <strong>{label.replaceAll("_", " ")}</strong>
              <code className="service-path">{surface}</code>
              <p>{surfaceHints[label] || "Reviewer-visible route or doc for the executive walkthrough."}</p>
            </div>
          ))}
        </div>
      </article>

      <div className="review-pack-grid">
        <article className="service-brief-card">
          <p className="service-card-label">Buyer promises</p>
          <ul className="service-brief-list">
            {buyerPromises.slice(0, compact ? 2 : 3).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="service-brief-card">
          <p className="service-card-label">Review sequence</p>
          <ul className="service-brief-list">
            {reviewSequence.slice(0, compact ? 3 : 4).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>
      </div>

      <article className="service-brief-card">
        <p className="service-card-label">2-minute proof path</p>
        <div className="review-pack-action-list">
          {twoMinuteReview.slice(0, compact ? 2 : 4).map((item) => (
            <div key={`${item.step}-${item.surface}`} className="review-pack-action-card">
              <strong>{item.step}</strong>
              <code className="service-path">{item.surface}</code>
              <p>{item.proof}</p>
            </div>
          ))}
        </div>
      </article>

      {rolePaths.length > 0 && (
        <article className="service-brief-card">
          <p className="service-card-label">Reviewer lanes</p>
          <div className="review-pack-action-list">
            {rolePaths.map((path) => (
              <div key={path.role} className="review-pack-action-card">
                <strong>{path.role}</strong>
                <p>{path.goal}</p>
                <code className="service-path">Entry: {path.first_surface}</code>
                <code className="service-path">Follow-up: {path.follow_up}</code>
              </div>
            ))}
          </div>
        </article>
      )}

      <div className="review-pack-columns">
        <article className="service-brief-card">
          <p className="service-card-label">Rollout tracks</p>
          <div className="review-pack-track-list">
            {rolloutTracks.slice(0, compact ? 2 : 3).map((track) => (
              <div key={track.track} className="review-pack-track-card">
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

      <div className="review-pack-columns">
        <article className="service-brief-card">
          <p className="service-card-label">Review actions</p>
          <div className="review-pack-action-list">
            {reviewActions.slice(0, compact ? 2 : 4).map((item) => (
              <div key={`${item.label}-${item.surface}`} className="review-pack-action-card">
                <strong>{item.label}</strong>
                <code className="service-path">{item.surface}</code>
                <p>{item.proof}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="service-brief-card">
          <p className="service-card-label">Proof assets</p>
          <div className="review-pack-asset-list">
            {reviewAssets.slice(0, compact ? 3 : 5).map((item) => (
              <div key={`${item.label}-${item.path}`} className="review-pack-asset-card">
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
