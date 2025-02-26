import openai
import os
import pdfplumber
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load OpenAI API key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI Client
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def process_text_with_ai(text):
    """Send extracted text to OpenAI and ensure a valid JSON response."""
    prompt = f"""
    Extract the following details from the given text:
    - Prénom
    - Nom
    - Adresse (Numéro, Voie, Code Postal, Ville)
    - Classe énergétique avant et après travaux
    - Date de réalisation de l’audit
    - Identifiant de l’audit
    - Consommation énergie (finale & primaire, avant & après)
    - Surface avant et après projet
    - Émission CO2 avant et après
    - Date de la visite audit

    Provide the data in **strict JSON format** with no extra text.

    Text:
    {text}
    """

    try:
        print(f"Using OpenAI API key: {OPENAI_API_KEY[:5]}*****")  # Debugging API key presence

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use GPT-4o Mini
            messages=[{"role": "system", "content": prompt}]
        )

        structured_data = response.choices[0].message.content.strip()  # Ensure no leading/trailing spaces

        print(f"Raw OpenAI Response: {structured_data}")  # Debugging OpenAI response

        # Ensure response is a valid JSON format
        try:
            return json.loads(structured_data)
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON received from OpenAI: {structured_data}")
            return {"error": "Invalid JSON format from OpenAI"}

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in OpenAI API call: {error_details}")  # Debugging
        return {"error": f"OpenAI API error: {str(e)}"}

def extract_audit_data(pdf_path):
    """Extracts text from PDF and processes it with OpenAI API."""
    extracted_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:20]:  # Limit extraction to first 20 pages
                if page.extract_text():
                    extracted_text += page.extract_text() + "\n"

        if not extracted_text.strip():
            print("ERROR: No text extracted from PDF")  # Debugging
            return {"error": "Could not extract text from the PDF"}

        print("Extracted Text:", extracted_text[:500])  # Debugging - Show first 500 chars

        structured_data = process_text_with_ai(extracted_text)
        return structured_data

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in PDF processing: {error_details}")  # Debugging
        return {"error": f"PDF processing error: {str(e)}"}

@app.route('/extract-audit-data', methods=['POST'])
def extract_data():
    """API endpoint to process uploaded PDF and return extracted data."""
    if 'file' not in request.files:
        print("ERROR: No file uploaded")  # Debugging
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if not file.filename.lower().endswith(".pdf"):
        print("ERROR: Uploaded file is not a PDF")  # Debugging
        return jsonify({"error": "Uploaded file is not a PDF"}), 400

    file_path = os.path.join("/tmp", file.filename)
    file.save(file_path)

    try:
        extracted_data = extract_audit_data(file_path)
        os.remove(file_path)  # Free up memory
        return jsonify(extracted_data)  # Ensures proper JSON formatting

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in extract_data: {error_details}")  # Debugging
        os.remove(file_path)  # Cleanup on failure
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")  # Debugging
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)
