from backend.models.environmental_state import EnvironmentalState


def build_environmental_queries(
    state: EnvironmentalState,
) -> list[str]:
    """
    Build focused semantic-search queries from the
    environmental variables supplied by the user.

    The goal is to retrieve evidence for multiple
    environmental dimensions instead of relying on
    one broad query.
    """

    queries: list[str] = []

    # -----------------------------------------------------
    # Soil
    # -----------------------------------------------------

    soil_terms: list[str] = []

    if state.soil.organic_carbon is not None:
        soil_terms.append(
            f"soil organic carbon {state.soil.organic_carbon}%"
        )

    if state.soil.ph is not None:
        soil_terms.append(
            f"soil pH {state.soil.ph}"
        )

    if state.soil.moisture:
        soil_terms.append(
            f"soil moisture {state.soil.moisture}"
        )

    if soil_terms:
        queries.append(
            " ".join(soil_terms)
            + " soil health agriculture"
        )

    # -----------------------------------------------------
    # Climate / water
    # -----------------------------------------------------

    climate_terms: list[str] = []

    if state.climate.rainfall:
        climate_terms.append(
            f"rainfall {state.climate.rainfall}"
        )

    if state.climate.temperature:
        climate_terms.append(
            f"temperature {state.climate.temperature}"
        )

    if climate_terms:
        queries.append(
            " ".join(climate_terms)
            + " water availability agricultural ecosystems"
        )

    # -----------------------------------------------------
    # Land use
    # -----------------------------------------------------

    land_terms: list[str] = []

    if state.land_use.crop:
        land_terms.append(
            f"crop {state.land_use.crop}"
        )

    if state.land_use.system:
        land_terms.append(
            f"land system {state.land_use.system}"
        )

    if state.land_use.land_use_type:
        land_terms.append(
            f"land use {state.land_use.land_use_type}"
        )

    if land_terms:
        queries.append(
            " ".join(land_terms)
            + " biodiversity habitat diversity"
        )

    # -----------------------------------------------------
    # Biodiversity
    # -----------------------------------------------------

    biodiversity_terms: list[str] = []

    if state.biodiversity.species_richness:
        biodiversity_terms.append(
            f"species richness {state.biodiversity.species_richness}"
        )

    if state.biodiversity.habitat_diversity:
        biodiversity_terms.append(
            f"habitat diversity {state.biodiversity.habitat_diversity}"
        )

    if biodiversity_terms:
        queries.append(
            " ".join(biodiversity_terms)
            + " ecosystem biodiversity conservation"
        )

    # -----------------------------------------------------
    # Human impact
    # -----------------------------------------------------

    impact_terms: list[str] = []

    if state.human_impact.pollution:
        impact_terms.append(
            f"pollution {state.human_impact.pollution}"
        )

    if (
    state.human_impact.deforestation
    and state.human_impact.deforestation.lower() != "none"
):
        impact_terms.append(
        f"deforestation {state.human_impact.deforestation}"
    )

    if impact_terms:
        queries.append(
            " ".join(impact_terms)
            + " biodiversity ecosystem impact"
        )

    # -----------------------------------------------------
    # Cross-variable query
    # -----------------------------------------------------

    cross_variable_terms: list[str] = []

    if state.soil.organic_carbon is not None:
        cross_variable_terms.append(
            "soil organic carbon"
        )

    if state.climate.rainfall:
        cross_variable_terms.append(
            "rainfall"
        )

    if state.land_use.system:
        cross_variable_terms.append(
            state.land_use.system
        )

    if (
        state.biodiversity.species_richness
        or state.biodiversity.habitat_diversity
    ):
        cross_variable_terms.append(
            "biodiversity"
        )

    if len(cross_variable_terms) >= 3:

        queries.append(
            " ".join(cross_variable_terms)
            + " environmental management interactions"
        )

    return queries