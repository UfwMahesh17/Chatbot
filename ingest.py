import os
import re
import time
import hashlib
import argparse
import logging
import unicodedata
from typing import List, Tuple, Dict

# Optional: load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import PyPDF2
from docx import Document as DocxDocument
from langchain_community.vectorstores import Chroma
from langchain_cohere import CohereEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ----- Config -----
ALLOWED_EXT = {".txt", ".md", ".pdf", ".docx"}
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 180
DEFAULT_BATCH_SIZE = 64
DEFAULT_COLLECTION = "langchain"
DEFAULT_CHROMA_DIR = "chroma_db"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# ----- Text utils -----
def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00A0", " ")
    text = re.sub(r"(?m)^\s*\.\s*$", "", text)                     # remove lone dot lines
    text = re.sub(r"(?m)^\s*_{3,}\s*$", "\n\n===SEP===\n\n", text) # treat underscore lines as separators
    text = re.sub(r"(?<=[A-Za-z])\d{1,3}(?=[^0-9A-Za-z]|$)", "", text)  # strip footnote-like digits
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in {".txt", ".md"}:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return normalize_text(f.read())
        if ext == ".pdf":
            out = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    out.append(page.extract_text() or "")
            return normalize_text("\n".join(out))
        if ext == ".docx":
            doc = DocxDocument(path)
            return normalize_text("\n".join(p.text for p in doc.paragraphs))
    except Exception as e:
        logging.warning(f"Read error for {path}: {e}")
    return ""


# ----- Structure-aware parsing -----
NUM_ITEM_RE = re.compile(
    r"(?m)^\s*(\d+)\.\s+([^\n]+)\n(.*?)(?=^\s*\d+\.\s+[^\n]+\n|^===SEP===|\\Z)",
    re.DOTALL,
)

def section_aware_chunks(text: str) -> List[Tuple[str, Dict]]:
    sections = [s.strip() for s in text.split("===SEP===")] if "===SEP===" in text else [text]
    chunks: List[Tuple[str, Dict]] = []

    for sec in sections:
        lines = [l for l in sec.splitlines() if l.strip()]
        if not lines:
            continue

        # Title heuristic: first short line without terminal punctuation
        first = lines[0].strip()
        if len(first) <= 120 and not first.endswith((".", ":", ";")):
            title = first
            body = "\n".join(lines[1:])
        else:
            title = "Section"
            body = sec

        # Prefer numbered items if present
        found_items = False
        for m in NUM_ITEM_RE.finditer(sec):
            found_items = True
            num = int(m.group(1))
            item_title = m.group(2).strip()
            body_text = normalize_text(m.group(3).strip())
            content = f"{title} — {item_title}\n\n{body_text}".strip()
            chunks.append((content, {"section": title, "type": "list_item", "item_title": item_title, "item_number": num}))
        if found_items:
            continue

        # Otherwise paragraph chunks
        for p in re.split(r"\n\s*\n", body):
            p = p.strip()
            if len(p) >= 60:
                chunks.append((f"{title}\n\n{p}", {"section": title, "type": "paragraph"}))

    return chunks


# ----- Chunking and IDs -----
def chunk_long(content: str, meta: Dict, chunk_size: int, overlap: int) -> List[Tuple[str, Dict]]:
    if len(content) <= chunk_size:
        return [(content, meta)]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", "! ", "? ", " "],
    )
    out = []
    for i, part in enumerate(splitter.split_text(content)):
        m = dict(meta)
        m["part_index"] = i
        out.append((part, m))
    return out


def chunk_id(source_key: str, chunk_text: str) -> str:
    h = hashlib.sha1()
    h.update((source_key + "::" + chunk_text).encode("utf-8", errors="ignore"))
    return h.hexdigest()


