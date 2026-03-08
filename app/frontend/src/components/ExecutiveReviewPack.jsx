import React from "react";

export default function ExecutiveReviewPack({ reviewPack, variant = "full" }) {
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
  const proofBundle = reviewPack.proof_bundle || {};
  const runtimeSummary = reviewPack.runtime_summary || {};

  return (
    <section className={`executive-review-pack${compact ? " compact" : ""}`}>
      <div className="service-brief-head">
        <div className="service-brief-copy">
          <p className="eyebrow">Executive Review Pack</p>
          <h3>Buyer thesis, proof bundle, and rollout narrative</h3>
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
      </div>

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
            {platformDialogues.slice(0, compact ? 3 : 5).map((item) => (
              <li key={item}>{item}</li>
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
