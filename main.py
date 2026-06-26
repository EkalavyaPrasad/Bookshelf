from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sqlite3
from pathlib import Path
from pydantic import BaseModel

from fastapi import File, UploadFile
import shutil

from extract_meta import run 


app = FastAPI()
BOOKS_DIR = Path("Books")
COVERS_DIR = Path("Covers")

import os

BOOKS_DIR = Path("Books")
DB_PATH = Path(os.getenv("DB_PATH", "bookshelf.db"))  
COVERS_DIR = Path("Covers")


def ensure_directories():
    BOOKS_DIR.mkdir(exist_ok=True)
    COVERS_DIR.mkdir(exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # creates data/ if using Docker


ensure_directories()


# Serve your static files (HTML, PDF.js)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/Covers", StaticFiles(directory="Covers"), name="covers")


def ensure_progress_table():
    
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            filename     TEXT PRIMARY KEY,
            current_page INTEGER NOT NULL DEFAULT 1,
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    con.commit()
    con.close()
 
 
ensure_progress_table()


@app.get("/")
def index():
    run()
    return FileResponse("static/homepage.html")

@app.get("/read")
def read_book(file: str):
    # Basic safety check — prevent path traversal attacks
    book_path = (BOOKS_DIR / file).resolve()
    if not book_path.is_relative_to(BOOKS_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not book_path.exists():
        raise HTTPException(status_code=404, detail="Book not found")
    return FileResponse("static/index.html")

@app.get("/books/{filename}")
def serve_book(filename: str):
    book_path = (BOOKS_DIR / filename).resolve()
    if not book_path.is_relative_to(BOOKS_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not book_path.exists():
        raise HTTPException(status_code=404, detail="Book not found")
    return FileResponse(book_path, media_type="application/pdf")


@app.get("/api/books")          
def list_books():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row          # lets us access columns by name
    cur = con.cursor()
 
    cur.execute("""
        SELECT id, filename, title, author, page_count, cover_path
        FROM books
        
    """)
 
    rows  = cur.fetchall()
    con.close()

    books = []
    for row in rows:
        cover = None
        if row["cover_path"] and Path(row["cover_path"]).exists():
            # Expose cover as a URL the browser can fetch
            stem  = Path(row["cover_path"]).stem
            cover = f"/Covers/{stem}.jpg"
 
        books.append({
            "id":         row["id"],
            "filename":   row["filename"],
            "title":      row["title"],
            "author":     row["author"],
            "page_count": row["page_count"],
            "cover":      cover,

        })
 
    return JSONResponse(content=books)

@app.get("/api/progress/{filename}")
def get_progress(filename: str):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT current_page FROM progress WHERE filename = ?", (filename,)
    ).fetchone()
    con.close()
    return JSONResponse({"page": row["current_page"] if row else 1})

class ProgressUpdate(BaseModel):
    page: int




@app.post("/api/progress/{filename}")
def save_progress(filename, body: ProgressUpdate):
    if body.page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
 
    # Verify the book exists
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    book = con.execute("SELECT filename FROM books WHERE filename = ?", (filename,)).fetchone()
    if not book:
        con.close()
        raise HTTPException(status_code=404, detail="Book not found")
 
    con.execute("""
        INSERT INTO progress (filename, current_page, updated_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(filename) DO UPDATE SET
            current_page = excluded.current_page,
            updated_at   = excluded.updated_at
    """, (filename, body.page))
    con.commit()
    con.close()
    return JSONResponse({"ok": True})


@app.post("/upload")
async def upload_book(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
        return FileResponse("static/homepage.html")

    dest = BOOKS_DIR / file.filename
    if dest.exists():
        return FileResponse("static/homepage.html")
        raise HTTPException(status_code=409, detail="A book with that filename already exists")
       

    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    # Re-scan metadata so the new book appears immediately
    run()
    return FileResponse("static/homepage.html")

    return JSONResponse({"ok": True, "filename": file.filename})


@app.delete("/api/books/{filename}")
def delete_book(filename: str):
    # Remove from DB first
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM books WHERE filename = ?", (filename,))
    con.execute("DELETE FROM progress WHERE filename = ?", (filename,))
    con.commit()
    con.close()

    # Remove the file
    book_path = (BOOKS_DIR / filename).resolve()
    if not book_path.is_relative_to(BOOKS_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if book_path.exists():
        book_path.unlink()

    return JSONResponse({"ok": True})
