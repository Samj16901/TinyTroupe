import os

with open("README.md", "r") as f:
    readme_content = f.read()

cli_docs_section = """
## Command-Line Interface (CLI) Tool

This repository includes a basic command-line tool, `run_chat_cli.py`, located in the `examples` directory, to quickly run chat simulations between two agents without needing to write Python code directly.

### Usage

**1. List Available Agents:**

To see a list of predefined agent personas available in the `examples/agents/` directory:

```bash
python examples/run_chat_cli.py --list_agents
```

**2. Run a Chat Simulation:**

To run a simulation, you need to specify two agents, an initial prompt for the first agent, and optionally the number of simulation steps.

```bash
python examples/run_chat_cli.py --agent1 <Agent1Name> --agent2 <Agent2Name> --prompt "Your starting message for Agent1" --steps <NumberOfSteps>
```

**Example:**

```bash
python examples/run_chat_cli.py --agent1 Lisa --agent2 Oscar --prompt "Hi Oscar, what are you working on these days?" --steps 4
```

**Note:** Running simulations requires a valid OpenAI API key to be configured in your environment, as the agents use OpenAI models for generating responses. If the API key is not set up, the script will likely fail when attempting to make LLM calls.
"""

# Attempt to insert before a "Contributing" or "License" section, otherwise append.
insert_points = ["\n## Contributing", "\n## License"]
inserted = False
for point in insert_points:
    if point in readme_content:
        parts = readme_content.split(point, 1)
        readme_content = parts[0] + "\n" + cli_docs_section.strip() + "\n" + point + parts[1]
        inserted = True
        break
if not inserted:
    readme_content += "\n" + cli_docs_section

with open("README.md", "w") as f:
    f.write(readme_content)

print("README.md updated with CLI tool documentation.")
