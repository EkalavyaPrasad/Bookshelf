#
import os
import pdf2image
from pypdf import PdfReader
import sqlite3
import sys
from pathlib import Path




#cur = con.cursor()
#try:
#    cur.execute("CREATE TABLE Books(id INTEGER PRIMARY KEY, filename, title, author, page_count, cover_path)")
#except:
#    print("db exists continuing..")

def get_metadata(filename, folder_name = "Books"):
    
    filepath = os.path.join(f"{folder_name}", filename)
    print(filepath)
    result = {
    "title":      None,
    "author":     None,
    "page_count": None,
}
    reader = PdfReader(filepath)
    meta = reader.metadata
    try:
        result["title"] = meta.title
        result["author"] = meta.author
        result["page_count"] = len(reader.pages)
    except Exception as e:
        print(f"  [warn] Could not read metadata from {filepath.name}: {e}")

    return result

#Generate Cover Images
def generate_cover_images(filename, folder_name = "Books", destination_name="Covers"):
    
    if not os.path.exists(f"{destination_name}"):
            os.makedirs(f"{destination_name}")
            
    #  for filename in os.listdir(f"Bookshelf/{folder_name}"):

    filepath = os.path.join(f"{folder_name}", filename)

    images = pdf2image.convert_from_path(
    filepath,
    dpi=100,
    first_page=1,
    last_page=1
)

    cover_name = os.path.splitext(filename)[0] + ".jpg"

    images[0].save(
    os.path.join(f"{destination_name}", cover_name),
    "JPEG"
    )

    print(f"Cover created for {os.path.splitext(filename)[0]}")

    return os.path.join(f"{destination_name}", cover_name)



def ingest_file(pdf_path: Path, cur: sqlite3.Cursor) -> bool:
    """
    Ingest a single PDF. Returns True if a new row was inserted, False if skipped.
    """
    filename = pdf_path
 
    # Skip if already in DB
    cur.execute("SELECT id FROM Books WHERE filename = ?", (filename,))
    if cur.fetchone():
        print(f"  [skip] Already in database: {filename}")
        return False
 
    print(f"  [ingest] {filename}")
 
    # 1. Metadata
    meta       = get_metadata(filename)
    title      = meta["title"]
    author     = meta["author"]
    page_count = meta["page_count"]
 
    print(f"    Title:  {title}")
    print(f"    Author: {author}")
    print(f"    Pages:  {page_count or 'unknown'}")

    cover_rel = generate_cover_images(filename)

    cur.execute(
        """
        INSERT INTO books (filename, title, author, page_count, cover_path)
        VALUES (?, ?, ?, ?, ?)
        """,
        (filename, title, author, page_count, cover_rel),
    )
 
    return True


def run(file_path="Books", targets: list[Path] | None = None):
    BOOKS_DIR = os.listdir(file_path)

    DB_PATH = Path("bookshelf.db") 
    con = sqlite3.connect(DB_PATH)

    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Books (
        id INTEGER PRIMARY KEY,
        filename TEXT,
        title TEXT,
        author TEXT,
        page_count INTEGER,
        cover_path TEXT
    )
    """)
 
    pdfs = targets if targets else sorted(BOOKS_DIR)
    print(f"Is this the pdfs thing? {pdfs}")
 
    if not pdfs:
        print("No PDFs found.")
        return
 
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
 
    ingested = 0
    for pdf in pdfs:
        pdf_path = os.path.join(f"{file_path}", pdf)
        print(f"pdf_path: {pdf_path}")
        if not Path(pdf_path).exists():
            print(f"  [error] File not found: {pdf_path}")
            continue
        if ingest_file(pdf, cur):
            ingested += 1


    keep_set = set(pdfs)

    if keep_set:
        placeholders = ",".join("?" for _ in keep_set)
        sql = f"DELETE FROM Books WHERE filename NOT IN ({placeholders})"
        cur.execute(sql, tuple(keep_set))
    else:
        cur.execute("DELETE FROM Books")
 
    con.commit()
    con.close()
 
    print(f"\nDone. {ingested} new book(s) added.")


    
if __name__ == "__main__":
            run()

DB_PATH = Path("bookshelf.db")
new_con = sqlite3.connect(DB_PATH)
new_cur = new_con.cursor()
for row in new_cur.execute("SELECT page_count, author, title FROM Books ORDER BY page_count"):
    print(row)
