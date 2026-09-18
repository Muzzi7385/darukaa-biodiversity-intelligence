# backend/services/groq_service.py

import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIStatusError,
    Groq,
    RateLimitError,
)


# ============================================================
# Configuration
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)


if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing from .env"
    )


client = Groq(
    api_key=GROQ_API_KEY,
    timeout=30.0,
)


# ============================================================
# Normal Groq text generation
# ============================================================

def ask_groq(
    prompt: str,
) -> str:
    """
    Normal text-generation request.
    """

    try:

        response = client.chat.completions.create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],

            reasoning_effort="low",
            include_reasoning=False,

            max_completion_tokens=1200,
        )

        return (
            response
            .choices[0]
            .message
            .content
            or ""
        ).strip()

    except RateLimitError as e:

        print(
            "\n❌ GROQ RATE LIMIT"
        )

        print(
            repr(e)
        )

        return (
            "Groq rate limit reached. "
            "Please try again shortly."
        )

    except APIStatusError as e:

        print(
            "\n❌ GROQ API ERROR"
        )

        print(
            "Status:",
            e.status_code,
        )

        body = getattr(
            e,
            "body",
            None,
        )

        if body:

            print(
                json.dumps(
                    body,
                    indent=2,
                    default=str,
                )
            )

        else:

            print(
                repr(e)
            )

        return (
            f"Groq API error "
            f"({e.status_code})."
        )

    except APIConnectionError as e:

        print(
            "\n❌ GROQ CONNECTION ERROR"
        )

        print(
            repr(e)
        )

        return (
            "Could not connect to Groq."
        )

    except Exception as e:

        print(
            "\n❌ GROQ ERROR"
        )

        print(
            repr(e)
        )

        return (
            "Unexpected Groq error."
        )


# ============================================================
# Structured JSON generation
# ============================================================

def ask_groq_json(
    prompt: str,
    schema_name: str,
    schema: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate a strict structured JSON response.

    Parameters:
        prompt:
            Prompt sent to the model.

        schema_name:
            Name of the JSON schema.

        schema:
            JSON schema generated from Pydantic.
    """

    try:

        response = client.chat.completions.create(
            model=GROQ_MODEL,

            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],

            # ------------------------------------------------
            # Strict JSON Schema output
            # ------------------------------------------------

            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },

            reasoning_effort="low",
            include_reasoning=False,

            max_completion_tokens=1800,
        )

        content = (
            response
            .choices[0]
            .message
            .content
            or ""
        ).strip()

        if not content:

            raise RuntimeError(
                "Groq returned empty structured output."
            )

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        try:

            parsed = json.loads(
                content
            )

        except json.JSONDecodeError as e:

            print(
                "\n❌ INVALID GROQ JSON"
            )

            print(
                "\nRAW OUTPUT:"
            )

            print(
                content
            )

            raise RuntimeError(
                "Groq returned invalid JSON."
            ) from e

        # ----------------------------------------------------
        # Ensure dictionary
        # ----------------------------------------------------

        if not isinstance(
            parsed,
            dict,
        ):

            raise RuntimeError(
                "Groq structured output "
                "must be a JSON object."
            )

        return parsed

    except RateLimitError as e:

        print(
            "\n❌ GROQ RATE LIMIT"
        )

        print(
            repr(e)
        )

        raise RuntimeError(
            "Groq rate limit reached. "
            "Please try again shortly."
        ) from e

    except APIStatusError as e:

        print(
            "\n❌ GROQ API ERROR"
        )

        print(
            "Status:",
            e.status_code,
        )

        body = getattr(
            e,
            "body",
            None,
        )

        print(
            "\nGROQ ERROR BODY:"
        )

        if body:

            print(
                json.dumps(
                    body,
                    indent=2,
                    default=str,
                )
            )

        else:

            print(
                repr(e)
            )

        raise RuntimeError(
            f"Groq API error "
            f"({e.status_code})."
        ) from e

    except APIConnectionError as e:

        print(
            "\n❌ GROQ CONNECTION ERROR"
        )

        print(
            repr(e)
        )

        raise RuntimeError(
            "Could not connect to Groq."
        ) from e

    except RuntimeError:
        raise

    except Exception as e:

        print(
            "\n❌ GROQ STRUCTURED OUTPUT ERROR"
        )

        print(
            repr(e)
        )

        raise RuntimeError(
            "Failed to generate "
            "structured response."
        ) from e