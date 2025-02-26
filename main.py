import json
import os
import pdfplumber
import openai
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key!")

openai.api_key = OPENAI_API_KEY

# Debug: Print API key (REMOVE this after debugging)
print("Loaded OpenAI API Key:", OPENAI_API_KEY[:5] + "*****" if OPENAI_API_KEY else "Not Found")

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
    except Exception as e:
        print(f"❌ Error extracting text from PDF: {e}")
    return text.strip()

def process_text_with_ai(text):
    """Processes extracted text with OpenAI API to extract structured data."""
    if not text:
        print("❌ No text extracted from PDF.")
        return json.dumps({"error": "Failed to extract text from PDF"})

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract key data fields from an energy audit report."},
                {"role": "user", "content": f"Extract the following details from this report:\n\n{text}"}
            ],
            temperature=0
        )

        # Debug: Log OpenAI API Response
        print("✅ OpenAI API Response:", response)

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("OpenAI returned an empty response.")

        return response.choices[0].message.content

    except openai.OpenAIError as e:
        print(f"❌ ERROR in OpenAI API call: {e}")
        return json.dumps({"error": "OpenAI API error", "details": str(e)})

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return json.dumps({"error": "Unexpected error", "details": str(e)})

@app.route("/extract-audit-data", methods=["POST"])
def extract_data():
    """Handles PDF file upload, processes it, and returns structured JSON data."""
    if "file" not in request.files:
        print("❌ No file uploaded.")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        print("❌ Empty file received.")
        return jsonify({"error": "Empty file"}), 400

    temp_pdf_path = "/tmp/uploaded_audit.pdf"
    file.save(temp_pdf_path)

    print(f"✅ Received file: {file.filename}")

    extracted_text = extract_text_from_pdf(temp_pdf_path)
    print(f"📄 Extracted text (first 500 chars): {extracted_text[:500]}")  # Debug: Show first 500 chars

    if not extracted_text:
        print("❌ No text extracted from PDF.")
        return jsonify({"error": "Failed to extract text from PDF"}), 500

    structured_data = process_text_with_ai(extracted_text)

    return safe_json_response(structured_data)

def safe_json_response(structured_data):
    """Ensures the structured data is returned as valid JSON."""
    try:
        structured_json = json.loads(structured_data)
        return jsonify(structured_json)
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decoding Error: {e}")
        return jsonify({"error": "Invalid JSON format"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
