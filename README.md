# Darukaa Biodiversity Intelligence

AI-powered environmental intelligence and biodiversity recommendation system. It takes soil, climate, land-use, biodiversity, and human-impact information — as natural language or structured input — and produces evidence-backed recommendations grounded in a retrieval-augmented knowledge base of scientific documents (IPCC, FAO), rather than in an LLM's unchecked internal knowledge.

**Repository:** https://github.com/Muzzi7385/darukaa-biodiversity-intelligence
**Live demo:** Not deployed; run locally using the instructions below.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Environmental Data Model](#environmental-data-model)
- [Knowledge Base / RAG](#knowledge-base--rag)
- [Database / Knowledge Schema](#database--knowledge-schema)
- [API Endpoints](#api-endpoints)
- [Local Setup](#local-setup)
- [Project Structure](#project-structure)
- [CI/CD](#cicd)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)

---

## Overview

The system maintains a structured `EnvironmentalState` (soil, land use, biodiversity, climate, human impact), reasons across multiple variables at once (e.g. rainfall ↔ soil moisture ↔ biodiversity), retrieves supporting scientific evidence for candidate interventions via RAG, and returns recommendations that include what to do, why it may help, affected metrics, time horizon, evidence quality, and caveats — each backed by a document and page-level citation.

A multi-turn `/chat` endpoint lets a user describe their land incrementally, with the system preserving previously extracted environmental information across turns via a `conversation_id`.

## Architecture


                    ┌──────────────────────┐
                    │       React UI       │
                    │     Vite Frontend    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │       Backend        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌──────────────┐  ┌───────────────┐
       │ Environment │  │ Multi-Metric │  │ Conversation  │
       │  Extractor  │  │   Reasoning  │  │    Service    │
       └──────┬──────┘  └──────┬───────┘  └───────────────┘
              │                │
              │                ▼
              │        ┌────────────────┐
              │        │ Recommendation │
              │        │    Engine      │
              │        └──────┬─────────┘
              │               │
              ▼               ▼
       ┌──────────────────────────────┐
       │           RAG Layer          │
       │                              │
       │ Query Builder → Retriever    │
       │ Embeddings → ChromaDB        │
       └──────────────┬───────────────┘
                      │
                      ▼
              ┌─────────────────┐
              │   Scientific    │
              │ Knowledge Base  │
              │                 │
              │ IPCC + FAO +    │
              │ Environmental   │
              │ Documents       │
              └─────────────────┘

**Components**

- **Frontend (React/Vite):** renders the environment input form, environmental state summary, cross-variable findings, and final recommendation.
- **Environment Extractor:** converts free-text or partial input into a structured `EnvironmentalState` using LLM-based extraction (Groq API), filling in only what the user actually provided.
- **Conversation Service:** tracks a `conversation_id` per session and preserves previously extracted environmental information across turns, updating state incrementally.
- **Reasoning Engine:** derives findings (e.g. low soil moisture, monoculture system) and connects multiple variables into relationship statements (e.g. rainfall ↔ soil moisture ↔ biodiversity).
- **RAG Layer:** embeds retrieval queries with a sentence-transformer model and retrieves relevant chunks from ChromaDB.
- **Recommendation Engine:** evaluates candidate interventions against retrieved evidence and reasoning-engine findings; outputs suitability, time horizon, problem coverage, evidence quality, affected metrics, and caveats.

## Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI, Pydantic, python-dotenv |
| AI / LLM | Groq API (LLM-based extraction and reasoning support) |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector store | ChromaDB (local) |
| Document processing | PyPDF |
| Frontend | React, Vite, JavaScript, CSS |
| Large file handling | Git LFS (for source PDF documents) |

## Environmental Data Model

`EnvironmentalState`:

```
region

soil:
  - ph
  - organic_carbon
  - moisture

land_use:
  - land_use_type
  - crop
  - system

biodiversity:
  - species_richness
  - habitat_diversity

climate:
  - temperature
  - rainfall

human_impact:
  - pollution
  - deforestation
```

### Multi-metric reasoning

The reasoning engine currently implements these cross-variable relationships:

- Rainfall ↔ Soil Moisture
- Temperature ↔ Soil Moisture
- Water Availability ↔ Land Use ↔ Biodiversity
- Soil Organic Carbon ↔ Soil Moisture
- Soil Health ↔ Water Availability ↔ Land Use
- Land-use Diversity ↔ Biodiversity
- Water Availability ↔ Biodiversity
- Land-use System ↔ Habitat Diversity
- Human Impact ↔ Biodiversity

## Knowledge Base / RAG

Source documents (in `data/documents/`, tracked via Git LFS):

- `IPCC_AR6_WGII_FullReport.pdf`
- `cb6378en.pdf`
- `i1861e.pdf`

**Pipeline:** documents → chunked → embedded with `all-MiniLM-L6-v2` → stored in a local ChromaDB instance. The generated ChromaDB database is **excluded from Git** (see `.gitignore`) because it can be deterministically rebuilt from the source PDFs — this is intentional, not a missing artifact.

At query time, candidate interventions are turned into retrieval queries, embedded with the same model, and matched against stored vectors. Retrieved chunks carry source filename and page number, which are surfaced as citations (e.g. `i1861e.pdf, p. 73`) in the final recommendation.

**Why RAG instead of prompting alone:** an LLM prompted directly for environmental advice can't show where a claim came from. Retrieving from indexed, page-numbered PDFs lets every recommendation carry a checkable citation, satisfying the requirement for a retrievable knowledge layer rather than knowledge existing only inside a prompt.

## Database / Knowledge Schema

Two data layers:

1. **Structured state** — `EnvironmentalState` is a Pydantic model passed between the frontend, extractor, reasoning engine, and recommendation engine. Not persisted in a relational database in this prototype; held in memory per request/conversation.
2. **Vector knowledge records** — each indexed document chunk is stored in ChromaDB as a vector record with its `all-MiniLM-L6-v2` embedding plus metadata (source filename, page number). Retrieval returns nearest chunks by embedding similarity.

## API Endpoints

| Method & Path | Purpose |
|---|---|
| `GET /health` | Service health check |
| `POST /environment/analyze` | Submit a structured or extracted environmental state for analysis |
| `POST /environment/reason` | Run the reasoning engine and recommendation engine over an environmental state |
| `POST /chat` | Multi-turn conversational endpoint; accepts `conversation_id` and natural-language input |

Interactive API docs are available at `/docs` once the backend is running.

## Local Setup

Clone the repository:

```bash
git clone https://github.com/Muzzi7385/darukaa-biodiversity-intelligence.git
cd darukaa-biodiversity-intelligence
```

Install Git LFS and pull large files (the PDF knowledge-base documents):

```bash
git lfs install
git lfs pull
```

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key
```

Build the RAG vector database from the source documents:

```bash
python -m backend.rag.ingest
```

Run the backend:

```bash
uvicorn backend.main:app --reload
```

- Backend: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs

Run the frontend (in a separate terminal):

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
darukaa-biodiversity-ai/
├── backend/
│   ├── main.py
│   ├── api/
│   ├── models/
│   ├── rag/
│   ├── reasoning/
│   └── services/
│
├── data/
│   └── documents/
│
├── frontend/
│   ├── public/
│   └── src/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```


## CI/CD

**Not configured** in this assessment prototype. There is no automated build, test, or deployment pipeline. See [Future Improvements](#future-improvements).

## Assessment Requirement Coverage

| Requirement | Implementation |
|---|---|
| Structured environmental knowledge | `EnvironmentalState` model |
| Retrievable environmental knowledge | ChromaDB + embeddings |
| Soil health | pH, SOC, soil moisture |
| Land use / land cover | Land-use type, crop, agricultural system |
| Biodiversity indicators | Species richness, habitat diversity |
| Climate | Temperature, rainfall |
| Human impact | Pollution, deforestation |
| Natural-language input | Environment extractor + `/chat` |
| Structured input | Pydantic `EnvironmentalState` |
| Conversational system | `/chat` + `conversation_id` |
| Multi-turn context | Conversation service |
| Evidence-backed recommendations | RAG + evidence evaluation |
| Multi-metric reasoning | Environmental relationship engine |
| Affected metrics | Recommendation output |
| Time horizon | Recommendation output |
| Vector database | ChromaDB |
| Embeddings | `all-MiniLM-L6-v2` |

## Limitations

- This is an assessment prototype, not a production system.
- Environmental thresholds and reasoning rules are prototype logic, not calibrated against regional agronomic data.
- Region-specific ecological calibration is not implemented.
- Production cloud deployment is not implemented; the project runs locally only.
- CI/CD is not implemented.
- Quantitative ecological impact prediction is not implemented — affected metrics are described qualitatively (e.g. "potential improvement"), not as invented percentages.
- Geographic coordinate-based analysis is not implemented.
- Real-time environmental data integration (e.g. live weather feeds) is not implemented.

## Future Improvements

- Geographic coordinate-based environmental analysis
- Satellite imagery integration
- Remote sensing land-cover data
- Real-time weather data integration
- Region-specific ecological thresholds
- Expanded biodiversity datasets
- Automated environmental monitoring
- Quantitative intervention impact estimates
- Confidence calibration
- Automated evaluation benchmarks
- CI/CD pipeline
- Cloud deployment
