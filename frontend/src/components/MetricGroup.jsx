import { formatValue, statusFor } from '../utils.js'

export default function MetricGroup({ title, metrics }) {
  return (
    <div className="metric-group">
      <h3 className="metric-group__title">{title}</h3>
      <dl className="metric-group__list">
        {metrics.map(({ label, value }) => {
          const status = statusFor(value)
          return (
            <div className="metric-row" key={label}>
              <dt className="metric-row__label">{label}</dt>
              <dd className="metric-row__value">
                <span className={`metric-row__dot metric-row__dot--${status}`} aria-hidden="true" />
                {formatValue(value)}
              </dd>
            </div>
          )
        })}
      </dl>
    </div>
  )
}
