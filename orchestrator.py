import json
import os
from thinker import process_query
from prompter import process_response
from autogen import ConversableAgent

# Step 1: Define the Routing Agent
routing_agent = ConversableAgent(
    name="Router",
    system_message=(
        "You are a response routing agent. Based on the provided inputs, "
        "route the response to the user using these rules:\n\n"
        "1. If the Thinker's response is 'NO LLM INFO', politely inform the user that we have insufficient knowledge to answer their inquiry.\n"
        "2. If the Prompter's response contains 'LLM APPROVED', output the Thinker's response exactly as it is, minus 'LLM APPROVED'.\n"
        "3. If the Prompter's response contains 'LLM IMPROVEMENT NEEDED', output the Prompter's improved response exactly as it is, minus 'LLM IMPROVEMENT NEEDED'.\n"
        "4. Handle unexpected scenarios with: 'An unexpected error occurred.'\n\n"
        "Print the final answer word for word without any additions or enhancements."
    ),
    llm_config={
        "config_list": [{"model": "gpt-4o", "api_key": os.getenv("OPENAI_API_KEY")}]
    },
)

# Step 2: Define the Dummy User Proxy
user_proxy = ConversableAgent(
    name="User",
    llm_config=False,
    is_termination_msg=lambda msg: msg.get("content") is not None and (
        "FINAL LLM RESPONSE" in msg["content"] or "NO LLM INFO" in msg["content"]
    ),
    human_input_mode="NEVER",
)

def orchestrate(user_input, context_so_far):
    """
    Orchestrates the interaction by passing the user input and context to Thinker,
    recording its response, and sending the response to the Prompter for evaluation if needed.
    """
    print("Orchestrator: Sending input to Thinker...")

    # Prepare the input for the thinker, including the context
    thinker_input = f"{user_input}\n\nChat context:\n{context_so_far}"
    thinker_response = process_query(thinker_input)

    # Determine routing scenario
    if thinker_response.strip() == "NO LLM INFO":
        # Case: Thinker has no knowledge
        print("Orchestrator: Thinker returned 'NO LLM INFO'.")
        routing_input = {
            "thinker_response": "NO LLM INFO",
            "prompter_result": "",
        }
    else:
        print("Orchestrator: Received response from Thinker.")
        print(f"Thinker Response: {thinker_response}")

        print("Orchestrator: Sending Thinker's response to Prompter for evaluation...")

        # Prepare input for Prompter, inserting context appropriately
        prompter_input = {
            "user_input": user_input,
            "chat_context": context_so_far,
            "thinker_response": thinker_response,
        }
        prompter_result = process_response(prompter_input)
        print("Orchestrator: Received response from Prompter.")

        # Prepare routing input
        routing_input = {
            "thinker_response": thinker_response,
            "prompter_result": prompter_result,
        }

    # Step 3: Route the response via the Routing Agent
    print("Orchestrator: Routing the final response...")
    routing_message = json.dumps(routing_input)  # Convert dictionary to a JSON-formatted string
    routing_response = user_proxy.initiate_chat(
        routing_agent,  # Pass the Routing Agent
        message=routing_message,  # JSON-formatted input for routing
        max_turns=1,  # Single-turn conversation
    )

    # Step 4: Extract and return the final response directly
    final_response = routing_response.summary.strip()
    print("\n=== Final Routed Response ===")
    print(final_response)
    return final_response

