import streamlit as st
import os
import time
import requests
import nltk
from nltk.tokenize import sent_tokenize
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

# ---------------- DOWNLOAD NLTK DATA ----------------
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)  # Add this line

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

    # ---------------- PDF GENERATION & DOWNLOAD (ReportLab) ----------------
    st.markdown("### 📥 Download Your Summary (PDF)")

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )

    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    def create_pdf(filename, include_summary=True, include_points=True):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
        story = []

        story.append(Paragraph("AI Document Summary", title_style))
        story.append(Spacer(1, 0.5*inch))

        if include_summary:
            story.append(Paragraph("Summary", heading_style))
            story.append(Paragraph(st.session_state.result["summary"].replace("\n", "<br/>"), normal_style))
            story.append(Spacer(1, 0.3*inch))

        if include_points:
            story.append(Paragraph("Key Points", heading_style))
            for i, point in enumerate(st.session_state.result["points"], 1):
                story.append(Paragraph(f"{i}. {point.replace('\n', '<br/>')}", normal_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    summary_pdf = create_pdf("summary.pdf", include_summary=True, include_points=False)
    points_pdf = create_pdf("key_points.pdf", include_summary=False, include_points=True)
    full_pdf = create_pdf("full_summary.pdf", include_summary=True, include_points=True)

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