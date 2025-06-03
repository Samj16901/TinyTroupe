import argparse
import os
import sys
import json

# Ensure the tinytroupe library can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import tinytroupe # Initializes configuration, logging, etc.
    from tinytroupe.agent import TinyPerson
    from tinytroupe.environment import TinyWorld
except ImportError as e:
    print(f"Error importing tinytroupe: {e}")
    print("Please ensure that tinytroupe is installed and the script is run from a context where it can be found.")
    print("If running from the examples directory, the sys.path modification should handle this.")
    sys.exit(1)

AGENTS_DIR = os.path.join(os.path.dirname(__file__), "agents")

def list_available_agents():
    print("Available agents:")
    try:
        agent_files = [f for f in os.listdir(AGENTS_DIR) if f.endswith(".agent.json")]
        if not agent_files:
            print("  No agent files found.")
            return
        for agent_file in agent_files:
            agent_name = agent_file.replace(".agent.json", "")
            print(f"  - {agent_name}")
    except FileNotFoundError:
        print(f"  Error: Agents directory not found at {AGENTS_DIR}")

def run_simulation(agent1_name, agent2_name, prompt, num_steps):
    agent1_file = os.path.join(AGENTS_DIR, f"{agent1_name}.agent.json")
    agent2_file = os.path.join(AGENTS_DIR, f"{agent2_name}.agent.json")

    if not os.path.exists(agent1_file):
        print(f"Error: Agent file for '{agent1_name}' not found at {agent1_file}")
        list_available_agents()
        return
    if not os.path.exists(agent2_file):
        print(f"Error: Agent file for '{agent2_name}' not found at {agent2_file}")
        list_available_agents()
        return

    print(f"Loading agent 1: {agent1_name}...")
    agent1 = TinyPerson.load_specification(agent1_file)
    print(f"Loading agent 2: {agent2_name}...")
    agent2 = TinyPerson.load_specification(agent2_file)

    if not agent1 or not agent2:
        print("Error loading one or both agents.")
        return

    print(f"Creating world and adding agents: {agent1.name}, {agent2.name}")
    world = TinyWorld(f"CLI Chat between {agent1.name} and {agent2.name}")
    world.add_agents([agent1, agent2])
    world.make_everyone_accessible()

    print(f"Initiating interaction. {agent1.name} will start with: '{prompt}'")
    # Agent1 receives the prompt as a stimulus from the world (or an external source)
    world.broadcast(f"{prompt}", source=agent1) # Corrected: use broadcast or agent1.listen(prompt, source=world) for clarity
    # Or, more directly, agent1 processes the prompt. For a direct command/query, think might be better.
    # agent1.listen(prompt, source=world) # Make it clear the world is 'saying' this to agent1 or it's an external stimulus

    # Let agent1 react to the initial prompt first
    print(f"\n--- {agent1.name}'s initial reaction ---")
    agent1.act(until_done=True)
    world._handle_actions(agent1, agent1.pop_latest_actions()) # Environment handles actions

    print(f"\n--- Running simulation for {num_steps} alternating steps after initial prompt ---")
    # In each step, one agent will react to what the other said in the previous step (or the initial prompt)
    for i in range(num_steps):
        print(f"\n--- Step {i+1}/{num_steps} ---")

        # Agent2 reacts to Agent1's last statement (or initial prompt if Agent1 didn't talk)
        print(f"\n--- {agent2.name}'s turn ---")
        agent2.act(until_done=True)
        world._handle_actions(agent2, agent2.pop_latest_actions())

        if i < num_steps -1 or num_steps == 1 : # if it's not the last action of agent2
             # Agent1 reacts to Agent2's last statement
            print(f"\n--- {agent1.name}'s turn ---")
            agent1.act(until_done=True)
            world._handle_actions(agent1, agent1.pop_latest_actions())


    print("\n--- Interaction Log ---")
    # Display communications from the world's perspective, which includes all agent interactions it processed
    for comm in world._displayed_communications_buffer: # Accessing internal buffer for simplicity here
        if comm.get("rendering"):
             print(comm.get("rendering"))

    # Alternatively, a more structured way to show conversation:
    # print("\n--- Agent Episodic Memories ---")
    # print(f"\n{agent1.name}'s perspective:")
    # agent1.pp_current_interactions(max_content_length=120)
    # print(f"\n{agent2.name}'s perspective:")
    # agent2.pp_current_interactions(max_content_length=120)

    print("\nSimulation finished.")

def main():
    parser = argparse.ArgumentParser(description="Run a simple chat simulation between two TinyTroupe agents.")

    parser.add_argument(
        "--list_agents",
        action="store_true",
        help="List available agent personas from the 'examples/agents' directory and exit."
    )
    parser.add_argument(
        "--agent1",
        type=str,
        help="Name of the first agent (must match a filename in 'examples/agents' without .agent.json)."
    )
    parser.add_argument(
        "--agent2",
        type=str,
        help="Name of the second agent (must match a filename in 'examples/agents' without .agent.json)."
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="The initial prompt or stimulus for the first agent to start the conversation."
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=3, # Changed default to 3 as 5 was a bit long for quick tests
        help="Number of full conversation exchanges (A1 -> A2 -> A1) to run (default: 3)."
    )

    args = parser.parse_args()

    if args.list_agents:
        list_available_agents()
        sys.exit(0)

    if not all([args.agent1, args.agent2, args.prompt]):
        parser.error("Arguments --agent1, --agent2, and --prompt are required unless --list_agents is used.")
        sys.exit(1) # Should be sys.exit(1) for error

    # Ensure agent names don't have the .agent.json suffix from user input
    agent1_name = args.agent1.replace(".agent.json", "")
    agent2_name = args.agent2.replace(".agent.json", "")

    run_simulation(agent1_name, agent2_name, args.prompt, args.steps)

if __name__ == "__main__":
    main()
EOF
