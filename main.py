import os
import pdfplumber
import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_path
from flask import Flask, request, jsonify

app = Flask(__name__)

def extract_text_from_pdf(pdf_path):
    """Extracts text from the first 20 pages of a PDF using pdfplumber and OCR (Tesseract) if necessary."""
    text = ""
    max_pages = 20  # Limit to first 20 pages
    try:
        # 1️⃣ Extraction du texte avec pdfplumber (méthode rapide)
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages[:max_pages]):
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"

        # 2️⃣ Si pdfplumber ne trouve pas assez de texte, utiliser OCR avec Tesseract
        if len(text.strip()) < 20:
            print("⚠️ pdfplumber a échoué, utilisation de l'OCR (Tesseract)")
            images = convert_from_path(pdf_path)
            for i, img in enumerate(images[:max_pages]):  # OCR sur 20 pages max
                img_array = np.array(img)
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
                text += pytesseract.image_to_string(gray, lang="eng+fra") + "\n"
    
    except Exception as e:
        print(f"❌ Erreur d'extraction du texte : {e}")
        return ""

    return text.strip()

@app.route("/extract-audit-data", methods=["POST"])
def extract_data():
    """Handles PDF file upload and returns the extracted text."""
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Fichier vide"}), 400

    temp_pdf_path = "/tmp/uploaded_audit.pdf"
    file.save(temp_pdf_path)

    extracted_text = extract_text_from_pdf(temp_pdf_path)
    if not extracted_text:
        return jsonify({"error": "Impossible d'extraire du texte du PDF"}), 500

    return jsonify({"extracted_text": extracted_text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
