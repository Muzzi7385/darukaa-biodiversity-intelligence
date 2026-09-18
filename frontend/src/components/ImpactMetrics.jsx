function extractImpacts(intervention, response) {
  const source = intervention?.affected_metrics || response?.affected_metrics
  if (!source) return []

  if (Array.isArray(source)) {
    return source
      .map((item) => {
        if (typeof item === 'string') return { metric: item, impact: null }
        if (item && typeof item === 'object') {
          return {
            metric: item.metric || item.name || item.label,
            impact: item.impact || item.effect || item.value || null
          }
        }
        return null
      })
      .filter((item) => item && item.metric)
  }

  if (typeof source === 'object') {
    return Object.entries(source).map(([metric, impact]) => ({ metric, impact }))
  }

  return []
}

export default function ImpactMetrics({ intervention, response }) {
  const impacts = extractImpacts(intervention, response)

  if (impacts.length === 0) return null

  return (
    <section className="panel" aria-labelledby="impact-heading">
      <h2 id="impact-heading" className="panel__heading">
        Affected metrics
      </h2>
      <div className="impact-list">
        {impacts.map(({ metric, impact }, i) => (
          <div className="impact-row" key={i}>
            <span className="impact-row__metric">{metric.replace(/_/g, ' ')}</span>
            {impact && <span className="impact-row__value">{impact}</span>}
          </div>
        ))}
      </div>
    </section>
  )
}
