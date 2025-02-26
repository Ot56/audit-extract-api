import openai
import os
import pdfplumber
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load OpenAI API key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI Client
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
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompt}]
        )

        structured_data = response.choices[0].message.content
        return structured_data

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in OpenAI API call: {error_details}")
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

def extract_audit_data(pdf_path):
    """Extracts text from PDF and processes it with OpenAI API."""
    extracted_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:20]:  # Limit to first 20 pages
                if page.extract_text():
                    extracted_text += page.extract_text() + "\n"

        if not extracted_text.strip():
            print("ERROR: No text extracted from PDF")
            return jsonify({"error": "Could not extract text from the PDF"}), 400

        print("Extracted Text:", extracted_text[:500])  # Debugging
        structured_data = process_text_with_ai(extracted_text)
        return structured_data

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in PDF processing: {error_details}")
        return jsonify({"error": f"PDF processing error: {str(e)}"}), 500

@app.route('/extract-audit-data', methods=['POST'])
def extract_data():
    """API endpoint to process uploaded PDF or download from URL."""
    temp_pdf_path = "/tmp/audit_file.pdf"

    try:
        # Case 1: File Upload
        if "file" in request.files:
            file = request.files["file"]
            file.save(temp_pdf_path)

        # Case 2: File URL
        elif "file_url" in request.json:
            file_url = request.json["file_url"]
            response = requests.get(file_url)
            if response.status_code == 200:
                with open(temp_pdf_path, "wb") as f:
                    f.write(response.content)
            else:
                return jsonify({"error": "Failed to download file"}), 400

        else:
            return jsonify({"error": "No file or URL received"}), 400

        extracted_data = extract_audit_data(temp_pdf_path)
        os.remove(temp_pdf_path)
        return jsonify(extracted_data)

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in extract_data: {error_details}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)
