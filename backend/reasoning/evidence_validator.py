from dataclasses import dataclass

from backend.models.environmental_state import EnvironmentalState
from backend.rag.embeddings import generate_embeddings
from backend.rag.retriever import retrieve_single_query
from backend.reasoning.recommendation_engine import RankedIntervention


# ---------------------------------------------------------
# Evidence validation result
# ---------------------------------------------------------

@dataclass
class EvidenceValidation:
    intervention_name: str

    evidence_score: float

    semantic_score: float
    variable_coverage: float
    context_applicability: float
    source_priority: float

    evidence_count: int

    supporting_sources: list[dict]

    supported_keywords: list[str]

    evidence_supported: bool


# ---------------------------------------------------------
# Source priority
# ---------------------------------------------------------

def get_source_priority(
    source: str | None,
) -> float:

    if not source:
        return 0.50

    normalized = source.lower()

    # Priority used only as an internal prototype heuristic.
    # It is NOT a measure of scientific truth.
    if "ipcc" in normalized:
        return 1.00

    if (
        "fao" in normalized
        or "cb6378en" in normalized
        or "i1861e" in normalized
    ):
        return 0.95

    return 0.75


# ---------------------------------------------------------
# Normalize text
# ---------------------------------------------------------

def normalize_text(
    text: str,
) -> str:

    return (
        text.lower()
        .replace("-", " ")
        .replace("/", " ")
        .replace("_", " ")
    )


# ---------------------------------------------------------
# Context terms
# ---------------------------------------------------------

def build_context_terms(
    state: EnvironmentalState,
) -> list[str]:

    terms: list[str] = []

    # Region
    if state.region:
        terms.append(
            normalize_text(state.region)
        )

    # Crop
    if state.land_use.crop:
        terms.append(
            normalize_text(state.land_use.crop)
        )

    # Land-use system
    if state.land_use.system:
        system = normalize_text(
            state.land_use.system
        )

        terms.append(system)

        if "monoculture" in system:
            terms.extend(
                [
                    "monoculture",
                    "continuous cropping",
                    "crop diversification",
                ]
            )

    # Rainfall
    if state.climate.rainfall:
        rainfall = normalize_text(
            state.climate.rainfall
        )

        terms.append(rainfall)

        if "low" in rainfall:
            terms.extend(
                [
                    "low rainfall",
                    "water scarcity",
                    "drought",
                    "dryland",
                ]
            )

    # Soil moisture
    if state.soil.moisture:
        moisture = normalize_text(
            state.soil.moisture
        )

        terms.append(moisture)

        if "low" in moisture:
            terms.extend(
                [
                    "low soil moisture",
                    "water retention",
                ]
            )

    # Temperature
    if state.climate.temperature:
        temperature = normalize_text(
            state.climate.temperature
        )

        terms.append(temperature)

        if "high" in temperature:
            terms.extend(
                [
                    "heat",
                    "high temperature",
                    "climate stress",
                ]
            )

    # Biodiversity
    if state.biodiversity.species_richness:
        richness = normalize_text(
            state.biodiversity.species_richness
        )

        terms.append(richness)

        terms.extend(
            [
                "species richness",
                "biodiversity",
            ]
        )

    if state.biodiversity.habitat_diversity:
        habitat = normalize_text(
            state.biodiversity.habitat_diversity
        )

        terms.append(habitat)

        terms.extend(
            [
                "habitat diversity",
                "habitat",
                "biodiversity",
            ]
        )

    return list(
        dict.fromkeys(
            terms
        )
    )


# ---------------------------------------------------------
# Build intervention-specific query
# ---------------------------------------------------------

