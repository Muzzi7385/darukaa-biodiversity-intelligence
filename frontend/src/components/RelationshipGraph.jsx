function toRelationship(item) {
  if (typeof item === 'string') {
    return {
      title: item,
      explanation: null,
      variables: []
    }
  }

  if (!item || typeof item !== 'object') {
    return null
  }

  return {
    title:
      item.relationship ||
      item.statement ||
      item.title ||
      item.text ||
      (
        item.from && item.to
          ? `${item.from} ${item.type === 'bidirectional' ? '↔' : '→'} ${item.to}`
          : null
      ) ||
      (
        item.a && item.b
          ? `${item.a} ↔ ${item.b}`
          : null
      ),

    explanation:
      item.explanation ||
      item.description ||
      null,

    variables: Array.isArray(item.variables)
      ? item.variables
      : []
  }
}

export default function RelationshipGraph({ reasoning }) {
  const findings = Array.isArray(reasoning?.findings)
    ? reasoning.findings
    : []

  const relationships = Array.isArray(reasoning?.relationships)
    ? reasoning.relationships
        .map(toRelationship)
        .filter(Boolean)
        .filter((item) => item.title)
    : []

  const hasContent =
    findings.length > 0 ||
    relationships.length > 0

  return (
    <section
      className="panel"
      aria-labelledby="relationships-heading"
    >
      <div className="panel__head panel__head--stacked">
        <h2
          id="relationships-heading"
          className="panel__heading"
        >
          Environmental relationships
        </h2>

        <p className="panel__description">
          The system connects multiple environmental variables
          before generating a recommendation.
        </p>
      </div>

      {!hasContent && (
        <p className="panel__empty">
          No variable relationships were returned for this input.
        </p>
      )}
      

      {findings.length > 0 && (
  <>
    <h3 className="reasoning-subheading">
      Environmental findings
    </h3>

    <div className="reasoning-findings">
      {findings.map((item, index) => (
        <div
          className="reasoning-finding"
          key={`finding-${index}`}
        >
          <span className="reasoning-finding__index">
            {String(index + 1).padStart(2, '0')}
          </span>

          <div>
            <strong>
              {item.title || item.text || item.explanation}
            </strong>

            {item.explanation && (
              <p>{item.explanation}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  </>
)}
<h3 className="reasoning-subheading">
  Variable relationships
</h3>

      {relationships.length > 0 && (
        <div className="relationship-list">
          {relationships.map((item, index) => (
            <div
              className="relationship-item"
              key={`relationship-${index}`}
            >
              <div className="relationship-item__title">
                {item.title}
              </div>

              {item.explanation && (
                <p className="relationship-item__description">
                  {item.explanation}
                </p>
              )}

              {item.variables.length > 0 && (
                <div className="relationship-item__variables">
                  {item.variables.map((variable) => (
                    <span
                      className="relationship-pill"
                      key={variable}
                    >
                      {variable.replaceAll('_', ' ')}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}