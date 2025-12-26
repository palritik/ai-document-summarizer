import streamlit as st
import os
import base64
import time
import requests
import nltk
from nltk.tokenize import sent_tokenize
import PyPDF2

# ---------------- DOWNLOAD NLTK DATA ----------------
nltk.download("punkt", quiet=True)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Document Summarizer", layout="centered")

# ---------------- SESSION STATE ----------------
if "final_text" not in st.session_state:
    st.session_state.final_text = ""

if "run" not in st.session_state:
    st.session_state.run = False

if "result" not in st.session_state:
    st.session_state.result = None

# ---------------- LOAD CSS ----------------
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# def load_css():
#     css = """
#     # .main-card {
#     #     background: rgba(255, 255, 255, 0.92);
#     #     padding: 2.5rem;
#     #     border-radius: 18px;
#     #     max-width: 900px;
#     #     margin: 2.5rem auto;   /* 🔥 spacing fix */
#     #     box-shadow: 0px 12px 35px rgba(0,0,0,0.25);
#     # }

#     # h1 {
#     #     text-align: center;
#     #     margin-bottom: 0.3rem;
#     # }

#     # p.subtitle {
#     #     text-align: center;
#     #     font-size: 1.05rem;
#     #     margin-bottom: 2rem;
#     #     color: #333;
#     # }

#     # textarea {
#     #     margin-top: 1rem;
#     #     margin-bottom: 1.5rem;
#     # }

#     # .stFileUploader {
#     #     margin-bottom: 1.5rem;
#     # }

#     # .stButton {
#     #     margin-top: 1.2rem;
#     # }
#     # """
#     st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# # load_css()  # Test without custom styles

# ---------------- BACKGROUND IMAGE ----------------
# def add_bg():
#     img_path = os.path.join(BASE_DIR, "assets", "bg.jpg")
#     if not os.path.exists(img_path):
#         return
#     with open(img_path, "rb") as f:
#         encoded = base64.b64encode(f.read()).decode()
#     st.markdown(
#         f"""
#         <style>
#         .stApp {{
#             background-image:
#             linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.45)),
#             url("data:image/jpg;base64,{encoded}");
#             background-size: cover;
#             background-attachment: fixed;
#         }}
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

# add_bg()

# ---------------- HERO + MAIN CARD ----------------
st.markdown("""
<h1>📄 AI Document Summarizer</h1>
<p class="subtitle">
Paste text or upload a document to generate a summary and key points.
</p>
<div class="main-card">
""", unsafe_allow_html=True)

# ---------------- INPUT ----------------
with st.form(key="input_form"):
    user_text = st.text_area(
        "Paste text",
        label_visibility="collapsed",
        height=200,
        placeholder="Paste your content here if you don't have a file..."
    )

    uploaded_file = st.file_uploader(
        "Upload document",
        label_visibility="collapsed",
        type=["txt", "pdf"]
    )

    submit_button = st.form_submit_button("🚀 Generate Summary")

# Move the text processing and session state logic OUTSIDE the form
current_text = ""

if user_text.strip():
    current_text = user_text.strip()
elif uploaded_file:
    if uploaded_file.type == "text/plain":
        current_text = uploaded_file.read().decode("utf-8")
    else:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                current_text += text + " "

if submit_button:
    if len(current_text) < 200:
        st.warning("⚠️ Please provide at least 200 characters.")
    else:
        st.session_state.final_text = current_text
        st.session_state.run = True
        st.session_state.result = None

# ---------------- BUTTON ----------------
if st.button("🚀 Generate Summary", key="generate_btn"):
    if len(current_text) < 200:
        st.warning("⚠️ Please provide at least 200 characters.")
    else:
        st.session_state.final_text = current_text
        st.session_state.run = True
        st.session_state.result = None

# 🔴 CLOSE MAIN CARD (ONLY ONCE)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- HF API CONFIG ----------------
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}"
}

def chunk_text(text, max_length=700):
    sentences = text.split(". ")
    chunks, current = [], ""
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
            "parameters": {"min_length": 80, "max_length": 200},
            "options": {"wait_for_model": True}
        }
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        if r.status_code != 200:
            return ""
        data = r.json()
        if isinstance(data, list):
            return data[0].get("summary_text") or data[0].get("generated_text", "")
        return ""
    except Exception:
        return ""

def fallback_summary(text, count=10):
    sentences = sent_tokenize(text)

    if len(sentences) <= count:
        return " ".join(sentences)

    # Take beginning + middle + end for better coverage
    part1 = sentences[:4]
    part2 = sentences[len(sentences)//2 : len(sentences)//2 + 3]
    part3 = sentences[-3:]

    return " ".join(part1 + part2 + part3)


# ---------------- PROCESS (RUN ONCE) ----------------
if st.session_state.run and st.session_state.result is None:
    with st.spinner("🤖 AI is summarizing your document..."):
        start = time.time()

        text = st.session_state.final_text
        chunks = chunk_text(text)[:5]

        summaries = []
        for c in chunks:
            s = summarize_chunk(c)
            if s.strip():
                summaries.append(s)

        # 🔥 GUARANTEED fallback
        if not summaries:
            summaries.append(fallback_summary(text))

        st.session_state.result = {
            "summary": " ".join(summaries),
            "points": sent_tokenize(text)[:5],
            "time": round(time.time() - start, 2),
            "chunks": len(chunks)
        }

    st.session_state.run = False

# ---------------- OUTPUT ----------------
if st.session_state.result:
    col1, col2, col3 = st.columns(3)
    col1.metric("⏱ Time", f"{st.session_state.result['time']}s")
    col2.metric("📄 Chunks", st.session_state.result["chunks"])
    col3.metric("📝 Text Length", len(st.session_state.final_text))

    st.subheader("🔹 Summary")
    st.write(st.session_state.result["summary"])

    st.subheader("🔹 Key Points")
    for i, p in enumerate(st.session_state.result["points"], 1):
        st.write(f"{i}. {p}")

