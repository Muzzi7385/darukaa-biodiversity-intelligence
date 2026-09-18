# backend/reasoning/multi_metric.py

from dataclasses import dataclass, field
from typing import List
import re

from backend.models.environmental_state import EnvironmentalState


# ============================================================
# Data structures
# ============================================================

@dataclass
class EnvironmentalFinding:
    title: str
    severity: str
    explanation: str
    variables: List[str] = field(default_factory=list)


@dataclass
class EnvironmentalRelationship:
    relationship: str
    explanation: str
    variables: List[str] = field(default_factory=list)


@dataclass
class EnvironmentalAnalysis:
    findings: List[EnvironmentalFinding] = field(
        default_factory=list
    )

    relationships: List[EnvironmentalRelationship] = field(
        default_factory=list
    )


# ============================================================
# Normalization helpers
# ============================================================

def normalize(value) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def is_low(value) -> bool:
    value = normalize(value)

    low_terms = {
        "very low",
        "very_low",
        "low",
        "poor",
        "limited",
        "scarce",
        "deficient",
    }

    return value in low_terms or any(
        term in value
        for term in [
            "very low",
            "very_low",
            "low",
            "poor",
            "scarce",
        ]
    )


def is_high(value) -> bool:
    value = normalize(value)

    high_terms = {
        "high",
        "very high",
        "very_high",
        "severe",
        "intense",
    }

    return value in high_terms or any(
        term in value
        for term in [
            "high",
            "very high",
            "very_high",
            "severe",
            "intense",
        ]
    )


