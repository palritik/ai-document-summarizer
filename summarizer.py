import streamlit as st
from transformers import pipeline


# ---------------- LOAD & CACHE MODEL ----------------

@st.cache_resource
def load_summarizer():
    return pipeline(
        "summarization",
        model="facebook/bart-large-cnn"
    )

summarizer = load_summarizer()


# ---------------- TEXT CHUNKING ----------------

def chunk_text(text, max_length=600):
    sentences = text.split(". ")
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# ---------------- SUMMARIZE ONE CHUNK ----------------

def summarize_chunk(chunk):
    length = len(chunk)

    # Adaptive summary length (performance + quality)
    if length < 400:
        max_len, min_len = 100, 50
    else:
        max_len, min_len = 150, 80

    result = summarizer(
        chunk,
        max_length=max_len,
        min_length=min_len,
        do_sample=False
    )

    if result and "summary_text" in result[0]:
        return result[0]["summary_text"]

    return ""