# ----- Upsert -----
def upsert_file(vectorstore: Chroma, source_key: str, items: List[Tuple[str, Dict]], batch_size: int) -> Tuple[int, int]:
    """
    source_key: relative path (e.g., 'ABOUT/Services.txt'); ensures uniqueness across subfolders.
    items: List of (text, metadata)
    Returns (added, removed)
    """
    ids = [chunk_id(source_key, t) for t, _ in items]
    for _, m in items:
        m["source"] = source_key
        m.setdefault("filename", os.path.basename(source_key))
        m.setdefault("dir", os.path.dirname(source_key) or ".")

    # Existing ids for this file
    try:
        existing = vectorstore._collection.get(where={"source": source_key}, include=["ids"])  # type: ignore
        existing_ids = set(existing.get("ids", [])) if isinstance(existing, dict) else set()
    except Exception:
        existing_ids = set()

    to_delete = list(existing_ids - set(ids))
    removed = 0
    if to_delete:
        try:
            vectorstore._collection.delete(ids=to_delete)  # type: ignore
            removed = len(to_delete)
        except Exception as e:
            logging.warning(f"Delete failed for {source_key}: {e}")

    add_idx = [i for i, cid in enumerate(ids) if cid not in existing_ids]
    added = 0
    for start in range(0, len(add_idx), batch_size):
        sel = add_idx[start:start + batch_size]
        texts = [items[i][0] for i in sel]
        metas = [items[i][1] for i in sel]
        ids_batch = [ids[i] for i in sel]

        delay = 1.0
        for attempt in range(5):
            try:
                vectorstore.add_texts(texts=texts, metadatas=metas, ids=ids_batch)
                added += len(texts)
                break
            except Exception as e:
                msg = str(e).lower()
                transient = any(s in msg for s in ["429", "rate", "timeout", "temporar", "connection"])
                if attempt < 4 and transient:
                    sleep_for = delay * (2 ** attempt)
                    logging.info(f"[RETRY] add_texts failed, sleep {sleep_for:.1f}s … {e}")
                    time.sleep(sleep_for)
                else:
                    logging.error(f"Failed to add batch for {source_key}: {e}")
                    break

    return added, removed


# ----- Main -----
def main():
    p = argparse.ArgumentParser(description="Ingest local files (with subfolders) into Chroma using Cohere embeddings.")
    p.add_argument("--input-dir", default="downloaded_content",
                   help="Root directory with .txt/.md/.pdf/.docx files and subfolders (default: downloaded_content)")
    p.add_argument("--chroma-dir", default=DEFAULT_CHROMA_DIR)
    p.add_argument("--collection", default=DEFAULT_COLLECTION)
    p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    p.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    p.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    p.add_argument("--api-key", default=None, help="Cohere API key (overrides env/.env)")
    args = p.parse_args()

    # Resolve and validate paths
    input_dir = os.path.abspath(args.input_dir)
    if not os.path.isdir(input_dir):
        raise RuntimeError(f"Input directory not found: {args.input_dir}")

    api_key = args.api_key or os.getenv("COHERE_API_KEY")
    if not api_key:
        raise RuntimeError("No Cohere API key found. Pass --api-key or set COHERE_API_KEY (or .env).")

    embeddings = CohereEmbeddings(model="embed-english-v3.0", cohere_api_key=api_key)
    vectorstore = Chroma(
        collection_name=args.collection,
        persist_directory=args.chroma_dir,
        embedding_function=embeddings
    )

    total_files = total_added = total_removed = total_skipped = 0

    for root, _, files in os.walk(input_dir):
        for fn in files:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in ALLOWED_EXT:
                continue

            path = os.path.join(root, fn)
            rel_path = os.path.relpath(path, input_dir)   # e.g., "ABOUT/overview.txt"
            source_key = rel_path.replace(os.sep, "/")     # normalize slashes
            total_files += 1

            text = read_text(path)
            if not text or len(text) < 60:
                logging.info(f"[SKIP] {source_key}: no usable text")
                total_skipped += 1
                continue

            # Structure-aware parse, then length-based chunk if needed
            structured = section_aware_chunks(text)
            final_items: List[Tuple[str, Dict]] = []
            for content, meta in structured:
                final_items.extend(chunk_long(content, meta, args.chunk_size, args.chunk_overlap))

            added, removed = upsert_file(vectorstore, source_key, final_items, args.batch_size)
            total_added += added
            total_removed += removed
            logging.info(f"[OK] {source_key}: added={added}, removed={removed}, chunks={len(final_items)}")

    try:
        vectorstore.persist()
    except Exception as e:
        logging.warning(f"Persist warning: {e}")

    print("\n=== DONE ===")
    print(f"Files processed: {total_files} | Skipped: {total_skipped}")
    print(f"Chunks added: {total_added} | Old chunks removed: {total_removed}")
    print(f"Chroma dir: {os.path.abspath(args.chroma_dir)} | Collection: {args.collection}")


if __name__ == "__main__":
    main()