def parse_numeric(value):
    """
    Extract the first numeric value from a string.

    Examples:
        "450 mm annually" -> 450.0
        "32°C" -> 32.0
        "0.4%" -> 0.4
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        text,
    )

    if not match:
        return None

    return float(match.group())


def is_low_rainfall(value) -> bool:
    """
    Prototype classification only.

    The 500 mm threshold is a simplified prototype
    rule and is not a universal ecological threshold.
    """

    normalized = normalize(value)

    if is_low(normalized):
        return True

    numeric = parse_numeric(value)

    if numeric is not None:
        return numeric < 500

    return False


def is_high_temperature(value) -> bool:
    """
    Prototype classification only.

    The 30°C threshold is context dependent and
    should not be treated as a universal threshold.
    """

    normalized = normalize(value)

    if is_high(normalized):
        return True

    numeric = parse_numeric(value)

    if numeric is not None:
        return numeric >= 30

    return False


# ============================================================
# Main analysis
# ============================================================

def analyze_environment(
    state: EnvironmentalState,
) -> EnvironmentalAnalysis:

    findings: List[EnvironmentalFinding] = []
    relationships: List[EnvironmentalRelationship] = []

    # --------------------------------------------------------
    # Extract values
    # --------------------------------------------------------

    moisture = normalize(
        state.soil.moisture
    )

    rainfall = normalize(
        state.climate.rainfall
    )

    temperature = normalize(
        state.climate.temperature
    )

    crop = normalize(
        state.land_use.crop
    )

    land_use_type = normalize(
        state.land_use.land_use_type
    )

    system = normalize(
        state.land_use.system
    )

    species_richness = normalize(
        state.biodiversity.species_richness
    )

    habitat_diversity = normalize(
        state.biodiversity.habitat_diversity
    )

    pollution = normalize(
        state.human_impact.pollution
    )

    deforestation = normalize(
        state.human_impact.deforestation
    )

    soc = state.soil.organic_carbon
    ph = state.soil.ph


    # ========================================================
    # FINDINGS
    # ========================================================

    # --------------------------------------------------------
    # Soil moisture
    # --------------------------------------------------------

    if is_low(moisture):
        findings.append(
            EnvironmentalFinding(
                title="Low soil moisture",
                severity="high",
                explanation=(
                    "The reported soil moisture is low, "
                    "indicating limited water availability "
                    "in the soil profile."
                ),
                variables=[
                    "soil.moisture"
                ],
            )
        )


    # --------------------------------------------------------
    # Rainfall
    # --------------------------------------------------------

    if is_low_rainfall(
        state.climate.rainfall
    ):
        findings.append(
            EnvironmentalFinding(
                title="Low rainfall",
                severity="high",
                explanation=(
                    "The reported rainfall is low, "
                    "indicating a water-limited climatic "
                    "context."
                ),
                variables=[
                    "climate.rainfall"
                ],
            )
        )


    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    if is_high_temperature(
        state.climate.temperature
    ):
        findings.append(
            EnvironmentalFinding(
                title="High temperature",
                severity="moderate",
                explanation=(
                    "The reported temperature is high "
                    "and may increase environmental "
                    "water stress."
                ),
                variables=[
                    "climate.temperature"
                ],
            )
        )


    # --------------------------------------------------------
    # Soil organic carbon
    # --------------------------------------------------------

    if (
        soc is not None
        and soc < 1.0
    ):
        findings.append(
            EnvironmentalFinding(
                title="Low soil organic carbon",
                severity="moderate",
                explanation=(
                    "The reported soil organic carbon "
                    "value falls below the prototype "
                    "threshold used by this assessment."
                ),
                variables=[
                    "soil.organic_carbon"
                ],
            )
        )


    # --------------------------------------------------------
    # pH
    # --------------------------------------------------------

    if ph is not None:

        if ph < 5.5 or ph > 8.5:
            findings.append(
                EnvironmentalFinding(
                    title="Potentially unsuitable soil pH",
                    severity="moderate",
                    explanation=(
                        f"The reported soil pH is {ph}, "
                        "which may limit suitability for "
                        "some crops or soil organisms."
                    ),
                    variables=[
                        "soil.ph"
                    ],
                )
            )


    # --------------------------------------------------------
    # Monoculture
    # --------------------------------------------------------

    is_monoculture = (
        "monoculture" in system
        or "single crop" in system
        or "single-crop" in system
    )

    if is_monoculture:
        findings.append(
            EnvironmentalFinding(
                title="Monoculture system",
                severity="moderate",
                explanation=(
                    "The reported production system is "
                    "monoculture, meaning the system is "
                    "centered on a single crop."
                ),
                variables=[
                    "land_use.system"
                ],
            )
        )


    # --------------------------------------------------------
    # Biodiversity
    # --------------------------------------------------------

    if species_richness:

        if is_low(species_richness):
            findings.append(
                EnvironmentalFinding(
                    title="Low species richness",
                    severity="high",
                    explanation=(
                        "The reported species richness is low."
                    ),
                    variables=[
                        "biodiversity.species_richness"
                    ],
                )
            )


    if habitat_diversity:

        if is_low(habitat_diversity):
            findings.append(
                EnvironmentalFinding(
                    title="Low habitat diversity",
                    severity="high",
                    explanation=(
                        "The reported habitat diversity is low."
                    ),
                    variables=[
                        "biodiversity.habitat_diversity"
                    ],
                )
            )


    # --------------------------------------------------------
    # Human impacts
    # --------------------------------------------------------

    if pollution:
        findings.append(
            EnvironmentalFinding(
                title="Pollution pressure",
                severity="moderate",
                explanation=(
                    f"Pollution is reported as "
                    f"'{state.human_impact.pollution}'."
                ),
                variables=[
                    "human_impact.pollution"
                ],
            )
        )


    # Only treat deforestation as a finding when it is
    # actually reported as present.
    if (
        deforestation
        and deforestation != "none"
    ):
        findings.append(
            EnvironmentalFinding(
                title="Deforestation pressure",
                severity="high",
                explanation=(
                    f"Deforestation is reported as "
                    f"'{state.human_impact.deforestation}'."
                ),
                variables=[
                    "human_impact.deforestation"
                ],
            )
        )


    # ========================================================
    # MULTI-METRIC RELATIONSHIPS
    # ========================================================

    # --------------------------------------------------------
    # Relationship 1:
    # Rainfall + soil moisture
    # --------------------------------------------------------

    if (
        is_low_rainfall(
            state.climate.rainfall
        )
        and is_low(moisture)
    ):
        relationships.append(
            EnvironmentalRelationship(
                relationship=(
                    "Rainfall ↔ Soil moisture"
                ),
                explanation=(
                    f"The reported rainfall "
                    f"({state.climate.rainfall}) occurs "
                    "alongside low soil moisture, indicating "
                    "a water-limited context. Limited "
                    "precipitation can constrain water "
                    "available to the soil and vegetation, "
                    "while low soil moisture provides direct "
                    "evidence of current water limitation."
                ),
                variables=[
                    "climate.rainfall",
                    "soil.moisture",
                ],
            )
        )


    # --------------------------------------------------------
    # Relationship 1B:
    # Temperature + soil moisture
    # --------------------------------------------------------

    if (
        is_high_temperature(
            state.climate.temperature
        )
        and is_low(moisture)
    ):
        relationships.append(
            EnvironmentalRelationship(
                relationship=(
                    "Temperature ↔ Soil moisture"
                ),
                explanation=(
                    f"The reported temperature "
                    f"({state.climate.temperature}) occurs "
                    "alongside low soil moisture. Higher "
                    "temperatures can increase evaporative "
                    "demand, which may place additional "
                    "pressure on soil water availability "
                    "when moisture is already limited."
                ),
                variables=[
                    "climate.temperature",
                    "soil.moisture",
                ],
            )
        )


    # --------------------------------------------------------
    # Relationship 2:
    # Rainfall + moisture + monoculture
    # --------------------------------------------------------

    if (
        is_low_rainfall(
            state.climate.rainfall
        )
        and is_low(moisture)
        and is_monoculture
    ):
        relationships.append(
            EnvironmentalRelationship(
                relationship=(
                    "Water availability ↔ Land-use system "
                    "↔ Biodiversity"
                ),
                explanation=(
                    "Low rainfall and low soil moisture "
                    "indicate water limitation, while "
                    "monoculture represents low crop-system "
                    "diversity. Together these conditions "
                    "create a potential pathway affecting "
                    "habitat and biodiversity outcomes. "
                    "Because biodiversity measurements may "
                    "not capture all ecological factors, "
                    "the biodiversity impact should be "
                    "interpreted cautiously."
                ),
                variables=[
                    "climate.rainfall",
                    "soil.moisture",
                    "land_use.system",
                    "biodiversity",
                ],
            )
        )


    # --------------------------------------------------------
    # Relationship 3:
    # Soil carbon + moisture
    # --------------------------------------------------------

    if (
        soc is not None
        and soc < 1.0
        and is_low(moisture)
    ):
        relationships.append(
            EnvironmentalRelationship(
                relationship=(
                    "Soil organic carbon ↔ Soil moisture"
                ),
                explanation=(
                    "Low soil organic carbon can be "
                    "associated with poorer soil structure "
                    "and reduced water-retention capacity. "
                    "When low soil organic carbon occurs "
                    "alongside low soil moisture, the "
                    "combination may increase water stress "
                    "and reduce resilience to rainfall "
                    "variability."
                ),
                variables=[
                    "soil.organic_carbon",
                    "soil.moisture",
                ],
            )
        )


    # --------------------------------------------------------
    # Relationship 4:
    # Soil carbon + moisture + land use
    # --------------------------------------------------------

    if (
        soc is not None
        and soc < 1.0
        and is_low(moisture)
        and (
            crop
            or land_use_type
            or system
        )
    ):
        relationships.append(
            EnvironmentalRelationship(
                relationship=(
                    "Soil health ↔ Water availability "
                    "↔ Land use"
                ),
                explanation=(
                    "Low soil organic carbon can be "
                    "associated with poorer soil structure "
                    "and reduced water-retention capacity. "
                    "Under low soil-moisture conditions, "
                    "this may increase water stress. "
                    "Because these conditions occur within "
                    "the reported agricultural land-use "
                    "system, soil management and land-use "
                    "decisions are interconnected."
                ),
                variables=[
                    "soil.organic_carbon",
                    "soil.moisture",
                    "land_use",
                ],
            )
        )


    # --------------------------------------------------------
    # Relationship 5:
    # Monoculture + biodiversity observations
    # --------------------------------------------------------

    if (
        is_monoculture
        and (
            is_low(species_richness)
            or is_low(habitat_diversity)
        )
    ):
        relationships.append(
            EnvironmentalRelationship(
                relationship=(
                    "Land-use diversity ↔ Biodiversity"
                ),
                explanation=(
                    "Monoculture reduces temporal crop "
                    "diversity and can simplify the resources "
                    "and habitat conditions available within "
                    "an agricultural system. Where species "
                    "richness and habitat diversity are also "
                    "reported as low, this suggests a "
                    "potential relationship between "
                    "simplified land use and biodiversity "
                    "condition."
                ),
                variables=[
                    "land_use.system",
                    "biodiversity.species_richness",
                    "biodiversity.habitat_diversity",
                ],
            )
        )


    # --------------------------------------------------------
    # Relationship 6:
    # Water + biodiversity when biodiversity exists
    # --------------------------------------------------------

    if (
        is_low(moisture)
        and (
            is_low(species_richness)
            or is_low(habitat_diversity)
        )
    ):
        relationships.append(
            EnvironmentalRelationship(
                relationship=(
                    "Water availability ↔ Biodiversity"
                ),
                explanation=(
                    "Low soil moisture indicates limited "
                    "water availability for vegetation and "
                    "other organisms. When this occurs "
                    "alongside low biodiversity indicators, "
                    "water limitation may contribute to "
                    "ecological stress, although the observed "
                    "biodiversity condition cannot be "
                    "attributed to water availability alone."
                ),
                variables=[
                    "soil.moisture",
                    "biodiversity",
                ],
            )
        )


    # --------------------------------------------------------
    # Relationship 7:
    # Land use + habitat diversity
    # --------------------------------------------------------

    if (
        system
        and habitat_diversity
    ):
        relationships.append(
            EnvironmentalRelationship(
                relationship=(
                    "Land-use system ↔ Habitat diversity"
                ),
                explanation=(
                    "The structure of the reported land-use "
                    "system can influence the variety of "
                    "habitat conditions present within the "
                    "agricultural landscape. Because habitat "
                    "diversity is reported as low, the "
                    "simplified land-use system should be "
                    "considered as a potential contributor "
                    "to reduced ecological habitat variety."
                ),
                variables=[
                    "land_use.system",
                    "biodiversity.habitat_diversity",
                ],
            )
        )


    # --------------------------------------------------------
    # Relationship 8:
    # Human impact + biodiversity
    # --------------------------------------------------------

    if (
        (
            pollution
            or (
                deforestation
                and deforestation != "none"
            )
        )
        and (
            species_richness
            or habitat_diversity
        )
    ):
        relationships.append(
            EnvironmentalRelationship(
                relationship=(
                    "Human impact ↔ Biodiversity"
                ),
                explanation=(
                    "The reported human-impact pressure "
                    "occurs alongside low biodiversity "
                    "indicators. This creates a potential "
                    "pathway through which human activities "
                    "may contribute to ecological stress, "
                    "although the available information does "
                    "not establish that the reported pressure "
                    "is the sole cause of the biodiversity "
                    "condition."
                ),
                variables=[
                    "human_impact",
                    "biodiversity",
                ],
            )
        )


    # ========================================================
    # Return analysis
    # ========================================================

    return EnvironmentalAnalysis(
        findings=findings,
        relationships=relationships,
    )