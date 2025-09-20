import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import pytesseract
from PIL import Image
import fitz  # PyMuPDF

# --- SETUP ---
app = Flask(__name__)
load_dotenv()
# Configure the Gemini API client with the key from your .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Routing Rules Dictionary ---
ROUTING_RULES = {
    "Invoice": "Notify Finance Department (finance@kmrl.com)",
    "Safety Circular": "Notify Operations & Safety Departments",
    "HR Policy": "Notify Human Resources Department",
    "Maintenance Report": "Notify Engineering & Rolling Stock Depts.",
    "Unclassified": "Flag for Manual Review"
}

# --- CORE FUNCTIONS ---

def extract_text_with_ocr(pdf_path):
    """Converts a scanned PDF to images and uses Tesseract to extract text."""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img)
        doc.close()
        return text
    except Exception as e:
        print(f"Error during OCR: {e}")
        return None

def classify_document(document_text):
    """Uses the Gemini API to classify a document."""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""
    Classify the following document into one of these categories: 'Invoice', 'Safety Circular', 'HR Policy', 'Maintenance Report'.
    Respond with ONLY the category name. TEXT: {document_text[:8000]}
    """
    try:
        response = model.generate_content(prompt)
        category = response.text.strip()
        if category in ROUTING_RULES:
            return category
        return "Unclassified"
    except Exception as e:
        print(f"An error during Gemini classification: {e}")
        return "Classification Error"

def extract_action_items(document_text):
    """Uses the Gemini API to extract action items."""
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""
    Analyze the following text and extract a bulleted list of specific action items, tasks, or deadlines.
    If there are no action items, respond with 'No specific action items found.'
    TEXT: {document_text[:8000]}
    """
    try:
        response = model.generate_content(prompt)
        # Split the response by newlines to create a list
        return response.text.strip().split('\n')
    except Exception as e:
        print(f"An error during action item extraction: {e}")
        return ["Error extracting action items."]

# --- API ENDPOINT ---
@app.route('/analyze_document', methods=['POST'])
def analyze_document_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        extracted_text = extract_text_with_ocr(filepath)
        if not extracted_text:
            return jsonify({"error": "Could not extract text from the document."}), 500

        category = classify_document(extracted_text)
        action_items = extract_action_items(extracted_text)
        routing_action = ROUTING_RULES.get(category, "Flag for Manual Review")

        os.remove(filepath)

        return jsonify({
            "filename": file.filename,
            "predicted_category": category,
            "routing_action": routing_action,
            "extracted_action_items": action_items,
            "text_preview": extracted_text[:200] + "..."
        })

# --- RUN THE APP ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)