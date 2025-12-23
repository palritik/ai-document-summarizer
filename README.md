📄 AI Document Summarizer

An AI-powered Document Summarizer built using Python, Streamlit, and NLP, capable of generating meaningful summaries and key points from TXT, PDF files, or pasted text.

This project combines abstractive summarization (AI) with a reliable fallback mechanism, ensuring results are always produced even when cloud AI services are unavailable.

🚀 Features

📂 Upload TXT or PDF documents

✍️ Paste raw text directly (no file needed)

🤖 AI-generated abstractive summaries

🧠 Automatic key point extraction

🔄 Smart fallback summarization (never empty output)

📊 Performance metrics (processing time, chunks, text length)

🎨 Clean UI with background image

☁️ Deployed on Streamlit Cloud

🛠️ Tech Stack

Python

Streamlit – Web UI

Hugging Face Inference API – AI summarization

NLTK – Tokenization & fallback logic
🌐 Live Demo

👉 Streamlit App
https://ai-document-summarizer-c4fd6eanlm4gjvem38rynm.streamlit.app/

📊 How It Works

User uploads a document or pastes text

Text is split into manageable chunks

Each chunk is sent to an AI summarization model

If AI fails, a smart extractive fallback is used

Final summary + key points are displayed

PyPDF2 – PDF text extraction

HTML + CSS – UI styling

👤 Author

Ritik Pal
GitHub: https://github.com/palritik
