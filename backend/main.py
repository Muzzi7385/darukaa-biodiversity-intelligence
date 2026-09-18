from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.models.environmental_state import (
    EnvironmentalState,
)

from backend.rag.retriever import (
    retrieve_multi_metric_knowledge,
)

from backend.reasoning.evidence_matrix import (
    evaluate_interventions,
)

from backend.reasoning.multi_metric import (
    analyze_environment,
)

from backend.reasoning.query_builder import (
    build_environmental_queries,
)

from backend.reasoning.recommendation_engine import (
    rank_interventions,
)

from backend.services.conversation_service import (
    process_chat,
)


# =========================================================
# FastAPI application
# =========================================================

app = FastAPI(
    title="Darukaa Biodiversity Intelligence API",
    description=(
        "AI-powered environmental reasoning and "
        "biodiversity recommendation system."
    ),
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# =========================================================
# Request models
# =========================================================

class ChatRequest(BaseModel):
    conversation_id: str = "default"
    message: str


# =========================================================
# Health
# =========================================================

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "darukaa-biodiversity-ai",
    }


# =========================================================
# Environment input
# =========================================================

@app.post("/environment/analyze")
def analyze_environment_input(
    state: EnvironmentalState,
):
    return {
        "message": (
            "Environmental state received successfully."
        ),
        "environment": state.model_dump(),
    }


# =========================================================
# Environmental reasoning
# =========================================================

@app.post("/environment/reason")
def reason_about_environment(
    state: EnvironmentalState,
):

    # -----------------------------------------------------
    # 1. Analyze environmental conditions
    # -----------------------------------------------------

    analysis = analyze_environment(
        state
    )

    # -----------------------------------------------------
    # 2. Build multiple focused search queries
    # -----------------------------------------------------

    knowledge_queries = (
        build_environmental_queries(
            state
        )
    )

    # -----------------------------------------------------
    # 3. Retrieve general scientific evidence
    # -----------------------------------------------------

    evidence = retrieve_multi_metric_knowledge(
        queries=knowledge_queries,
        top_k_per_query=3,
    )

    # -----------------------------------------------------
    # 4. Generate candidate interventions
    # -----------------------------------------------------

    ranked_interventions = rank_interventions(
        state,
        analysis,
    )

    # -----------------------------------------------------
    # 5. Evaluate every intervention using
    #    metric-specific scientific retrieval
    # -----------------------------------------------------

    evaluated_interventions = (
        evaluate_interventions(
            ranked_interventions,
            state,
        )
    )

    # -----------------------------------------------------
    # 6. Select strongest eligible intervention
    # -----------------------------------------------------

    selected_intervention = next(
        (
            item
            for item in evaluated_interventions
            if item[
                "recommendation_eligible"
            ]
        ),
        None,
    )

    # -----------------------------------------------------
    # 7. Return complete reasoning context
    # -----------------------------------------------------

    return {

        "environment": state.model_dump(),

        "knowledge_queries": (
            knowledge_queries
        ),

        "findings": [
            {
                "title": finding.title,
                "severity": finding.severity,
                "explanation": finding.explanation,
                "variables": finding.variables,
            }
            for finding
            in analysis.findings
        ],

        "relationships": [
            {
                "relationship": (
                    relationship.relationship
                ),
                "explanation": (
                    relationship.explanation
                ),
                "variables": (
                    relationship.variables
                ),
            }
            for relationship
            in analysis.relationships
        ],

        "scientific_evidence": [
            {
                "source": result["source"],
                "page": result["page"],
                "distance": result["distance"],
                "query": result["query"],
                "text": result["text"],
            }
            for result
            in evidence
        ],

        "candidate_interventions": (
            evaluated_interventions
        ),

        "selected_intervention": (
            selected_intervention
        ),
    }


# =========================================================
# Conversational biodiversity intelligence
# =========================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
):
    return process_chat(
        conversation_id=request.conversation_id,
        message=request.message,
    )