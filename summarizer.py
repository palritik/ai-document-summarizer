import requests
import os
import time

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
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json={"inputs": chunk, "options": {"wait_for_model": True}},
        timeout=60
    )

    result = response.json()

    if isinstance(result, list) and "summary_text" in result[0]:
        return result[0]["summary_text"]

    return ""
