import { formatValue } from '../utils.js'

function extractReasons(intervention) {
  const candidates =
    intervention.reasons ||
    intervention.explanations ||
    intervention.rationale ||
    intervention.key_points ||
    intervention.why

  if (!candidates) return []
  if (Array.isArray(candidates)) {
    return candidates
      .map((c) => (typeof c === 'string' ? c : c?.text || c?.statement))
      .filter(Boolean)
  }
  if (typeof candidates === 'string') return [candidates]
  return []
}

function formatScore(value) {
  if (value === null || value === undefined) return null
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toFixed(2)
}

export default function RecommendationCard({ intervention }) {
  if (!intervention) {
    return (
      <section className="panel" aria-labelledby="recommendation-heading">
        <h2 id="recommendation-heading" className="panel__heading">
          Recommended intervention
        </h2>
        <p className="panel__empty">
          No intervention could be selected from the available evidence.
        </p>
      </section>
    )
  }

  const reasons = extractReasons(intervention)
  const coverage = formatScore(intervention.problem_coverage)
  const evidenceQuality = formatScore(intervention.evidence_quality)

  return (
    <section className="panel" aria-labelledby="recommendation-heading">
      <h2 id="recommendation-heading" className="panel__heading">
        Recommended intervention
      </h2>

      <div className="recommendation-card">
        <div className="recommendation-card__top">
          <div>
            <p className="recommendation-card__name">{intervention.name || 'Not provided'}</p>
            {intervention.time_horizon && (
              <p className="recommendation-card__horizon">
                {formatValue(intervention.time_horizon)}
              </p>
            )}
          </div>
          {intervention.status && (
            <span className="recommendation-card__status">{intervention.status}</span>
          )}
        </div>

        {intervention.description && (
          <p className="recommendation-card__description">{intervention.description}</p>
        )}

        <div className="recommendation-card__meta">
          {coverage !== null && (
            <div className="recommendation-card__meta-item">
              <span className="recommendation-card__meta-label">Problem coverage</span>
              <span className="recommendation-card__meta-value">{coverage}</span>
            </div>
          )}
          {evidenceQuality !== null && (
            <div className="recommendation-card__meta-item">
              <span className="recommendation-card__meta-label">Evidence quality</span>
              <span className="recommendation-card__meta-value">{evidenceQuality}</span>
            </div>
          )}
          {intervention.status && (
            <div className="recommendation-card__meta-item">
              <span className="recommendation-card__meta-label">Status</span>
              <span className="recommendation-card__meta-value">{intervention.status}</span>
            </div>
          )}
        </div>

        {reasons.length > 0 && (
          <div className="recommendation-card__why">
            <span className="recommendation-card__why-label">Why this intervention</span>
            <ul className="recommendation-card__why-list">
              {reasons.slice(0, 3).map((reason, i) => (
                <li key={i}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  )
}
