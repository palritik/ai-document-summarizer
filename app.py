import streamlit as st
import os
import base64
import time

from summarizer import chunk_text, summarize_chunk
from keypoints import extract_key_points
from pdf_reader import read_pdf

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Document Summarizer",
    layout="centered"
)

# ---------------- LOAD CSS ----------------
def load_css(path):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_css(os.path.join(BASE_DIR, "assets", "style.css"))

# ---------------- BACKGROUND IMAGE ----------------
def add_bg(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
            linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)),
            url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg(os.path.join(BASE_DIR, "assets", "bg.jpg"))

# ---------------- HERO SECTION ----------------
st.markdown("""
<div class="hero-box"></div>
<h1 class="hero-title">📄 AI Document Summarizer</h1>
<p class="hero-desc">
Upload a document or paste text to generate a detailed AI summary and key points.
</p>
""", unsafe_allow_html=True)

# ---------------- MAIN CARD ----------------
st.markdown('<div class="main-card">', unsafe_allow_html=True)

# ---------------- TEXT INPUT ----------------
user_text = st.text_area(
    "Paste text input",
    label_visibility="collapsed",
    height=200,
    placeholder="Paste your text here if you don't have a file..."
)

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "Upload document",
    label_visibility="collapsed",
    type=["txt", "pdf"]
)

text = ""

if user_text.strip():
    text = user_text.strip()

elif uploaded_file:
    if uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")

    elif uploaded_file.type == "application/pdf":
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        text = read_pdf("temp.pdf")

# ---------------- BUTTON ----------------
if st.button("🚀 Generate Summary", key="generate_summary_btn"):

    if len(text) < 200:
        st.warning("⚠️ Please provide more text for better summarization.")
    else:
        with st.spinner("🤖 AI is summarizing your document, please wait..."):

            start = time.time()

            # limit chunks for faster response
            chunks = chunk_text(text)[:5]
            progress = st.progress(0)

            summaries = []

            for i, chunk in enumerate(chunks, 1):
                summary = summarize_chunk(chunk)
                summaries.append(summary)
                progress.progress(int((i / len(chunks)) * 100))

            total_time = round(time.time() - start, 2)

        st.success("✅ Summary generated successfully!")

        st.subheader("🔹 Summary")
        st.write(" ".join(summaries))

        st.subheader("🔹 Key Points")
        for i, point in enumerate(extract_key_points(text), 1):
            st.write(f"{i}. {point}")

