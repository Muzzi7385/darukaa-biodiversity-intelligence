import { useState } from 'react'
import Header from './components/Header.jsx'
import AnalysisInput from './components/AnalysisInput.jsx'
import LoadingState from './components/LoadingState.jsx'
import ErrorState from './components/ErrorState.jsx'
import EnvironmentalState from './components/EnvironmentalState.jsx'
import RelationshipGraph from './components/RelationshipGraph.jsx'
import RecommendationCard from './components/RecommendationCard.jsx'
import ImpactMetrics from './components/ImpactMetrics.jsx'
import Assessment from './components/Assessment.jsx'
import EvidenceList from './components/EvidenceList.jsx'
import './App.css'

const API_URL = 'http://127.0.0.1:8000/chat'

export default function App() {
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState('empty')
  const [response, setResponse] = useState(null)

  // Keep ONE conversation ID so multi-turn memory actually works
  const [conversationId] = useState(
    () => `frontend-${Date.now()}`
  )

  async function handleAnalyze() {
    const trimmed = message.trim()

    if (!trimmed) return

    setStatus('loading')

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: trimmed
        })
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(
          data?.detail ||
          data?.message ||
          `Request failed with status ${res.status}`
        )
      }

      setResponse(data)
      setStatus('result')

    } catch (err) {
      console.error('Chat request failed:', err)

      setResponse({
        error: err.message
      })

      setStatus('error')
    }
  }

  const selectedIntervention =
    response?.reasoning?.selected_intervention || null

  const evidenceCards =
    response?.evidence_cards || []

  return (
    <div className="app-shell">
      <Header />

      <main className="app-main">

        <AnalysisInput
          value={message}
          onChange={setMessage}
          onSubmit={handleAnalyze}
          loading={status === 'loading'}
          showExamples={status === 'empty'}
        />

        {status === 'empty' && (
          <p className="tagline">
            Science-backed environmental analysis for better decisions.
          </p>
        )}

        {status === 'loading' && (
          <LoadingState />
        )}

        {status === 'error' && (
          <ErrorState
            error={response?.error}
            onRetry={handleAnalyze}
          />
        )}

        {status === 'result' && response && (
          <div className="results">

            <EnvironmentalState
              environment={response.environment}
            />

            <RelationshipGraph
              reasoning={response.reasoning}
            />

            <RecommendationCard
              intervention={selectedIntervention}
            />

            <ImpactMetrics
              intervention={selectedIntervention}
              response={response}
            />

            <Assessment
              message={response.message}
              assessmentScope={response.assessment_scope}
            />

            <EvidenceList
              sources={evidenceCards}
            />

          </div>
        )}

      </main>
    </div>
  )
}