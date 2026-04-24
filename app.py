import streamlit as st
import os
import time
import requests
import nltk
from nltk.tokenize import sent_tokenize
import PyPDF2
from docx import Document
from io import BytesIO
from datetime import datetime
from gtts import gTTS
import re
from collections import Counter

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# ══════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="SummarAI",
    layout="centered",
    page_icon="✦",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════
#  GLOBAL CSS
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --bg:        #0a0c10;
    --surface:   #12151c;
    --border:    #1e2330;
    --gold:      #d4a853;
    --gold-dim:  #a07830;
    --text:      #e2ddd4;
    --muted:     #6b7280;
    --success:   #22c55e;
}

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main, .block-container {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
}
.block-container { padding: 1.5rem 1.5rem 4rem !important; max-width: 780px !important; }
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color: var(--gold) !important; }

/* ── Typography ── */
h1, h2, h3 { font-family: 'Playfair Display', serif !important; }

/* ── Inputs ── */
.stTextArea textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}
.stTextArea textarea:focus { border-color: var(--gold) !important; box-shadow: 0 0 0 2px #d4a85322 !important; }
.stTextInput input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}
.stTextInput input:focus { border-color: var(--gold) !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px !important;
}

/* ── Buttons ── */
.stFormSubmitButton > button {
    background: linear-gradient(135deg, var(--gold), var(--gold-dim)) !important;
    border: none !important; border-radius: 10px !important;
    color: #0a0c10 !important; font-weight: 700 !important;
    font-size: 15px !important; padding: 0.7rem 2rem !important;
    width: 100% !important; letter-spacing: 0.04em !important;
    transition: opacity 0.2s !important;
}
.stFormSubmitButton > button:hover { opacity: 0.88 !important; }
.stButton > button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important; color: var(--gold) !important;
    font-weight: 500 !important; font-size: 14px !important;
    transition: border-color 0.2s, background 0.2s !important;
}
.stButton > button:hover { border-color: var(--gold) !important; background: #1a1f2e !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important; margin-bottom: 1.5rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; border: none !important;
    border-bottom: 2px solid transparent !important;
    color: var(--muted) !important; font-size: 14px !important;
    font-weight: 500 !important; padding: 0.65rem 1.4rem !important;
    margin-bottom: -1px !important;
}
.stTabs [aria-selected="true"] { color: var(--gold) !important; border-bottom-color: var(--gold) !important; }

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1rem !important;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: var(--gold) !important; font-size: 1.5rem !important; font-weight: 600 !important; }

/* ── Expander ── */
.stExpander { border: 1px solid var(--border) !important; border-radius: 12px !important; background: var(--surface) !important; }
.stExpander summary { color: var(--text) !important; font-size: 14px !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; }

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: 8px !important; color: var(--text) !important;
    font-size: 13px !important;
}
[data-testid="stDownloadButton"] > button:hover { border-color: var(--gold) !important; color: var(--gold) !important; }

/* ── Custom components ── */
.hero-wrap { text-align: center; padding: 2.5rem 0 2rem; }
.hero-badge {
    display: inline-block; font-size: 10px; font-weight: 600;
    letter-spacing: 0.2em; text-transform: uppercase;
    color: var(--gold); border: 1px solid #d4a85344;
    border-radius: 20px; padding: 4px 14px; margin-bottom: 1rem;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2rem, 5vw, 3rem);
    color: #f5f0e8; line-height: 1.2; margin-bottom: 0.6rem;
}
.hero-title em { color: var(--gold); font-style: italic; }

