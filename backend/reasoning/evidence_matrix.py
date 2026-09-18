from dataclasses import dataclass, field

from backend.models.environmental_state import (
    EnvironmentalState,
)

from backend.rag.retriever import (
    retrieve_single_query,
)

from backend.reasoning.recommendation_engine import (
    RankedIntervention,
)

from backend.reasoning.tradeoff_detector import (
    detect_tradeoffs,
)


# =========================================================
# Metric configuration
# =========================================================

METRIC_TERMS: dict[str, str] = {
    "soil_organic_carbon": (
        "soil organic carbon soil health soil organic matter"
    ),

    "soil_moisture": (
        "soil moisture water infiltration water retention "
        "drought resilience"
    ),

    "crop_system": (
        "crop diversification monoculture crop rotation "
        "intercropping agricultural biodiversity"
    ),

    "land_use": (
        "land use land cover agricultural diversification "
        "ecosystem biodiversity"
    ),

    "species_richness": (
        "species richness biodiversity agricultural ecosystems"
    ),

    "habitat_diversity": (
        "habitat diversity habitat complexity biodiversity "
        "agricultural landscapes"
    ),

    "pollution": (
        "agricultural pollution biodiversity ecosystem impact"
    ),

    "deforestation": (
        "deforestation habitat loss biodiversity ecosystem impact"
    ),
}


# =========================================================
# Metric evidence result
# =========================================================

@dataclass
class MetricEvidenceResult:

    metric: str

    support_level: str

    best_similarity: float

    context_score: float

    source_priority: float

    evidence_score: float

    evidence_count: int

    supporting_sources: list[dict] = field(
        default_factory=list
    )


# =========================================================
# Complete intervention evidence matrix
# =========================================================

@dataclass
class InterventionEvidenceMatrix:

    intervention_name: str

    problem_metrics: list[str]

    relevant_metrics: list[str]

    problem_coverage: float

    evidence_quality: float

    support_score: float

    caution_score: float

    has_tradeoff: bool

    status: str

    final_score: float

    recommendation_eligible: bool

    metric_results: list[MetricEvidenceResult] = field(
        default_factory=list
    )

    supporting_sources: list[dict] = field(
        default_factory=list
    )

    caution_sources: list[dict] = field(
        default_factory=list
    )


# =========================================================
# Helpers
# =========================================================

def normalize_text(
    text: str | None,
) -> str:

    if not text:
        return ""

    return (
        text
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("/", " ")
    )


# =========================================================
# Source priority
# =========================================================

def get_source_priority(
    source: str | None,
) -> float:

    if not source:
        return 0.50

    normalized = source.lower()

    # Internal prototype heuristic.
    # This is NOT a measure of scientific truth.
    if "ipcc" in normalized:
        return 1.00

    if (
        "fao" in normalized
        or "cb6378en" in normalized
        or "i1861e" in normalized
    ):
        return 0.95

    return 0.75


# =========================================================
# Context score
# =========================================================

def calculate_context_score(
    evidence_text: str,
    state: EnvironmentalState,
) -> float:

    text = normalize_text(
        evidence_text
    )

    context_terms: list[str] = []

    # Region
    if state.region:
        context_terms.append(
            normalize_text(
                state.region
            )
        )

    # Crop
    if state.land_use.crop:
        context_terms.append(
            normalize_text(
                state.land_use.crop
            )
        )

    # Land-use system
    if state.land_use.system:
        context_terms.append(
            normalize_text(
                state.land_use.system
            )
        )

    # Rainfall
    if state.climate.rainfall:
        context_terms.append(
            normalize_text(
                state.climate.rainfall
            )
        )

    # Temperature
    if state.climate.temperature:
        context_terms.append(
            normalize_text(
                state.climate.temperature
            )
        )

    # Soil moisture
    if state.soil.moisture:
        context_terms.append(
            normalize_text(
                state.soil.moisture
            )
        )

    # Remove duplicates / empty values.
    context_terms = list(
        dict.fromkeys(
            term
            for term in context_terms
            if term
        )
    )

    if not context_terms:
        return 0.50

    matched = sum(
        1
        for term in context_terms
        if term in text
    )

    return min(
        1.0,
        matched
        / max(
            1,
            min(
                5,
                len(context_terms)
            )
        ),
    )


# =========================================================
# Identify actionable problem metrics
# =========================================================

