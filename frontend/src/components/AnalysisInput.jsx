import ExamplePrompt from './ExamplePrompt.jsx'

const EXAMPLES = [
  'Analyze a semi-arid wheat farm with low rainfall.',
  'Assess biodiversity risk from monoculture agriculture.',
  'Evaluate a landscape with low soil moisture and habitat diversity.'
]

export default function AnalysisInput({ value, onChange, onSubmit, loading, showExamples }) {
  function handleExample(text) {
    onChange(text)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      onSubmit()
    }
  }

  return (
    <section className="hero" id="analysis">
      <div className="hero__intro">
        <p className="hero__eyebrow">Built on science, designed for decisions</p>
        <h1 className="hero__heading">Understand your environment.</h1>
        <p className="hero__subtext">
          Describe the environmental conditions, land-use system, climate context, or
          biodiversity concerns you want to analyze.
        </p>
      </div>

      <div className="hero__input-panel">
        <textarea
          className="hero__textarea"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe an environmental situation, for example: a semi-arid wheat farming region with low rainfall, low soil moisture, monoculture, and declining species richness."
          rows={5}
        />
        <div className="hero__input-footer">
          <span className="hero__hint">⌘ / Ctrl + Enter to analyze</span>
          <button
            type="button"
            className="btn btn--primary"
            onClick={onSubmit}
            disabled={loading || value.trim().length === 0}
          >
            {loading ? 'Analyzing…' : 'Analyze environment'}
          </button>
        </div>
      </div>

      {showExamples && (
        <div className="hero__examples">
          <span className="hero__examples-label">Try an example</span>
          <div className="hero__examples-list">
            {EXAMPLES.map((text) => (
              <ExamplePrompt key={text} text={text} onClick={handleExample} />
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
