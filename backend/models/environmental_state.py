from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# =========================================================
# Numeric normalization helpers
# =========================================================

def parse_numeric_value(value):
    """
    Convert numeric values returned by the LLM into floats.

    Examples:
        7.8       -> 7.8
        "7.8"     -> 7.8
        "0.4%"    -> 0.4
        "0.4 %"   -> 0.4
        None      -> None
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        cleaned = value.strip()

        if not cleaned:
            return None

        # Remove percentage symbols for fields such as
        # soil organic carbon.
        cleaned = cleaned.replace("%", "")

        # Remove common textual suffixes if present.
        cleaned = cleaned.replace(
            "percent",
            "",
        ).strip()

        try:
            return float(cleaned)

        except ValueError:
            return value

    return value


# =========================================================
# Soil
# =========================================================

class SoilData(BaseModel):

    ph: Optional[float] = Field(
        default=None,
        ge=0,
        le=14,
    )

    organic_carbon: Optional[float] = Field(
        default=None,
        ge=0,
        description="Soil organic carbon percentage",
    )

    moisture: Optional[
        Literal[
            "very_low",
            "low",
            "moderate",
            "high",
            "very_high",
        ]
    ] = None

    @field_validator(
        "ph",
        mode="before",
    )
    @classmethod
    def normalize_ph(cls, value):
        return parse_numeric_value(value)

    @field_validator(
        "organic_carbon",
        mode="before",
    )
    @classmethod
    def normalize_organic_carbon(cls, value):
        return parse_numeric_value(value)


# =========================================================
# Land Use
# =========================================================

class LandUseData(BaseModel):

    land_use_type: Optional[str] = None
    crop: Optional[str] = None
    system: Optional[str] = None


# =========================================================
# Biodiversity
# =========================================================

class BiodiversityData(BaseModel):

    species_richness: Optional[str] = None
    habitat_diversity: Optional[str] = None


# =========================================================
# Climate
# =========================================================

class ClimateData(BaseModel):

    temperature: Optional[str] = None
    rainfall: Optional[str] = None

    @field_validator(
        "temperature",
        "rainfall",
        mode="before",
    )
    @classmethod
    def normalize_climate_values(cls, value):

        if value is None:
            return None

        return str(value)


# =========================================================
# Human Impact
# =========================================================

class HumanImpactData(BaseModel):

    pollution: Optional[str] = None
    deforestation: Optional[str] = None


# =========================================================
# Complete Environmental State
# =========================================================

class EnvironmentalState(BaseModel):

    region: Optional[str] = None

    soil: SoilData = Field(
        default_factory=SoilData
    )

    land_use: LandUseData = Field(
        default_factory=LandUseData
    )

    biodiversity: BiodiversityData = Field(
        default_factory=BiodiversityData
    )

    climate: ClimateData = Field(
        default_factory=ClimateData
    )

    human_impact: HumanImpactData = Field(
        default_factory=HumanImpactData
    )