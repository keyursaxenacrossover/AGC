About:
This is an autogen-based chatbot that relies on a FAISS based index to lookup answers for user inputs. The index is currently built using the Discover XI (Tivian) knowledge base articles from Zendesk.

How it works:
1. main.py handles the workflow.
2. The combined user input (text+images) are sent to securityagent.py which processes it for malicious intent after generating descriptions from attached images. If malicious intent is detected, we inform the user and end the workflow. If not, we proceed with the next step.
3. The input (with image descriptions) is handed off to orchestrator.py which passes it to thinker.py. This is our first responder that searches the local FAISS index for relevant data. The search is a tool registered with the autogen agent and the function is available in faisslookup.py. If no data is found, it innforms the orchestrator which terminates the workflow and informs the user that we do not have sufficient info to address their input.
4. If the thinker finds information, if composes a draft response and sends it to the orchestrator.
5. The orchestrator then sends this to prompter.py which acts as the final responder. It searches for possible improvements to the thinker response using the same FAISS index. It decides whether the thinker response is acceptable as is, or if improvements are needed. If improvements are possible it makes them and composes the final reply.
6. We then store the chat context so far using contexter.py which we send in subsequent messages.
7. At this point, the frontend should display the final response based on the outcomes decided by the orchestrator's routing agent:
```
"1. If the Thinker's response is 'NO LLM INFO', politely inform the user that we have insufficient knowledge to answer their inquiry."
"2. If the Prompter's response contains 'LLM APPROVED', output the Thinker's response exactly as it is, minus 'LLM APPROVED'."
"3. If the Prompter's response contains 'LLM IMPROVEMENT NEEDED', output the Prompter's improved response exactly as it is, minus 'LLM IMPROVEMENT NEEDED'."
"4. Handle unexpected scenarios with: 'An unexpected error occurred.'"
```
8. The user is free to resume the conversation.

How to use (for Windows, extrapolate to Mac and Linux based on these instructions, I am not familiar with these systems):

1. Get the 'Source code (zip)' from the latest release: https://github.com/keyursaxenacrossover/AGC/releases and copy the 'AGC-AGC' folder from the archive to your machine. Rename it 'AGC' so in this AGC folder you should see several other folders and several .py files.
2. Add the following system level environment variables on the machine where you will be running the code:
- OPENAI_API_KEY with your key.
- AUTOGEN_USE_DOCKER set to 0.
3. Ensure that you have the latest Python 3.12 installed https://www.python.org/downloads/release/python-3128/ (scroll down for installers, not tested with other builds and 3.13 is not compatible with autogen).
4. Verfy that Python is working my entering `python --version` in PowerShell. You should get an output like 'Python 3.12.8' depending on your build, if you get 'The term 'python' is not recognized' instead, fix your Python installation (probably need to add it to PATH).
5. Once Python is installed, Navigate to your AGC directory in PowerShell (`cd C:\AGC` if you placed the AGC folder in your C drive directory, for example).
6. Run `pip install -r requirements.txt`
7. Once the process is complete, run `python .\main.py`
8. Wait for the console to show something like:
```
 * Debugger is active!
 * Debugger PIN: 806-584-423
 ```
 9. Then, open your web browser (please do not use IE for the sake of everyone's sanity) and navigate to http://127.0.0.1:5000/
 10. The chatbot interface should load up. At the bottom, you should see 'Type your message here...' where you input text, and a browse button where you can click to select PNG image files to add context to your text input. You can also directly drag and drop the PNG files on this button to attach them.
 11. Once ready, click send. The application will start processing your input and show a "Processing" message while it prepares a response. You can see the workflow directly in the PowerShell window where you ran `python .\main.py`