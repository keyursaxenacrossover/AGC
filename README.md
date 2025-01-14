# Autogen-Based Chatbot

## About
This is an autogen-based chatbot that relies on a FAISS-based index to lookup answers for user inputs. The index is currently built using the Discover XI (Tivian) knowledge base articles from Zendesk.

## How It Works
1. **`main.py`** handles the workflow.
2. The combined user input (text + images) is sent to **`securityagent.py`**, which processes it for malicious intent after generating descriptions from attached images. If malicious intent is detected, the user is informed, and the workflow ends. Otherwise, the process continues.
3. If iumages are provided, they are sent to the **`.\images`** directory and after processing, transferred to the **`.\images_to_delete`** directory.
4. The input (with image descriptions) is handed off to **`orchestrator.py`**, which passes it to **`thinker.py`**. This acts as the first responder, searching the local FAISS index for relevant data using **`faisslookup.py`**, a tool registered with the autogen agent. If no data is found, the orchestrator terminates the workflow and informs the user about the lack of sufficient information.
5. If the thinker finds information, it composes a draft response and sends it to the orchestrator.
6. The orchestrator sends this draft to **`prompter.py`**, the final responder. It searches for possible improvements to the thinker response using the same FAISS index. It determines whether the response is acceptable as is or needs improvement. If improvement is possible, it makes the necessary changes and composes the final reply.
7. The chat context is stored using **`contexter.py`** for subsequent messages.
8. At this point, the frontend displays the final response based on the outcomes decided by the orchestrator's routing agent:
    - **Scenario 1**: If the Thinker's response is `NO LLM INFO`, inform the user that insufficient knowledge is available to answer their inquiry.
    - **Scenario 2**: If the Prompter's response contains `LLM APPROVED`, output the Thinker's response exactly as it is, minus `LLM APPROVED`.
    - **Scenario 3**: If the Prompter's response contains `LLM IMPROVEMENT NEEDED`, output the Prompter's improved response exactly as it is, minus `LLM IMPROVEMENT NEEDED`.
    - **Scenario 4**: Handle unexpected scenarios with: `An unexpected error occurred.`
9. The user can then resume the conversation.

## Helper Files
1. **`config.py`**: Dynamically passes directories for the project to various other files.
2. **`process_json_docs.py`**: Handles chunking of the JSON articles downloaded via the Zendesk API. Uses hashing to determine if chunks need updating (for new/updated articles) or can remain unchanged for the next run.
3. **`generate_embeddings.py`**: Embeds the chunks in the FAISS index for speedy lookups and encodes the chunks in metadata. It is fully regenerated in every run to avoid retaining outdated information.
4. **`testfaisslookup.py`**: Used for testing the FAISS lookup with a query directly outside the chatbot workflow, useful for debugging the FAISS index.

## How to Use (Windows Instructions)
Extrapolate these instructions for Mac and Linux as needed.

1. Download the 'Source code (zip)' from the [latest release](https://github.com/keyursaxenacrossover/AGC/releases) and extract the application folder from the archive to your machine.
2. Add the following system-level environment variables to the machine where the code will run:
    - `OPENAI_API_KEY`: Set this to your OpenAI API key.
    - `AUTOGEN_USE_DOCKER`: Set this to `0`.
3. Ensure Python 3.12 is installed. Download it from [Python.org](https://www.python.org/downloads/release/python-3128/). Scroll down for installers. **Do not use Python 3.13 as it is incompatible with autogen**.
4. Verify Python installation by entering `python --version` in PowerShell. If you see `'The term 'python' is not recognized'`, fix the installation (likely need to add Python to PATH).
5. Navigate to the application folder directory in PowerShell, e.g., `cd C:\AGC-AGC` if placed in the C drive and if the folder is named AGC-AGC.
6. Run the command: `pip install -r requirements.txt`.
7. After installation, run: `python .\main.py`.
8. Wait for the console to display something like:
    ```
     * Debugger is active!
     * Debugger PIN: 806-584-423
    ```
9. Open your web browser (avoid using IE) and go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).
10. The chatbot interface will load. Use the input box at the bottom to type your message. You can attach PNG images using the browse button or drag and drop them.
11. Click "Send". The application will process your input, showing a "Processing" message. The workflow can be observed in the PowerShell window.

---
