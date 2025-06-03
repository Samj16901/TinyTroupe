from tinytroupe.agent import logger, default, Self, AgentOrWorld, CognitiveActionModel
from tinytroupe.agent.memory import EpisodicMemory, SemanticMemory
import tinytroupe.openai_utils as openai_utils
from tinytroupe.utils import JsonSerializableRegistry, repeat_on_error, name_or_empty
import tinytroupe.utils as utils
from tinytroupe.control import transactional, current_simulation


import os
import json
import copy
import textwrap  # to dedent strings
import chevron  # to parse Mustache templates
from typing import Any
from rich import print



#######################################################################################################################
# TinyPerson itself
#######################################################################################################################
@utils.post_init
class TinyPerson(JsonSerializableRegistry):
    """
    A simulated person in the TinyTroupe universe.

    This class represents an agent with a persona, mental state, memory, and mental faculties.
    Agents can perceive stimuli, act in an environment, and interact with other agents.

    :param name: The name of the TinyPerson.
    :type name: str
    :param episodic_memory: The agent's episodic memory. Defaults to a new :class:`~tinytroupe.agent.memory.EpisodicMemory` instance.
    :type episodic_memory: EpisodicMemory, optional
    :param semantic_memory: The agent's semantic memory. Defaults to a new :class:`~tinytroupe.agent.memory.SemanticMemory` instance.
    :type semantic_memory: SemanticMemory, optional
    :param mental_faculties: A list of mental faculties that define the agent's capabilities. Defaults to an empty list.
    :type mental_faculties: list, optional

    **Core Attributes:**

    *   ``name (str)``: The name of the TinyPerson.
    *   ``episodic_memory (EpisodicMemory)``: Stores time-ordered sequences of events and experiences.
    *   ``semantic_memory (SemanticMemory)``: Stores general knowledge, facts, and concepts.
    *   ``_mental_faculties (list)``: A list of :class:`~tinytroupe.agent.mental_faculty.MentalFaculty` instances that define the agent's capabilities for action and perception processing.
    *   ``_persona (dict)``: A dictionary containing the agent's defining characteristics such as age, occupation, personality traits, interests, and skills.
    *   ``_mental_state (dict)``: A dictionary representing the agent's current internal state, including current datetime, location, ongoing goals, focus of attention, emotions, and accessible agents.

    **Key Methods:**

    *   **Persona Management**: :meth:`~define`, :meth:`~get`, :meth:`~import_fragment`, :meth:`~include_persona_definitions`.
    *   **Action and Perception**: :meth:`~act`, :meth:`~listen`, :meth:`~see`, :meth:`~think`.
    *   **Memory Interaction**: :meth:`~store_in_memory`, :meth:`~retrieve_memories`, :meth:`~retrieve_recent_memories`, :meth:`~retrieve_relevant_memories`.
    *   **State Management**: :meth:`~move_to`, :meth:`~change_context`, :meth:`~make_agent_accessible`.
    *   **Serialization**: :meth:`~save_specification`, :meth:`~load_specification`.

    **Basic Usage Example:**

    Creating a new TinyPerson and defining some persona attributes:
    Creating a new TinyPerson and defining some persona attributes:

    .. code-block:: python

        from tinytroupe.agent import TinyPerson

        # Create a new agent named Alice
        alice = TinyPerson(name="Alice")

        # Define Alice's age and occupation
        alice.define("age", 30)
        alice.define("occupation", {"title": "Software Engineer", "company": "Tech Solutions Inc."})
        alice.define("personal_interests", ["hiking", "reading sci-fi novels"])

        # Display Alice's mini biography
        print(alice.minibio())
        # Output might be: Alice is a 30 year old Software Engineer, None, currently living in None. ... (extended bio)

        # Alice perceives a visual stimulus
        alice.see("A small, curious robot rolls into the room.")

        # Alice decides to act
        actions = alice.act(return_actions=True)
        for action in actions:
            print(f"Alice's action: {action['action']['type']} - {action['action'].get('content', '')}")

    Loading a TinyPerson from a specification file:

    .. code-block:: python

        from tinytroupe.agent import TinyPerson

        # Assume "examples/agents/Alice.agent.json" exists and is a valid agent specification file.
        # This path might vary based on your project structure.
        try:
            bob = TinyPerson.load_specification("examples/agents/Bob.agent.json") # Fictional agent for example
            print(f"Loaded {bob.name} successfully.")
        except FileNotFoundError:
            print("Bob's agent file not found. Please create it or use an existing one.")
        except Exception as e:
            print(f"Error loading Bob: {e}")


    **Agent Specification Files (JSON):**

    Agent specification files are JSON documents that define the persona, memory, and mental faculties of a TinyPerson.
    This allows for easy persistence and sharing of agent configurations.

    **Structure:**

    The root of the JSON object should have a ``"type": "TinyPerson"`` field.
    Key components include:

    *   ``"persona"``: An object detailing the agent's characteristics.
        *   ``"name"``: (str) The agent's name.
        *   ``"age"``: (int) Age in years.
        *   ``"nationality"``: (str) Agent's nationality.
        *   ``"country_of_residence"``: (str) Current country of residence.
        *   ``"occupation"``: (object) Details about the agent's job.
            *   ``"title"``: (str) Job title.
            *   ``"description"``: (str, optional) Brief description of the occupation.
        *   ``"personality_traits"``: (list of str) e.g., "Creative", "Introverted".
        *   ``"personal_interests"``: (list of str) e.g., "Reading", "Hiking".
        *   ``"skills"``: (list of str) e.g., "Writing", "Programming".
        *   ``"relationships"``: (list of objects) Describes connections to other agents.
            *   ``"Name"``: (str) Name of the other agent.
            *   ``"Description"``: (str) Nature of the relationship (e.g., "colleague", "friend").
    *   ``"episodic_memory"`` (optional): An object representing the agent's :class:`~tinytroupe.agent.memory.EpisodicMemory`.
    *   ``"semantic_memory"`` (optional): An object representing the agent's :class:`~tinytroupe.agent.memory.SemanticMemory`.
    *   ``"mental_faculties"`` (optional): A list of objects, each representing a :class:`~tinytroupe.agent.mental_faculty.MentalFaculty`.

    **Example JSON Specification:**

    .. code-block:: json

        {
            "type": "TinyPerson",
            "persona": {
                "name": "Elena_Vargas",
                "age": 47,
                "nationality": "Spanish",
                "country_of_residence": "Spain",
                "occupation": {
                    "title": "Investigative Journalist",
                    "description": "Uncovers corporate and governmental misconduct."
                },
                "personality_traits": ["Cynical", "Determined", "Incorruptible"],
                "personal_interests": ["Chess", "Classic literature"],
                "skills": ["Interviewing", "Data analysis", "Writing", "Stealth"]
            }
        }

    You can also include ``episodic_memory``, ``semantic_memory``, and ``mental_faculties`` in the specification file if you want to persist these aspects.

    **Fragments:**

    Fragments are partial JSON specifications that can be merged into an existing agent's persona to customize or update it.
    This is useful for applying common sets of traits or characteristics to multiple agents.

    A fragment file must have ``"type": "Fragment"`` and a ``"persona"`` object.

    **Example Fragment (e.g., `tech_enthusiast.agent.fragment.json`):**

    .. code-block:: json

        {
            "type": "Fragment",
            "persona": {
                "personal_interests": ["Latest gadgets", "AI development", "Virtual reality"],
                "skills": ["Coding in Python", "Hardware tinkering"]
            }
        }

    **Importing a Fragment:**

    .. code-block:: python

        from tinytroupe.agent import TinyPerson
        # Assuming 'alice' is an existing TinyPerson instance
        # alice = TinyPerson(name="Alice")
        # alice.define("personal_interests", ["gardening"]) # Initial interest

        # try:
        #     alice.import_fragment("tech_enthusiast.agent.fragment.json") # Fictional fragment
        #     print(f"Alice's interests after import: {alice.get('personal_interests')}")
        #     # Expected: ['gardening', 'Latest gadgets', 'AI development', 'Virtual reality'] (if merge=True is default)
        # except FileNotFoundError:
        #     print("Fragment file not found.")
        # except Exception as e:
        #     print(f"Error importing fragment: {e}")

    """

    # The maximum number of actions that an agent is allowed to perform before DONE.
    # This prevents the agent from acting without ever stopping.
    MAX_ACTIONS_BEFORE_DONE = 15

    PP_TEXT_WIDTH = 100

    serializable_attributes = ["_persona", "_mental_state", "_mental_faculties", "episodic_memory", "semantic_memory"]
    serializable_attributes_renaming = {"_mental_faculties": "mental_faculties", "_persona": "persona", "_mental_state": "mental_state"}


    # A dict of all agents instantiated so far.
    all_agents = {}  # name -> agent

    # The communication style for all agents: "simplified" or "full".
    communication_style:str="simplified"
    
    # Whether to display the communication or not. True is for interactive applications, when we want to see simulation
    # outputs as they are produced.
    communication_display:bool=True
    

    def __init__(self, name:str=None, 
                 episodic_memory=None,
                 semantic_memory=None,
                 mental_faculties:list=None):
        """
        Creates a TinyPerson.

        :param name: The name of the TinyPerson. Must be unique if the agent is registered globally.
        :type name: str
        :param episodic_memory: The episodic memory implementation to use.
                                If None, a new :class:`~tinytroupe.agent.memory.EpisodicMemory` instance is created.
        :type episodic_memory: EpisodicMemory, optional
        :param semantic_memory: The semantic memory implementation to use.
                                If None, a new :class:`~tinytroupe.agent.memory.SemanticMemory` instance is created.
        :type semantic_memory: SemanticMemory, optional
        :param mental_faculties: A list of mental faculties to add to the agent.
                                 If None, an empty list is used.
        :type mental_faculties: list, optional
        """

        # NOTE: default values will be given in the _post_init method, as that's shared by
        #       direct initialization as well as via deserialization.

        if episodic_memory is not None:
            self.episodic_memory = episodic_memory
        
        if semantic_memory is not None:
            self.semantic_memory = semantic_memory

        # Mental faculties
        if mental_faculties is not None:
            self._mental_faculties = mental_faculties
        
        assert name is not None, "A TinyPerson must have a name."
        self.name = name

        # @post_init makes sure that _post_init is called after __init__

    
    def _post_init(self, **kwargs):
        """
        This will run after __init__, since the class has the @post_init decorator.
        It is convenient to separate some of the initialization processes to make deserialize easier.
        """

        ############################################################
        # Default values
        ############################################################

        self.current_messages = []
        
        # the current environment in which the agent is acting
        self.environment = None

        # The list of actions that this agent has performed so far, but which have not been
        # consumed by the environment yet.
        self._actions_buffer = []

        # The list of agents that this agent can currently interact with.
        # This can change over time, as agents move around the world.
        self._accessible_agents = []

        # the buffer of communications that have been displayed so far, used for
        # saving these communications to another output form later (e.g., caching)
        self._displayed_communications_buffer = []

        if not hasattr(self, 'episodic_memory'):
            # This default value MUST NOT be in the method signature, otherwise it will be shared across all instances.
            self.episodic_memory = EpisodicMemory()
        
        if not hasattr(self, 'semantic_memory'):
            # This default value MUST NOT be in the method signature, otherwise it will be shared across all instances.
            self.semantic_memory = SemanticMemory()
        
        # _mental_faculties
        if not hasattr(self, '_mental_faculties'):
            # This default value MUST NOT be in the method signature, otherwise it will be shared across all instances.
            self._mental_faculties = []

        # create the persona configuration dictionary
        if not hasattr(self, '_persona'):          
            self._persona = {
                "name": self.name,
                "age": None,
                "nationality": None,
                "country_of_residence": None,
                "occupation": None,
                "routines": [],
                "occupation_description": None,
                "personality_traits": [],
                "professional_interests": [],
                "personal_interests": [],
                "skills": [],
                "relationships": []
            }
        
        if not hasattr(self, 'name'): 
            self.name = self._persona["name"]

        # create the mental state dictionary
        if not hasattr(self, '_mental_state'):
            self._mental_state = {
                "datetime": None,
                "location": None,
                "context": [],
                "goals": [],
                "attention": None,
                "emotions": "Feeling nothing in particular, just calm.",
                "memory_context": None,
                "accessible_agents": []  # [{"agent": agent_1, "relation": "My friend"}, {"agent": agent_2, "relation": "My colleague"}, ...]
            }
        
        if not hasattr(self, '_extended_agent_summary'):
            self._extended_agent_summary = None

        self._prompt_template_path = os.path.join(
            os.path.dirname(__file__), "prompts/tiny_person.mustache"
        )
        self._init_system_message = None  # initialized later


        ############################################################
        # Special mechanisms used during deserialization
        ############################################################

        # rename agent to some specific name?
        if kwargs.get("new_agent_name") is not None:
            self._rename(kwargs.get("new_agent_name"))
        
        # If auto-rename, use the given name plus some new number ...
        if kwargs.get("auto_rename") is True:
            new_name = self.name # start with the current name
            rename_succeeded = False
            while not rename_succeeded:
                try:
                    self._rename(new_name)
                    TinyPerson.add_agent(self)
                    rename_succeeded = True                
                except ValueError:
                    new_id = utils.fresh_id()
                    new_name = f"{self.name}_{new_id}"
        
        # ... otherwise, just register the agent
        else:
            # register the agent in the global list of agents
            TinyPerson.add_agent(self)

        # start with a clean slate
        self.reset_prompt()

        # it could be the case that the agent is being created within a simulation scope, in which case
        # the simulation_id must be set accordingly
        if current_simulation() is not None:
            current_simulation().add_agent(self)
        else:
            self.simulation_id = None
    
    def _rename(self, new_name:str):    
        self.name = new_name
        self._persona["name"] = self.name


    def generate_agent_system_prompt(self):
        with open(self._prompt_template_path, "r") as f:
            agent_prompt_template = f.read()

        # let's operate on top of a copy of the configuration, because we'll need to add more variables, etc.
        template_variables = self._persona.copy()    
        template_variables["persona"] = json.dumps(self._persona.copy(), indent=4)    

        # Prepare additional action definitions and constraints
        actions_definitions_prompt = ""
        actions_constraints_prompt = ""
        for faculty in self._mental_faculties:
            actions_definitions_prompt += f"{faculty.actions_definitions_prompt()}\n"
            actions_constraints_prompt += f"{faculty.actions_constraints_prompt()}\n"
        
        # Make the additional prompt pieces available to the template. 
        # Identation here is to align with the text structure in the template.
        template_variables['actions_definitions_prompt'] = textwrap.indent(actions_definitions_prompt.strip(), "  ")
        template_variables['actions_constraints_prompt'] = textwrap.indent(actions_constraints_prompt.strip(), "  ")

        # RAI prompt components, if requested
        template_variables = utils.add_rai_template_variables_if_enabled(template_variables)

        return chevron.render(agent_prompt_template, template_variables)

    def reset_prompt(self):

        # render the template with the current configuration
        self._init_system_message = self.generate_agent_system_prompt()

        # TODO actually, figure out another way to update agent state without "changing history"

        # reset system message
        self.current_messages = [
            {"role": "system", "content": self._init_system_message}
        ]

        # sets up the actual interaction messages to use for prompting
        self.current_messages += self.retrieve_recent_memories()

        # add a final user message, which is neither stimuli or action, to instigate the agent to act properly
        self.current_messages.append({"role": "user", 
                                      "content": "Now you **must** generate a sequence of actions following your interaction directives, " +\
                                                 "and complying with **all** instructions and contraints related to the action you use." +\
                                                 "DO NOT repeat the exact same action more than once in a row!" +\
                                                 "DO NOT keep saying or doing very similar things, but instead try to adapt and make the interactions look natural." +\
                                                 "These actions **MUST** be rendered following the JSON specification perfectly, including all required keys (even if their value is empty), **ALWAYS**."
                                     })

    def get(self, key):
        """
        Returns the definition of a key in the TinyPerson's persona.

        :param key: The key to retrieve from the persona.
        :type key: str
        :return: The value associated with the key, or None if the key is not found.
        :rtype: Any

        Example:
            >>> alice.get("age")
            30
            >>> alice.get("non_existent_key")
            None
        """
        return self._persona.get(key, None)

    @transactional
    def import_fragment(self, path: str):
        """
        Imports a fragment of a persona configuration from a JSON file.

        Fragments are JSON files that define a part of an agent's persona.
        They can be used to customize agents by merging the fragment's definitions
        with the agent's existing persona. The merge behavior is determined by
        :func:`~tinytroupe.utils.merge_dicts`. After importing, the agent's
        internal prompt is reset to reflect the changes.

        :param path: The path to the JSON fragment file.
        :type path: str
        :raises ValueError: If the imported JSON file is not a valid fragment (e.g., missing "type": "Fragment" or "persona" key).

        Example:
            Assuming `artist_fragment.json` contains:

            .. code-block:: json

                {
                  "type": "Fragment",
                  "persona": {
                    "occupation": {"title": "Artist", "medium": "Oil Painting"},
                    "skills": ["Painting", "Color Theory"]
                  }
                }

            .. code-block:: python

                # agent = TinyPerson(name="Carol")
                # agent.define("occupation", {"title": "Hobbyist"})
                # agent.import_fragment("artist_fragment.json")
                # print(agent.get("occupation"))
                # # Output: {'title': 'Artist', 'medium': 'Oil Painting'}
                # print(agent.get("skills"))
                # # Output: ['Painting', 'Color Theory'] (assuming skills wasn't defined before or merge appends)

        """
        with open(path, "r") as f:
            fragment = json.load(f)

        # check the type is "Fragment" and that there's also a "persona" key
        if fragment.get("type", None) == "Fragment" and fragment.get("persona", None) is not None:
            self.include_persona_definitions(fragment["persona"])
        else:
            raise ValueError("The imported JSON file must be a valid fragment of a persona configuration.")
        
        # must reset prompt after adding to configuration
        self.reset_prompt()

    @transactional
    def include_persona_definitions(self, additional_definitions: dict):
        """
        Includes a set of definitions into the TinyPerson's persona.

        The provided definitions will be merged with the current persona using
        :func:`~tinytroupe.utils.merge_dicts`. This is a convenient way to add
        multiple bundled definitions to the agent at once. After inclusion,
        the agent's internal prompt is reset.

        :param additional_definitions: A dictionary containing the definitions to import.
        :type additional_definitions: dict

        Example:
            >>> definitions = {
            ...     "personality_traits": ["Outgoing", "Optimistic"],
            ...     "home_city": "Metropolis"
            ... }
            >>> agent.include_persona_definitions(definitions)
            >>> agent.get("personality_traits") # Assuming it was empty or merged
            ['Outgoing', 'Optimistic']
        """

        self._persona = utils.merge_dicts(self._persona, additional_definitions)

        # must reset prompt after adding to configuration
        self.reset_prompt()
        
    
    @transactional
    def define(self, key, value, merge=True, overwrite_scalars=True):
        """
        Define a value in the TinyPerson's persona configuration.

        The value can be a scalar, dictionary, or list.
        If the value is a dictionary or list, the `merge` parameter controls whether
        it's merged with an existing value (using :func:`~tinytroupe.utils.merge_dicts`)
        or replaces it. For scalar values, `overwrite_scalars` controls behavior if the
        key already exists. The agent's internal prompt is reset after definition.

        :param key: The key to define in the persona.
        :type key: str
        :param value: The value to associate with the key. If a string, it will be dedented.
        :type value: Any
        :param merge: Whether to merge dictionary or list values with existing values.
                      Defaults to True. If False, replaces the existing value.
        :type merge: bool, optional
        :param overwrite_scalars: Whether to overwrite existing scalar values.
                                 Defaults to True. If False and the key exists with a scalar value,
                                 a ValueError is raised.
        :type overwrite_scalars: bool, optional
        :raises ValueError: If `overwrite_scalars` is False and an attempt is made to
                           overwrite an existing scalar value.

        Example:
            >>> agent = TinyPerson(name="Dave")
            >>> agent.define("age", 45)
            >>> agent.get("age")
            45
            >>> agent.define("personal_interests", ["Golf"])
            >>> agent.get("personal_interests")
            ['Golf']
            >>> agent.define("personal_interests", ["Fishing"], merge=True)
            >>> agent.get("personal_interests")
            ['Golf', 'Fishing']
            >>> agent.define("occupation", {"title": "Accountant"}, merge=False)
            >>> agent.get("occupation")
            {'title': 'Accountant'}
            >>> agent.define("occupation", {"department": "Finance"}, merge=True)
            >>> agent.get("occupation")
            {'title': 'Accountant', 'department': 'Finance'}
        """

        # dedent value if it is a string
        if isinstance(value, str):
            value = textwrap.dedent(value)

        # if the value is a dictionary, we can choose to merge it with the existing value or replace it
        if isinstance(value, dict) or isinstance(value, list):
            if merge:
                self._persona = utils.merge_dicts(self._persona, {key: value})
            else:
                self._persona[key] = value

        # if the value is a scalar, we can choose to overwrite it or not
        elif overwrite_scalars or (key not in self._persona):
            self._persona[key] = value
        
        else:
            raise ValueError(f"The key '{key}' already exists in the persona configuration and overwrite_scalars is set to False.")

            
        # must reset prompt after adding to configuration
        self.reset_prompt()

    
    @transactional
    def define_relationships(self, relationships, replace=True):
        """
        Defines or updates the TinyPerson's relationships.

        Relationships are stored in the persona under the "relationships" key, which is a list of dictionaries.
        Each dictionary should ideally have "Name" (of the other agent) and "Description" (of the relationship) keys.

        :param relationships: The relationships to add or replace.
                              Can be a list of relationship dictionaries (e.g., `[{"Name": "Bob", "Description": "colleague"}]`)
                              or a single relationship dictionary (e.g., `{"Name": "Carol", "Description": "sibling"}`).
        :type relationships: list or dict
        :param replace: Whether to replace the current list of relationships or add to them.
                        Defaults to True (replace). If False, new relationships are appended.
        :type replace: bool, optional
        :raises Exception: If arguments are invalid (e.g., `replace` is True but `relationships` is not a list for replacement).
        """

        if (replace == True) and (isinstance(relationships, list)):
            self._persona['relationships'] = relationships

        elif replace == False:
            current_relationships = self._persona['relationships']
            if isinstance(relationships, list):
                for r in relationships:
                    current_relationships.append(r)
                
            elif isinstance(relationships, dict) and len(relationships) == 2: #{"Name": ..., "Description": ...}
                current_relationships.append(relationships)

            else:
                raise Exception("Only one key-value pair is allowed in the relationships dict.")

        else:
            raise Exception("Invalid arguments for define_relationships.")

    @transactional
    def clear_relationships(self):
        """
        Clears the TinyPerson's relationships.
        """
        self._persona['relationships'] = []  

        return self      
    
    @transactional
    def related_to(self, other_agent, description, symmetric_description=None):
        """
        Defines a relationship between this agent and another agent.

        This is a convenience method that updates the "relationships" list in the persona for both agents
        if `symmetric_description` is provided.

        :param other_agent: The other agent.
        :type other_agent: TinyPerson
        :param description: The description of the relationship from this agent's perspective (e.g., "my boss").
        :type description: str
        :param symmetric_description: The description of the relationship from the other agent's perspective
                                      (e.g., "my subordinate"). If None, only this agent's perspective is recorded.
                                      Defaults to None.
        :type symmetric_description: str, optional
        :return: The agent itself, to facilitate method chaining.
        :rtype: TinyPerson
        """
        self.define_relationships([{"Name": other_agent.name, "Description": description}], replace=False)
        if symmetric_description is not None:
            other_agent.define_relationships([{"Name": self.name, "Description": symmetric_description}], replace=False)

        return self

    def add_mental_faculties(self, mental_faculties: list):
        """
        Adds a list of :class:`~tinytroupe.agent.mental_faculty.MentalFaculty` instances to the agent.

        Each faculty in the list is added using :meth:`~add_mental_faculty`.

        :param mental_faculties: A list of mental faculty objects.
        :type mental_faculties: list
        :return: The agent itself, for chaining.
        :rtype: TinyPerson
        """
        for faculty in mental_faculties:
            self.add_mental_faculty(faculty)

        return self

    def add_mental_faculty(self, faculty):
        """
        Adds a single :class:`~tinytroupe.agent.mental_faculty.MentalFaculty` to the agent.

        The faculty is appended to the `_mental_faculties` list.
        The agent's internal prompt is reset after adding a faculty.

        :param faculty: The mental faculty object to add.
        :type faculty: MentalFaculty
        :raises Exception: If the faculty is already present in the agent.
        :return: The agent itself, for chaining.
        :rtype: TinyPerson
        """
        # check if the faculty is already there or not
        if faculty not in self._mental_faculties:
            self._mental_faculties.append(faculty)
            self.reset_prompt() # Reset prompt as faculties define actions
        else:
            raise Exception(f"The mental faculty {faculty} is already present in the agent.")

        return self

    @transactional
    def act(
        self,
        until_done=True,
        n=None,
        return_actions=False,
        max_content_length=default["max_content_display_length"],
    ):
        """
        Prompts the agent to generate and perform a sequence of actions.

        The agent's action generation is based on its current persona, mental state, memories,
        and the available mental faculties. Actions are generated by an LLM based on a
        system prompt constructed from these elements.

        The agent can either act until it generates a "DONE" action (signifying it has completed
        its current turn or requires more stimuli) or perform a fixed number of actions.
        These modes are mutually exclusive.

        Each generated action is stored in episodic memory, and its declared cognitive state
        (goals, attention, emotions) updates the agent's `_mental_state`.
        Mental faculties may also process actions for immediate side-effects (e.g., a "SEND_MESSAGE"
        action processed by a communication faculty).

        :param until_done: If True, the agent acts until a "DONE" action is produced or
                           `MAX_ACTIONS_BEFORE_DONE` is reached. Defaults to True.
        :type until_done: bool
        :param n: Specific number of actions to perform. If provided, `until_done` is ignored.
                  Must be less than `TinyPerson.MAX_ACTIONS_BEFORE_DONE`. Defaults to None.
        :type n: int, optional
        :param return_actions: Whether to return the list of raw action content dictionaries.
                               Defaults to False.
        :type return_actions: bool
        :param max_content_length: Max length for displaying content in communications if `communication_display` is True.
                                   Defaults to `tinytroupe.agent.default["max_content_display_length"]`.
        :type max_content_length: int, optional
        :return: A list of action content dictionaries if `return_actions` is True, otherwise None.
        :rtype: list, optional
        :raises AssertionError: If `until_done` is True and `n` is also provided, or if `n` exceeds `MAX_ACTIONS_BEFORE_DONE`.

        Example:
            >>> # Agent alice sees a message and then acts
            >>> alice.see("A new message appears on the community board: 'Town meeting tonight at 7 PM.'")
            >>> actions_taken = alice.act(return_actions=True)
            >>> if actions_taken:
            ...     for action_content in actions_taken:
            ...         action_type = action_content.get("action", {}).get("type")
            ...         action_details = action_content.get("action", {}).get("content", "")
            ...         print(f"Alice performed: {action_type} - {action_details}")
            ...         if action_type == "DONE":
            ...             print("Alice decided she is done for now.")
            >>> # Example Output (will vary based on LLM):
            >>> # Alice performed: REFLECT - I should note this down.
            >>> # Alice performed: UPDATE_TASK_LIST - Add 'Attend town meeting at 7 PM' to my tasks.
            >>> # Alice performed: DONE -
            >>> # Alice decided she is done for now.
        """

        # either act until done or act a fixed number of times, but not both
        assert not (until_done and n is not None)
        if n is not None:
            assert n < TinyPerson.MAX_ACTIONS_BEFORE_DONE

        contents = []

        # A separate function to run before each action, which is not meant to be repeated in case of errors.
        def aux_pre_act():
            # TODO maybe we don't need this at all anymore?
            #
            # A quick thought before the action. This seems to help with better model responses, perhaps because
            # it interleaves user with assistant messages.
            pass # self.think("I will now think, reflect and act a bit, and then issue DONE.")

        # Aux function to perform exactly one action.
        # Occasionally, the model will return JSON missing important keys, so we just ask it to try again
        # Sometimes `content` contains EpisodicMemory's MEMORY_BLOCK_OMISSION_INFO message, which raises a TypeError on line 443
        @repeat_on_error(retries=5, exceptions=[KeyError, TypeError, AttributeError]) # Added AttributeError
        def aux_act_once():
            role, content = self._produce_message()

            # Ensure content and its nested structures are dictionaries before accessing keys
            if not isinstance(content, dict):
                logger.error(f"[{self.name}] Produced message content is not a dictionary: {content}")
                raise TypeError("Produced message content is not a dictionary.")

            cognitive_state = content.get("cognitive_state")
            if not isinstance(cognitive_state, dict):
                logger.error(f"[{self.name}] Cognitive state in produced message is not a dictionary: {cognitive_state}")
                raise TypeError("Cognitive state is not a dictionary.")


            action_data = content.get('action')
            if not isinstance(action_data, dict):
                logger.error(f"[{self.name}] Action data in produced message is not a dictionary: {action_data}")
                raise TypeError("Action data is not a dictionary.")

            logger.debug(f"{self.name}'s action: {action_data}")

            # Safely get goals, attention, and emotions
            goals = cognitive_state.get('goals', []) # Default to empty list if not present
            attention = cognitive_state.get('attention', None)
            emotions = cognitive_state.get('emotions', "Feeling nothing in particular, just calm.") # Default emotion

            self.store_in_memory({'role': role, 'content': content,
                                  'type': 'action',
                                  'simulation_timestamp': self.iso_datetime()})

            self._actions_buffer.append(action_data)
            self._update_cognitive_state(goals=goals,
                                        attention=attention,
                                        emotions=emotions)

            contents.append(content)
            if TinyPerson.communication_display:
                self._display_communication(role=role, content=content, kind='action', simplified=True, max_content_length=max_content_length)

            #
            # Some actions induce an immediate stimulus or other side-effects. We need to process them here, by means of the mental faculties.
            #
            for faculty in self._mental_faculties:
                faculty.process_action(self, action_data)


        #
        # How to proceed with a sequence of actions.
        #

        ##### Option 1: run N actions ######
        if n is not None:
            for i in range(n):
                aux_pre_act()
                aux_act_once()

        ##### Option 2: run until DONE ######
        elif until_done:
            while (len(contents) == 0) or (
                not contents[-1]["action"]["type"] == "DONE"
            ):


                # check if the agent is acting without ever stopping
                if len(contents) > TinyPerson.MAX_ACTIONS_BEFORE_DONE:
                    logger.warning(f"[{self.name}] Agent {self.name} is acting without ever stopping. This may be a bug. Let's stop it here anyway.")
                    break
                if len(contents) > 4: # just some minimum number of actions to check for repetition, could be anything >= 3
                    # if the last three actions were the same, then we are probably in a loop
                    if contents[-1]['action'] == contents[-2]['action'] == contents[-3]['action']:
                        logger.warning(f"[{self.name}] Agent {self.name} is acting in a loop. This may be a bug. Let's stop it here anyway.")
                        break

                aux_pre_act()
                aux_act_once()

        if return_actions:
            return contents

    @transactional
    def listen(
        self,
        speech,
        source: AgentOrWorld = None,
        max_content_length=default["max_content_display_length"],
    ):
        """
        Processes auditory stimuli (speech) from another agent or the environment.

        This method wraps :meth:`~_observe` to specifically handle speech.
        The stimulus is stored in episodic memory.

        :param speech: The speech content to process.
        :type speech: str
        :param source: The source of the speech (another agent or the world).
                       Defaults to None, indicating an unspecified or environmental source.
        :type source: AgentOrWorld, optional
        :param max_content_length: Max length for displaying content in communications.
                                   Defaults to `tinytroupe.agent.default["max_content_display_length"]`.
        :type max_content_length: int, optional
        :return: The agent itself, to facilitate method chaining.
        :rtype: TinyPerson
        """

        return self._observe(
            stimulus={
                "type": "CONVERSATION",
                "content": speech,
                "source": name_or_empty(source),
            },
            max_content_length=max_content_length,
        )

    def socialize(
        self,
        social_description: str,
        source: AgentOrWorld = None,
        max_content_length=default["max_content_display_length"],
    ):
        """
        Processes social stimuli described textually.

        This method wraps :meth:`~_observe` to handle general social interactions.
        The stimulus is stored in episodic memory.

        :param social_description: A textual description of the social stimulus
                                   (e.g., "Alice waves hello to Bob.", "A heated argument breaks out.").
        :type social_description: str
        :param source: The source or instigator of the social stimulus, if applicable.
                       Defaults to None.
        :type source: AgentOrWorld, optional
        :param max_content_length: Max length for displaying content in communications.
                                   Defaults to `tinytroupe.agent.default["max_content_display_length"]`.
        :type max_content_length: int, optional
        :return: The agent itself, to facilitate method chaining.
        :rtype: TinyPerson
        """
        return self._observe(
            stimulus={
                "type": "SOCIAL",
                "content": social_description,
                "source": name_or_empty(source),
            },
            max_content_length=max_content_length,
        )

    def see(
        self,
        visual_description,
        source: AgentOrWorld = None,
        max_content_length=default["max_content_display_length"],
    ):
        """
        Processes visual stimuli described textually.

        This method wraps :meth:`~_observe` for visual perceptions.
        The stimulus is stored in episodic memory.

        :param visual_description: A textual description of the visual stimulus
                                   (e.g., "A red car drives past.", "The room is dimly lit.").
        :type visual_description: str
        :param source: The object or agent that is the primary focus of the visual stimulus, if applicable.
                       Defaults to None.
        :type source: AgentOrWorld, optional
        :param max_content_length: Max length for displaying content in communications.
                                   Defaults to `tinytroupe.agent.default["max_content_display_length"]`.
        :type max_content_length: int, optional
        :return: The agent itself, to facilitate method chaining.
        :rtype: TinyPerson
        """
        return self._observe(
            stimulus={
                "type": "VISUAL",
                "content": visual_description,
                "source": name_or_empty(source),
            },
            max_content_length=max_content_length,
        )

    def think(self, thought, max_content_length=default["max_content_display_length"]):
        """
        Introduces a thought directly into the agent's cognitive process.

        This wraps :meth:`~_observe`, treating the thought as an internal stimulus.
        The source of the thought is considered to be the agent itself.
        The thought is stored in episodic memory.

        :param thought: The content of the thought (e.g., "I should check my messages.").
        :type thought: str
        :param max_content_length: Max length for displaying content in communications.
                                   Defaults to `tinytroupe.agent.default["max_content_display_length"]`.
        :type max_content_length: int, optional
        :return: The agent itself, to facilitate method chaining.
        :rtype: TinyPerson
        """
        return self._observe(
            stimulus={
                "type": "THOUGHT",
                "content": thought,
                "source": name_or_empty(self),
            },
            max_content_length=max_content_length,
        )

    def internalize_goal(
        self, goal, max_content_length=default["max_content_display_length"]
    ):
        """
        Internalizes a new goal.

        This wraps :meth:`~_observe`, treating goal formulation as an internal stimulus.
        The source of the goal is considered to be the agent itself.
        The goal is stored in episodic memory as a stimulus. While the agent's LLM also
        manages goals in its `cognitive_state` during actions, this method allows for
        explicit external or internal setting of goals.

        :param goal: The description of the goal to internalize (e.g., "Find out who sent the mysterious package.").
        :type goal: str
        :param max_content_length: Max length for displaying content in communications.
                                   Defaults to `tinytroupe.agent.default["max_content_display_length"]`.
        :type max_content_length: int, optional
        :return: The agent itself, to facilitate method chaining.
        :rtype: TinyPerson
        """
        return self._observe(
            stimulus={
                "type": "INTERNAL_GOAL_FORMULATION",
                "content": goal,
                "source": name_or_empty(self),
            },
            max_content_length=max_content_length,
        )

    @transactional
    def _observe(self, stimulus, max_content_length=default["max_content_display_length"]):
        stimuli = [stimulus]

        content = {"stimuli": stimuli}

        logger.debug(f"[{self.name}] Observing stimuli: {content}")

        # whatever comes from the outside will be interpreted as coming from 'user', simply because
        # this is the counterpart of 'assistant'

        self.store_in_memory({'role': 'user', 'content': content, 
                              'type': 'stimulus',
                              'simulation_timestamp': self.iso_datetime()})

        if TinyPerson.communication_display:
            self._display_communication(
                role="user",
                content=content,
                kind="stimuli",
                simplified=True,
                max_content_length=max_content_length,
            )

        return self  # allows easier chaining of methods

    @transactional
    def listen_and_act(
        self,
        speech,
        return_actions=False,
        max_content_length=default["max_content_display_length"],
    ):
        """
        Convenience method that combines :meth:`~listen` and :meth:`~act`.

        The agent first processes the speech input and then performs a sequence of actions.

        :param speech: The speech content to process.
        :type speech: str
        :param return_actions: Whether to return the list of action contents from `act`.
                               Defaults to False.
        :type return_actions: bool
        :param max_content_length: Max length for displaying content in communications.
                                   Defaults to `tinytroupe.agent.default["max_content_display_length"]`.
        :type max_content_length: int, optional
        :return: A list of action contents if `return_actions` is True, otherwise None.
        :rtype: list, optional
        """

        self.listen(speech, max_content_length=max_content_length)
        return self.act(
            return_actions=return_actions, max_content_length=max_content_length
        )

    @transactional
    def see_and_act(
        self,
        visual_description,
        return_actions=False,
        max_content_length=default["max_content_display_length"],
    ):
        """
        Convenience method that combines :meth:`~see` and :meth:`~act`.

        The agent first processes the visual description and then performs a sequence of actions.

        :param visual_description: A textual description of the visual stimulus.
        :type visual_description: str
        :param return_actions: Whether to return the list of action contents from `act`.
                               Defaults to False.
        :type return_actions: bool
        :param max_content_length: Max length for displaying content in communications.
                                   Defaults to `tinytroupe.agent.default["max_content_display_length"]`.
        :type max_content_length: int, optional
        :return: A list of action contents if `return_actions` is True, otherwise None.
        :rtype: list, optional
        """

        self.see(visual_description, max_content_length=max_content_length)
        return self.act(
            return_actions=return_actions, max_content_length=max_content_length
        )

    @transactional
    def think_and_act(
        self,
        thought,
        return_actions=False,
        max_content_length=default["max_content_display_length"],
    ):
        """
        Convenience method that combines :meth:`~think` and :meth:`~act`.

        The agent first processes the thought and then performs a sequence of actions.

        :param thought: The content of the thought.
        :type thought: str
        :param return_actions: Whether to return the list of action contents from `act`.
                               Defaults to False.
        :type return_actions: bool
        :param max_content_length: Max length for displaying content in communications.
                                   Defaults to `tinytroupe.agent.default["max_content_display_length"]`.
        :type max_content_length: int, optional
        :return: A list of action contents if `return_actions` is True, otherwise None.
        :rtype: list, optional
        """

        self.think(thought, max_content_length=max_content_length)
        return self.act(return_actions=return_actions, max_content_length=max_content_length)

    def read_documents_from_folder(self, documents_path: str):
        """
        Reads documents from a specified local directory and loads them into the agent's semantic memory
        via :meth:`~tinytroupe.agent.memory.SemanticMemory.add_documents_path`.

        This allows the agent to ground its knowledge and responses on the content of these documents.

        :param documents_path: The path to the directory containing the documents.
        :type documents_path: str
        """
        logger.info(f"Setting documents path to {documents_path} and loading documents.")

        self.semantic_memory.add_documents_path(documents_path)

    def read_document_from_file(self, file_path: str):
        """
        Reads a single document from a local file and loads it into the agent's semantic memory
        via :meth:`~tinytroupe.agent.memory.SemanticMemory.add_document_path`.

        :param file_path: The path to the document file.
        :type file_path: str
        """
        logger.info(f"Reading document from file: {file_path}")

        self.semantic_memory.add_document_path(file_path)

    def read_documents_from_web(self, web_urls: list):
        """
        Reads documents from a list of web URLs and loads them into the agent's semantic memory
        via :meth:`~tinytroupe.agent.memory.SemanticMemory.add_web_urls`.

        :param web_urls: A list of URLs pointing to the web documents.
        :type web_urls: list[str]
        """
        logger.info(f"Reading documents from the following web URLs: {web_urls}")

        self.semantic_memory.add_web_urls(web_urls)

    def read_document_from_web(self, web_url: str):
        """
        Reads a document from a single web URL and loads it into the agent's semantic memory
        via :meth:`~tinytroupe.agent.memory.SemanticMemory.add_web_url`.

        :param web_url: The URL of the web document.
        :type web_url: str
        """
        logger.info(f"Reading document from web URL: {web_url}")

        self.semantic_memory.add_web_url(web_url)

    @transactional
    def move_to(self, location, context=[]):
        """
        Moves the agent to a new location and updates its `_mental_state`.

        Changing location also implies a change in the environmental context.
        The provided `context` list describes this new environmental situation.

        :param location: The new location of the agent (e.g., "Town Square", "Library").
        :type location: str
        :param context: A list of strings describing aspects of the new location or situation.
                        Defaults to an empty list.
        :type context: list, optional
        """
        self._mental_state["location"] = location

        # context must also be updated when moved, since we assume that context is dictated partly by location.
        self.change_context(context)

    @transactional
    def change_context(self, context: list):
        """
        Changes the agent's current environmental context in its `_mental_state`.

        The context is a list of descriptive strings. This method also calls
        :meth:`~_update_cognitive_state` to ensure the agent's internal state reflects this change.

        :param context: A list of strings describing the new context (e.g., ["It is raining.", "The park is crowded."]).
        :type context: list
        """
        # The original code had a potential issue here: `{"description": item for item in context}`
        # This would only store the last item if context had multiple items, due to dict comprehension overriding keys.
        # Assuming the intent was to store the list of descriptions directly or a structured representation:
        # For simplicity and to match potential original intent of having a list of context strings:
        self._mental_state["context"] = context # Store as a list of strings

        # If it was meant to be a dictionary with unique keys, the structure would need to be different, e.g.:
        # self._mental_state["context"] = {"descriptions": context}
        # Or if each item was a key-value pair itself, that's different too.
        # Given the method signature `context: list`, storing it as a list seems most straightforward.

        self._update_cognitive_state(context=context)


    @transactional
    def make_agent_accessible(
        self,
        agent: Self,
        relation_description: str = "An agent I can currently interact with.",
    ):
        """
        Makes another agent accessible for interaction with this agent.

        Updates the internal `_accessible_agents` list and the `accessible_agents`
        field in `_mental_state`. This information is used in the system prompt
        to inform the LLM about potential interaction partners.

        :param agent: The :class:`TinyPerson` instance to make accessible.
        :type agent: TinyPerson
        :param relation_description: A description of the relationship with the accessible agent
                                     (e.g., "My colleague", "A stranger I just met").
                                     Defaults to "An agent I can currently interact with.".
        :type relation_description: str, optional
        """
        if agent not in self._accessible_agents:
            self._accessible_agents.append(agent)
            # Ensure mental_state["accessible_agents"] is a list
            if not isinstance(self._mental_state.get("accessible_agents"), list):
                self._mental_state["accessible_agents"] = []
            self._mental_state["accessible_agents"].append(
                {"name": agent.name, "relation_description": relation_description}
            )
            self.reset_prompt() # Prompt needs to be updated with new accessible agents
        else:
            logger.warning(
                f"[{self.name}] Agent {agent.name} is already accessible to {self.name}."
            )

    @transactional
    def make_agent_inaccessible(self, agent: Self):
        """
        Makes another agent inaccessible to this agent.

        Removes the agent from `_accessible_agents` and updates `_mental_state`.
        The agent's internal prompt is reset.

        :param agent: The :class:`TinyPerson` to make inaccessible.
        :type agent: TinyPerson
        """
        if agent in self._accessible_agents:
            self._accessible_agents.remove(agent)
            # Update mental state by filtering out the removed agent
            if isinstance(self._mental_state.get("accessible_agents"), list):
                self._mental_state["accessible_agents"] = [
                    a for a in self._mental_state["accessible_agents"] if a.get("name") != agent.name
                ]
            self.reset_prompt() # Prompt needs to be updated
        else:
            logger.warning(
                f"[{self.name}] Agent {agent.name} is already inaccessible to {self.name}."
            )

    @transactional
    def make_all_agents_inaccessible(self):
        """
        Makes all other agents inaccessible to this agent.

        Clears `_accessible_agents` and the `accessible_agents` list in `_mental_state`.
        The agent's internal prompt is reset.
        """
        self._accessible_agents = []
        self._mental_state["accessible_agents"] = []
        self.reset_prompt() # Prompt needs to be updated

    @transactional
    def _produce_message(self):
        # logger.debug(f"Current messages: {self.current_messages}")

        # ensure we have the latest prompt (initial system message + selected messages from memory)
        self.reset_prompt()

        messages = [
            {"role": msg["role"], "content": json.dumps(msg["content"])}
            for msg in self.current_messages
        ]

        logger.debug(f"[{self.name}] Sending messages to OpenAI API")
        logger.debug(f"[{self.name}] Last interaction: {messages[-1]}")

        next_message = openai_utils.client().send_message(messages, response_format=CognitiveActionModel)

        logger.debug(f"[{self.name}] Received message: {next_message}")

        return next_message["role"], utils.extract_json(next_message["content"])

    ###########################################################
    # Internal cognitive state changes
    ###########################################################
    @transactional
    def _update_cognitive_state(
        self, goals=None, context=None, attention=None, emotions=None
    ):
        """
        Updates the agent's `_mental_state` with new information.

        This method is called internally after actions are performed or when major state
        changes occur (like moving or changing context). It ensures that the datetime (if an
        environment is present), goals, context, attention, and emotions are current.
        It also updates `memory_context` by retrieving relevant memories for the new state
        and then resets the agent's prompt.

        :param goals: New list of goals. If None, existing goals are maintained.
        :type goals: list, optional
        :param context: New context description. If None, existing context is maintained.
        :type context: list, optional
        :param attention: New focus of attention. If None, existing attention is maintained.
        :type attention: str, optional
        :param emotions: New emotional state. If None, existing emotions are maintained.
        :type emotions: str, optional
        """

        # Update current datetime. The passage of time is controlled by the environment, if any.
        if self.environment is not None and self.environment.current_datetime is not None:
            self._mental_state["datetime"] = utils.pretty_datetime(self.environment.current_datetime)

        # update current goals
        if goals is not None:
            self._mental_state["goals"] = goals

        # update current context
        if context is not None:
            self._mental_state["context"] = context

        # update current attention
        if attention is not None:
            self._mental_state["attention"] = attention

        # update current emotions
        if emotions is not None:
            self._mental_state["emotions"] = emotions

        # update relevant memories for the current situation
        current_memory_context = self.retrieve_relevant_memories_for_current_context()
        self._mental_state["memory_context"] = current_memory_context

        self.reset_prompt()


    ###########################################################
    # Memory management
    ###########################################################
    def store_in_memory(self, value: Any):
        """
        Stores a value (typically a stimulus or action dictionary) in the agent's
        :class:`~tinytroupe.agent.memory.EpisodicMemory`.

        The `value` dictionary is expected to have 'role', 'content', 'type', and 'simulation_timestamp' keys.

        :param value: The dictionary representing the memory to store.
        :type value: Any (typically dict)
        """
        # TODO find another smarter way to abstract episodic information into semantic memory
        # self.semantic_memory.store(value)

        self.episodic_memory.store(value)

    def optimize_memory(self):
        """
        Placeholder for future memory optimization routines (e.g., summarization, consolidation).
        Currently does nothing.
        """
        pass #TODO

    def retrieve_memories(self, first_n: int, last_n: int, include_omission_info: bool = True, max_content_length: int = None) -> list:
        """
        Retrieves a slice of memories from :class:`~tinytroupe.agent.memory.EpisodicMemory`.

        Allows fetching the first N, last N, or a combination of memories.
        Content can be truncated for brevity.

        :param first_n: Number of earliest memories to retrieve.
        :type first_n: int
        :param last_n: Number of latest memories to retrieve.
        :type last_n: int
        :param include_omission_info: Whether to include placeholder messages if memories are omitted between first_n and last_n.
                                      Defaults to True.
        :type include_omission_info: bool, optional
        :param max_content_length: If provided, truncates the 'content' field of retrieved memories.
                                   Defaults to None (no truncation).
        :type max_content_length: int, optional
        :return: A list of memory dictionaries.
        :rtype: list
        """
        episodes = self.episodic_memory.retrieve(first_n=first_n, last_n=last_n, include_omission_info=include_omission_info)

        if max_content_length is not None:
            episodes = utils.truncate_actions_or_stimuli(episodes, max_content_length)

        return episodes


    def retrieve_recent_memories(self, max_content_length: int = None) -> list:
        """
        Retrieves recent memories from :class:`~tinytroupe.agent.memory.EpisodicMemory`
        based on its internal recency criteria (e.g., `EpisodicMemory.RECENCY_WINDOW`).

        Content can be truncated.

        :param max_content_length: If provided, truncates the 'content' field of retrieved memories.
                                   Defaults to None.
        :type max_content_length: int, optional
        :return: A list of recent memory dictionaries.
        :rtype: list
        """
        episodes = self.episodic_memory.retrieve_recent()

        if max_content_length is not None:
            episodes = utils.truncate_actions_or_stimuli(episodes, max_content_length)

        return episodes

    def retrieve_relevant_memories(self, relevance_target: str, top_k: int = 20) -> list:
        """
        Retrieves memories from :class:`~tinytroupe.agent.memory.SemanticMemory` that are
        semantically relevant to a given `relevance_target` string.

        Uses vector similarity search if the semantic memory is so configured.

        :param relevance_target: The text to find relevant memories for.
        :type relevance_target: str
        :param top_k: The maximum number of relevant memories to return. Defaults to 20.
        :type top_k: int, optional
        :return: A list of relevant memory content (typically strings or structured data).
        :rtype: list
        """
        relevant = self.semantic_memory.retrieve_relevant(relevance_target, top_k=top_k)

        return relevant

    def retrieve_relevant_memories_for_current_context(self, top_k: int = 7) -> list:
        """
        Constructs a relevance target string from the agent's current mental state
        (context, goals, attention, emotions, recent episodic memories) and then uses
        :meth:`~retrieve_relevant_memories` to find semantically similar memories from
        :class:`~tinytroupe.agent.memory.SemanticMemory`.

        These relevant memories are then stored in `_mental_state["memory_context"]` and
        are used in the agent's prompt generation.

        :param top_k: The maximum number of relevant memories to return for the context. Defaults to 7.
        :type top_k: int, optional
        :return: A list of relevant memory content.
        :rtype: list
        """
        # current context is composed of th recent memories, plus context, goals, attention, and emotions
        context_info = self._mental_state.get("context", "")
        goals_info = self._mental_state.get("goals", [])
        attention_info = self._mental_state.get("attention", "")
        emotions_info = self._mental_state.get("emotions", "")
        # Ensure recent_memories are properly formatted; handle potential non-dict items if any issue in retrieve_memories
        recent_memories_list = self.retrieve_memories(first_n=0, last_n=10, max_content_length=100)
        recent_memories_str = "\n".join([f"  - {m.get('content', '')}" for m in recent_memories_list if isinstance(m, dict)])

        # put everything together in a nice markdown string to fetch relevant memories
        target = f"""
        Current Context: {context}
        Current Goals: {goals}
        Current Attention: {attention}
        Current Emotions: {emotions}
        Recent Memories:
        {recent_memories}
        """

        logger.debug(f"Retrieving relevant memories for contextual target: {target}")

        return self.retrieve_relevant_memories(target, top_k=top_k)


    ###########################################################
    # Inspection conveniences
    ###########################################################
    def _display_communication(
        self,
        role,
        content,
        kind,
        simplified=True,
        max_content_length=default["max_content_display_length"],
    ):
        """
        Displays the current communication and stores it in a buffer for later use.
        """
        if kind == "stimuli":
            rendering = self._pretty_stimuli(
                role=role,
                content=content,
                simplified=simplified,
                max_content_length=max_content_length,
            )
            source = content["stimuli"][0]["source"]
            target = self.name
            
        elif kind == "action":
            rendering = self._pretty_action(
                role=role,
                content=content,
                simplified=simplified,
                max_content_length=max_content_length,
            )
            source = self.name
            target = content["action"]["target"]

        else:
            raise ValueError(f"Unknown communication kind: {kind}")

        # if the agent has no parent environment, then it is a free agent and we can display the communication.
        # otherwise, the environment will display the communication instead. This is important to make sure that
        # the communication is displayed in the correct order, since environments control the flow of their underlying
        # agents.
        if self.environment is None:
            self._push_and_display_latest_communication({"kind": kind, "rendering":rendering, "content": content, "source":source, "target": target})
        else:
            self.environment._push_and_display_latest_communication({"kind": kind, "rendering":rendering, "content": content, "source":source, "target": target})

    def _push_and_display_latest_communication(self, communication):
        """
        Pushes the latest communications to the agent's buffer.
        """
        self._displayed_communications_buffer.append(communication)
        print(communication["rendering"])

    def pop_and_display_latest_communications(self):
        """
        Pops the latest communications and displays them.
        """
        communications = self._displayed_communications_buffer
        self._displayed_communications_buffer = []

        for communication in communications:
            print(communication)

        return communications

    def clear_communications_buffer(self):
        """
        Cleans the communications buffer.
        """
        self._displayed_communications_buffer = []

    @transactional
    def pop_latest_actions(self) -> list:
        """
        Returns the latest actions performed by this agent. Typically used
        by an environment to consume the actions and provide the appropriate
        environmental semantics to them (i.e., effects on other agents).
        """
        actions = self._actions_buffer
        self._actions_buffer = []
        return actions

    @transactional
    def pop_actions_and_get_contents_for(
        self, action_type: str, only_last_action: bool = True
    ) -> list:
        """
        Returns the contents of actions of a given type performed by this agent.
        Typically used to perform inspections and tests.

        Args:
            action_type (str): The type of action to look for.
            only_last_action (bool, optional): Whether to only return the contents of the last action. Defaults to False.
        """
        actions = self.pop_latest_actions()
        # Filter the actions by type
        actions = [action for action in actions if action["type"] == action_type]

        # If interested only in the last action, return the latest one
        if only_last_action:
            return actions[-1].get("content", "")

        # Otherwise, return all contents from the filtered actions
        return "\n".join([action.get("content", "") for action in actions])

    #############################################################################################
    # Formatting conveniences
    #
    # For rich colors,
    #    see: https://rich.readthedocs.io/en/latest/appendix/colors.html#appendix-colors
    #############################################################################################

    def __repr__(self):
        return f"TinyPerson(name='{self.name}')"

    @transactional
    def minibio(self, extended=True):
        """
        Returns a mini-biography of the TinyPerson.

        Args:
            extended (bool): Whether to include extended information or not.

        Returns:
            str: The mini-biography.
        """

        base_biography = f"{self.name} is a {self._persona['age']} year old {self._persona['occupation']['title']}, {self._persona['nationality']}, currently living in {self._persona['residence']}."

        if self._extended_agent_summary is None and extended:
            logger.debug(f"Generating extended agent summary for {self.name}.")
            self._extended_agent_summary = openai_utils.LLMRequest(
                                                system_prompt="""
                                                You are given a short biography of an agent, as well as a detailed specification of his or her other characteristics
                                                You must then produce a short paragraph (3 or 4 sentences) that **complements** the short biography, adding details about
                                                personality, interests, opinions, skills, etc. Do not repeat the information already given in the short biography.
                                                repeating the information already given. The paragraph should be coherent, consistent and comprehensive. All information
                                                must be grounded on the specification, **do not** create anything new.
                                                """, 

                                                user_prompt=f"""
                                                **Short biography:** {base_biography}

                                                **Detailed specification:** {self._persona}
                                                """).call()

        if extended:
            biography = f"{base_biography} {self._extended_agent_summary}"
        else:
            biography = base_biography

        return biography

    def pp_current_interactions(
        self,
        simplified=True,
        skip_system=True,
        max_content_length=default["max_content_display_length"],
    ):
        """
        Pretty prints the current messages.
        """
        print(
            self.pretty_current_interactions(
                simplified=simplified,
                skip_system=skip_system,
                max_content_length=max_content_length,
            )
        )

    def pretty_current_interactions(self, simplified=True, skip_system=True, max_content_length=default["max_content_display_length"], first_n=None, last_n=None, include_omission_info:bool=True):
      """
      Returns a pretty, readable, string with the current messages.
      """
      lines = []
      for message in self.episodic_memory.retrieve(first_n=first_n, last_n=last_n, include_omission_info=include_omission_info):
        try:
            if not (skip_system and message['role'] == 'system'):
                msg_simplified_type = ""
                msg_simplified_content = ""
                msg_simplified_actor = ""

                lines.append(self._pretty_timestamp(message['role'], message['simulation_timestamp']))

                if message["role"] == "system":
                    msg_simplified_actor = "SYSTEM"
                    msg_simplified_type = message["role"]
                    msg_simplified_content = message["content"]

                    lines.append(
                        f"[dim] {msg_simplified_type}: {msg_simplified_content}[/]"
                    )

                elif message["role"] == "user":
                    lines.append(
                        self._pretty_stimuli(
                            role=message["role"],
                            content=message["content"],
                            simplified=simplified,
                            max_content_length=max_content_length,
                        )
                    )

                elif message["role"] == "assistant":
                    lines.append(
                        self._pretty_action(
                            role=message["role"],
                            content=message["content"],
                            simplified=simplified,
                            max_content_length=max_content_length,
                        )
                    )
                else:
                    lines.append(f"{message['role']}: {message['content']}")
        except:
            # print(f"ERROR: {message}")
            continue

      return "\n".join(lines)

    def _pretty_stimuli(
        self,
        role,
        content,
        simplified=True,
        max_content_length=default["max_content_display_length"],
    ) -> list:
        """
        Pretty prints stimuli.
        """

        lines = []
        msg_simplified_actor = "USER"
        for stimus in content["stimuli"]:
            if simplified:
                if stimus["source"] != "":
                    msg_simplified_actor = stimus["source"]

                else:
                    msg_simplified_actor = "USER"

                msg_simplified_type = stimus["type"]
                msg_simplified_content = utils.break_text_at_length(
                    stimus["content"], max_length=max_content_length
                )

                indent = " " * len(msg_simplified_actor) + "      > "
                msg_simplified_content = textwrap.fill(
                    msg_simplified_content,
                    width=TinyPerson.PP_TEXT_WIDTH,
                    initial_indent=indent,
                    subsequent_indent=indent,
                )

                #
                # Using rich for formatting. Let's make things as readable as possible!
                #

                rich_style = utils.RichTextStyle.get_style_for("stimulus", msg_simplified_type)
                lines.append(
                    f"[{rich_style}][underline]{msg_simplified_actor}[/] --> [{rich_style}][underline]{self.name}[/]: [{msg_simplified_type}] \n{msg_simplified_content}[/]"
                )
            else:
                lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _pretty_action(
        self,
        role,
        content,
        simplified=True,
        max_content_length=default["max_content_display_length"],
    ) -> str:
        """
        Pretty prints an action.
        """
        if simplified:
            msg_simplified_actor = self.name
            msg_simplified_type = content["action"]["type"]
            msg_simplified_content = utils.break_text_at_length(
                content["action"].get("content", ""), max_length=max_content_length
            )

            indent = " " * len(msg_simplified_actor) + "      > "
            msg_simplified_content = textwrap.fill(
                msg_simplified_content,
                width=TinyPerson.PP_TEXT_WIDTH,
                initial_indent=indent,
                subsequent_indent=indent,
            )

            #
            # Using rich for formatting. Let's make things as readable as possible!
            #
            rich_style = utils.RichTextStyle.get_style_for("action", msg_simplified_type)
            return f"[{rich_style}][underline]{msg_simplified_actor}[/] acts: [{msg_simplified_type}] \n{msg_simplified_content}[/]"
        
        else:
            return f"{role}: {content}"
    
    def _pretty_timestamp(
        self,
        role,
        timestamp,
    ) -> str:
        """
        Pretty prints a timestamp.
        """
        return f">>>>>>>>> Date and time of events: {timestamp}"

    def iso_datetime(self) -> str:
        """
        Returns the current datetime of the environment, if any.

        Returns:
            datetime: The current datetime of the environment in ISO forat.
        """
        if self.environment is not None and self.environment.current_datetime is not None:
            return self.environment.current_datetime.isoformat()
        else:
            return None

    ###########################################################
    # IO
    ###########################################################

    def save_specification(self, path, include_mental_faculties=True, include_memory=False):
        """
        Saves the current agent specification to a JSON file.

        This method serializes the agent's core attributes (persona, and optionally
        mental faculties and memory) to a JSON file. This allows the agent's state
        to be persisted and reloaded later using :meth:`~load_specification`.

        The actual attributes included depend on the `serializable_attributes` class variable
        and the `suppress_attributes` list constructed based on the method arguments.

        :param path: The file path where the JSON specification will be saved.
        :type path: str
        :param include_mental_faculties: Whether to include mental faculties
                                         in the saved specification. Defaults to True.
        :type include_mental_faculties: bool, optional
        :param include_memory: Whether to include episodic and semantic memory
                               in the saved specification. Defaults to False.
        :type include_memory: bool, optional

        Example:
            >>> agent.save_specification("my_agent_spec.json", include_memory=True)
        """

        suppress_attributes = []

        # should we include the memory?
        if not include_memory:
            suppress_attributes.append("episodic_memory")
            suppress_attributes.append("semantic_memory")

        # should we include the mental faculties?
        if not include_mental_faculties:
            suppress_attributes.append("_mental_faculties")

        self.to_json(suppress=suppress_attributes, file_path=path,
                     serialization_type_field_name="type")

    
    @staticmethod
    def load_specification(path_or_dict, suppress_mental_faculties=False, suppress_memory=False, auto_rename_agent=False, new_agent_name=None):
        """
        Loads an agent specification from a JSON file or a dictionary.

        This static method deserializes an agent's specification and creates a new
        :class:`TinyPerson` instance. It handles attribute suppression (e.g., not loading
        memory or faculties if desired) and agent renaming to avoid conflicts if
        `auto_rename_agent` or `new_agent_name` is used.

        The agent is registered in the global `TinyPerson.all_agents` list unless
        renaming fails due to persistent name collision (if `auto_rename_agent` is False
        and name exists).

        :param path_or_dict: The path to the JSON specification file or a dictionary
                             containing the specification.
        :type path_or_dict: str or dict
        :param suppress_mental_faculties: Whether to prevent loading
                                          mental faculties from the specification. Defaults to False.
        :type suppress_mental_faculties: bool, optional
        :param suppress_memory: Whether to prevent loading episodic and
                                semantic memory from the specification. Defaults to False.
        :type suppress_memory: bool, optional
        :param auto_rename_agent: If True and the agent name from the specification
                                  is already in use, automatically generates a new unique name
                                  (e.g., "AgentName_XXXX"). Defaults to False.
        :type auto_rename_agent: bool, optional
        :param new_agent_name: A specific new name to assign to the loaded agent,
                               overriding the name in the specification. If this name is
                               already in use, loading will fail unless `auto_rename_agent` is also True.
                               Defaults to None.
        :type new_agent_name: str, optional
        :return: A new :class:`TinyPerson` instance loaded from the specification.
        :rtype: TinyPerson

        Example:
            >>> loaded_agent = TinyPerson.load_specification("my_agent_spec.json")
            >>> print(f"Loaded agent: {loaded_agent.name}")
            >>> another_agent = TinyPerson.load_specification("my_agent_spec.json", new_agent_name="Agent_Clone")
        """

        suppress_attributes = []

        # should we suppress the mental faculties?
        if suppress_mental_faculties:
            suppress_attributes.append("_mental_faculties")

        # should we suppress the memory?
        if suppress_memory:
            suppress_attributes.append("episodic_memory")
            suppress_attributes.append("semantic_memory")

        return TinyPerson.from_json(json_dict_or_path=path_or_dict, suppress=suppress_attributes, 
                                    serialization_type_field_name="type",
                                    post_init_params={"auto_rename_agent": auto_rename_agent, "new_agent_name": new_agent_name})


    def encode_complete_state(self) -> dict:
        """
        Encodes the complete state of the TinyPerson, including the current messages, accessible agents, etc.
        This is meant for serialization and caching purposes, not for exporting the state to the user.
        """
        to_copy = copy.copy(self.__dict__)

        # delete the logger and other attributes that cannot be serialized
        del to_copy["environment"]
        del to_copy["_mental_faculties"]

        to_copy["_accessible_agents"] = [agent.name for agent in self._accessible_agents]
        to_copy['episodic_memory'] = self.episodic_memory.to_json()
        to_copy['semantic_memory'] = self.semantic_memory.to_json()
        to_copy["_mental_faculties"] = [faculty.to_json() for faculty in self._mental_faculties]

        state = copy.deepcopy(to_copy)

        return state

    def decode_complete_state(self, state: dict) -> Self:
        """
        Loads the complete state of the TinyPerson, including the current messages,
        and produces a new TinyPerson instance.
        """
        state = copy.deepcopy(state)
        
        self._accessible_agents = [TinyPerson.get_agent_by_name(name) for name in state["_accessible_agents"]]
        self.episodic_memory = EpisodicMemory.from_json(state['episodic_memory'])
        self.semantic_memory = SemanticMemory.from_json(state['semantic_memory'])
        
        for i, faculty in enumerate(self._mental_faculties):
            faculty = faculty.from_json(state['_mental_faculties'][i])

        # delete fields already present in the state
        del state["_accessible_agents"]
        del state['episodic_memory']
        del state['semantic_memory']
        del state['_mental_faculties']

        # restore other fields
        self.__dict__.update(state)


        return self
    
    def create_new_agent_from_current_spec(self, new_name:str) -> Self:
        """
        Creates a new agent from the current agent's specification. 

        Args:
            new_name (str): The name of the new agent. Agent names must be unique in the simulation, 
              this is why we need to provide a new name.
        """
        new_agent = TinyPerson(name=new_name, spec_path=None)
        
        new_persona = copy.deepcopy(self._persona)
        new_persona['name'] = new_name

        new_agent._persona = new_persona

        return new_agent
        

    @staticmethod
    def add_agent(agent):
        """
        Adds an agent to the global list of agents. Agent names must be unique,
        so this method will raise an exception if the name is already in use.
        """
        if agent.name in TinyPerson.all_agents:
            raise ValueError(f"Agent name {agent.name} is already in use.")
        else:
            TinyPerson.all_agents[agent.name] = agent

    @staticmethod
    def has_agent(agent_name: str):
        """
        Checks if an agent is already registered.
        """
        return agent_name in TinyPerson.all_agents

    @staticmethod
    def set_simulation_for_free_agents(simulation):
        """
        Sets the simulation if it is None. This allows free agents to be captured by specific simulation scopes
        if desired.
        """
        for agent in TinyPerson.all_agents.values():
            if agent.simulation_id is None:
                simulation.add_agent(agent)

    @staticmethod
    def get_agent_by_name(name):
        """
        Gets an agent by name.
        """
        if name in TinyPerson.all_agents:
            return TinyPerson.all_agents[name]
        else:
            return None
    
    @staticmethod
    def all_agents_names():
        """
        Returns the names of all agents.
        """
        return list(TinyPerson.all_agents.keys())

    @staticmethod
    def clear_agents():
        """
        Clears the global list of agents.
        """
        TinyPerson.all_agents = {}        