def identify_problem_metrics(
    state: EnvironmentalState,
) -> list[str]:

    metrics: list[str] = []

    # -----------------------------------------------------
    # Soil
    # -----------------------------------------------------

    if (
        state.soil.organic_carbon is not None
        and state.soil.organic_carbon < 1.0
    ):
        metrics.append(
            "soil_organic_carbon"
        )

    if (
        state.soil.moisture is not None
        and normalize_text(
            state.soil.moisture
        )
        in {
            "very low",
            "low",
        }
    ):
        metrics.append(
            "soil_moisture"
        )

    # -----------------------------------------------------
    # Land use
    # -----------------------------------------------------

    system = normalize_text(
        state.land_use.system
    )

    if "monoculture" in system:

        metrics.append(
            "crop_system"
        )


    # -----------------------------------------------------
    # Biodiversity
    # -----------------------------------------------------

    if normalize_text(
        state.biodiversity.species_richness
    ) in {
        "very low",
        "low",
    }:

        metrics.append(
            "species_richness"
        )

    if normalize_text(
        state.biodiversity.habitat_diversity
    ) in {
        "very low",
        "low",
    }:

        metrics.append(
            "habitat_diversity"
        )

    # -----------------------------------------------------
    # Human impact
    # -----------------------------------------------------

    if normalize_text(
        state.human_impact.pollution
    ) in {
        "very high",
        "high",
    }:

        metrics.append(
            "pollution"
        )

    if normalize_text(
        state.human_impact.deforestation
    ) in {
        "very high",
        "high",
    }:

        metrics.append(
            "deforestation"
        )

    return list(
        dict.fromkeys(metrics)
    )


# =========================================================
# Build metric-specific query
# =========================================================

def build_metric_query(
    intervention: RankedIntervention,
    metric: str,
    state: EnvironmentalState,
) -> str:

    metric_terms = METRIC_TERMS.get(
        metric,
        metric.replace(
            "_",
            " ",
        ),
    )

    context_parts: list[str] = []

    # Region
    if state.region:
        context_parts.append(
            state.region
        )

    # Crop
    if state.land_use.crop:
        context_parts.append(
            state.land_use.crop
        )

    # Land-use system
    if state.land_use.system:
        context_parts.append(
            state.land_use.system
        )

    # Rainfall
    if state.climate.rainfall:
        context_parts.append(
            f"rainfall {state.climate.rainfall}"
        )

    # Temperature
    if state.climate.temperature:
        context_parts.append(
            f"temperature {state.climate.temperature}"
        )

    # Soil moisture
    if state.soil.moisture:
        context_parts.append(
            f"soil moisture {state.soil.moisture}"
        )

    parts = [
        intervention.intervention.name,
        intervention.intervention.description,
        metric_terms,
        *intervention.evidence_queries,
        *context_parts,
        "scientific evidence",
        "environmental impacts",
        "applicability",
    ]

    return " ".join(
        dict.fromkeys(
            part.strip()
            for part in parts
            if part and part.strip()
        )
    )


# =========================================================
# Evaluate one intervention against one metric
# =========================================================

def evaluate_metric(
    intervention: RankedIntervention,
    metric: str,
    state: EnvironmentalState,
) -> MetricEvidenceResult:

    query = build_metric_query(
        intervention,
        metric,
        state,
    )

    retrieved = retrieve_single_query(
        query=query,
        top_k=3,
    )

    # -----------------------------------------------------
    # No evidence
    # -----------------------------------------------------

    if not retrieved:

        return MetricEvidenceResult(
            metric=metric,
            support_level="weak",
            best_similarity=0.0,
            context_score=0.0,
            source_priority=0.0,
            evidence_score=0.0,
            evidence_count=0,
            supporting_sources=[],
        )

    scored_sources: list[dict] = []

    # -----------------------------------------------------
    # Score retrieved evidence
    # -----------------------------------------------------

    for result in retrieved:

        distance = float(
            result.get(
                "distance",
                1.0,
            )
        )

        # Chroma cosine distance.
        similarity = max(
            0.0,
            min(
                1.0,
                1.0 - distance,
            ),
        )

        context_score = calculate_context_score(
            result.get(
                "text",
                "",
            ),
            state,
        )

        source_priority = get_source_priority(
            result.get(
                "source"
            )
        )

        evidence_score = (
            similarity * 0.60
            + context_score * 0.20
            + source_priority * 0.20
        )

        scored_sources.append(
            {
                "source": result.get(
                    "source"
                ),
                "page": result.get(
                    "page"
                ),
                "chunk_index": result.get(
                    "chunk_index"
                ),
                "distance": round(
                    distance,
                    4,
                ),
                "similarity": round(
                    similarity,
                    3,
                ),
                "context_score": round(
                    context_score,
                    3,
                ),
                "source_priority": round(
                    source_priority,
                    3,
                ),
                "evidence_score": round(
                    evidence_score,
                    3,
                ),
                "query": query,
                "text": result.get(
                    "text",
                    "",
                ),
            }
        )

    # -----------------------------------------------------
    # Rank evidence
    # -----------------------------------------------------

    scored_sources.sort(
        key=lambda item: item[
            "evidence_score"
        ],
        reverse=True,
    )

    best = scored_sources[0]

    best_similarity = best[
        "similarity"
    ]

    context_score = best[
        "context_score"
    ]

    source_priority = best[
        "source_priority"
    ]

    evidence_score = best[
        "evidence_score"
    ]

    # -----------------------------------------------------
    # Support level
    #
    # Prototype thresholds only.
    # They are NOT scientific probabilities.
    # -----------------------------------------------------

    if evidence_score >= 0.68:

        support_level = "strong"

    elif evidence_score >= 0.55:

        support_level = "moderate"

    else:

        support_level = "weak"

    return MetricEvidenceResult(
        metric=metric,
        support_level=support_level,
        best_similarity=best_similarity,
        context_score=context_score,
        source_priority=source_priority,
        evidence_score=evidence_score,
        evidence_count=len(
            scored_sources
        ),
        supporting_sources=scored_sources[:2],
    )


