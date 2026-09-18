from dataclasses import dataclass

from backend.models.environmental_state import EnvironmentalState
from backend.reasoning.multi_metric import EnvironmentalAnalysis


# ---------------------------------------------------------
# Candidate intervention
# ---------------------------------------------------------

@dataclass(frozen=True)
class Intervention:
    name: str
    description: str
    target_variables: tuple[str, ...]
    keywords: tuple[str, ...]
    time_horizon: str


@dataclass
class RankedIntervention:
    intervention: Intervention
    base_score: float
    matched_variables: list[str]
    evidence_queries: list[str]


# ---------------------------------------------------------
# Intervention library
# ---------------------------------------------------------

INTERVENTIONS = [

    Intervention(
        name="Cover crops",
        description=(
            "Introduce suitable cover crops between or alongside "
            "production cycles where locally appropriate."
        ),
        target_variables=(
            "land_use",
            "crop_system",
            "soil_organic_carbon",
            "soil_moisture",
            "species_richness",
            "habitat_diversity",
        ),
        keywords=(
            "cover crops",
            "soil organic carbon",
            "soil moisture",
            "vegetation cover",
            "biodiversity",
        ),
        time_horizon="medium term",
    ),

    Intervention(
        name="Crop rotation",
        description=(
            "Move away from continuous monoculture by rotating "
            "crops with an appropriate local sequence."
        ),
        target_variables=(
            "land_use",
            "crop_system",
            "soil_organic_carbon",
            "species_richness",
            "habitat_diversity",
        ),
        keywords=(
            "crop rotation",
            "monoculture",
            "soil organic carbon",
            "crop diversification",
            "biodiversity",
            "species diversity",
        ),
        time_horizon="medium term",
    ),

    Intervention(
        name="Intercropping",
        description=(
            "Introduce a complementary crop with the primary crop "
            "where water and agronomic conditions permit."
        ),
        target_variables=(
            "land_use",
            "crop_system",
            "soil_organic_carbon",
            "species_richness",
            "habitat_diversity",
        ),
        keywords=(
            "intercropping",
            "mixed planting",
            "crop diversity",
            "biodiversity",
            "soil organic carbon",
        ),
        time_horizon="medium term",
    ),

    Intervention(
        name="Agroforestry",
        description=(
            "Integrate suitable trees or woody vegetation into "
            "the agricultural landscape where locally appropriate."
        ),
        target_variables=(
            "land_use",
            "soil_organic_carbon",
            "soil_moisture",
            "species_richness",
            "habitat_diversity",
        ),
        keywords=(
            "agroforestry",
            "tree-based systems",
            "soil organic carbon",
            "soil structure",
            "water infiltration",
            "biodiversity",
            "habitat",
        ),
        time_horizon="long term",
    ),

    Intervention(
        name="Conservation farming",
        description=(
            "Consider reduced or no-tillage, residue retention "
            "and related soil-conservation practices where suitable."
        ),
        target_variables=(
            "soil_organic_carbon",
            "soil_moisture",
        ),
        keywords=(
            "conservation farming",
            "no-till",
            "zero-tillage",
            "residue retention",
            "soil organic carbon",
            "soil moisture",
            "water infiltration",
        ),
        time_horizon="medium term",
    ),
]


# ---------------------------------------------------------
# Environmental variables available in the user's input
# ---------------------------------------------------------

def get_active_variables(
    state: EnvironmentalState,
) -> set[str]:

    active_variables: set[str] = set()

    if state.soil.organic_carbon is not None:
        active_variables.add(
            "soil_organic_carbon"
        )

    if state.soil.moisture:
        active_variables.add(
            "soil_moisture"
        )

    if state.soil.ph is not None:
        active_variables.add(
            "soil_ph"
        )

    if state.climate.rainfall:
        active_variables.add(
            "rainfall"
        )

    if state.climate.temperature:
        active_variables.add(
            "temperature"
        )

    if state.land_use.system:
        active_variables.add(
            "crop_system"
        )

    if state.land_use.land_use_type:
        active_variables.add(
            "land_use"
        )

    if state.land_use.crop:
        active_variables.add(
            "crop"
        )

    if state.biodiversity.species_richness:
        active_variables.add(
            "species_richness"
        )

    if state.biodiversity.habitat_diversity:
        active_variables.add(
            "habitat_diversity"
        )

    if state.human_impact.pollution:
        active_variables.add(
            "pollution"
        )

    if state.human_impact.deforestation:
        active_variables.add(
            "deforestation"
        )

    return active_variables


# ---------------------------------------------------------
# Score intervention
# ---------------------------------------------------------

def score_intervention(
    intervention: Intervention,
    state: EnvironmentalState,
    analysis: EnvironmentalAnalysis,
) -> RankedIntervention:

    active_variables = get_active_variables(
        state
    )

    matched_variables = sorted(
        set(
            intervention.target_variables
        )
        & active_variables
    )

    # -----------------------------------------------------
    # Base variable score
    # -----------------------------------------------------

    variable_score = (
        len(matched_variables) * 2.0
    )

    # -----------------------------------------------------
    # Multi-metric relationship bonus
    # -----------------------------------------------------

    relationship_score = 0.0

    for relationship in analysis.relationships:

        overlap = (
            set(relationship.variables)
            & set(intervention.target_variables)
        )

        if overlap:
            relationship_score += (
                len(overlap) * 1.5
            )

    # -----------------------------------------------------
    # Evidence search queries
    # -----------------------------------------------------

    evidence_queries = list(
        intervention.keywords
    )

    # -----------------------------------------------------
    # Final base score
    # -----------------------------------------------------

    base_score = (
        variable_score
        + relationship_score
    )

    return RankedIntervention(
        intervention=intervention,
        base_score=base_score,
        matched_variables=matched_variables,
        evidence_queries=evidence_queries,
    )


# ---------------------------------------------------------
# Rank interventions before evidence validation
# ---------------------------------------------------------

def rank_interventions(
    state: EnvironmentalState,
    analysis: EnvironmentalAnalysis,
) -> list[RankedIntervention]:

    ranked = [
        score_intervention(
            intervention,
            state,
            analysis,
        )
        for intervention in INTERVENTIONS
    ]

    ranked.sort(
        key=lambda item: item.base_score,
        reverse=True,
    )

    return ranked