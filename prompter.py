import os
from autogen import ConversableAgent, register_function
from faisslookup import faiss_lookup

# Step 1: Define the Prompter Agent
prompter = ConversableAgent(
    name="Prompter",
    system_message=(
        "You are a critical evaluator for suggested responses to user input. The user input can include text and/or images. "
        "Image descriptions (if any) will be provided to you. Your task is as follows:\n"
        " 1. Understand what the user wants by assessing the user's text input (if any) and accompanying image descriptions (if any). If the chat context is provided, you can also refer to that to understand the conversation flow so far./n" 
        " 2. Now that you know what the user wants, use the FAISS lookup tool to search the available knowledge to become familiar with the subject matter. You can repeat the searches up to 5 times to learn more, if necessary.\n"
        " 3. Now that you are familiar with the subject matter, analyze the suggested response given to you initially, and answer this simple question: 'Does the original suggested response completely address the user input **using only the knowledge from the FAISS lookup(s)**?' There is **no speculation or assumption or extrapolation** allowed, you **only** rely on the knowledge obtained from the FAISS lookup(s) to answer this question.\n" 
        " 4. If you answered yes, you agree that based purely on the knowledge from the FAISS lookup(s), this is the best answer we can give. In this case, print only 'LLM APPROVED' and you do not need to proceed any further.\n"
        " 5. If you answered no, you found **explicit** knowledge from the FAISS lookup(s) that can be used to make improvments to the suggested response. Note that you **cannot speculate about improvements** they **must** be backed by clear evidence **from the knowledge you obtained from the FAISS lookup(s).** Using this knowledge, make a list of improvements.\n"
        " 6. Finally, say 'Here is my revised response:' on a new line and on the line below, print your revised response to showcase **exactly** how your response is superior to the suggested response. To reiterate, **there is no room for vagueness or supposition or assumptions in your response.** On the last line after your response, also print 'LLM IMPROVEMENT NEEDED'"
    ),
    llm_config={
        "config_list": [{"model": "gpt-4o", "api_key": os.getenv("OPENAI_API_KEY")}]
    },
)

# Step 2: Define the User Proxy Agent
user_proxy = ConversableAgent(
    name="User",
    llm_config=False,
    is_termination_msg=lambda msg: msg.get("content") is not None and (
        "LLM APPROVED" in msg["content"] or "NO LLM INFO" in msg["content"] or "LLM IMPROVEMENT NEEDED" in msg["content"]
    ),
    human_input_mode="NEVER",
)

# Step 3: Register the FAISS Lookup Tool
register_function(
    faiss_lookup,
    caller=prompter,
    executor=user_proxy,
    name="faiss_lookup",
    description="A tool to search for information using FAISS-based retrieval. Provide a query to get relevant information.",
)

def process_response(input_data):
    """
    Evaluate the Thinker's response using the Prompter.
    Args:
        input_data (dict): A dictionary containing 'user_input', 'chat_context', and 'thinker_response'.

    Returns:
        dict: The Prompter's evaluation result.
    """
    user_input = input_data.get("user_input", "")
    chat_context = input_data.get("chat_context", "")
    thinker_response = input_data.get("thinker_response", "")

    # Combine inputs into a structured message for the Prompter
    combined_input = (
        f"User input: {user_input}\n\nChat context:\n{chat_context}\n\n"
        f"Suggested response:\n{thinker_response}"
    )

    # Send the message to the Prompter and retrieve the evaluation
    result = user_proxy.initiate_chat(
        prompter,
        message=combined_input,
        max_turns=6,  # Includes the initial message and up to 5 retries
    )

    # Return the summary of the Prompter's evaluation
    return result.summary

# Example Usage
if __name__ == "__main__":
    # Simulate data coming from the orchestrator
    input_data = {
        "user_input": "What is disposition code 15?",
        "thinker_response": "It means the mail failed.",
    }

    # Run the Prompter with the test data
    print("\n=== Test Case ===")
    print(f"Input Data: {input_data}")

    # Process the Prompter's response
    result = process_response(input_data)
    print("\n=== Prompter Result ===")
    print(result)
