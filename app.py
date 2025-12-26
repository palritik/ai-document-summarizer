import streamlit as st
import os
import time
import requests
import nltk
from nltk.tokenize import sent_tokenize
import PyPDF2
from fpdf import FPDF
from io import BytesIO
import re

# Helper: Clean common problematic Unicode characters
def clean_text_for_pdf(text):
    replacements = {
        "\u2013": "-",  # en-dash
        "\u2014": "-",  # em-dash
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u2026": "...", # ellipsis
        "\u00a0": " ",  # non-breaking space
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text

# Helper: Insert breaks for long words (prevents overflow)
def insert_breaks(text, max_word_len=20):
    def add_breaks(match):
        word = match.group()
        return '\u200b'.join([word[i:i+max_word_len] for i in range(0, len(word), max_word_len)])
    return re.sub(r'\S{' + str(max_word_len+1) + r',}', add_breaks, text)

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

# ---------------- HERO SECTION ----------------
st.markdown(
    """
    <h1 style="text-align: center; margin-bottom: 0.5rem;">📄 AI Document Summarizer</h1>
    <p style="text-align: center; color: #666; margin-bottom: 2rem;">
        Upload a document OR paste text to get an AI-generated summary.
    </p>
    """,
    unsafe_allow_html=True
)

# ---------------- INPUT FORM ----------------
with st.form(key="input_form", clear_on_submit=False):
    st.markdown(
        """
        <p style="text-align: center; font-size: 1.2rem; margin-bottom: 0.5rem;">✏️ Paste Your Text Here (Optional)</p>
        <p style="text-align: center; color: #888; margin-bottom: 1rem;">
            Paste your story, notes, or content below.
        </p>
        """,
        unsafe_allow_html=True
    )

    user_text = st.text_area(
        label="Paste text",
        label_visibility="collapsed",
        height=250,
        placeholder="Paste text here if you don't have a file..."
    )

    st.markdown(
        """
        <p style="text-align: center; font-size: 1.2rem; margin: 2rem 0 0.5rem 0;">📁 Or Upload a File</p>
        <p style="text-align: center; color: #888; margin-bottom: 1rem;">
            Upload a TXT or PDF file
        </p>
        """,
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        label="Upload document",
        label_visibility="collapsed",
        type=["txt", "pdf"],
        help="Limit 200MB per file • TXT, PDF"
    )

    submit_button = st.form_submit_button("🚀 Generate Summary", use_container_width=True)

# ---------------- PROCESS INPUT ----------------
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
        r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=20)
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

    st.markdown("### 🔹 Summary")
    st.write(st.session_state.result["summary"])

    st.markdown("### 🔹 Key Points")
    for i, p in enumerate(st.session_state.result["points"], 1):
        st.write(f"{i}. {p}")

    # ---------------- PDF GENERATION & DOWNLOAD ----------------
    st.markdown("### 📥 Download Your Summary (PDF)")

    def create_pdf(title, summary_text=None, key_points=None):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, "AI Document Summary", ln=True, align='C')
        pdf.ln(10)

        if summary_text:
            clean_summary = clean_text_for_pdf(summary_text)
            safe_summary = insert_breaks(clean_summary)
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 10, "Summary", ln=True)
            pdf.set_font("Helvetica", '', 12)
            pdf.multi_cell(0, 8, safe_summary)
            pdf.ln(10)

        if key_points:
            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 10, "Key Points", ln=True)
            pdf.set_font("Helvetica", '', 12)
            for i, point in enumerate(key_points, 1):
                clean_point = clean_text_for_pdf(point)
                safe_point = insert_breaks(f"{i}. {clean_point}")
                pdf.multi_cell(0, 8, safe_point)

        buffer = BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    summary_pdf = create_pdf("Summary", summary_text=st.session_state.result["summary"])
    points_pdf = create_pdf("Key Points", key_points=st.session_state.result["points"])
    full_pdf = create_pdf("Full Summary", summary_text=st.session_state.result["summary"], key_points=st.session_state.result["points"])

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        st.download_button(
            label="📄 Download Summary PDF",
            data=summary_pdf,
            file_name="summary.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_d2:
        st.download_button(
            label="🔹 Download Key Points PDF",
            data=points_pdf,
            file_name="key_points.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_d3:
        st.download_button(
            label="📑 Download Full PDF",
            data=full_pdf,
            file_name="full_summary.pdf",
            mime="application/pdf",
            use_container_width=True
        )