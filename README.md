# 🚀 Agent42Labs Chatbot

**Production-ready Retrieval-Augmented Generation (RAG) chatbot** with:
- **Strict, extractive answers** (no hallucinations)
- **Cohere reranking** for high-precision retrieval
- **File uploads** (PDF, DOCX, TXT)
- **Branded PDF/DOCX exports** (including a tri-fold brochure)
- **Clean single-file HTML frontend**

---

## 🛠 Tech Stack

| Layer            | Technology |
|------------------|------------|
| Backend          | Flask, LangChain, Chroma |
| Embeddings/Rerank| Cohere |
| Storage          | Chroma (local or mounted volume) |
| Frontend         | Single HTML file (`ui.html`) |

---

## ✨ Features

### 📄 Retrieval-Augmented Generation
- Extractive-only answers (directly copied from retrieved context)
- Grounding check threshold for factual accuracy
- Cohere Rerank (`rerank-english-v3.0`) for relevance
- Maximal Marginal Relevance (MMR) retrieval for diverse results

### 🛡 Guardrails & Intents
- Pricing/cost questions → Contact info
- Professional fallback responses
- Greetings / thanks / goodbye intent handling

---

## 📥 Document Ingestion
- Upload PDFs, DOCX, TXT via `/upload`
- Batch ingest from a local directory (`ingest.py`)
- Optional web crawl (`ingest_web.py`)
- Stable IDs, deduplication, upserts

---

## 📤 Export Options
- Plain TXT / JSON / PDF / DOCX
- One-pager “brochure” (answer-based)
- Tri-fold brochure with:
  - Brand title & hero image
  - Multiple section blocks
  - Contact info

---

## 🎨 Frontend (`ui.html`)
- Mobile-style, light theme
- Sources displayed as chips under answers
- “Save as” toolbar:
  - Save latest answer
  - Save full conversation
- `window.API_BASE` override for any API host

---

## 📂 Repository Structure
Agent42labs ChatBot
|
├─ app.py # Flask API (chat, upload, export)
├─ ingest.py # Local directory ingestion
├─ ingest_web.py # Optional web crawler
├─ requirements.txt
├─ Procfile # For Railway/Heroku-like deployment
├─ prestart.sh # Optional: DB download at startup
├─ ui.html # Frontend UI
├─ assets/ # Optional logos for exports
└─ downloaded_content/ # Optional docs to ingest


---

## ⚙️ Environment Variables

| Variable            | Description |
|---------------------|-------------|
| `COHERE_API_KEY`    | Cohere API key |
| `PERSIST_DIR`       | Absolute path to Chroma DB (`./chroma_db` default) |
| **Optional (Exports)** |
| `LOGO_PATH`         | Path to logo image (PNG/JPG) |
| `FONT_TTF`          | Path to Unicode TTF font for PDFs |
| **Optional (Railway)** |
| `CHROMA_GDRIVE_ID`  | Google Drive ID for `chroma_db.zip` |
| `CHROMA_ZIP_URL`    | Direct URL to `chroma_db.zip` |
| `CHROMA_FORCE_RELOAD` | Force DB re-download |

---

## 🚀 Quick Start (Local)

### 1️⃣ Clone & Install
```bash
git clone https://github.com/<you>/Chatbot.git
cd Chatbot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt

export COHERE_API_KEY=your_key
python ingest.py --input-dir ./downloaded_content


