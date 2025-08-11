Agent42Labs Chatbot

Production-ready RAG chatbot with strict, extractive answers, Cohere reranking, file uploads, and branded PDF/DOCX exports (including tri-fold brochures).
Frontend is a single-file HTML UI with a clean, mobile-friendly look.

Tech Stack
Backend: Flask + LangChain + Chroma

Embeddings / Rerank: Cohere

Storage: Chroma (local or mounted volume)

Frontend: Single HTML file (ui.html)

Features
Retrieval-Augmented Generation (RAG)
Extractive-only answers — copied directly from retrieved context

Grounding check threshold — ensures accuracy

Cohere rerank (rerank-english-v3.0) for high-precision results

MMR retrieval for diverse candidate results

Guardrails & Intents
Pricing/cost questions → return contact info

Greetings / thanks / goodbye handled naturally

Rotating fallbacks for reliability

Document Ingestion
Upload: PDFs, DOCX, TXT via /upload

Batch ingest: from local directory (ingest.py)

Optional web crawl: via ingest_web.py

Stable IDs, deduplication, and upserts

Export Options
Plain formats: TXT / JSON / PDF / DOCX

One-pager brochure (answer-based)

Tri-fold brochure with:

Brand title & hero image

Section blocks

Contact info

Frontend (ui.html)
Clean, mobile-style light theme

Sources shown as chips under answers

Save as toolbar:

Save latest answer

Save full conversation

window.API_BASE override for any API host

Repo Layout
bash
Copy
Edit
.
├─ app.py                 # Flask API (chat, upload, export)
├─ ingest.py              # Local directory ingestion
├─ ingest_web.py          # Optional web crawler
├─ requirements.txt
├─ Procfile               # For Railway/Heroku-like platforms
├─ prestart.sh            # Optional: DB download at startup
├─ ui.html                # Frontend
├─ assets/                # Optional logos for exports
└─ downloaded_content/    # Optional docs to ingest
Environment Variables
Variable	Description
COHERE_API_KEY	Cohere API key
PERSIST_DIR	Absolute path to Chroma DB (./chroma_db default)
Optional (Exports)	
LOGO_PATH	Path to logo image (PNG/JPG)
FONT_TTF	Unicode TTF font for PDFs
Optional (Railway)	
CHROMA_GDRIVE_ID	Google Drive ID for chroma_db.zip
CHROMA_ZIP_URL	Direct URL to chroma_db.zip
CHROMA_FORCE_RELOAD	Force DB re-download

Quick Start (Local)
1. Clone & Install
bash
Copy
Edit
git clone https://github.com/<you>/Chatbot.git
cd Chatbot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
2. Ingest Documents (Optional)
bash
Copy
Edit
export COHERE_API_KEY=your_key
python ingest.py --input-dir ./downloaded_content
3. Run Backend
bash
Copy
Edit
export COHERE_API_KEY=your_key
export PERSIST_DIR="$(pwd)/chroma_db"
python app.py
# Server running at http://127.0.0.1:5000
4. Open UI
Edit in ui.html:

html
Copy
Edit
<script>window.__API_BASE__ = "http://127.0.0.1:5000";</script>
Serve locally:

bash
Copy
Edit
python -m http.server 8000
# Open http://localhost:8000/ui.html
API Endpoints
POST /chat
Request

json
Copy
Edit
{"question": "...", "history": [], "fail_count": 0}
Response

json
Copy
Edit
{"answer": "...", "fail_count": 0, "sources": [...]}
POST /upload
Form-data: files=[PDF|DOCX|TXT,...]

Adds chunks to Chroma (upsert per file)

POST /export
Plain Export
json
Copy
Edit
{"type": "pdf|docx|txt|json", "content": "...", "filename": "name"}
One-pager Brochure
json
Copy
Edit
{
  "type": "pdf|docx",
  "template": "brochure",
  "question": "...",
  "answer": "...",
  "sources": [...],
  "brandTitle": "Agent42Labs"
}
Tri-fold Brochure
json
Copy
Edit
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
        {"type": "h", "text": "WHY US"},
        {"type": "p", "text": "We deliver secure, scalable AI solutions to automate workflows and elevate customer experiences."},
        {"type": "bullets", "items": ["Secure by design", "Cloud-native architecture", "Rapid delivery"]},
        {"type": "contact"}
      ]
    },
    "middle": {"blocks": [{"type": "title"}, {"type": "subtitle"}]},
    "right": {
      "blocks": [
        {"type": "h", "text": "OUR SOLUTIONS"},
        {"type": "bullets", "items": ["Fraud detection", "Automated KYC", "Credit risk", "Real-time payments"]}
      ]
    },
    "contact": {
      "phone": "+91 7027119799",
      "email": "support@agent42labs.com",
      "website": "https://agent42labs.com"
    }
  }
}
