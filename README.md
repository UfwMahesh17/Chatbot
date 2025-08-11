Agent42Labs Chatbot
Production‑ready RAG chatbot for Agent42Labs with strict, extractive answers, Cohere reranking, file uploads, and branded PDF/DOCX exports (including a tri‑fold brochure), plus a clean single‑file HTML UI.

Backend: Flask + LangChain + Chroma
Embeddings/Rerank: Cohere
Storage: Chroma (local or mounted volume)
Frontend: Single HTML file (ui.html)
Features
Retrieval‑augmented generation (RAG) without hallucinations
Extractive‑only answers (copies from retrieved context)
Grounding check threshold
Cohere rerank (rerank‑english‑v3.0) for high‑precision hits
MMR retrieval for diverse candidates
Guardrails and intents
Pricing/cost questions always return contact info
Professional rotating fallbacks
Greetings/thanks/goodbye intent handling
Ingestion
Upload PDFs/DOCX/TXT via /upload
Batch ingest from a local directory with ingest.py
Optional web crawl (if you add ingest_web.py)
Stable IDs, dedupe, upsert
Exports
Plain TXT/JSON/PDF/DOCX
One‑pager “brochure” (answer‑based) PDF/DOCX
Tri‑fold brochure PDF/DOCX (brand title, hero image, sections, contact)
Frontend (ui.html)
Clean, mobile‑style light theme
Sources shown as chips under answers
“Save as” toolbar (Save latest answer / full conversation)
window.API_BASE override for any API host
Repo layout (typical)
text

.
├─ app.py                 # Flask API (chat, upload, export)
├─ ingest.py              # local directory ingestion
├─ ingest_web.py          # optional website crawler (if used)
├─ requirements.txt
├─ Procfile               # for Railway/Heroku-like platforms
├─ prestart.sh            # optional: download DB zip at startup (Railway)
├─ ui.html                # frontend
├─ assets/                # optional logo for exports
└─ downloaded_content/    # optional docs to ingest on the server
Environment variables
COHERE_API_KEY: Cohere API key
PERSIST_DIR: Absolute path to Chroma DB (local default ./chroma_db; Railway /data/chroma_db)
Optional (exports)
LOGO_PATH: Absolute path to logo image (PNG/JPG) for exports
FONT_TTF: Unicode TTF font for PDFs (e.g., /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf)
Optional (Railway prestart download)
CHROMA_GDRIVE_ID: Google Drive file ID for chroma_db.zip
CHROMA_ZIP_URL: Direct URL to chroma_db.zip (if not using Drive)
CHROMA_FORCE_RELOAD=1: Force re‑download of the DB on next deploy
Quick start (local)
Clone and install
Bash

git clone https://github.com/<you>/Chatbot.git
cd Chatbot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
Ingest some documents (optional if you already have chroma_db)
Bash

export COHERE_API_KEY=your_key
python ingest.py --input-dir ./downloaded_content
Run the backend
Bash

export COHERE_API_KEY=your_key
export PERSIST_DIR="$(pwd)/chroma_db"
python app.py
# Server on http://127.0.0.1:5000
Open the UI
In ui.html, set your API host if needed:
HTML

<script>window.__API_BASE__ = "http://127.0.0.1:5000";</script>
Serve the file locally (optional):
Bash

python -m http.server 8000
# open http://localhost:8000/ui.html
API
POST /chat
Request: {"question": "...", "history": [], "fail_count": 0}
Response: {"answer": "...", "fail_count": 0, "sources": [...]}

POST /upload
Form-data: files=[PDF|DOCX|TXT,...]
Adds chunks to Chroma (upsert per file)

POST /export
Plain export:

JSON

{"type": "pdf|docx|txt|json", "content": "...", "filename": "name"}
One‑pager brochure:

JSON

{"type":"pdf|docx","template":"brochure","question":"...","answer":"...","sources":[...],"brandTitle":"Agent42Labs"}
Tri‑fold brochure:

JSON

{"type":"pdf|docx","template":"trifold","trifold":{ ... see below ... }}
GET /debug/index (optional)
Health check with {"vector_count": N, ...}

Tri‑fold example payload:

JSON

{
  "type": "pdf",
  "template": "trifold",
  "trifold": {
    "brandTitle": "Agent42Labs",
    "title": "Pushing Limits",
    "subtitle": "AI, automation, and secure platforms for finance.",
    "accent": "#84cc16",
    "bg": "#0b1215",
    "text": "#e5e7eb",
    "logo": "/app/assets/logo.png",
    "heroImage": "/app/assets/hero.jpg",
    "left": {
      "blocks": [
        {"type":"h","text":"WHY US"},
        {"type":"p","text":"We deliver secure, scalable AI solutions to automate workflows and elevate customer experiences."},
        {"type":"bullets","items":["Secure by design","Cloud‑native architecture","Rapid delivery"]},
        {"type":"contact"}
      ]
    },
    "middle": {"blocks":[{"type":"title"},{"type":"subtitle"}]},
    "right": {
      "blocks": [
        {"type":"h","text":"OUR SOLUTIONS"},
        {"type":"bullets","items":["Fraud detection","Automated KYC","Credit risk","Real‑time payments"]}
      ]
    },
    "contact": {
      "phone":"+91 7027119799",
      "email":"support@agent42labs.com",
      "website":"https://agent42labs.com"
    }
  }
}
