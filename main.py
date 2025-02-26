import os
import pdfplumber
from flask import Flask, request, jsonify

app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    """Extracts text from the first 20 pages of a PDF."""
    extracted_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                if page_num >= 20:  # Limit to first 20 pages
                    break
                if page.extract_text():
                    extracted_text += page.extract_text() + "\n"

        # If no text was extracted, return an error
        if not extracted_text.strip():
            print("ERROR: No text extracted from PDF")
            return "ERROR: No text extracted from PDF", 400

        print("Extracted Text (First 500 chars):", extracted_text[:500])  # Debugging
        return extracted_text

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in PDF processing: {error_details}")
        return f"ERROR: PDF processing failed - {str(e)}", 500

@app.route('/extract-audit-text', methods=['POST'])
def extract_text():
    """API endpoint to process uploaded PDF and return extracted text."""
    if 'file' not in request.files:
        print("ERROR: No file uploaded")
        return "ERROR: No file uploaded", 400

    file = request.files['file']
    
    # Ensure the file is a PDF
    if not file.filename.lower().endswith(".pdf"):
        print("ERROR: Uploaded file is not a PDF")
        return "ERROR: Uploaded file is not a PDF", 400

    file_path = os.path.join("/tmp", file.filename)
    file.save(file_path)

    try:
        extracted_text = extract_text_from_pdf(file_path)
        os.remove(file_path)  # Clean up temporary file
        return extracted_text, 200  # Return plain text

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in extract_text: {error_details}")
        os.remove(file_path)  # Ensure cleanup even on failure
        return f"ERROR: {str(e)}", 500

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)