# =========================================================
# Evaluate one intervention
# =========================================================

def build_evidence_matrix(
    intervention: RankedIntervention,
    state: EnvironmentalState,
) -> InterventionEvidenceMatrix:

    # -----------------------------------------------------
    # Identify the user's actual problem metrics
    # -----------------------------------------------------

    problem_metrics = identify_problem_metrics(
        state
    )

    # -----------------------------------------------------
    # Identify which problems this intervention targets
    # -----------------------------------------------------

    relevant_metrics = [
        metric
        for metric in problem_metrics
        if metric
        in intervention.intervention.target_variables
    ]

    # -----------------------------------------------------
    # Evaluate each relevant metric
    # -----------------------------------------------------

    metric_results: list[
        MetricEvidenceResult
    ] = []

    for metric in relevant_metrics:

        metric_result = evaluate_metric(
            intervention,
            metric,
            state,
        )

        metric_results.append(
            metric_result
        )

    # -----------------------------------------------------
    # No relevant metrics
    # -----------------------------------------------------

    if not relevant_metrics:

        return InterventionEvidenceMatrix(
            intervention_name=(
                intervention.intervention.name
            ),
            problem_metrics=problem_metrics,
            relevant_metrics=[],
            problem_coverage=0.0,
            evidence_quality=0.0,
            support_score=0.0,
            caution_score=0.0,
            has_tradeoff=False,
            status="Insufficient Evidence",
            final_score=(
                intervention.base_score
            ),
            recommendation_eligible=False,
            metric_results=[],
            supporting_sources=[],
            caution_sources=[],
        )

    # -----------------------------------------------------
    # Problem coverage
    #
    # Percentage of identified user problems that
    # this intervention directly targets.
    # -----------------------------------------------------

    problem_coverage = (
        len(relevant_metrics)
        / max(
            1,
            len(problem_metrics),
        )
    )

    # -----------------------------------------------------
    # Average evidence quality
    # -----------------------------------------------------

    evidence_quality = (
        sum(
            result.evidence_score
            for result in metric_results
        )
        / len(metric_results)
    )

    # -----------------------------------------------------
    # Detect intervention trade-offs
    # -----------------------------------------------------

    tradeoff = detect_tradeoffs(
        intervention_name=(
            intervention.intervention.name
        ),
        intervention_description=(
            intervention.intervention.description
        ),
        evidence_queries=(
            intervention.evidence_queries
        ),
        state=state,
    )

    # -----------------------------------------------------
    # Supported metrics
    # -----------------------------------------------------

    supported_metric_count = sum(
        1
        for result in metric_results
        if result.support_level
        in {
            "strong",
            "moderate",
        }
    )

    # -----------------------------------------------------
    # Weak metrics
    # -----------------------------------------------------

    weak_metric_count = sum(
        1
        for result in metric_results
        if result.support_level
        == "weak"
    )

    # -----------------------------------------------------
    # Minimum evidence requirement
    #
    # One metric is enough when the intervention targets
    # only one relevant metric.
    #
    # Multiple metrics are preferred when the intervention
    # is being evaluated against several problems.
    # -----------------------------------------------------

    minimum_supported_metrics = (
        1
        if len(relevant_metrics) == 1
        else 2
    )

    # -----------------------------------------------------
    # Eligibility
    #
    # This is an application heuristic.
    # It is NOT a scientific confidence probability.
    # -----------------------------------------------------

    recommendation_eligible = (
        supported_metric_count
        >= minimum_supported_metrics

        and problem_coverage
        >= 0.40

        and tradeoff.status
        != "Insufficient Evidence"
    )

    # -----------------------------------------------------
    # Trade-off penalty
    # -----------------------------------------------------

    tradeoff_penalty = (
        3.0
        if tradeoff.has_tradeoff
        else 0.0
    )

    # -----------------------------------------------------
    # Final ranking score
    # -----------------------------------------------------

    final_score = (
        intervention.base_score
        + problem_coverage * 8
        + evidence_quality * 5
        - weak_metric_count * 1.5
        - tradeoff_penalty
    )

    # -----------------------------------------------------
    # Return matrix
    # -----------------------------------------------------

    return InterventionEvidenceMatrix(
        intervention_name=(
            intervention.intervention.name
        ),

        problem_metrics=problem_metrics,

        relevant_metrics=relevant_metrics,

        problem_coverage=round(
            problem_coverage,
            3,
        ),

        evidence_quality=round(
            evidence_quality,
            3,
        ),

        support_score=(
            tradeoff.support_score
        ),

        caution_score=(
            tradeoff.caution_score
        ),

        has_tradeoff=(
            tradeoff.has_tradeoff
        ),

        status=(
            tradeoff.status
        ),

        final_score=round(
            final_score,
            2,
        ),

        recommendation_eligible=(
            recommendation_eligible
        ),

        metric_results=metric_results,

        supporting_sources=(
            tradeoff.supporting_sources
        ),

        caution_sources=(
            tradeoff.caution_sources
        ),
    )


