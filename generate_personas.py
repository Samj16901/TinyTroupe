import sys
sys.path.insert(0, '.')  # Add project root to Python path
import tinytroupe # Initializes configuration, logging, etc.
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.agent import TinyPerson
import os

# Define a context for persona generation
context = "Individuals living in a near-future society grappling with technological advancements and social change. Some are excited by the possibilities, others are wary of the consequences, and many are just trying to adapt."

# Create a TinyPersonFactory instance
factory = TinyPersonFactory(context_text=context)

# Define particularities for the new personas
persona_particularities = [
    {"name_hint": "Elena_Vargas", "particularity": "A seasoned female journalist in her late 40s, known for her fearless investigative work into corporate scandals and government cover-ups. She's cynical but deeply committed to truth and justice."},
    {"name_hint": "Dr_Anya_Sharma", "particularity": "A brilliant but conflicted young female bio-engineer in her early 30s, working on cutting-edge gene-editing technology. She faces profound ethical dilemmas about the potential applications and misuse of her work."},
    {"name_hint": "Professor_Alaric_Blackwood", "particularity": "An eccentric elderly male historian in his late 70s, specializing in ancient, forgotten civilizations and esoteric knowledge. He's a recluse, often lost in his research, and possesses a dry wit."}
]

# Generate and save each persona
output_dir = "examples/agents"
os.makedirs(output_dir, exist_ok=True)

for p_info in persona_particularities:
    print(f"Generating persona for: {p_info['name_hint']}")
    # Attempt to generate a unique agent. The factory checks existing names.
    # We pass a high temperature for more creative/varied outputs.
    new_persona = factory.generate_person(
        agent_particularities=p_info['particularity'],
        temperature=1.7, # Higher temperature for more diverse/creative output
        presence_penalty=0.5 # Encourage new topics
    )

    if new_persona:
        # Sanitize the generated name for use as a filename if necessary,
        # or use the name_hint if the generated name is problematic for a filename.
        # For simplicity here, we'll try to use the generated name directly
        # but in a real scenario, more robust sanitization might be needed.
        file_name = f"{new_persona.name.replace(' ', '_').replace('.', '')}.agent.json"
        file_path = os.path.join(output_dir, file_name)

        # Ensure the agent name is not already used by an existing file (paranoid check)
        idx = 0
        original_file_path = file_path
        while os.path.exists(file_path):
            idx += 1
            file_name = f"{new_persona.name.replace(' ', '_').replace('.', '')}_{idx}.agent.json"
            file_path = os.path.join(output_dir, file_name)

        if idx > 0:
            print(f"Warning: Original filename {original_file_path} existed. Saved as {file_path}")

        new_persona.save_specification(file_path)
        print(f"Saved: {file_path}")
        print(f"Minibio: {new_persona.minibio()}")
    else:
        print(f"Failed to generate persona for: {p_info['name_hint']}")

print("Persona generation complete.")
