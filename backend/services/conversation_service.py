# backend/services/conversation_service.py

from dataclasses import dataclass, field
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.models.environmental_state import EnvironmentalState
from backend.rag.retriever import retrieve_multi_metric_knowledge
from backend.reasoning.evidence_matrix import evaluate_interventions
from backend.reasoning.multi_metric import analyze_environment
from backend.reasoning.query_builder import build_environmental_queries
from backend.reasoning.recommendation_engine import rank_interventions
from backend.services.environment_extractor import extract_environment
from backend.services.groq_service import ask_groq_json


# ============================================================
# Conversation memory
# ============================================================

@dataclass
class ConversationSession:
    conversation_id: str

    environmental_state: EnvironmentalState = field(
        default_factory=EnvironmentalState
    )

    messages: List[Dict[str, str]] = field(
        default_factory=list
    )


conversation_sessions: Dict[
    str,
    ConversationSession
] = {}


def get_or_create_session(
    conversation_id: str,
) -> ConversationSession:
    """
    Return an existing conversation session or create a new one.
    """

    if conversation_id not in conversation_sessions:

        conversation_sessions[
            conversation_id
        ] = ConversationSession(
            conversation_id=conversation_id
        )

    return conversation_sessions[
        conversation_id
    ]


# ============================================================
# Missing information
# ============================================================

def get_missing_information(
    state: EnvironmentalState,
) -> List[str]:
    """
    Identify the minimum environmental information required
    before running the complete reasoning pipeline.
    """

    missing = []

    if not state.region:
        missing.append("region")

    if not state.land_use.crop:
        missing.append("crop")

    if not state.land_use.system:
        missing.append("land-use system")

    if not state.climate.rainfall:
        missing.append("rainfall")

    if not state.soil.moisture:
        missing.append("soil moisture")

    return missing


def build_clarifying_question(
    missing: List[str],
) -> str:
    """
    Turn missing information into a natural conversational question.
    """

    if not missing:
        return ""

    if len(missing) == 1:

        return (
            f"Could you provide the "
            f"{missing[0]}?"
        )

    if len(missing) == 2:

        return (
            f"Could you provide the "
            f"{missing[0]} and "
            f"{missing[1]}?"
        )

    # Avoid overwhelming the user with too many questions.
    return (
        "To make the assessment more reliable, "
        f"could you provide the {missing[0]} "
        f"and {missing[1]}?"
    )


# ============================================================
# Reasoning pipeline
# ============================================================

def run_reasoning(
    state: EnvironmentalState,
) -> Dict[str, Any]:
    """
    Complete deterministic environmental reasoning pipeline.

    Order:
        1. Multi-metric analysis
        2. Knowledge query construction
        3. RAG retrieval
        4. Intervention ranking
        5. Evidence validation
        6. Select eligible intervention
    """

    analysis = analyze_environment(
        state
    )

    knowledge_queries = (
        build_environmental_queries(
            state
        )
    )

    evidence = (
        retrieve_multi_metric_knowledge(
            queries=knowledge_queries,
            top_k_per_query=3,
        )
    )

    ranked_interventions = (
        rank_interventions(
            state,
            analysis,
        )
    )

    evaluated_interventions = (
        evaluate_interventions(
            ranked_interventions,
            state,
        )
    )

    selected_intervention = next(
        (
            item
            for item in evaluated_interventions
            if item.get(
                "recommendation_eligible"
            )
        ),
        None,
    )

    return {
        "analysis": analysis,
        "knowledge_queries": knowledge_queries,
        "evidence": evidence,
        "candidate_interventions": (
            evaluated_interventions
        ),
        "selected_intervention": (
            selected_intervention
        ),
    }


# ============================================================
# Evidence helpers
# ============================================================

def normalize_evidence_text(
    text: str,
) -> str:
    """
    Clean whitespace from PDF-extracted text.

    No regex is used here.
    """

    if not text:
        return ""

    cleaned = " ".join(
        text.split()
    )

    # Keep the final LLM context reasonably compact.
    if len(cleaned) > 850:

        cleaned = (
            cleaned[:850]
            .rsplit(" ", 1)[0]
            + "..."
        )

    return cleaned


