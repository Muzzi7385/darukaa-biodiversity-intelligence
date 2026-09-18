import { useEffect, useState } from 'react'

const STEPS = [
  'Extracting environmental state',
  'Connecting environmental variables',
  'Retrieving scientific evidence',
  'Generating recommendation'
]

export default function LoadingState() {
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((i) => Math.min(i + 1, STEPS.length - 1))
    }, 1100)
    return () => clearInterval(interval)
  }, [])

  return (
    <section className="loading-state" aria-live="polite">
      <p className="loading-state__title">Analyzing environmental conditions…</p>
      <ol className="loading-state__steps">
        {STEPS.map((step, i) => (
          <li
            key={step}
            className={
              'loading-state__step' +
              (i < activeIndex ? ' loading-state__step--done' : '') +
              (i === activeIndex ? ' loading-state__step--active' : '')
            }
          >
            <span className="loading-state__indicator" aria-hidden="true" />
            {step}
          </li>
        ))}
      </ol>
    </section>
  )
}
