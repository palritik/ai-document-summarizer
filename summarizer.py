import requests
import os

API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

HEADERS = {
    "Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}"
}

def chunk_text(text, max_length=700):
    sentences = text.split(". ")
    chunks = []
    current = ""

    for s in sentences:
        if len(current) + len(s) < max_length:
            current += s + ". "
        else:
            chunks.append(current.strip())
            current = s + ". "

    if current:
        chunks.append(current.strip())

    return chunks


def summarize_chunk(chunk):
    try:
        payload = {
            "inputs": chunk,
            "parameters": {
                "min_length": 80,     # 🔥 IMPORTANT
                "max_length": 200,    # 🔥 IMPORTANT
                "do_sample": False
            },
            "options": {
                "wait_for_model": True
            }
        }

        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            return ""

        result = response.json()

        # ✅ Handle all valid HF response formats
        if isinstance(result, list):
            if "summary_text" in result[0]:
                return result[0]["summary_text"]
            if "generated_text" in result[0]:
                return result[0]["generated_text"]

        return ""

    except requests.exceptions.Timeout:
        return "[⏳ Model is warming up, please try again]"

    except Exception as e:
        return ""
