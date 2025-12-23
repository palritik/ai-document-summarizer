import streamlit as st
import base64
import os
import time

from summarizer import chunk_text, summarize_chunk
from keypoints import extract_key_points
from pdf_reader import read_pdf

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Document Summarizer", layout="centered")

# ---------------- LOAD CSS ----------------
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/style.css")

# ---------------- BACKGROUND IMAGE ----------------
def add_bg_from_local(image_file):
    with open(image_file, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
            linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.45)),
            url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
bg_path = os.path.join(BASE_DIR, "assets", "bg.jpg")
add_bg_from_local(bg_path)

# ---------------- HERO SECTION ----------------
st.markdown(
    '<div class="hero-title">📄 AI Document Summarizer</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="hero-desc">'
    'Upload a document OR paste text to get an AI-generated summary.'
    '</div>',
    unsafe_allow_html=True
)

# ---------------- INPUT SECTION ----------------
st.markdown('<div class="section-title">✍️ Paste Your Text Here (Optional)</div>', unsafe_allow_html=True)

user_text = st.text_area(
    "",
    height=200,
    placeholder="Paste text here if you don't have a file...",
    key="text_input"
)

st.markdown('<div class="section-title">📂 Or Upload a File</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "",
    type=["txt", "pdf"],
    key="file_input"
)

# ---------------- TEXT SELECTION ----------------
text = ""

if user_text.strip():
    text = user_text.strip()

elif uploaded_file is not None:
    if uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8").strip()

    elif uploaded_file.type == "application/pdf":
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        text = read_pdf("temp.pdf").strip()

# ---------------- BUTTON & PROCESS ----------------
if st.button("Generate Summary", key="generate_btn"):

    if not text or len(text) < 200:
        st.warning("⚠️ Please provide sufficient readable content (minimum a few paragraphs).")

    else:
        # ⏱️ START TIMER
        start_time = time.time()

        # Chunking (optimized)
        chunks = chunk_text(text)
        if len(chunks) > 4:
            chunks = chunks[:4]

        total_chunks = len(chunks)

        progress_bar = st.progress(0)
        status_text = st.empty()

        summaries = []

        for i, chunk in enumerate(chunks, start=1):
            status_text.text(f"⏳ Processing chunk {i} of {total_chunks}...")
            summaries.append(summarize_chunk(chunk))
            progress_bar.progress(int((i / total_chunks) * 100))

        progress_bar.progress(100)
        status_text.text("✅ Summarization completed!")

        # ⏱️ END TIMER
        end_time = time.time()
        total_time = round(end_time - start_time, 2)

        final_summary = " ".join(summaries)

        # ---------------- OUTPUT ----------------
        st.subheader("🔹 Summary")
        st.write(final_summary)

        st.subheader("🔹 Important Points")
        points = extract_key_points(final_summary)
        for i, point in enumerate(points, 1):
            st.write(f"{i}. {point}")

        # -------- SEPARATOR --------
        with st.container():
            st.markdown("---")

        # ---------------- PERFORMANCE DASHBOARD ----------------
        st.subheader("📊 Performance Metrics")

        col1, col2, col3 = st.columns(3)
        col1.metric("⏱️ Processing Time", f"{total_time} sec")
        col2.metric("🧩 Chunks Processed", total_chunks)
        col3.metric("🧠 Model Used", "BART Large CNN")

        col4, col5, col6 = st.columns(3)
        col4.metric("📄 Input Length", f"{len(text)} chars")
        col5.metric("📝 Summary Length", f"{len(final_summary)} chars")
        col6.metric("⚡ Avg Time / Chunk", f"{round(total_time / total_chunks, 2)} sec")