# =========================================================
# Evaluate all interventions
# =========================================================

def evaluate_interventions(
    ranked_interventions: list[
        RankedIntervention
    ],
    state: EnvironmentalState,
) -> list[dict]:

    evaluated: list[dict] = []

    for intervention in ranked_interventions:

        matrix = build_evidence_matrix(
            intervention,
            state,
        )

        evaluated.append(
            {
                # -----------------------------------------
                # Intervention
                # -----------------------------------------

                "name": (
                    intervention.intervention.name
                ),

                "description": (
                    intervention.intervention.description
                ),

                "time_horizon": (
                    intervention.intervention.time_horizon
                ),

                # -----------------------------------------
                # Ranking
                # -----------------------------------------

                "base_score": (
                    intervention.base_score
                ),

                "final_score": (
                    matrix.final_score
                ),

                # -----------------------------------------
                # Problem coverage
                # -----------------------------------------

                "problem_metrics": (
                    matrix.problem_metrics
                ),

                "relevant_metrics": (
                    matrix.relevant_metrics
                ),

                "matched_variables": (
                    intervention.matched_variables
                ),

                "problem_coverage": (
                    matrix.problem_coverage
                ),

                # -----------------------------------------
                # Evidence
                # -----------------------------------------

                "evidence_quality": (
                    matrix.evidence_quality
                ),

                "support_score": (
                    matrix.support_score
                ),

                "caution_score": (
                    matrix.caution_score
                ),

                "has_tradeoff": (
                    matrix.has_tradeoff
                ),

                "status": (
                    matrix.status
                ),

                "recommendation_eligible": (
                    matrix.recommendation_eligible
                ),

                # -----------------------------------------
                # Metric-level evidence matrix
                # -----------------------------------------

                "metric_evidence": [
                    {
                        "metric": result.metric,

                        "support_level": (
                            result.support_level
                        ),

                        "best_similarity": (
                            result.best_similarity
                        ),

                        "context_score": (
                            result.context_score
                        ),

                        "source_priority": (
                            result.source_priority
                        ),

                        "evidence_score": (
                            result.evidence_score
                        ),

                        "evidence_count": (
                            result.evidence_count
                        ),

                        "supporting_sources": (
                            result.supporting_sources
                        ),
                    }
                    for result
                    in matrix.metric_results
                ],

                # -----------------------------------------
                # Supporting evidence
                # -----------------------------------------

                "supporting_sources": (
                    matrix.supporting_sources
                ),

                # -----------------------------------------
                # Caution / trade-off evidence
                # -----------------------------------------

                "caution_sources": (
                    matrix.caution_sources
                ),
            }
        )

    # -----------------------------------------------------
    # Put eligible interventions first,
    # then rank by final score.
    # -----------------------------------------------------

    evaluated.sort(
        key=lambda item: (
            item["recommendation_eligible"],
            item["final_score"],
        ),
        reverse=True,
    )

    return evaluated