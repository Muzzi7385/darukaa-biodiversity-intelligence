from dataclasses import dataclass

from backend.models.environmental_state import (
    EnvironmentalState,
)
from backend.rag.retriever import (
    retrieve_single_query,
)


# =========================================================
# Data structure
# =========================================================

@dataclass
class TradeoffAnalysis:

    support_score: float
    caution_score: float

    supporting_evidence_count: int
    caution_evidence_count: int

    supporting_sources: list[dict]
    caution_sources: list[dict]

    has_tradeoff: bool
    status: str


# =========================================================
# Caution language
# =========================================================

CAUTION_TERMS = (
    "however",
    "but",
    "although",
    "limitation",
    "limitations",
    "trade off",
    "tradeoff",
    "risk",
    "risky",
    "may reduce",
    "may increase",
    "can reduce",
    "can increase",
    "constrained",
    "constraint",
    "uncertain",
    "uncertainty",
    "depends on",
    "depending on",
    "not suitable",
    "not appropriate",
    "carefully managed",
    "knowledge gap",
    "negative impact",
    "adverse",
    "water demand",
    "water use",
)


# =========================================================
# Helpers
# =========================================================

def normalize_text(text: str | None) -> str:

    if not text:
        return ""

    return (
        text
        .lower()
        .replace("-", " ")
        .replace("/", " ")
        .replace("_", " ")
    )


def calculate_caution_language_score(
    text: str,
) -> float:

    normalized = normalize_text(
        text
    )

    if not normalized:
        return 0.0

    matches = 0

    for term in CAUTION_TERMS:

        if term in normalized:
            matches += 1

    return min(
        1.0,
        matches / 4.0,
    )


# =========================================================
# Build context query
# =========================================================

def build_context_terms(
    state: EnvironmentalState,
) -> list[str]:

    terms: list[str] = []

    if state.region:
        terms.append(
            state.region
        )

    if state.land_use.crop:
        terms.append(
            state.land_use.crop
        )

    if state.land_use.system:
        terms.append(
            state.land_use.system
        )

    if state.climate.rainfall:
        terms.append(
            f"rainfall {state.climate.rainfall}"
        )

    if state.climate.temperature:
        terms.append(
            f"temperature {state.climate.temperature}"
        )

    if state.soil.moisture:
        terms.append(
            f"soil moisture {state.soil.moisture}"
        )

    return terms


# =========================================================
# Analyze intervention trade-offs
# =========================================================

def detect_tradeoffs(
    intervention_name: str,
    intervention_description: str,
    evidence_queries: list[str],
    state: EnvironmentalState,
) -> TradeoffAnalysis:

    context_terms = build_context_terms(
        state
    )

    # -----------------------------------------------------
    # Query specifically for supporting evidence
    # -----------------------------------------------------

    support_query = " ".join(
        [
            intervention_name,
            intervention_description,
            *evidence_queries,
            *context_terms,
            "benefits effectiveness positive environmental outcomes",
        ]
    )

    supporting_evidence = retrieve_single_query(
        query=support_query,
        top_k=5,
    )

    # -----------------------------------------------------
    # Query specifically for limitations / trade-offs
    # -----------------------------------------------------

    caution_query = " ".join(
        [
            intervention_name,
            intervention_description,
            *evidence_queries,
            *context_terms,
            (
                "limitations risks trade-offs "
                "negative impacts constraints "
                "water demand uncertainty applicability"
            ),
        ]
    )

    caution_evidence = retrieve_single_query(
        query=caution_query,
        top_k=5,
    )

    # -----------------------------------------------------
    # Score support evidence
    # -----------------------------------------------------

    support_scores: list[float] = []

    for evidence in supporting_evidence:

        distance = float(
            evidence.get(
                "distance",
                1.0,
            )
        )

        similarity = max(
            0.0,
            min(
                1.0,
                1.0 - distance,
            ),
        )

        support_scores.append(
            similarity
        )

    # -----------------------------------------------------
    # Score caution evidence
    # -----------------------------------------------------

    scored_cautions: list[dict] = []

    caution_scores: list[float] = []

    for evidence in caution_evidence:

        distance = float(
            evidence.get(
                "distance",
                1.0,
            )
        )

        similarity = max(
            0.0,
            min(
                1.0,
                1.0 - distance,
            ),
        )

        language_score = (
            calculate_caution_language_score(
                evidence.get(
                    "text",
                    "",
                )
            )
        )

        combined_score = (
            similarity * 0.60
            + language_score * 0.40
        )

        caution_scores.append(
            combined_score
        )

        scored_cautions.append(
            {
                "source": evidence.get(
                    "source"
                ),
                "page": evidence.get(
                    "page"
                ),
                "distance": round(
                    distance,
                    4,
                ),
                "similarity": round(
                    similarity,
                    3,
                ),
                "caution_language_score": round(
                    language_score,
                    3,
                ),
                "caution_score": round(
                    combined_score,
                    3,
                ),
                "query": evidence.get(
                    "query"
                ),
                "text": evidence.get(
                    "text",
                    "",
                ),
            }
        )

    # -----------------------------------------------------
    # Aggregate scores
    # -----------------------------------------------------

    support_score = (
        max(support_scores)
        if support_scores
        else 0.0
    )

    caution_score = (
        max(caution_scores)
        if caution_scores
        else 0.0
    )

    scored_cautions.sort(
        key=lambda item: item[
            "caution_score"
        ],
        reverse=True,
    )

    # -----------------------------------------------------
    # Determine trade-off
    # -----------------------------------------------------

    has_tradeoff = (
        support_score >= 0.55
        and caution_score >= 0.60
    )

    # -----------------------------------------------------
    # Determine status
    # -----------------------------------------------------

    if support_score < 0.50:

        status = "Insufficient Evidence"

    elif has_tradeoff:

        status = "Conditionally Suitable"

    else:

        status = "Recommended"

    return TradeoffAnalysis(
        support_score=round(
            support_score,
            3,
        ),

        caution_score=round(
            caution_score,
            3,
        ),

        supporting_evidence_count=len(
            supporting_evidence
        ),

        caution_evidence_count=len(
            scored_cautions
        ),

        supporting_sources=[
            {
                "source": item.get(
                    "source"
                ),
                "page": item.get(
                    "page"
                ),
                "distance": item.get(
                    "distance"
                ),
                "text": item.get(
                    "text",
                    "",
                ),
            }
            for item
            in supporting_evidence[:3]
        ],

        caution_sources=scored_cautions[:3],

        has_tradeoff=(
            has_tradeoff
        ),

        status=status,
    )