def build_intervention_query(
    intervention: RankedIntervention,
    state: EnvironmentalState,
) -> str:

    context_terms = build_context_terms(
        state
    )

    variable_terms = [
        variable.replace(
            "_",
            " ",
        )
        for variable
        in intervention.matched_variables
    ]

    keyword_terms = list(
        intervention.evidence_queries
    )

    parts = [
        intervention.intervention.name,
        intervention.intervention.description,
        *keyword_terms,
        *variable_terms,
        *context_terms,
        "scientific evidence",
        "environmental impacts",
        "applicability",
    ]

    # Remove duplicate terms while keeping order.
    return " ".join(
        dict.fromkeys(
            part.strip()
            for part in parts
            if part.strip()
        )
    )


# ---------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:

    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        return 0.0

    dot_product = sum(
        a * b
        for a, b
        in zip(
            vector_a,
            vector_b,
        )
    )

    # generate_embeddings() uses normalized embeddings,
    # so the dot product is cosine similarity.
    return max(
        0.0,
        min(
            1.0,
            dot_product,
        )
    )


# ---------------------------------------------------------
# Context applicability
# ---------------------------------------------------------

def calculate_context_applicability(
    evidence_text: str,
    state: EnvironmentalState,
) -> float:

    normalized_evidence = normalize_text(
        evidence_text
    )

    context_terms = build_context_terms(
        state
    )

    if not context_terms:
        return 0.50

    matched_terms = 0

    for term in context_terms:

        normalized_term = normalize_text(
            term
        )

        if (
            normalized_term
            and normalized_term
            in normalized_evidence
        ):
            matched_terms += 1

    return min(
        1.0,
        matched_terms
        / max(1, min(5, len(context_terms))),
    )


# ---------------------------------------------------------
# Validate intervention
# ---------------------------------------------------------

