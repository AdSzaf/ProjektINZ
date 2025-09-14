import os
import requests

HF_API_KEY = os.getenv("HF_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-small"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

def analyze_tasks(tasks: list[str]) -> str:
    """
    Wysyła listę zadań do modelu i zwraca propozycję kolejności.
    """
    prompt = "Posortuj te zadania według ważności:\n" + "\n".join(tasks)

    response = requests.post(API_URL, headers=HEADERS, json={"inputs": prompt})

    if response.status_code != 200:
        return f"Error: {response.status_code}, {response.text}"

    return response.json()[0]["generated_text"]
