import json
import os
import pdfplumber
import openai
import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_path
from flask import Flask, request, jsonify

app = Flask(__name__)

# Charger la clé API OpenAI depuis les variables d’environnement
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ Clé API OpenAI manquante ! Ajoutez-la dans les variables d’environnement.")

openai.api_key = OPENAI_API_KEY

def extract_text_from_pdf(pdf_path):
    """Extrait du texte depuis un PDF avec pdfplumber, et utilise Tesseract OCR si nécessaire."""
    text = ""

    try:
        # 1️⃣ Extraction du texte avec pdfplumber (limité à 20 pages)
                with pdfplumber.open(pdf_path) as pdf:
                    num_pages = min(len(pdf.pages), 20)  # Limiter à 20 pages maximum
                    for i in range(num_pages):
                        page = pdf.pages[i]
                        extracted_text = page.extract_text()
                        if extracted_text:
                            text += extracted_text + "\n"

        # 2️⃣ Si pdfplumber ne trouve pas assez de texte, utiliser OCR avec Tesseract
        if len(text.strip()) < 20:
            print("⚠️ pdfplumber a échoué, utilisation de l'OCR (Tesseract)")
            images = convert_from_path(pdf_path)
            for img in images:
                img_array = np.array(img)
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
                text += pytesseract.image_to_string(gray, lang="eng+fra") + "\n"

    except Exception as e:
        print(f"❌ Erreur d'extraction du texte : {e}")
        return ""

    return text.strip()

def process_text_with_ai(text):
    """Envoie le texte extrait à OpenAI pour extraire les données structurées."""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extrais les données clés d'un rapport d'audit énergétique."},
                {"role": "user", "content": f"Analyse ce rapport et retourne les informations en JSON formaté :\n\n{text}"}
            ],
            temperature=0
        )
        return response.choices[0].message.content
    except openai.OpenAIError as e:
        print(f"❌ Erreur API OpenAI : {e}")
        return json.dumps({"error": "Erreur OpenAI", "details": str(e)})

def safe_json_response(structured_data):
    """Vérifie et retourne une réponse JSON valide."""
    try:
        print(f"📄 Données brutes extraites : {structured_data}")  # Debugging
        if not structured_data or structured_data.strip() == "":
            raise ValueError("Réponse JSON vide reçue.")

        structured_json = json.loads(structured_data)
        return jsonify(structured_json)
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON : {e}")
        return jsonify({"error": "Format JSON invalide", "details": str(e)}), 500
    except ValueError as e:
        print(f"❌ Erreur de valeur : {e}")
        return jsonify({"error": "Réponse vide de l'API OpenAI", "details": str(e)}), 500

@app.route("/extract-audit-data", methods=["POST"])
def extract_data():
    """Gère l'upload de fichier PDF, le traite et renvoie un JSON structuré."""
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

    structured_data = process_text_with_ai(extracted_text)
    return safe_json_response(structured_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
