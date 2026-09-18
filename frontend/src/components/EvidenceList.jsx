import EvidenceCard from './EvidenceCard.jsx'

export default function EvidenceList({ sources }) {
  const list = Array.isArray(sources) ? sources : []

  return (
    <section className="panel" aria-labelledby="evidence-heading" id="evidence">
      <h2 id="evidence-heading" className="panel__heading">
        Scientific evidence
      </h2>
      {list.length === 0 ? (
        <p className="panel__empty">No supporting sources were returned for this assessment.</p>
      ) : (
        <div className="evidence-list">
          {list.map((source, i) => (
            <EvidenceCard source={typeof source === 'string' ? { name: source } : source} key={i} />
          ))}
        </div>
      )}
    </section>
  )
}
