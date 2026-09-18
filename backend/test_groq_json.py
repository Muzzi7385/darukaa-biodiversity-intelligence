import json
import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

print("MODEL:", model)
print("API KEY LOADED:", bool(api_key))

client = Groq(
    api_key=api_key,
    timeout=30.0,
)

prompt = """
Return a JSON object.

Use exactly this structure:

{
  "message": "Hello",
  "evidence_ids": ["E1"]
}

Return only JSON.
"""


try:

    print("\nSending JSON-mode request...\n")

    response = client.chat.completions.create(
        model=model,

        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],

        response_format={
            "type": "json_object"
        },

        reasoning_format="hidden",

        reasoning_effort="low",

        max_completion_tokens=2000,
    )

    content = (
        response.choices[0]
        .message
        .content
        or ""
    ).strip()

    print("✅ JSON MODE REQUEST SUCCEEDED")

    print("\nRAW RESPONSE:")
    print(content)

    print("\nPARSED JSON:")

    parsed = json.loads(content)

    print(
        json.dumps(
            parsed,
            indent=2
        )
    )


except Exception as e:

    print("\n❌ JSON MODE REQUEST FAILED")

    print(
        "TYPE:",
        type(e).__name__
    )

    print(
        "ERROR:",
        repr(e)
    )

    body = getattr(
        e,
        "body",
        None
    )

    if body:

        print("\nERROR BODY:")

        print(
            json.dumps(
                body,
                indent=2,
                default=str
            )
        )
