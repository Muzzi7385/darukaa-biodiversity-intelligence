export default function EvidenceCard({ source }) {
  const name = source.name || source.source || source.title || 'Source'
  const page = source.page || source.page_number
  const snippet = source.snippet || source.excerpt || source.text || source.summary
  const url = source.url || source.link

  return (
    <article className="evidence-card">
      <div className="evidence-card__ref">
        <span className="evidence-card__name">{name}</span>
        {page && <span className="evidence-card__page">Page {page}</span>}
      </div>
      {snippet && <p className="evidence-card__snippet">{snippet}</p>}
      {url && (
        <a className="evidence-card__link" href={url} target="_blank" rel="noreferrer">
          View source
        </a>
      )}
    </article>
  )
}
