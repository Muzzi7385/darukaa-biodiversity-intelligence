import { parseAssessmentMessage } from '../utils.js'

export default function Assessment({ message, assessmentScope }) {
  const sections = parseAssessmentMessage(message)

  return (
    <section className="panel" aria-labelledby="assessment-heading">
      <div className="panel__head panel__head--stacked">
        <h2 id="assessment-heading" className="panel__heading">
          Assessment
        </h2>
        {assessmentScope && (
          <span className={`scope-tag scope-tag--${assessmentScope}`}>
            {assessmentScope} assessment
          </span>
        )}
      </div>

      {assessmentScope === 'preliminary' && (
        <p className="panel__note">
          Some ecological indicators are missing, so biodiversity effects are treated as
          potential rather than measured.
        </p>
      )}

      {sections.length === 0 && <p className="panel__empty">No assessment text was returned.</p>}

      <div className="assessment-body">
        {sections.map((section, i) => (
          <div className="assessment-section" key={i}>
            {section.heading && <h3 className="assessment-section__heading">{section.heading}</h3>}
            <p className="assessment-section__body">{section.body}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
