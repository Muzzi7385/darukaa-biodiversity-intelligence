from backend.services.environment_extractor import extract_environment


message_1 = """
I have a wheat farm in a semi-arid region.
"""

state_1 = extract_environment(message_1)

print("\nFIRST MESSAGE:\n")
print(state_1.model_dump_json(indent=2))


message_2 = """
The farm uses continuous monoculture and rainfall is low.
"""

state_2 = extract_environment(
    message_2,
    previous_state=state_1,
)

print("\nAFTER SECOND MESSAGE:\n")
print(state_2.model_dump_json(indent=2))