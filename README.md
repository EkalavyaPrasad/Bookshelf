# Bookshelf

# Bookshelf

A lightweight, self-hosted PDF library server. Drop PDFs onto your machine, browse your collection from any device on your local network, and read them in the browser — no downloading, no syncing apps required.

Built as a personal alternative to services like Readarr, following the same self-hosting philosophy as the *arr stack. This project does **not** connect to trackers or handle automated downloading — PDFs are added manually by you.

---

## Features

- Browse your PDF collection as a visual grid with cover images and metadata
- Read PDFs on any device via browser, no download needed
- Tracks reading progress per book across sessions
- Automatically extracts title, author, and page count from PDF metadata on startup
- Generates cover thumbnails from the first page of each PDF

---

## Tech Stack

| Layer | Tool |
|---|---|
| Backend | FastAPI (Python) |
| PDF Rendering | PDF.js (Mozilla, prebuilt dist) |
| Database | SQLite |
| Frontend | Vanilla HTML + CSS + JS |
| Server | Uvicorn |

---

## Prerequisites

**Python dependencies** (via pip):
```
fastapi
uvicorn
pypdf
pdf2image
pydantic
```

**System dependency — Poppler** (required by `pdf2image`, install via apt):
```bash
sudo apt install poppler-utils
```

> `pdf2image` is a Python wrapper around Poppler. Without this system package installed, cover generation will fail with a cryptic error.

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/EkalavyaPrasad/Bookshelf.git
cd Bookshelf

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Poppler
sudo apt install poppler-utils
```

---

## Running the Server

```bash
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open a browser and visit:
```
http://<your-server-ip>:8000
```

To find your server's IP:
```bash
hostname -I
```

---

## Adding Books

Drop PDF files into the `Books/` folder. On the next page load, the server will automatically scan for new files, extract their metadata, generate cover images, and add them to the library.

```bash
cp mybook.pdf ~/Bookshelf/Books/
```

---

## File Structure

```
Bookshelf/
├── main.py               ← FastAPI app, API routes
├── extract_meta.py       ← PDF ingestion, metadata extraction, cover generation
├── requirements.txt
├── Books/                ← Drop your PDFs here (gitignored)
├── Covers/               ← Auto-generated cover thumbnails (gitignored)
└── static/
    ├── homepage.html     ← Library grid view
    ├── index.html        ← PDF reader view
    └── pdfjs/
        ├── pdf.js
        ├── pdf.worker.js
        └── pdf_viewer.css
```

---

## Notes

- **Single user only** — no authentication is implemented. Intended for use on a trusted local network.
- The SQLite database (`bookshelf.db`) is created automatically on first run.
- The `Books/` and `Covers/` directories are created automatically if they don't exist.
- PDF.js handles rendering entirely in the browser using HTTP range requests — only the pages you view are fetched, not the whole file.
