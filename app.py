import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import docx

# --- SETUP ---
app = Flask(__name__)
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Routing Rules Dictionary (This will now be our single source of truth) ---
ROUTING_RULES = {
    "Invoice": "Notify Finance Department (finance@kmrl.com)",
    "Safety Circular": "Notify Operations & Safety Departments",
    "HR Policy": "Notify Human Resources Department",
    "Maintenance Report": "Notify Engineering & Rolling Stock Depts.",
    "Unclassified": "Flag for Manual Review"
}

# --- UNIFIED CORE FUNCTION (with a simpler prompt) ---

def analyze_document_with_gemini(file_path=None, text_content=None):
    """
    Analyzes a document using Gemini 1.5 Flash for classification and action items.
    """
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    # This prompt is now simpler and only asks for the category and action items.
    prompt = """
    You are an expert document sorter. Analyze the provided document and respond in a valid JSON format with two keys:
    1. "predicted_category": Classify the document into one of these categories: 'Invoice', 'Safety Circular', 'HR Policy', 'Maintenance Report', or 'Unclassified'.
    2. "extracted_action_items": A list of specific action items, tasks, or deadlines found in the document as strings. If none are found, provide an empty list [].
    """

    try:
        prompt_parts = [prompt]
        uploaded_file = None

        if text_content:
            prompt_parts.append(text_content)
        elif file_path:
            uploaded_file = genai.upload_file(path=file_path)
            prompt_parts.append(uploaded_file)
        else:
            return {"error": "No content provided to analyze."}

        response = model.generate_content(prompt_parts)
        
        if uploaded_file:
            genai.delete_file(uploaded_file.name)

        clean_json_string = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_json_string)

    except Exception as e:
        print(f"An error occurred during Gemini analysis: {e}")
        return {"error": "Failed to analyze document", "details": str(e)}

# --- UPDATED API ENDPOINT (with added routing logic) ---
@app.route('/analyze_document', methods=['POST'])
def analyze_document_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    filename = file.filename
    if filename == '':
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    results = {}
    file_extension = filename.split('.')[-1].lower()

    if file_extension == 'docx':
        try:
            doc = docx.Document(filepath)
            full_text = "\n".join([para.text for para in doc.paragraphs])
            results = analyze_document_with_gemini(text_content=full_text)
        except Exception as e:
            results = {"error": f"Failed to read DOCX file: {e}"}
    
    elif file_extension in ['pdf', 'png', 'jpg', 'jpeg']:
        results = analyze_document_with_gemini(file_path=filepath)
    
    else:
        results = {"error": f"Unsupported file type: '{file_extension}'"}

    os.remove(filepath)

    # --- THIS IS THE FIX ---
    # We now add the routing action here, based on the reliable rules dictionary.
    if "error" not in results:
        category = results.get("predicted_category", "Unclassified")
        results["routing_action"] = ROUTING_RULES.get(category, "Flag for Manual Review")

    return jsonify(results)

# --- RUN THE APP ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)