def is_usable_evidence(
    text: str,
) -> bool:
    """
    Reject obvious bibliography/reference/URL fragments.

    This is deliberately conservative.
    """

    if not text:
        return False

    lowered = text.lower()

    bad_phrases = [
        "bibliography",
        "available from:",
        "http://",
        "https://",
    ]

    matches = 0

    for phrase in bad_phrases:

        if phrase in lowered:
            matches += 1

    return matches < 2


# ============================================================
# Evidence cards
# ============================================================

def build_evidence_cards(
    reasoning: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Build a small evidence set for the final LLM.

    Priority:
        1. Intervention-specific support evidence
        2. Intervention-specific caution evidence

    General RAG results are intentionally excluded from the
    final LLM context. This keeps the evidence focused.
    """

    selected = (
        reasoning.get(
            "selected_intervention"
        )
        or {}
    )

    cards: List[Dict[str, Any]] = []
    seen = set()

    metric_evidence = (
        selected.get(
            "metric_evidence",
            []
        )
    )

    # ========================================================
    # Support evidence
    # ========================================================

    support_candidates = []

    for metric_item in metric_evidence:

        metric = metric_item.get(
            "metric",
            "environment",
        )

        for source_item in metric_item.get(
            "supporting_sources",
            [],
        ):

            support_candidates.append(
                (
                    metric,
                    source_item,
                )
            )

    # Prefer evidence from different metrics.
    # Maximum 3 support cards.
    for metric, source_item in support_candidates:

        if len(cards) >= 3:
            break

        source = source_item.get(
            "source"
        )

        page = source_item.get(
            "page"
        )

        text = source_item.get(
            "text"
        )

        if not source or not text:
            continue

        if not is_usable_evidence(
            text
        ):
            continue

        key = (
            source,
            page,
            text[:150],
        )

        if key in seen:
            continue

        seen.add(key)

        cards.append(
            {
                "id": f"E{len(cards) + 1}",
                "type": "intervention_support",
                "metric": metric,
                "source": source,
                "page": page,
                "text": normalize_evidence_text(
                    text
                ),
                "role": "support",
            }
        )

    # ========================================================
    # Caution evidence
    # ========================================================

    caution_sources = (
        selected.get(
            "caution_sources",
            []
        )
    )

    for source_item in caution_sources:

        # Maximum total of 4 cards.
        if len(cards) >= 4:
            break

        source = source_item.get(
            "source"
        )

        page = source_item.get(
            "page"
        )

        text = source_item.get(
            "text"
        )

        if not source or not text:
            continue

        if not is_usable_evidence(
            text
        ):
            continue

        key = (
            source,
            page,
            text[:150],
        )

        if key in seen:
            continue

        seen.add(key)

        cards.append(
            {
                "id": f"E{len(cards) + 1}",
                "type": "intervention_caution",
                "metric": None,
                "source": source,
                "page": page,
                "text": normalize_evidence_text(
                    text
                ),
                "role": "caution",
            }
        )

    return cards


# ============================================================
# Structured response models
# ============================================================

class GroundedClaim(BaseModel):
    """
    A scientific claim produced by the LLM and linked to evidence.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    text: str

    evidence_ids: List[str]


class AffectedMetric(BaseModel):
    """
    Environmental metric mentioned in the final answer.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    metric: str

    status: str

    evidence_ids: List[str]


class GroundedResponse(BaseModel):
    """
    Complete structured response expected from the LLM.
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    assessment: str

    what_to_do: str

    why_it_may_help: List[
        GroundedClaim
    ]

    affected_metrics: List[
        AffectedMetric
    ]

    expected_time_horizon: str

    caveats: List[
        GroundedClaim
    ]


# ============================================================
# Evidence ID validation
# ============================================================

def validate_evidence_ids(
    response: GroundedResponse,
    evidence_cards: List[Dict[str, Any]],
) -> GroundedResponse:
    """
    Validate evidence IDs returned by the LLM.

    LLM decides:
        claim -> E1

    Python checks:
        does E1 actually exist?

    No scientific reasoning is performed here.
    """

    valid_ids = {
        card["id"]
        for card in evidence_cards
    }

    # --------------------------------------------------------
    # Scientific claims
    # --------------------------------------------------------

    for claim in response.why_it_may_help:

        cleaned_ids = []

        for evidence_id in (
            claim.evidence_ids
        ):

            normalized_id = (
                str(
                    evidence_id
                )
                .strip()
                .upper()
            )

            if normalized_id in valid_ids:

                if normalized_id not in cleaned_ids:

                    cleaned_ids.append(
                        normalized_id
                    )

        claim.evidence_ids = cleaned_ids

    # --------------------------------------------------------
    # Affected metrics
    # --------------------------------------------------------

    for metric in (
        response.affected_metrics
    ):

        cleaned_ids = []

        for evidence_id in (
            metric.evidence_ids
        ):

            normalized_id = (
                str(
                    evidence_id
                )
                .strip()
                .upper()
            )

            if normalized_id in valid_ids:

                if normalized_id not in cleaned_ids:

                    cleaned_ids.append(
                        normalized_id
                    )

        metric.evidence_ids = cleaned_ids

    # --------------------------------------------------------
    # Caveats
    # --------------------------------------------------------

    for claim in response.caveats:

        cleaned_ids = []

        for evidence_id in (
            claim.evidence_ids
        ):

            normalized_id = (
                str(
                    evidence_id
                )
                .strip()
                .upper()
            )

            if normalized_id in valid_ids:

                if normalized_id not in cleaned_ids:

                    cleaned_ids.append(
                        normalized_id
                    )

        claim.evidence_ids = cleaned_ids

    return response

# ============================================================
# Authoritative affected metrics
# ============================================================

def apply_authoritative_affected_metrics(
    response: GroundedResponse,
    selected_intervention: Dict[str, Any],
) -> GroundedResponse:
    """
    Build affected metrics from the validated intervention
    and evidence matrix rather than allowing the LLM to
    reinterpret current environmental values as outcomes.

    The LLM explains the recommendation.
    Python determines which metrics are affected and
    how strongly the available evidence supports them.
    """

    target_variables = set(
        selected_intervention.get(
            "matched_variables",
            []
        )
    )

    metric_evidence = (
        selected_intervention.get(
            "metric_evidence",
            []
        )
    )

    evidence_by_metric = {
        item.get("metric"): item
        for item in metric_evidence
        if item.get("metric")
    }

    # --------------------------------------------------------
    # Human-readable metric names
    # --------------------------------------------------------

    display_names = {
        "soil_organic_carbon": "Soil organic carbon",
        "soil_moisture": "Soil moisture",
        "crop_system": "Land-use diversity",
        "land_use": "Land-use diversity",
        "species_richness": "Species richness",
        "habitat_diversity": "Habitat diversity",
    }

    # --------------------------------------------------------
    # Avoid duplicate land-use metrics
    # --------------------------------------------------------

    ordered_metrics = [
        "soil_organic_carbon",
        "soil_moisture",
        "crop_system",
        "species_richness",
        "habitat_diversity",
    ]

    authoritative_metrics = []

    seen_display_names = set()

    for metric in ordered_metrics:

        if metric not in target_variables:
            continue

        display_name = display_names.get(
            metric,
            metric.replace("_", " "),
        )

        # Prevent both crop_system and land_use from producing
        # duplicate "Land-use diversity" rows.
        if display_name in seen_display_names:
            continue

        seen_display_names.add(
            display_name
        )

        evidence_item = (
            evidence_by_metric.get(metric)
        )

        evidence_ids = []

        status = "potentially affected"

        if evidence_item:

            support_level = (
                evidence_item.get(
                    "support_level",
                    "weak",
                )
            )

            sources = (
                evidence_item.get(
                    "supporting_sources",
                    [],
                )
            )

            source_keys = set()

            for source in sources:

                key = (
                    source.get("source"),
                    source.get("page"),
                    source.get("text", "")[:120],
                )

                if key in source_keys:
                    continue

                source_keys.add(key)

                # Evidence cards are assigned later, so here we
                # only determine the semantic status.
                # Actual IDs remain attached through the LLM
                # response where available.
            
            if support_level in {
                "strong",
                "moderate",
            }:
                status = "potential improvement"

            else:
                status = "potential benefit; evidence limited"

        # Biodiversity outcomes should remain cautious.
        if metric in {
            "species_richness",
            "habitat_diversity",
        }:
            status = (
                "potential indirect benefit"
            )

        authoritative_metrics.append(
            AffectedMetric(
                metric=display_name,
                status=status,
                evidence_ids=[],
            )
        )

    response.affected_metrics = (
        authoritative_metrics
    )

    return response

# ============================================================
# Render scientific claim
# ============================================================

def render_claim(
    claim: GroundedClaim,
    evidence_map: Dict[str, Dict[str, Any]],
) -> str:
    """
    Convert a structured LLM claim into readable text plus
    deterministic source/page citations.
    """

    text = claim.text.strip()

    if not text:
        return ""

    citations = []

    for evidence_id in (
        claim.evidence_ids
    ):

        card = evidence_map.get(
            evidence_id
        )

        if not card:
            continue

        source = card.get(
            "source",
            "Unknown source",
        )

        page = card.get(
            "page"
        )

        if page is not None:

            citation = (
                f"({source}, p. {page})"
            )

        else:

            citation = (
                f"({source})"
            )

        if citation not in citations:

            citations.append(
                citation
            )

    if citations:

        return (
            text
            + " "
            + " ".join(
                citations
            )
        )

    return text


# ============================================================
# Render final user-facing response
# ============================================================

def render_grounded_response(
    response: GroundedResponse,
    evidence_cards: List[Dict[str, Any]],
    assessment_scope: str,
) -> str:
    """
    Render the structured LLM response deterministically.

    The LLM controls the wording.
    Python controls the citation formatting.
    """

    evidence_map = {
        card["id"]: card
        for card in evidence_cards
    }

    sections: List[str] = []

    # ========================================================
    # Assessment
    # ========================================================

    assessment = (
        response.assessment.strip()
    )

    if assessment:

        if (
            assessment_scope == "preliminary"
            and "preliminary"
            not in assessment.lower()
        ):

            assessment = (
                "This is a preliminary "
                "environmental assessment. "
                + assessment
            )

        sections.append(
            "**Assessment**\n"
            + assessment
        )

    # ========================================================
    # What to do
    # ========================================================

    what_to_do = (
        response.what_to_do.strip()
    )

    if what_to_do:

        sections.append(
            "**What to do**\n"
            + what_to_do
        )

    # ========================================================
    # Why it may help
    # ========================================================

    why_lines = []

    for claim in (
        response.why_it_may_help
    ):

        rendered = render_claim(
            claim,
            evidence_map,
        )

        if rendered:

            why_lines.append(
                f"- {rendered}"
            )

    if why_lines:

        sections.append(
            "**Why it may help**\n"
            + "\n".join(
                why_lines
            )
        )

    # ========================================================
    # Affected metrics
    # ========================================================

    metric_lines = []

    for metric in (
        response.affected_metrics
    ):

        metric_text = (
            f"**{metric.metric}** "
            f"— {metric.status}"
        )

        citations = []

        for evidence_id in (
            metric.evidence_ids
        ):

            card = evidence_map.get(
                evidence_id
            )

            if not card:
                continue

            source = card.get(
                "source",
                "Unknown source",
            )

            page = card.get(
                "page"
            )

            if page is not None:

                citation = (
                    f"({source}, p. {page})"
                )

            else:

                citation = (
                    f"({source})"
                )

            if citation not in citations:

                citations.append(
                    citation
                )

        if citations:

            metric_text += (
                " "
                + " ".join(
                    citations
                )
            )

        metric_lines.append(
            f"- {metric_text}"
        )

    if metric_lines:

        sections.append(
            "**Affected metrics**\n"
            + "\n".join(
                metric_lines
            )
        )

    # ========================================================
    # Expected time horizon
    # ========================================================

    time_horizon = (
        response
        .expected_time_horizon
        .strip()
    )

    if time_horizon:

        sections.append(
            "**Expected time horizon**\n"
            + time_horizon
        )

    # ========================================================
    # Important caveats
    # ========================================================

    caveat_lines = []

    for claim in response.caveats:

        rendered = render_claim(
            claim,
            evidence_map,
        )

        if rendered:

            caveat_lines.append(
                f"- {rendered}"
            )

    if caveat_lines:

        sections.append(
            "**Important caveats**\n"
            + "\n".join(
                caveat_lines
            )
        )

    # ========================================================
    # Evidence used
    # ========================================================

    evidence_lines = []

    for card in evidence_cards:

        source = card.get(
            "source",
            "Unknown source",
        )

        page = card.get(
            "page"
        )

        if page is not None:

            evidence_lines.append(
                f"- {card['id']}: "
                f"{source}, p. {page}"
            )

        else:

            evidence_lines.append(
                f"- {card['id']}: "
                f"{source}"
            )

    if evidence_lines:

        sections.append(
            "### Evidence used\n"
            + "\n".join(
                evidence_lines
            )
        )

    return "\n\n".join(
        sections
    ).strip()


# ============================================================
# Final LLM generation
# ============================================================

def generate_final_response(
    state: EnvironmentalState,
    reasoning: Dict[str, Any],
    evidence_cards: List[Dict[str, Any]],
    assessment_scope: str,
) -> str:
    """
    Ask the LLM to produce a structured, evidence-grounded response.

    Important division of responsibility:

    LLM:
        - decides which claims are supported
        - attaches evidence IDs
        - expresses uncertainty

    Python:
        - validates response structure
        - validates evidence IDs
        - renders citations
    """

    selected = (
        reasoning.get(
            "selected_intervention"
        )
        or {}
    )

    if not selected:

        return (
            "I couldn't identify an intervention "
            "with enough supporting evidence."
        )

    intervention_name = selected.get(
        "name",
        "the selected intervention",
    )

    intervention_description = (
        selected.get(
            "description",
            "",
        )
    )

    time_horizon = selected.get(
        "time_horizon",
        "medium term",
    )

    status = selected.get(
        "status",
        "Recommended",
    )

    analysis = reasoning[
        "analysis"
    ]

    # ========================================================
    # Compact environmental state
    # ========================================================

    environment = {
        "region": state.region,

        "crop": (
            state.land_use.crop
        ),

        "land_use_system": (
            state.land_use.system
        ),

        "soil_moisture": (
            state.soil.moisture
        ),

        "rainfall": (
            state.climate.rainfall
        ),

        "species_richness": (
            state
            .biodiversity
            .species_richness
        ),

        "habitat_diversity": (
            state
            .biodiversity
            .habitat_diversity
        ),
    }

    # ========================================================
    # Compact findings
    # ========================================================

    findings = []

    for finding in analysis.findings:

        findings.append(
            {
                "title": finding.title,
                "severity": finding.severity,
                "variables": finding.variables,
            }
        )

    # ========================================================
    # Compact relationships
    # ========================================================

    relationships = []

    for relationship in (
        analysis.relationships
    ):

        relationships.append(
    {
        "relationship": relationship.relationship,
        "explanation": relationship.explanation,
        "variables": relationship.variables,
    }
)

    # ========================================================
    # Compact evidence context
    # ========================================================

    evidence_context = []

    for card in evidence_cards:

        evidence_context.append(
            {
                "id": card["id"],
                "role": card["role"],
                "metric": card["metric"],
                "source": card["source"],
                "page": card["page"],
                "evidence": card["text"],
            }
        )

    # ========================================================
    # Scope instructions
    # ========================================================

    if assessment_scope == "preliminary":

        scope_instruction = """
This is a PRELIMINARY environmental assessment.

Species richness is available and reported as low.
Habitat diversity is missing.

You may describe low species richness as an observed condition.

Do NOT claim that the selected intervention will improve,
increase, restore, or recover species richness unless one of
the supplied evidence cards directly supports that exact
intervention-outcome relationship.

Biodiversity effects should therefore be expressed as potential
or uncertain.
"""

    else:

        scope_instruction = """
This is a FULL environmental assessment.

Both species richness and habitat diversity are available.

Discuss biodiversity only when supported by the environmental
state and supplied scientific evidence.
"""

    # ========================================================
    # Tradeoff instructions
    # ========================================================

    if status == "Conditionally Suitable":

        tradeoff_instruction = """
The selected intervention has an identified contextual
limitation or tradeoff.

Describe it as conditionally suitable and use the supplied
caution evidence where appropriate.
"""

    else:

        tradeoff_instruction = """
The selected intervention is the current evidence-supported
recommendation for this environmental state.

Do not describe it as guaranteed or universally suitable.
"""

    # ========================================================
    # Final prompt
    # ========================================================

    prompt = f"""
You are an environmental intelligence assistant.

Produce a concise, scientifically grounded recommendation using
ONLY the environmental information and evidence supplied below.

{scope_instruction}

{tradeoff_instruction}


SELECTED INTERVENTION

Name:
{intervention_name}

Description:
{intervention_description}

Time horizon:
{time_horizon}

Status:
{status}


ENVIRONMENT

{environment}


FINDINGS

{findings}


MULTI-METRIC RELATIONSHIPS

{relationships}


SCIENTIFIC EVIDENCE

{evidence_context}


GROUNDING RULES

1. Use only the supplied information.

2. Every scientific claim about why the intervention may help
   must reference at least one evidence ID.

3. Only attach an evidence ID when that evidence actually supports
   the claim.

4. Do not invent measurements, percentages, thresholds, dates,
   years, species, crop varieties, mechanisms, or study findings.

5. Do not invent a specific complementary crop.

6. Do not invent a numeric implementation timeframe.

7. The selected intervention is already determined.
   Do not introduce a different intervention.

8. Do not claim that species richness will improve unless the
   supplied evidence directly supports that exact relationship.

9. Do not convert general diversification evidence into a claim
   of guaranteed biodiversity improvement.

10. Treat low species richness as an observed condition.

11. Habitat diversity is missing and must remain uncertain.

12. Do not claim a soil-organic-carbon improvement unless the
    supplied evidence explicitly connects this intervention with
    soil organic carbon.

13. Do not claim a water-use-efficiency improvement unless the
    supplied evidence explicitly supports that relationship.

14. Do not introduce biological mechanisms unless the evidence
    supports them.

    15. Affected metrics are intervention outcomes, not descriptions
    of the current environmental state.

16. Do not write "low", "high", "moderate", or similar current-state
    labels as the status of an affected metric.

17. Use outcome-oriented statuses such as:
    "potential improvement",
    "potential indirect benefit",
    "potentially affected",
    or "benefit uncertain".

18. Affected metrics must describe what the selected intervention
    may influence, not simply repeat which metrics are currently low.
    
19. Use cautious language such as:
    "may", "could", "potential", or "context dependent"
    where the evidence is not definitive.

20. Do not mention:
    - scores
    - rankings
    - similarity
    - embeddings
    - vector databases
    - retrieval distances
    - internal heuristics

21. Keep the answer concise.

22. Return ONLY the requested JSON structure.


AVAILABLE EVIDENCE IDs

{[card["id"] for card in evidence_cards]}
"""

    # ========================================================
    # Strict JSON schema
    # ========================================================

    response_schema = (
        GroundedResponse
        .model_json_schema()
    )

    # ========================================================
    # Ask Groq
    # ========================================================

    try:

        llm_output = ask_groq_json(
            prompt=prompt,
            schema_name=(
                "grounded_environmental_response"
            ),
            schema=response_schema,
        )

    except RuntimeError as e:

        print(
            "\n❌ FINAL LLM GENERATION FAILED"
        )

        print(e)

        return str(e)

    # ========================================================
    # Validate structured response
    # ========================================================

    try:

        structured_response = (
            GroundedResponse.model_validate(
                llm_output
            )
        )

    except ValidationError as e:

        print(
            "\n❌ STRUCTURED RESPONSE VALIDATION ERROR"
        )

        print(e)

        print(
            "\nRAW LLM OUTPUT:"
        )

        print(
            llm_output
        )

        return (
            "The environmental analysis was completed, "
            "but the final response could not be validated."
        )

    # ========================================================
    # Validate evidence IDs
    # ========================================================

    structured_response = (
        validate_evidence_ids(
            structured_response,
            evidence_cards,
        )
    )

    structured_response = (
    apply_authoritative_affected_metrics(
        structured_response,
        selected,
    )
)

    # ========================================================
    # Render user-facing response
    # ========================================================

    return render_grounded_response(
        response=structured_response,
        evidence_cards=evidence_cards,
        assessment_scope=assessment_scope,
    )


# ============================================================
# Main chat processor
# ============================================================

def process_chat(
    conversation_id: str,
    message: str,
) -> Dict[str, Any]:
    """
    Main conversational entry point.
    """

    session = get_or_create_session(
        conversation_id
    )

    # ========================================================
    # 1. Store user message
    # ========================================================

    session.messages.append(
        {
            "role": "user",
            "content": message,
        }
    )

    # ========================================================
    # 2. Extract / update environmental state
    # ========================================================

    updated_state = extract_environment(
        message=message,
        previous_state=(
            session.environmental_state
        ),
    )

    session.environmental_state = (
        updated_state
    )

    # ========================================================
    # 3. Check required information
    # ========================================================

    missing_information = (
        get_missing_information(
            updated_state
        )
    )

    if missing_information:

        question = (
            build_clarifying_question(
                missing_information
            )
        )

        session.messages.append(
            {
                "role": "assistant",
                "content": question,
            }
        )

        return {
            "status": (
                "needs_clarification"
            ),

            "conversation_id": (
                conversation_id
            ),

            "message": question,

            "environment": (
                updated_state.model_dump()
            ),

            "missing_information": (
                missing_information
            ),

            "conversation_turns": (
                len(session.messages)
            ),
        }

    # ========================================================
    # 4. Run deterministic reasoning pipeline
    # ========================================================

    reasoning = run_reasoning(
        updated_state
    )

    # ========================================================
    # 5. Determine assessment scope
    # ========================================================

    has_species_richness = (
        updated_state
        .biodiversity
        .species_richness
        is not None
    )

    has_habitat_diversity = (
        updated_state
        .biodiversity
        .habitat_diversity
        is not None
    )

    assessment_scope = (
        "full"
        if (
            has_species_richness
            and has_habitat_diversity
        )
        else "preliminary"
    )

    # ========================================================
    # 6. Build focused evidence cards
    # ========================================================

    evidence_cards = (
        build_evidence_cards(
            reasoning
        )
    )

    # ========================================================
    # 7. Generate grounded response
    # ========================================================

    final_message = (
        generate_final_response(
            state=updated_state,
            reasoning=reasoning,
            evidence_cards=evidence_cards,
            assessment_scope=(
                assessment_scope
            ),
        )
    )

    # ========================================================
    # 8. Store assistant response
    # ========================================================

    session.messages.append(
        {
            "role": "assistant",
            "content": final_message,
        }
    )

    # ========================================================
    # 9. Build analysis output
    # ========================================================

    analysis = reasoning[
        "analysis"
    ]

    # ========================================================
    # 10. Return API response
    # ========================================================

    return {
        "status": "completed",

        "conversation_id": (
            conversation_id
        ),

        "assessment_scope": (
            assessment_scope
        ),

        "message": final_message,

        "environment": (
            updated_state.model_dump()
        ),

        "missing_information": (
            missing_information
        ),

        "reasoning": {
            "findings": [
                {
                    "title": finding.title,
                    "severity": finding.severity,
                    "explanation": (
                        finding.explanation
                    ),
                    "variables": (
                        finding.variables
                    ),
                }
                for finding in (
                    analysis.findings
                )
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
                for relationship in (
                    analysis.relationships
                )
            ],

            "knowledge_queries": (
                reasoning[
                    "knowledge_queries"
                ]
            ),

            "selected_intervention": (
                reasoning[
                    "selected_intervention"
                ]
            ),

            "candidate_interventions": (
                reasoning[
                    "candidate_interventions"
                ]
            ),
        },

        "evidence_cards": evidence_cards,

        "conversation_turns": (
            len(session.messages)
        ),
    }