import pdfplumber
import re
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

def extract_audit_data(pdf_path):
    """Extracts relevant audit data from the PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    # Extract key values using regex
    data = {
        "prenom": re.search(r"Prénom\s*:\s*(.*)", text),
        "nom": re.search(r"Nom\s*:\s*(.*)", text),
        "adresse_numero": re.search(r"Adresse\s*:\s*(\d+)", text),
        "adresse_voie": re.search(r"Adresse\s*:\s*\d+\s*(.*)", text),
        "adresse_code_postal": re.search(r"Code Postal\s*:\s*(\d+)", text),
        "adresse_ville": re.search(r"Ville\s*:\s*(.*)", text),
        "classe_energie_avant": re.search(r"Classe énergétique avant\s*:\s*(.*)", text),
        "classe_energie_apres": re.search(r"Classe énergétique après\s*:\s*(.*)", text),
        "date_audit": re.search(r"Date de réalisation de l’audit\s*:\s*(.*)", text),
        "id_audit": re.search(r"Identifiant de l’audit\s*:\s*(.*)", text),
        "conso_finale_avant": re.search(r"Consommation énergie finale avant\s*:\s*(.*)", text),
        "conso_primaire_avant": re.search(r"Consommation énergie primaire avant\s*:\s*(.*)", text),
        "conso_finale_apres": re.search(r"Consommation énergie finale après\s*:\s*(.*)", text),
        "conso_primaire_apres": re.search(r"Consommation énergie primaire après\s*:\s*(.*)", text),
        "surface_avant": re.search(r"Surface avant projet\s*:\s*(.*)", text),
        "surface_apres": re.search(r"Surface après projet\s*:\s*(.*)", text),
        "co2_avant": re.search(r"Émission CO2 avant\s*:\s*(.*)", text),
        "co2_apres": re.search(r"Émission CO2 après\s*:\s*(.*)", text),
        "date_visite": re.search(r"Date de la visite audit\s*:\s*(.*)", text)
    }

    extracted_data = {key: (match.group(1).strip() if match else "N/A") for key, match in data.items()}

    return extracted_data

@app.route('/extract-audit-data', methods=['POST'])
def extract_data():
    """API endpoint to process uploaded PDF and return extracted data."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    file_path = os.path.join("/tmp", file.filename)
    file.save(file_path)

    extracted_data = extract_audit_data(file_path)
    os.remove(file_path)  # Clean up

    return jsonify(extracted_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
