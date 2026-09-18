# Darukaa Biodiversity Intelligence

An AI-powered environmental intelligence system that analyzes environmental conditions, connects multiple ecological variables, retrieves scientific evidence, and generates evidence-backed recommendations.

## Overview

The system is designed around a structured environmental knowledge layer rather than relying only on an LLM.

A user can describe an environmental situation using natural language, for example:

> "The region is semi-arid with wheat monoculture. Soil pH is 7.8, organic carbon is 0.4%, moisture is low, rainfall is 450 mm, temperature is 32°C, species richness and habitat diversity are low, and pesticide pollution is moderate."

The system extracts the environmental state, identifies important environmental findings, reasons across multiple variables, retrieves relevant scientific literature using RAG, evaluates possible interventions, and returns an evidence-backed recommendation.

## Key Features

- Natural-language environmental input
- Structured environmental state extraction
- Multi-turn conversational context
- Retrieval-Augmented Generation (RAG)
- Semantic search using sentence embeddings
- ChromaDB vector database
- Scientific evidence retrieval
- Multi-metric environmental reasoning
- Soil health analysis
- Land-use analysis
- Biodiversity analysis
- Climate analysis
- Human-impact analysis
- Evidence-backed recommendations
- Intervention eligibility and evidence evaluation
- Affected-metric identification
- Frontend visualization of environmental findings and relationships

## Environmental Variables

The system models five major environmental dimensions.

### Soil

- pH
- Soil organic carbon (SOC)
- Soil moisture

### Land Use

- Land-use type
- Crop
- Agricultural system

### Biodiversity

- Species richness
- Habitat diversity

### Climate

- Temperature
- Rainfall

### Human Impact

- Pollution
- Deforestation

## Architecture

