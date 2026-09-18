import json
import os
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

from backend.models.environmental_state import EnvironmentalState


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. Add it to your .env file."
    )

client = Groq(api_key=GROQ_API_KEY)


# =========================================================
# Environmental extraction structure
# =========================================================

ENVIRONMENT_SCHEMA = {
    "region": None,
    "soil": {
        "ph": None,
        "organic_carbon": None,
        "moisture": None,
    },
    "land_use": {
        "land_use_type": None,
        "crop": None,
        "system": None,
    },
    "biodiversity": {
        "species_richness": None,
        "habitat_diversity": None,
    },
    "climate": {
        "temperature": None,
        "rainfall": None,
    },
    "human_impact": {
        "pollution": None,
        "deforestation": None,
    },
}


# =========================================================
# Deterministic normalization
# =========================================================

def normalize_extracted_data(
    data: dict,
) -> dict:
    """
    Clean up common ambiguities in LLM extraction.

    The LLM understands the user's language, while this
    layer makes sure extracted values conform to the
    application schema.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Extracted environmental data must be a JSON object."
        )

    # -----------------------------------------------------
    # Ensure nested objects exist
    # -----------------------------------------------------

    data.setdefault(
        "soil",
        {},
    )

    data.setdefault(
        "land_use",
        {},
    )

    data.setdefault(
        "biodiversity",
        {},
    )

    data.setdefault(
        "climate",
        {},
    )

    data.setdefault(
        "human_impact",
        {},
    )

    land_use = data.get("land_use") or {}

    land_use_type = land_use.get(
        "land_use_type"
    )

    system = land_use.get(
        "system"
    )

    # -----------------------------------------------------
    # Cropping-system normalization
    # -----------------------------------------------------

    system_aliases = {
        "monoculture": "monoculture",
        "mono culture": "monoculture",
        "single crop": "monoculture",
        "single-crop": "monoculture",
        "continuous monoculture": "monoculture",

        "crop rotation": "crop rotation",
        "crop rotations": "crop rotation",
        "rotation": "crop rotation",
        "rotational cropping": "crop rotation",

        "intercropping": "intercropping",
        "inter cropping": "intercropping",
        "mixed cropping": "intercropping",
        "mixed crop": "intercropping",
    }

    # -----------------------------------------------------
    # Case 1:
    # LLM correctly put the agricultural system into
    # `system`
    # -----------------------------------------------------

    if isinstance(
        system,
        str,
    ):
        normalized_system = (
            system.strip().lower()
        )

        if normalized_system in system_aliases:
            land_use["system"] = (
                system_aliases[
                    normalized_system
                ]
            )

    # -----------------------------------------------------
    # Case 2:
    # LLM placed cropping system into land_use_type
    #
    # Example:
    # land_use_type = "monoculture"
    # system = None
    #
    # Move it into `system`.
    # -----------------------------------------------------

    if (
        isinstance(
            land_use_type,
            str,
        )
        and not land_use.get("system")
    ):
        normalized_land_use_type = (
            land_use_type.strip().lower()
        )

        if (
            normalized_land_use_type
            in system_aliases
        ):
            land_use["system"] = (
                system_aliases[
                    normalized_land_use_type
                ]
            )

            land_use["land_use_type"] = (
                "agriculture"
            )

    # -----------------------------------------------------
    # If a crop exists and no broad land-use type exists,
    # infer agriculture.
    #
    # This is a structural inference, not a scientific
    # recommendation.
    # -----------------------------------------------------

    if (
        land_use.get("crop")
        and not land_use.get(
            "land_use_type"
        )
    ):
        land_use[
            "land_use_type"
        ] = "agriculture"

    data["land_use"] = land_use

    # -----------------------------------------------------
    # Region normalization
    # -----------------------------------------------------

    region = data.get(
        "region"
    )

    if isinstance(
        region,
        str,
    ):
        region = region.strip()

        removable_suffixes = [
            " region",
            " area",
            " zone",
        ]

        lower_region = (
            region.lower()
        )

        for suffix in removable_suffixes:
            if lower_region.endswith(
                suffix
            ):
                region = region[
                    : -len(suffix)
                ].strip()

                break

        data["region"] = region

    # -----------------------------------------------------
    # Climate normalization
    #
    # Keep these values flexible:
    # 450
    # "450"
    # "450 mm"
    # "low"
    # "32"
    # "32°C"
    #
    # EnvironmentalState converts them consistently.
    # -----------------------------------------------------

    climate = data.get(
        "climate"
    ) or {}

    if climate.get(
        "temperature"
    ) is not None:
        climate[
            "temperature"
        ] = str(
            climate[
                "temperature"
            ]
        )

    if climate.get(
        "rainfall"
    ) is not None:
        climate[
            "rainfall"
        ] = str(
            climate[
                "rainfall"
            ]
        )

    data["climate"] = climate

    return data


# =========================================================
# Groq extraction
# =========================================================

def extract_environment(
    message: str,
    previous_state: Optional[
        EnvironmentalState
    ] = None,
) -> EnvironmentalState:
    """
    Convert a user's natural-language environmental
    description into EnvironmentalState.

    The LLM is responsible for understanding the user's
    language.

    Deterministic normalization is responsible for keeping
    the extracted structure consistent.

    Pydantic performs the final validation.
    """

    # -----------------------------------------------------
    # Previous state
    # -----------------------------------------------------

    if previous_state is not None:
        previous_environment = (
            previous_state.model_dump()
        )
    else:
        previous_environment = (
            ENVIRONMENT_SCHEMA
        )

    # -----------------------------------------------------
    # System prompt
    # -----------------------------------------------------

    system_prompt = f"""
