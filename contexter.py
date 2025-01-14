import json
import os
from autogen import ConversableAgent

# Step 1: Define the Contexter Agent
contexter_agent = ConversableAgent(
    name="Contexter",
    system_message=(
        "You are a context manager agent. Your task is to maintain a running context of interactions, "
        "prioritizing recent interactions while phasing out older ones. "
        "Ensure the context is concise, focused, and limited to 200 words. "
        "The context must retain critical information from the most recent interactions."
    ),
    llm_config={
        "config_list": [{"model": "gpt-4o", "api_key": os.getenv('OPENAI_API_KEY')}]
    },
)

# Step 2: Define the Dummy User Proxy
user_proxy = ConversableAgent(
    name="User",
    llm_config=False,
    is_termination_msg=lambda msg: msg.get("content") is not None and "FINAL LLM RESPONSE" in msg["content"],
    human_input_mode="NEVER",
)


def update_context(interaction_data):
    """
    Updates the context based on the latest interaction data.

    Args:
        interaction_data (dict): Contains the current context, user input, image descriptions, and response.

    Returns:
        str: Updated context limited to 200 words.
    """
    # Convert the interaction data to JSON string format for the agent
    context_message = json.dumps(interaction_data)

    # Use the user proxy to initiate a chat with the Contexter agent
    context_response = user_proxy.initiate_chat(
        contexter_agent,  # Pass the Contexter Agent
        message=context_message,  # JSON-formatted input for context update
        max_turns=1,  # Single-turn context update
    )

    # Extract the updated context from the response
    updated_context = context_response.summary.strip()
    return updated_context