```text
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
              │        ┌───────────────┐
              │        │ Recommendation│
              │        │    Engine     │
              │        └──────┬────────┘
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
RAG Pipeline

The system uses Retrieval-Augmented Generation so environmental knowledge is retrieved from a scientific knowledge base instead of relying only on the LLM's internal knowledge.

User Environmental Input
          ↓
Environmental State Extraction
          ↓
Structured Environmental State
          ↓
Environmental Query Builder
          ↓
Sentence Transformer Embeddings
          ↓
ChromaDB Semantic Search
          ↓
Relevant Scientific Passages
          ↓
Evidence Validation
          ↓
Multi-Metric Reasoning
          ↓
Intervention Evaluation
          ↓
Evidence-Backed Recommendation
Knowledge Base

The current knowledge base contains scientific and environmental documents including:

IPCC AR6 WGII Full Report
FAO environmental/agricultural documentation
Additional biodiversity and environmental reference material

The documents are stored in:

data/documents/

The documents are processed into retrievable chunks, converted into vector embeddings using:

all-MiniLM-L6-v2

and stored in ChromaDB for semantic retrieval.

The large PDF knowledge sources are tracked using Git LFS.

Database / Knowledge Schema

The structured environmental state follows this schema:

EnvironmentalState
│
├── region
│
├── soil
│   ├── ph
│   ├── organic_carbon
│   └── moisture
│
├── land_use
│   ├── land_use_type
│   ├── crop
│   └── system
│
├── biodiversity
│   ├── species_richness
│   └── habitat_diversity
│
├── climate
│   ├── temperature
│   └── rainfall
│
└── human_impact
    ├── pollution
    └── deforestation

The vector knowledge layer stores document chunks with associated metadata:

Document Chunk
│
├── text
├── source
├── page
├── embedding
└── metadata
Multi-Metric Environmental Reasoning

A core part of the system is its ability to reason across multiple environmental variables instead of treating each metric independently.

The reasoning layer currently models relationships including:

Rainfall ↔ Soil Moisture
Temperature ↔ Soil Moisture
Water Availability ↔ Land Use ↔ Biodiversity
Soil Organic Carbon ↔ Soil Moisture
Soil Health ↔ Water Availability ↔ Land Use
Land-use Diversity ↔ Biodiversity
Water Availability ↔ Biodiversity
Land-use System ↔ Habitat Diversity
Human Impact ↔ Biodiversity

This allows the system to identify interactions between environmental conditions.

For example, reduced rainfall can contribute to lower water availability and soil moisture, which can interact with land-use practices and potentially affect biodiversity.

Environmental Findings

The reasoning engine identifies environmental pressures based on the structured environmental state.

Examples include:

Low soil moisture
Low rainfall
High temperature
Low soil organic carbon
Soil pH concerns
Monoculture pressure
Low species richness
Low habitat diversity
Pollution pressure
Deforestation pressure when applicable

The system uses prototype thresholds and qualitative environmental indicators as part of the reasoning layer.

Recommendation Engine

The recommendation engine evaluates candidate interventions against the detected environmental conditions.

The recommendation output can contain:

Recommended intervention
Intervention suitability
Time horizon
Problem coverage
Evidence quality
Affected environmental metrics
Scientific evidence
Caveats

Affected metrics are represented using qualitative descriptions such as:

Potential improvement
Potential indirect benefit

The system uses deterministic reasoning together with retrieved scientific evidence to evaluate candidate interventions.

The system does not claim unsupported numerical ecological improvements.

Evidence-Backed Recommendations

Recommendations are connected to retrieved scientific evidence from the knowledge base.

Retrieved evidence can contain:

Evidence
│
├── Source
├── Page
├── Retrieved Text
├── Query
└── Similarity / Distance

This provides traceability between environmental recommendations and the scientific material retrieved from the knowledge base.

Conversational Intelligence

The /chat endpoint supports multi-turn environmental conversations using a conversation_id.

The system can:

Extract environmental information from natural language.
Preserve previously provided environmental information.
Update the environmental state when new information is provided.
Use the accumulated environmental context for subsequent reasoning.
Retrieve evidence based on the current environmental state.

Example:

User:
The region is semi-arid with wheat cultivation.

System:
The environmental state is updated with the available information.

User:
It is a monoculture system and soil moisture is low.

System:
The existing environmental state is updated and the system
can reason using the combined land-use and soil-moisture context.
API Endpoints
Health Check
GET /health

Returns the current backend service status.

Environment Analysis
POST /environment/analyze

Accepts a structured EnvironmentalState.

Environmental Reasoning
POST /environment/reason

Performs:

Environmental analysis
Environmental query generation
Scientific retrieval
Multi-metric reasoning
Intervention evaluation
Evidence evaluation
Conversational Analysis
POST /chat

Accepts a conversational message and conversation ID.

Example:

{
  "conversation_id": "default",
  "message": "The region has low rainfall and wheat monoculture."
}
Technology Stack
Backend
Python
FastAPI
Pydantic
Groq API
Sentence Transformers
ChromaDB
PyPDF
python-dotenv
Frontend
React
Vite
JavaScript
CSS
AI / ML
all-MiniLM-L6-v2
Vector embeddings
Retrieval-Augmented Generation
LLM-based environmental information extraction
Multi-metric environmental reasoning
Evidence-based intervention evaluation
Project Structure
darukaa-biodiversity-ai/
│
├── backend/
│   ├── main.py
│   │
│   ├── api/
│   │   └── health.py
│   │
│   ├── models/
│   │   ├── environmental_state.py
│   │   └── recommendation.py
│   │
│   ├── rag/
│   │   ├── embeddings.py
│   │   ├── ingest.py
│   │   └── retriever.py
│   │
│   ├── reasoning/
│   │   ├── evidence_matrix.py
│   │   ├── evidence_validator.py
│   │   ├── multi_metric.py
│   │   ├── query_builder.py
│   │   ├── recommendation_engine.py
│   │   └── tradeoff_detector.py
│   │
│   └── services/
│       ├── conversation_service.py
│       ├── environment_extractor.py
│       └── groq_service.py
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
Local Setup
1. Clone the repository
git clone https://github.com/Muzzi7385/darukaa-biodiversity-intelligence.git
cd darukaa-biodiversity-intelligence
2. Install Git LFS

The scientific PDF files are stored using Git LFS.

git lfs install
git lfs pull
3. Create Python Environment
python3 -m venv .venv
source .venv/bin/activate

For Windows:

.venv\Scripts\activate
4. Install Backend Dependencies
pip install -r requirements.txt
5. Configure Environment Variables

Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key

A template is available in:

.env.example

Do not commit the .env file.

6. Build the RAG Database

The source documents are located in:

data/documents/

The generated ChromaDB database is intentionally excluded from Git because it can be recreated locally.

Run:

python -m backend.rag.ingest
7. Start the Backend

From the project root:

uvicorn backend.main:app --reload

Backend:

http://127.0.0.1:8000

FastAPI documentation:

http://127.0.0.1:8000/docs
8. Start the Frontend

Open another terminal:

cd frontend
npm install
npm run dev

The Vite development server will provide the frontend URL in the terminal.

Environment Variables
Variable	Purpose
GROQ_API_KEY	Authentication for the Groq LLM API

The .env file is excluded through .gitignore.

Generated Data

The following directories are intentionally excluded from Git:

.venv/
node_modules/
data/chroma/
__pycache__/

The ChromaDB database can be recreated from the source documents using the ingestion pipeline.

CI/CD

CI/CD is not configured in the current assessment prototype.

The project can be extended with GitHub Actions for automated testing and deployment.

Assessment Requirement Coverage
Assessment Requirement	Implementation
Structured environmental knowledge layer	Structured EnvironmentalState model
Retrievable environmental knowledge	ChromaDB semantic retrieval
Soil health	pH, SOC, soil moisture
Land use / land cover	Land-use type, crop, agricultural system
Biodiversity indicators	Species richness, habitat diversity
Climate	Temperature, rainfall
Human impact	Pollution, deforestation
RAG	Document retrieval + embeddings
Vector database	ChromaDB
Natural-language input	Environmental information extractor
Conversational system	/chat endpoint
Multi-turn context	Conversation service
Evidence-backed recommendations	Retrieved evidence + intervention evaluation
Multi-metric reasoning	Environmental relationship engine
Affected metrics	Recommendation output
Time horizon	Recommendation output
Structured input	Pydantic environmental state
Example Scenario
Input
Region: Semi-arid

Crop: Wheat

System: Monoculture

Soil pH: 7.8

Soil Organic Carbon: 0.4%

Soil Moisture: Low

Rainfall: 450 mm

Temperature: 32°C

Species Richness: Low

Habitat Diversity: Low

Pollution: Moderate pesticide pressure

Deforestation: None
Example Findings

The system can identify:

Low soil moisture
Low rainfall
High temperature
Low soil organic carbon
Monoculture pressure
Low species richness
Low habitat diversity
Pollution pressure
Example Relationships

The system can connect:

Rainfall
    ↕
Soil Moisture
Water Availability
        ↕
    Land Use
        ↕
   Biodiversity
Soil Organic Carbon
        ↕
   Soil Moisture

The system then retrieves relevant scientific evidence and evaluates candidate interventions against the identified environmental conditions.

Limitations

This project is an assessment prototype.

Environmental thresholds and reasoning rules are prototype logic.
Region-specific calibration is not currently implemented.
Production cloud deployment is not implemented.
CI/CD is not currently configured.
Quantitative ecological impact prediction is not implemented.
Geographic coordinate-based analysis is not implemented.
Real-time environmental data integration is not implemented.

The qualitative recommendations should be validated against region-specific datasets and environmental domain expertise before operational use.

Future Improvements

Potential future improvements include:

Geographic coordinate-based environmental analysis
Satellite imagery integration
Remote sensing land-cover data
Real-time weather data
Region-specific ecological thresholds
Biodiversity datasets
Automated environmental monitoring
Quantitative intervention impact estimates
Confidence calibration
Automated evaluation benchmarks
CI/CD pipelines
Cloud deployment
Persistent production vector infrastructure
Repository

GitHub:

https://github.com/Muzzi7385/darukaa-biodiversity-intelligence

Notes

This repository contains the assessment prototype and its source code.

Large scientific PDF files are tracked using Git LFS.

The generated ChromaDB database is excluded from Git and can be recreated locally using the ingestion pipeline.