def validate_intervention_evidence(
    intervention: RankedIntervention,
    state: EnvironmentalState,
    scientific_evidence: list[dict],
) -> EvidenceValidation:

    # -----------------------------------------------------
    # Candidate-specific retrieval
    # -----------------------------------------------------

    intervention_query = build_intervention_query(
        intervention,
        state,
    )

    candidate_evidence = retrieve_single_query(
        query=intervention_query,
        top_k=5,
    )

    # -----------------------------------------------------
    # Combine general + candidate-specific evidence
    # -----------------------------------------------------

    combined_evidence: dict[str, dict] = {}

    for evidence in (
        scientific_evidence
        + candidate_evidence
    ):

        unique_id = (
            f"{evidence.get('source')}_"
            f"{evidence.get('page')}_"
            f"{evidence.get('chunk_index')}"
        )

        existing = combined_evidence.get(
            unique_id
        )

        if existing is None:
            combined_evidence[
                unique_id
            ] = evidence

        else:
            existing_distance = existing.get(
                "distance",
                1.0,
            )

            current_distance = evidence.get(
                "distance",
                1.0,
            )

            if current_distance < existing_distance:
                combined_evidence[
                    unique_id
                ] = evidence

    evidence_pool = list(
        combined_evidence.values()
    )

    if not evidence_pool:
        return EvidenceValidation(
            intervention_name=(
                intervention.intervention.name
            ),
            evidence_score=0.0,
            semantic_score=0.0,
            variable_coverage=0.0,
            context_applicability=0.0,
            source_priority=0.0,
            evidence_count=0,
            supporting_sources=[],
            supported_keywords=[],
            evidence_supported=False,
        )

    # -----------------------------------------------------
    # Embed intervention query
    # -----------------------------------------------------

    query_embedding = generate_embeddings(
        [intervention_query]
    )[0]

    # -----------------------------------------------------
    # Embed evidence chunks
    # -----------------------------------------------------

    evidence_texts = [
        evidence.get(
            "text",
            "",
        )
        for evidence
        in evidence_pool
    ]

    evidence_embeddings = generate_embeddings(
        evidence_texts
    )

    scored_evidence: list[dict] = []

    for evidence, evidence_embedding in zip(
        evidence_pool,
        evidence_embeddings,
    ):

        evidence_text = evidence.get(
            "text",
            "",
        )

        # -------------------------------------------------
        # Semantic relevance
        # -------------------------------------------------

        semantic_score = cosine_similarity(
            query_embedding,
            evidence_embedding,
        )

        # -------------------------------------------------
        # Context applicability
        # -------------------------------------------------

        context_score = (
            calculate_context_applicability(
                evidence_text,
                state,
            )
        )

        # -------------------------------------------------
        # Source priority
        # -------------------------------------------------

        source_priority = (
            get_source_priority(
                evidence.get(
                    "source"
                )
            )
        )

        # -------------------------------------------------
        # Combined evidence quality
        # -------------------------------------------------

        evidence_quality = (
            semantic_score * 0.55
            + context_score * 0.25
            + source_priority * 0.20
        )

        scored_evidence.append(
            {
                "source": evidence.get(
                    "source"
                ),
                "page": evidence.get(
                    "page"
                ),
                "chunk_index": evidence.get(
                    "chunk_index"
                ),
                "query": evidence.get(
                    "query"
                ),
                "distance": evidence.get(
                    "distance"
                ),
                "semantic_score": round(
                    semantic_score,
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
                "evidence_quality": round(
                    evidence_quality,
                    3,
                ),
                "text": evidence_text,
            }
        )

    # -----------------------------------------------------
    # Keep strongest evidence
    # -----------------------------------------------------

    scored_evidence.sort(
        key=lambda item: item[
            "evidence_quality"
        ],
        reverse=True,
    )

    supporting_sources = (
        scored_evidence[:5]
    )

    # -----------------------------------------------------
    # Semantic score
    # -----------------------------------------------------

    semantic_score = (
        sum(
            item["semantic_score"]
            for item
            in supporting_sources
        )
        / len(supporting_sources)
    )

    # -----------------------------------------------------
    # Context applicability score
    # -----------------------------------------------------

    context_applicability = (
        sum(
            item["context_score"]
            for item
            in supporting_sources
        )
        / len(supporting_sources)
    )

    # -----------------------------------------------------
    # Source priority score
    # -----------------------------------------------------

    source_priority = (
        sum(
            item["source_priority"]
            for item
            in supporting_sources
        )
        / len(supporting_sources)
    )

    # -----------------------------------------------------
    # Environmental variable coverage
    # -----------------------------------------------------

    active_variable_count = max(
        1,
        len(
            intervention.matched_variables
        ),
    )

    variable_coverage = min(
        1.0,
        active_variable_count
        / len(
            intervention.intervention.target_variables
        ),
    )

    # -----------------------------------------------------
    # Supported keywords
    # -----------------------------------------------------

    supported_keywords: set[str] = set()

    for keyword in intervention.evidence_queries:

        normalized_keyword = normalize_text(
            keyword
        )

        for evidence in supporting_sources:

            if (
                normalized_keyword
                in normalize_text(
                    evidence["text"]
                )
            ):
                supported_keywords.add(
                    keyword
                )

                break

    # -----------------------------------------------------
    # Final evidence support score
    # -----------------------------------------------------

    evidence_score = (
        semantic_score * 0.45
        + variable_coverage * 0.20
        + context_applicability * 0.20
        + source_priority * 0.15
    )

    evidence_score = round(
        min(
            1.0,
            max(
                0.0,
                evidence_score,
            )
        ),
        3,
    )

    # -----------------------------------------------------
    # Support threshold
    #
    # This is a prototype threshold, not a probability.
    # -----------------------------------------------------

    evidence_supported = (
        evidence_score >= 0.60
        and semantic_score >= 0.50
    )

    return EvidenceValidation(
        intervention_name=(
            intervention.intervention.name
        ),
        evidence_score=evidence_score,
        semantic_score=round(
            semantic_score,
            3,
        ),
        variable_coverage=round(
            variable_coverage,
            3,
        ),
        context_applicability=round(
            context_applicability,
            3,
        ),
        source_priority=round(
            source_priority,
            3,
        ),
        evidence_count=len(
            supporting_sources
        ),
        supporting_sources=(
            supporting_sources
        ),
        supported_keywords=sorted(
            supported_keywords
        ),
        evidence_supported=(
            evidence_supported
        ),
    )