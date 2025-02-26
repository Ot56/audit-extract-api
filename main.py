import openai
import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

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

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}],
        api_key=OPENAI_API_KEY  # Securely retrieve API key
    )

    structured_data = response["choices"][0]["message"]["content"]
    return structured_data
