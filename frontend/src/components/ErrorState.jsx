export default function ErrorState({ onRetry }) {
  return (
    <section className="error-state" role="alert">
      <p className="error-state__title">Unable to reach the environmental analysis service.</p>
      <p className="error-state__body">Check that the FastAPI backend is running on port 8000.</p>
      {onRetry && (
        <button type="button" className="btn btn--secondary" onClick={onRetry}>
          Try again
        </button>
      )}
    </section>
  )
}
