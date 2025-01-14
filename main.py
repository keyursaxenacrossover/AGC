import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from securityagent import analyze_images, run_security_check
from orchestrator import orchestrate
from contexter import update_context
from config import imagedir

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = imagedir  # Directory to temporarily store uploaded images
app.config['ALLOWED_EXTENSIONS'] = {'png'}

context_so_far = ""  # Global context for maintaining chat history

def allowed_file(filename):
    """Check if the file is a valid PNG."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Render the main frontend."""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_input():
    """Handle user input and image uploads."""
    global context_so_far

    # Get user input
    user_question = request.form.get('user_text', '').strip()

    # Handle uploaded images
    uploaded_files = request.files.getlist('images[]')
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

    # Analyze images
    image_descriptions = analyze_images(app.config['UPLOAD_FOLDER'], user_question)

    # Run security check
    result = run_security_check(user_question, image_descriptions)
    if result["malicious"] == "Y":
        malicious_reason = result["final_response"].split("MALICIOUS: ")[-1]
        return jsonify({"error": f"Malicious input detected: {malicious_reason}"})

    # Orchestrate response
    full_user_input = (
        f"The user provided this text input:\n{result['user_input']}\n\n"
        f"The user also provided these images:\n" + "\n".join(result['image_descriptions'])
    )
    orchestrator_result = orchestrate(full_user_input, context_so_far)

    # Update context
    interaction_data = {
        "context_so_far": context_so_far,
        "user_text_input": result["user_input"],
        "user_image_descriptions": result["image_descriptions"],
        "response_to_user": orchestrator_result,
    }
    context_so_far = update_context(interaction_data)

    # Return final response
    return jsonify({"response": orchestrator_result})

if __name__ == '__main__':
    app.run(debug=True)