.sec-label {
    font-size: 10px; font-weight: 600; letter-spacing: 0.18em;
    text-transform: uppercase; color: var(--muted); margin-bottom: 0.5rem;
}
.result-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 1.4rem 1.6rem;
    margin: 0.75rem 0; font-size: 15px; line-height: 1.8; color: #ccc5b3;
}
.kp-wrap { border: 1px solid var(--border); border-radius: 12px; padding: 0.4rem 1.4rem; }
.kp-row {
    display: flex; gap: 12px; align-items: flex-start;
    padding: 0.65rem 0; border-bottom: 1px solid var(--border);
    font-size: 14px; line-height: 1.65; color: #a09888;
}
.kp-row:last-child { border-bottom: none; }
.kp-dot { width: 6px; height: 6px; min-width: 6px; background: var(--gold); border-radius: 50%; margin-top: 8px; }
.success-bar {
    background: #0d2018; border: 1px solid #1a4028; border-radius: 10px;
    padding: 0.7rem 1.2rem; font-size: 13px; color: var(--success);
    margin-bottom: 1.2rem;
}
.divider { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }
.login-title { font-family: 'Playfair Display', serif; font-size: 1.9rem; color: #f5f0e8; margin-bottom: 0.3rem; }
.login-sub { color: var(--muted); font-size: 14px; margin-bottom: 1.5rem; }
label { color: #6b7280 !important; font-size: 11px !important; font-weight: 500 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; }

/* ── Navbar ── */
.navbar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.9rem 1.8rem; background: var(--surface);
    border-bottom: 1px solid var(--border); border-radius: 12px;
    margin-bottom: 1.5rem;
}
.nav-brand { font-family: 'Playfair Display', serif; font-size: 1.3rem; color: var(--gold); letter-spacing: 0.02em; }
.nav-links { display: flex; gap: 1.5rem; font-size: 13px; color: var(--muted); }
.nav-links span { cursor: pointer; transition: color 0.2s; }
.nav-links span:hover { color: var(--gold); }
.nav-badge {
    background: #d4a85322; border: 1px solid var(--gold); color: var(--gold);
    font-size: 11px; font-weight: 600; padding: 3px 12px;
    border-radius: 20px; letter-spacing: 0.1em;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════
defaults = {
    "logged_in": False,
    "auth_page": "login",
    "credentials": {"admin": "admin123"},
    "reset_user": None,
    "history": [],
    "result": None,
    "final_text": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ══════════════════════════════════════════════════════
def extract_text(f):
    n = f.name.lower()
    try:
        if n.endswith(".txt"):
            return f.read().decode("utf-8", errors="ignore")
        if n.endswith(".pdf"):
            r = PyPDF2.PdfReader(f)
            return "".join(p.extract_text() or "" for p in r.pages)
        if n.endswith(".docx"):
            d = Document(f)
            return "\n".join(p.text for p in d.paragraphs if p.text.strip())
    except Exception as e:
        st.error(f"File read error: {e}")
    return ""


def groq_summarize(text, key):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": f"Summarize the following text in 5-7 clear, fluent sentences. Write ONLY the summary paragraph:\n\n{text[:4000]}"}],
                "temperature": 0.3, "max_tokens": 500,
            },
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return None


def local_summarize(text):
    sentences = sent_tokenize(text)
    if len(sentences) <= 6:
        return " ".join(sentences)
    stop = {"the","a","an","is","it","in","on","at","to","and","or","of","for","with",
            "this","that","was","are","be","been","by","from","as","but","not","have",
            "has","had","were","they","their","its","we","he","she","you","i","my","our",
            "his","her","so","if","do","did","does","can","will","would","could","should"}
    words = re.findall(r"\w+", text.lower())
    freq = Counter(w for w in words if w not in stop and len(w) > 2)
    def score(s): return sum(freq.get(w, 0) for w in re.findall(r"\w+", s.lower()) if w not in stop)
    ranked = set(sorted(sentences, key=score, reverse=True)[:6])
    return " ".join(s for s in sentences if s in ranked)


def make_audio(text):
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf
    except Exception as e:
        st.error(f"Audio error: {e}")
    return None


# ══════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if st.session_state.auth_page == "login":
            st.markdown('<div style="text-align:center;padding:2.5rem 0 1.5rem;"><p class="login-title">Welcome back.</p><p class="login-sub">Sign in to SummarAI</p></div>', unsafe_allow_html=True)
            with st.form("lf"):
                u = st.text_input("Username", placeholder="admin")
                p = st.text_input("Password", type="password", placeholder="admin123")
                s = st.form_submit_button("Sign in →", use_container_width=True)
            if s:
                if u.strip() in st.session_state.credentials and st.session_state.credentials[u.strip()] == p.strip():
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Wrong credentials. Default: admin / admin123")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Forgot password?", use_container_width=True):
                st.session_state.auth_page = "forgot"; st.rerun()

        elif st.session_state.auth_page == "forgot":
            st.markdown('<div style="text-align:center;padding:2.5rem 0 1.5rem;"><p class="login-title">Reset password.</p><p class="login-sub">Enter your username to continue.</p></div>', unsafe_allow_html=True)
            with st.form("ff"):
                u = st.text_input("Username", placeholder="Enter username")
                s = st.form_submit_button("Verify →", use_container_width=True)
            if s:
                if u.strip() in st.session_state.credentials:
                    st.session_state.reset_user = u.strip()
                    st.session_state.auth_page = "reset"; st.rerun()
                else:
                    st.error("❌ Username not found.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Back to login", use_container_width=True):
                st.session_state.auth_page = "login"; st.rerun()

        elif st.session_state.auth_page == "reset":
            user = st.session_state.reset_user
            st.markdown(f'<div style="text-align:center;padding:2.5rem 0 1.5rem;"><p class="login-title">New password.</p><p class="login-sub">For: <strong>{user}</strong></p></div>', unsafe_allow_html=True)
            with st.form("rf"):
                np_ = st.text_input("New password", type="password", placeholder="Min 6 characters")
                cp_ = st.text_input("Confirm password", type="password", placeholder="Repeat password")
                s   = st.form_submit_button("Update password →", use_container_width=True)
            if s:
                if len(np_.strip()) < 6:
                    st.error("❌ Minimum 6 characters.")
                elif np_.strip() != cp_.strip():
                    st.error("❌ Passwords do not match.")
                else:
                    st.session_state.credentials[user] = np_.strip()
                    st.session_state.auth_page = "login"
                    st.success("✅ Password updated! Please sign in."); st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Back to login", use_container_width=True):
                st.session_state.auth_page = "login"; st.rerun()
    st.stop()


# ══════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ✦ SummarAI")
    st.caption("AI-Powered Document Summarizer")
    st.divider()

    st.markdown("### ⚙️ Settings")
    summary_style = st.select_slider("Summary Length", ["Short", "Medium", "Long"], value="Medium")

    st.divider()
    if st.session_state.history:
        st.markdown("### 📜 Recent")
        for i, item in enumerate(st.session_state.history[:5]):
            with st.expander(f"🕐 {item['timestamp']}", expanded=False):
                st.write(item["summary"][:100] + "…")

    st.divider()
    if st.button("🚪 Sign out", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()


# ══════════════════════════════════════════════════════
#  NAVBAR + HERO
# ══════════════════════════════════════════════════════
st.markdown("""
<div class="navbar">
    <div class="nav-brand">✦ SummarAI</div>
    <div class="nav-links">
        <span>Summarize</span>
        <span>History</span>
        <span>About</span>
    </div>
    <div class="nav-badge">AI Powered</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-wrap">
    <div class="hero-badge">✦ AI Powered</div>
    <div class="hero-title">Turn any document into<br><em>instant clarity</em></div>
    <p style="text-align:center; font-size:15px; color:#6b7280; margin-top:0.5rem; margin-bottom:0; width:100%;">
        Paste text or upload PDF, Word, or TXT — get a clean AI summary with audio playback.
    </p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["✦  Summarize", "  History"])


# ══════════════════════════════════════════════════════
#  TAB 1 — SUMMARIZE
# ══════════════════════════════════════════════════════
with tab1:

    with st.form("main_form"):
        st.markdown('<p class="sec-label">Paste your text</p>', unsafe_allow_html=True)
        user_text = st.text_area(
            "Text input", height=230,
            placeholder="Paste an article, research paper, meeting notes, report, or any text you want summarized…",
            label_visibility="collapsed",
        )
        st.markdown('<p class="sec-label" style="margin-top:1rem;">Or upload a file</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "File upload", type=["txt", "pdf", "docx"],
            label_visibility="collapsed", help="Supports .txt .pdf .docx",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("✦ Generate Summary", use_container_width=True)

    if submit:
        content = user_text.strip()
        if uploaded_file:
            extracted = extract_text(uploaded_file)
            if extracted:
                content = extracted
        if len(content) < 200:
            st.warning("⚠️ Please provide at least 200 characters of text.")
        else:
            st.session_state.final_text = content
            st.session_state.result = None

            with st.spinner("Analyzing your document…"):
                pg = st.progress(10, text="Starting…")
                start = time.time()

                # Get Groq key from secrets only
                groq_key = None
                try:
                    groq_key = st.secrets.get("GROQ_API_KEY")
                except Exception:
                    groq_key = os.getenv("GROQ_API_KEY")

                summary = None
                if groq_key:
                    pg.progress(35, text="Running Groq AI…")
                    summary = groq_summarize(content, groq_key)

                if not summary:
                    pg.progress(55, text="Using smart local summarizer…")
                    summary = local_summarize(content)

                pg.progress(85, text="Extracting key points…")
                key_points = sent_tokenize(content)[:7]
                elapsed = round(time.time() - start, 2)
                pg.progress(100, text="Done!"); pg.empty()

            result = {
                "summary":   summary,
                "points":    key_points,
                "time":      elapsed,
                "chars":     len(content),
                "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                "full_text": f"Summary:\n{summary}\n\nKey Points:\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(key_points, 1)),
            }
            st.session_state.result = result
            st.session_state.history.insert(0, result)
            if len(st.session_state.history) > 20:
                st.session_state.history.pop()

    # ── Output ──
    if st.session_state.result:
        res = st.session_state.result

        st.markdown('<div class="success-bar">✓ Summary generated successfully</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("⏱ Time", f"{res['time']}s")
        c2.metric("📝 Characters", f"{res['chars']:,}")
        c3.metric("📌 Key Points", len(res["points"]))

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<p class="sec-label">Summary</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="result-card">{res["summary"]}</div>', unsafe_allow_html=True)

        st.markdown('<p class="sec-label" style="margin-top:1.5rem;">Key Points</p>', unsafe_allow_html=True)
        kp_html = "".join(f'<div class="kp-row"><div class="kp-dot"></div><span>{p}</span></div>' for p in res["points"])
        st.markdown(f'<div class="kp-wrap">{kp_html}</div>', unsafe_allow_html=True)

        st.markdown('<p class="sec-label" style="margin-top:1.5rem;">Save</p>', unsafe_allow_html=True)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("📄 Download Summary", data=res["summary"], file_name="summary.txt", mime="text/plain", use_container_width=True)
        with d2:
            pts = "\n".join(f"• {p}" for p in res["points"])
            st.download_button("📌 Download Key Points", data=pts, file_name="key_points.txt", mime="text/plain", use_container_width=True)

        # ── AUDIO ──
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<p class="sec-label">🔊 Audio Summary</p>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:13px;color:#6b7280;margin-bottom:0.8rem;">Click to convert the summary to speech and listen directly in your browser.</p>', unsafe_allow_html=True)

        if st.button("🔊 Generate & Play Audio", use_container_width=True):
            with st.spinner("Creating audio… please wait"):
                speak_text = f"Here is the document summary. {res['summary']}. Key points follow. " + ". ".join(res["points"])
                audio_buf = make_audio(speak_text)
                if audio_buf:
                    st.audio(audio_buf, format="audio/mp3")
                    st.success("✅ Audio ready! Press ▶ play above to listen.")
                else:
                    st.error("❌ Audio failed. Check your internet connection.")


# ══════════════════════════════════════════════════════
#  TAB 2 — HISTORY
# ══════════════════════════════════════════════════════
with tab2:
    if not st.session_state.history:
        st.markdown('<div style="text-align:center;padding:3rem 1rem;color:#374151;"><p style="font-size:2rem;">◌</p><p>No summaries yet. Generate your first one above.</p></div>', unsafe_allow_html=True)
    else:
        count = len(st.session_state.history)
        st.markdown(f'<p style="font-size:13px;color:#6b7280;margin-bottom:1rem;">{count} summar{"ies" if count > 1 else "y"} saved this session</p>', unsafe_allow_html=True)
        for item in st.session_state.history:
            with st.expander(f"✦  {item['timestamp']}"):
                st.markdown(f'<div class="result-card">{item["summary"]}</div>', unsafe_allow_html=True)
                st.markdown('<p class="sec-label" style="margin-top:1rem;">Key Points</p>', unsafe_allow_html=True)
                kp_html = "".join(f'<div class="kp-row"><div class="kp-dot"></div><span>{p}</span></div>' for p in item["points"])
                st.markdown(f'<div class="kp-wrap">{kp_html}</div>', unsafe_allow_html=True)
                st.download_button("📄 Download", data=item.get("full_text", item["summary"]),
                    file_name=f"summary_{item['timestamp'].replace(' ','_').replace(',','')}.txt",
                    mime="text/plain", key=f"dl_{item['timestamp']}")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear all history", use_container_width=False):
            st.session_state.history = []
            st.session_state.result = None
            st.rerun()