You are the environmental information extraction
component of a biodiversity intelligence system.

Your job is ONLY to extract environmental information
from the user's message.

Do NOT provide recommendations.
Do NOT explain the environmental situation.
Do NOT answer the user's environmental question.

Rules:

1. Never invent information.
2. Never create numeric values that the user did not provide.
3. Preserve information from previous_environment.
4. New information can update previous information when
   the user clearly corrects it.
5. Use null for unknown information.
6. Return ONLY valid JSON.
7. Do not add fields outside the required structure.
8. Preserve quantitative values explicitly provided by the user.

IMPORTANT FIELD DEFINITIONS:

land_use.land_use_type describes the broad type of land use.

Examples:
- agriculture
- forest
- grassland
- wetland

land_use.system describes the agricultural cropping system.

Examples:
- monoculture
- crop rotation
- intercropping

Therefore:

"we grow only wheat"
→ system = "monoculture"

"we rotate wheat and legumes"
→ system = "crop rotation"

"we grow wheat and legumes together"
→ system = "intercropping"

Do NOT put "monoculture",
"crop rotation", or
"intercropping"
into land_use_type.

For soil moisture use one of:
- very_low
- low
- moderate
- high
- very_high

For pH:
- number between 0 and 14 only when explicitly provided.

For organic_carbon:
- number only when explicitly provided.

For temperature:
- preserve the value exactly when explicitly provided.
- a numeric value is allowed, such as 32.
- a textual value is allowed, such as "high".
- a value with units is allowed, such as "32°C".
- do not convert units.

For rainfall:
- preserve the value exactly when explicitly provided.
- a numeric value is allowed, such as 450.
- a textual value is allowed, such as "low".
- a value with units is allowed, such as "450 mm".
- do not convert units.

For biodiversity:
- only record species richness or habitat diversity when
  explicitly mentioned.
- never infer a missing biodiversity measurement.

For human impact:
- only record pollution or deforestation when
  explicitly mentioned.
- do not invent severity levels.

Previous structured state:

{json.dumps(
    previous_environment,
    indent=2,
)}

Return exactly this structure:

{json.dumps(
    ENVIRONMENT_SCHEMA,
    indent=2,
)}
"""

    # -----------------------------------------------------
    # User prompt
    # -----------------------------------------------------

    user_prompt = f"""
Current user message:

{message}

Extract only information explicitly supported by
the user's message.

Merge the newly extracted information with
previous_environment.

Preserve previous values unless the user clearly
provides updated information.

Return ONLY the JSON object.
"""

    try:

        # -------------------------------------------------
        # Groq request
        #
        # json_object is intentionally used here instead
        # of strict json_schema because quantitative
        # climate values may naturally be returned as
        # numbers by the model.
        # -------------------------------------------------

        response = client.chat.completions.create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            response_format={
                "type": "json_object"
            },

            reasoning_format="hidden",
            reasoning_effort="low",

            max_completion_tokens=1000,
        )

        # -------------------------------------------------
        # Read model response
        # -------------------------------------------------

        content = (
            response.choices[0]
            .message
            .content
        )

        if not content:
            raise ValueError(
                "Groq returned an empty response."
            )

        # -------------------------------------------------
        # Parse JSON
        # -------------------------------------------------

        parsed = json.loads(
            content
        )

        if not isinstance(
            parsed,
            dict,
        ):
            raise ValueError(
                "Groq response must be a JSON object."
            )

        # -------------------------------------------------
        # Deterministic cleanup
        # -------------------------------------------------

        normalized = (
            normalize_extracted_data(
                parsed
            )
        )

        # -------------------------------------------------
        # Final Pydantic validation
        # -------------------------------------------------

        state = (
            EnvironmentalState.model_validate(
                normalized
            )
        )

        return state

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            f"Groq returned invalid JSON: {exc}"
        ) from exc

    except Exception as exc:

        raise RuntimeError(
            f"Environmental extraction failed: {exc}"
        ) from exc