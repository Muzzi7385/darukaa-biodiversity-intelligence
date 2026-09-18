import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

print("MODEL:", model)
print("API KEY LOADED:", bool(api_key))

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from .env")

client = Groq(
    api_key=api_key,
    timeout=30.0,
)

try:
    print("\nSending minimal Groq request...\n")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Say hello in one sentence."
            }
        ],
        max_completion_tokens=100,
    )

    print("✅ GROQ REQUEST SUCCEEDED")
    print("\nRESPONSE:")
    print(response.choices[0].message.content)

except Exception as e:
    print("\n❌ GROQ REQUEST FAILED")
    print(type(e).__name__)
    print(repr(e))
