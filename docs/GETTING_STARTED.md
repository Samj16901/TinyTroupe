# Getting Started with TinyTroupe

Welcome to TinyTroupe! This guide will help you get started with creating and running your first simulations.

## Introduction

TinyTroupe is a Python-based framework for creating and simulating small-scale multi-agent systems. It allows you to define agents (called `TinyPerson` instances) with distinct personas, memories, and behaviors, and then place them in a simulated environment (`TinyWorld`) to observe their interactions.

Main use cases include:
- Simulating social interactions and group dynamics.
- Generating synthetic data for training other models.
- Prototyping and testing game AI or chatbot personalities.
- Exploring emergent behaviors in small, controlled systems.

## Prerequisites

Before you begin, ensure you have the following:

- **Python 3.8 or higher:** You can download Python from [python.org](https://www.python.org/downloads/).
- **OpenAI API Key:** TinyTroupe uses OpenAI's language models (like GPT-3.5 or GPT-4) to power agent cognition. You'll need an API key from [OpenAI](https://platform.openai.com/signup/).
- **Git:** Required for installing directly from the GitHub repository. You can download Git from [git-scm.com](https://git-scm.com/downloads).

## Installation

You can install TinyTroupe directly from its GitHub repository using pip:

```bash
pip install git+https://github.com/microsoft/tinytroupe.git
```

This command will download and install the latest version of TinyTroupe along with its dependencies.

## Configuration

TinyTroupe requires you to configure your OpenAI API key and preferred model.

1.  **Locate or Create `config.ini`:**
    After installation, you might need to create a `config.ini` file. A good practice is to place it in a directory where you'll run your simulations, or in the `tinytroupe` library's root if you are developing the library itself. You can copy the `tinytroupe/config.ini` file from the library source (if you cloned the repository) or the `examples/config.ini` as a template.

    The library looks for `config.ini` in the following order:
    * Current working directory.
    * The directory of the script that's running.
    * The `tinytroupe` package directory.

2.  **Edit `config.ini`:**
    Open the `config.ini` file in a text editor. It should look something like this:

    ```ini
    [openai]
    api_key = YOUR_OPENAI_API_KEY
    # organization_id = YOUR_OPENAI_ORGANIZATION_ID (optional)
    # api_version = API_VERSION (optional, for Azure OpenAI)
    # api_base = API_ENDPOINT (optional, for Azure OpenAI or custom endpoints)
    default_model = gpt-3.5-turbo # Or your preferred model, e.g., gpt-4
    # default_embeddings_model = text-embedding-ada-002 (optional)

    [simulation]
    # cache_backend = default (options: default, sqlite, redis, or fully qualified class name)
    # cache_path = ./tinytroupe-cache.json (for default backend)
    # communication_display = True
    # communication_style = simplified
    ```

3.  **Set Your API Key:**
    Replace `YOUR_OPENAI_API_KEY` with your actual OpenAI API key.
    If you are part of an OpenAI organization, you can optionally add your `organization_id`.
    If using Azure OpenAI services, you'll need to provide `api_version` and `api_base`.

4.  **Choose a Model:**
    The `default_model` is set to `gpt-3.5-turbo` by default. You can change this to other models like `gpt-4` or `gpt-4-turbo-preview` if you have access and prefer them, but be mindful of different pricing and rate limits.

5.  **Save the file.**

TinyTroupe will automatically load these settings when you import and use its components.

## Your First Simulation

Let's create a simple simulation with two agents who meet and interact.

**Step 1: Import necessary classes**

Create a new Python file (e.g., `my_first_simulation.py`) and add the following imports:

```python
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld
from datetime import datetime, timedelta
```

**Step 2: Define your agents**

We'll create two agents: Alex, who is talkative, and Ben, who is quiet.

```python
# Create Alex - a talkative agent
alex = TinyPerson(name="Alex")
alex.define("age", 28)
alex.define("occupation", {"title": "Writer"})
alex.define("personality_traits", ["Outgoing", "Talkative", "Friendly"])
alex.define("personal_interests", ["Storytelling", "Meeting new people"])
alex.internalize_goal("Start a conversation with anyone new I meet.")

# Create Ben - a quiet agent
ben = TinyPerson(name="Ben")
ben.define("age", 32)
ben.define("occupation", {"title": "Librarian"})
ben.define("personality_traits", ["Introverted", "Observant", "Calm"])
ben.define("personal_interests", ["Reading", "Quiet places"])
ben.internalize_goal("Observe my surroundings and speak only when necessary.")
```

**Step 3: Create the world**

Now, let's create an environment for Alex and Ben.

```python
# Create a TinyWorld for our agents
world = TinyWorld(name="Quiet Park", initial_datetime=datetime(2024, 3, 15, 14, 0, 0))

# Add Alex and Ben to the world
world.add_agents([alex, ben])

# Make them aware of each other's presence
world.make_everyone_accessible() # Makes all agents in the world accessible to each other

# You can also set a general context for the world that agents will perceive
world.broadcast_context_change(["You are both in a quiet park on a sunny afternoon."])
```

**Step 4: Run the simulation**

Let's run the simulation for a few steps. Each step can represent a passage of time.

```python
print(f"Starting simulation in {world.name} at {world.current_datetime}")

# Run the simulation for 3 steps, with each step advancing time by 5 minutes
# Set TinyWorld.communication_display = True to see live interactions (default is True)
# TinyPerson.communication_display = True (default is True)
world.run(steps=3, timedelta_per_step=timedelta(minutes=5))

print(f"\nSimulation finished. Current time: {world.current_datetime}")
```

**Step 5: View the interaction log**

By default, TinyTroupe prints interactions to the console as they happen. If you want to review the full history after the simulation:

```python
print("\n--- Full Interaction Log ---")
# The pop_and_display_latest_communications method is primarily for real-time display.
# For a post-simulation log, you'd typically rely on the console output during the run,
# or implement custom logging if you need to save it to a file.

# However, each agent stores its own history:
print("\n--- Alex's Perspective ---")
alex.pp_current_interactions()

print("\n--- Ben's Perspective ---")
ben.pp_current_interactions()

# The world can also print a combined log of what its agents experienced:
print("\n--- World's Perspective (Combined Agent Logs) ---")
world.pp_current_interactions()
```
*(Note: For more advanced logging or saving interactions to a file, you would typically integrate Python's `logging` module or redirect console output.)*

## Understanding the Output

When you run the simulation, you'll see output similar to this (simplified):

```
Quiet Park step 1 of 3 (2024-03-15 14:00:00)
USER --> Alex: [INTERNAL_GOAL_FORMULATION]
          > Start a conversation with anyone new I meet.
USER --> Ben: [INTERNAL_GOAL_FORMULATION]
          > Observe my surroundings and speak only when necessary.
USER --> Alex: [CONTEXT_CHANGE]
          > You are both in a quiet park on a sunny afternoon.
USER --> Ben: [CONTEXT_CHANGE]
          > You are both in a quiet park on a sunny afternoon.
Alex acts: [TALK]
          > Hello there! Beautiful day to be in the park, isn't it? (Target: Ben)
Ben listens: [CONVERSATION]
          > Hello there! Beautiful day to be in the park, isn't it? (Source: Alex)
Ben acts: [TALK]
          > Indeed. (Target: Alex)
Alex listens: [CONVERSATION]
          > Indeed. (Source: Ben)
... and so on ...
```

-   **`Quiet Park step 1 of 3...`**: Indicates the current step and time in the simulation.
-   **`USER --> AgentName: [STIMULUS_TYPE]`**: Shows a stimulus being presented to an agent. `USER` here represents the simulation environment or an internal process. `STIMULUS_TYPE` can be `CONVERSATION`, `VISUAL`, `INTERNAL_GOAL_FORMULATION`, `CONTEXT_CHANGE`, etc.
-   **`AgentName acts: [ACTION_TYPE]`**: Shows an action performed by an agent. `ACTION_TYPE` can be `TALK`, `MOVE`, `DONE` (meaning the agent has no immediate further actions), etc. The content of the action and its target (if any) are also shown.
-   **`AgentName listens: [STIMULUS_TYPE]`**: This is a common pattern where one agent's `TALK` action becomes a `CONVERSATION` stimulus for another.

The interaction log helps you trace how agents perceive their environment and each other, and how they decide to act.

## Next Steps

Now that you've run your first simulation, here are some ways to continue exploring TinyTroupe:

-   **Explore the Examples:** The `examples/` directory in the GitHub repository contains various Jupyter notebooks showcasing different features and use cases (e.g., `simple_chat.ipynb`, `creating_and_validating_agents.ipynb`).
-   **Read the API Documentation:** For detailed information on classes and methods, refer to the API documentation (you can generate it from the source or find it online if available).
-   **Experiment:** Try modifying agent personas, adding more agents, or creating more complex scenarios.
-   **Customize Agents with Fragments:** Look into how `.fragment.json` files can be used to layer characteristics onto agents.
-   **Use Agent Factories:** For generating many diverse agents based on a theme, explore `TinyPersonFactory`.

## Troubleshooting

Here are a few common issues and how to address them:

-   **`openai.error.AuthenticationError: Incorrect API key provided`**:
    -   Ensure your OpenAI API key in `config.ini` is correct and active.
    -   Make sure there are no extra spaces or characters around the key.
    -   Verify that your OpenAI account has sufficient credits.

-   **`ModuleNotFoundError: No module named 'tinytroupe'`**:
    -   Make sure you have successfully installed TinyTroupe using `pip install git+https://github.com/microsoft/tinytroupe.git`.
    -   If you are running your script from within a cloned repository directory, ensure your Python environment can find the `tinytroupe` package (you might need to install it in editable mode `pip install -e .` from the repo root, or adjust your `PYTHONPATH`).

-   **`FileNotFoundError: [Errno 2] No such file or directory: 'config.ini'` (or similar for prompt files)**:
    -   Ensure `config.ini` is in one of the expected locations (current working directory, script directory, or package directory).
    -   If you are working with a cloned repository, ensure all necessary files are present.

-   **Agents are not behaving as expected:**
    -   **Check Personas:** Are the personality traits, interests, and goals clearly defined and suggestive of the desired behavior?
    -   **Review Prompts:** The underlying LLM prompts guide agent behavior. Complex interactions might require more nuanced persona definitions.
    -   **Temperature Settings:** If using `TinyPersonFactory`, the `temperature` setting for generation can influence persona creativity. For direct agent interaction, the model's inherent temperature (usually managed by OpenAI) applies.
    -   **Stimuli:** Ensure agents are receiving the correct stimuli. An agent won't react to something it hasn't perceived.

If you encounter other issues, checking the full error message and the TinyTroupe source code or examples can often provide clues.

Happy simulating!
```
