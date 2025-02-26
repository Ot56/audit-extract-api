import openai
import os
import pdfplumber
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load OpenAI API key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI Client for v1.0
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def process_text_with_ai(text):
    """Send extracted text to OpenAI to structure the data."""
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

    Provide the data in JSON format.

    Text:
    {text}
    """

    try:
        print(f"Using OpenAI API key: {OPENAI_API_KEY[:5]}*****")  # Debugging API key presence

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use GPT-4o Mini
            messages=[{"role": "system", "content": prompt}]
        )

        structured_data = response.choices[0].message.content
        return structured_data

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in OpenAI API call: {error_details}")  # Debugging - Print full error details
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

def extract_audit_data(pdf_path):
    """Extracts text from PDF and processes it with OpenAI API."""
    extracted_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    extracted_text += page.extract_text() + "\n"

        # If no text was extracted, return an error
        if not extracted_text.strip():
            print("ERROR: No text extracted from PDF")  # Debugging
            return jsonify({"error": "Could not extract text from the PDF"}), 400

        print("Extracted Text:", extracted_text[:500])  # Debugging - Show first 500 chars

        # Process the extracted text using OpenAI
        structured_data = process_text_with_ai(extracted_text)
        return structured_data

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in PDF processing: {error_details}")  # Debugging - Print errors in Render logs
        return jsonify({"error": f"PDF processing error: {str(e)}"}), 500

@app.route('/extract-audit-data', methods=['POST'])
def extract_data():
    """API endpoint to process uploaded PDF and return extracted data."""
    if 'file' not in request.files:
        print("ERROR: No file uploaded")  # Debugging
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    
    # Ensure the file is a PDF
    if not file.filename.lower().endswith(".pdf"):
        print("ERROR: Uploaded file is not a PDF")  # Debugging
        return jsonify({"error": "Uploaded file is not a PDF"}), 400

    file_path = os.path.join("/tmp", file.filename)
    file.save(file_path)

    try:
        extracted_data = extract_audit_data(file_path)
        os.remove(file_path)  # Free up memory
        import json
return jsonify(json.loads(structured_data))


    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in extract_data: {error_details}")  # Debugging - Print errors in Render logs
        os.remove(file_path)  # Ensure cleanup even on failure
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")  # Debugging
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)
