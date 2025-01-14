import os
from autogen import ConversableAgent, register_function
from faisslookup import faiss_lookup
from config import openaikey

# Step 1: Define the Assistant Agent
assistant = ConversableAgent(
    name="Assistant",
    system_message=(
        "You are an experienced technical support rep responding to the user input. The user input can include text and/or images. "
        "Image descriptions (if any) will be provided to you. Your task is as follows:\n"
        " 1. Understand what the user wants by assessing the user's text input (if any) and accompanying image descriptions (if any). If the chat context is provided, you can also refer to that to understand the conversation flow so far./n" 
        " 2. Now that you know what the user wants, use the FAISS lookup tool to search the available knowledge to become familiar with the subject matter. You can repeat the searches up to 5 times to learn more, if necessary.\n"
        " 3. If you found no relevant data in the knowledge after the FAISS lookup(s), we do not have enough information to provide a proper response to the user. Just say 'NO LLM INFO' and nothing else. No further steps are necessary.\n"
        " 4. If we have relevant data from the knowledge after the FAISS lookup(s), compose a complete, comprehensive, systematic, highly technical response for the user without being overly verbose. The response should address the user input fully in one go, leaving no room for doubts or follow ups. Make the response readable rather than printing walls of text. Also, make it engaging by providing examples where necessary. Use **only** information you found with the FAISS lookup(s) in your response.\n"
        " 5. Ensure that you print 'FINAL LLM RESPONSE' on a new line after your response if the result is **not** 'NO LLM INFO' and you have composed a suitable response to the user. Otherwise, your response is just 'NO LLM INFO' because there is no relevant data in the FAISS lookup(s) to address the user input."
    ),
    llm_config={
        "config_list": [{"model": "gpt-4o", "api_key": openaikey}]
    },
)

# Step 2: Define the User Proxy Agent
user_proxy = ConversableAgent(
    name="User",
    llm_config=False,
    is_termination_msg=lambda msg: msg.get("content") is not None and (
        "FINAL LLM RESPONSE" in msg["content"] or "NO LLM INFO" in msg["content"]
    ),
    human_input_mode="NEVER",
)

# Step 3: Register the faiss_lookup Tool
register_function(
    faiss_lookup,
    caller=assistant,
    executor=user_proxy,
    name="faiss_lookup",
    description="A tool to search for information using FAISS-based retrieval. Provide a query to get relevant information.",
)

def process_query(user_question):
    """
    Process the user question using the thinker logic and return the result.
    """
    max_retries = 5  # Maximum retries for FAISS lookup
    result = user_proxy.initiate_chat(
        assistant,
        message=user_question,
        max_turns=max_retries + 1,  # Include the initial query and retries
    )
    return result.summary
