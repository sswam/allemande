The conductor determines which agent(s) should respond to a message, considering various factors.

*   **Invocation Methods:**
    *   `@mention`: Invokes agents explicitly mentioned using the `@` symbol. The `at_only` flag forces only specifically mentioned agents to respond, while not mentioning anyone results in no agents responding.
    *   Plain Name: Invokes agents by their plain names within the message content, without the `@` symbol.
    *   Direct Reply: Invokes the agent who spoke last in the chat history.
    *   Mediator: Invokes a specified mediator agent.
    *   Default: Invokes a default list of agents if no other invocation method applies.
    *   Last AI Speaker: Invokes the AI agent who spoke last if other methods fail.
    *   Random AI: Selects a random AI agent from the list of participants.

*   **Exclusion and Prioritization:**
    *   Excludes specified participants, tools, and system messages from consideration.
    *   Filters out human users from responding if `include_humans` is set to `False`.
    *   Filters agents based on access control lists defined for the room.

*   **Agent Configuration:**
    *   Distinguishes between human agents, AI agents, and tool agents based on their `type` attribute.
    *   Supports aliasing, mapping lower-case names and aliases to canonical agent names.

*   **Room Context:**
    *   Considers the chat history, including the message content and the order of speakers.
    *   Identifies the responsible human user based on the most recent human message or the room name.
    *   Allows skipping image replies, removing them from the history considered.

*   **Agent Selection Logic:**
    *   Prioritizes explicit `@mention` invocation over other methods.
    *   Allows for configuration of a `direct_reply_chance` to control the likelihood of responding to the last speaker.
    *   Allows for configuration of an `ai_invoked_reply_chance` to control the likelihood of an AI responding.
    *   Uses mediators to handle the conversation flow.

*   **Access Control:**
    *   Uses a cache to efficiently check agent access permissions for the current room.

*   **Configuration Options:**
    *   `include_self`: Allows agents to respond to themselves.
    *   `include_humans_for_ai_message` and `include_humans_for_human_message`: Controls whether human agents are included in the list of potential responders based on the speaker type.
    *   `may_use_mediator`: Allows the conductor to select a mediator agent.
    *    `at_only`: If at_only is True, only agents who have been @ mentioned should reply, and if nobody is mentioned, no one should reply
    *   `use_aggregates`: if false, @everyone style directives are ignored.

*   **Return Values:**
    *   Returns the responsible human user and a list of agent names that should respond.
