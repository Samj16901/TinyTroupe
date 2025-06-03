import os

readme_file = "README.md"

try:
    with open(readme_file, "r", encoding='utf-8') as f:
        readme_content = f.read()
except FileNotFoundError:
    print(f"Error: {readme_file} not found.")
    exit(1)

cli_section_header = "## Command-Line Interface (CLI) Tool"
# Ensure the exact original line is targeted, including potential leading/trailing whitespace in its paragraph context
# Based on the previous run, the line is exactly as below within its paragraph.
old_intro_line_exact = "This repository includes a basic command-line tool, `run_chat_cli.py`, located in the `examples` directory, to quickly run chat simulations between two agents without needing to write Python code directly."

# Find the start of the CLI section
cli_section_start_index = readme_content.find(cli_section_header)

if cli_section_start_index == -1:
    print(f"Error: CLI section header '{cli_section_header}' not found in {readme_file}.")
    exit(1)

# Find the old intro line within the CLI section
intro_line_index = readme_content.find(old_intro_line_exact, cli_section_start_index)

if intro_line_index != -1:
    # Construct the new line
    new_intro_line = old_intro_line_exact + " The `examples/agents/` directory contains a diverse set of personas, including professionals, college students, and other characters, offering a range of scenarios for simulation."
    # Replace only the first occurrence after the header
    readme_content = readme_content.replace(old_intro_line_exact, new_intro_line, 1)
    print(f"{readme_file} CLI section introduction updated successfully.")
else:
    print(f"Warning: Could not find the exact introductory sentence ('{old_intro_line_exact}') to replace in {readme_file} for CLI documentation update.")
    # Fallback: try to update the --list_agents description as a less ideal alternative
    old_list_agents_desc = "To see a list of predefined agent personas available in the `examples/agents/` directory:"
    new_list_agents_desc = "To see a list of predefined agent personas (e.g., professionals, students, and other characters) available in the `examples/agents/` directory:"

    list_agents_index = readme_content.find(old_list_agents_desc, cli_section_start_index)
    if list_agents_index != -1:
        readme_content = readme_content.replace(old_list_agents_desc, new_list_agents_desc, 1)
        print(f"README.md --list_agents description updated as a fallback.")
    else:
        print("Fallback update for --list_agents description also failed. No changes made to the CLI section text.")

try:
    with open(readme_file, "w", encoding='utf-8') as f:
        f.write(readme_content)
    print(f"{readme_file} writing process complete.")
except Exception as e:
    print(f"Error writing to {readme_file}: {e}")
