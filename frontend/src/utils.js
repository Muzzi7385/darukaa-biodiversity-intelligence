// Small, dependency-free helpers shared across components.
// Nothing here invents data — they only format or classify values
// that already came back from the backend.

export function formatValue(value) {
  if (value === null || value === undefined || value === '') {
    return 'Not provided'
  }
  if (typeof value === 'number') {
    return String(value)
  }
  return String(value)
    .replace(/_/g, ' ')
    .replace(/^./, (c) => c.toUpperCase())
}

const ATTENTION_PATTERN = /low|declin|poor|limited|high pollution|deforest|degrad|scarc|stress/i

export function statusFor(value) {
  if (value === null || value === undefined || value === '') {
    return 'missing'
  }
  if (typeof value === 'string' && ATTENTION_PATTERN.test(value)) {
    return 'attention'
  }
  return 'normal'
}

// Turns the backend's free-text "message" into labelled sections.
// The backend writes markdown-style bold headers ("**Assessment**",
// "**What to do**", ...). We split on those headers and keep the
// rest of the copy exactly as written, just stripped of stray
// markdown characters.
const KNOWN_HEADERS = [
  'Assessment',
  'What to do',
  'Why it may help',
  'Affected metrics',
  'Expected time horizon',
  'Important caveats'
]

export function parseAssessmentMessage(message) {
  if (!message || typeof message !== 'string') return []

  const headerPattern = new RegExp(
    `\\*\\*(${KNOWN_HEADERS.join('|')})\\*\\*:?`,
    'gi'
  )

  const matches = [...message.matchAll(headerPattern)]

  if (matches.length === 0) {
    return [
      {
        heading: null,
        body: cleanMarkdown(message)
      }
    ]
  }

  const sections = []
  for (let i = 0; i < matches.length; i++) {
    const current = matches[i]
    const next = matches[i + 1]
    const start = current.index + current[0].length
    const end = next ? next.index : message.length
    const body = message.slice(start, end)
    sections.push({
      heading: current[1],
      body: cleanMarkdown(body)
    })
  }

  const before = message.slice(0, matches[0].index).trim()
  if (before) {
    sections.unshift({ heading: null, body: cleanMarkdown(before) })
  }

  return sections
}

function cleanMarkdown(text) {
  return text
    .replace(/\*\*/g, '')
    .replace(/^[\s\-•]+/gm, '')
    .trim()
}
