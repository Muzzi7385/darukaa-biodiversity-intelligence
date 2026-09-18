from pathlib import Path
from typing import Iterator

import chromadb
from pypdf import PdfReader

from backend.rag.embeddings import generate_embeddings


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"


# ---------------------------------------------------------
# Chroma
# ---------------------------------------------------------

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name="environmental_knowledge",
    metadata={"hnsw:space": "cosine"},
)


# ---------------------------------------------------------
# Chunking
# ---------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> Iterator[str]:
    """
    Split extracted text into overlapping character chunks.

    Overlap helps preserve context between neighbouring chunks.
    """

    cleaned = " ".join(text.split())

    if not cleaned:
        return

    start = 0
    text_length = len(cleaned)

    while start < text_length:
        end = min(
            start + chunk_size,
            text_length
        )

        chunk = cleaned[start:end].strip()

        if chunk:
            yield chunk

        if end >= text_length:
            break

        start = end - overlap


# ---------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------

def extract_pdf_chunks(
    pdf_path: Path,
) -> list[dict]:
    """
    Extract text from every page of a PDF and generate
    chunks with source metadata.
    """

    reader = PdfReader(str(pdf_path))

    chunks: list[dict] = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text() or ""

        if not text.strip():
            continue

        page_chunks = list(
            chunk_text(text)
        )

        for chunk_index, chunk in enumerate(
            page_chunks
        ):

            chunks.append(
                {
                    "text": chunk,
                    "source": pdf_path.name,
                    "page": page_number,
                    "chunk_index": chunk_index,
                }
            )

    return chunks


# ---------------------------------------------------------
# Ingest documents
# ---------------------------------------------------------

def ingest_documents() -> None:

    pdf_files = sorted(
        DOCUMENTS_DIR.glob("*.pdf")
    )

    if not pdf_files:
        print(
            "No PDF files found in:",
            DOCUMENTS_DIR
        )
        return

    all_chunks: list[dict] = []

    # -----------------------------------------------------
    # Extract chunks from all PDFs
    # -----------------------------------------------------

    for pdf_file in pdf_files:

        print()
        print("=" * 60)
        print(f"Processing: {pdf_file.name}")
        print("=" * 60)

        document_chunks = extract_pdf_chunks(
            pdf_file
        )

        print(
            f"Extracted {len(document_chunks)} chunks"
        )

        all_chunks.extend(
            document_chunks
        )

    # -----------------------------------------------------
    # Validate extraction
    # -----------------------------------------------------

    if not all_chunks:
        print("No text could be extracted.")
        return

    # -----------------------------------------------------
    # Prepare text
    # -----------------------------------------------------

    texts = [
        item["text"]
        for item in all_chunks
    ]

    print()
    print(
        f"Generating embeddings for {len(texts)} chunks..."
    )

    embeddings = generate_embeddings(
        texts
    )

    # -----------------------------------------------------
    # Prepare Chroma metadata
    # -----------------------------------------------------

    print("Preparing Chroma records...")

    ids: list[str] = []
    metadatas: list[dict] = []

    for index, item in enumerate(
        all_chunks
    ):

        ids.append(
            f"{item['source']}__"
            f"page_{item['page']}__"
            f"chunk_{item['chunk_index']}__"
            f"{index}"
        )

        metadatas.append(
            {
                "source": item["source"],
                "page": item["page"],
                "chunk_index": item["chunk_index"],
            }
        )

    # -----------------------------------------------------
    # Chroma batch upload
    # -----------------------------------------------------

    print()
    print("Adding chunks to Chroma...")

    # Chroma has a maximum batch size of 5461.
    # We intentionally stay below that limit.
    BATCH_SIZE = 5000

    total_items = len(ids)

    for start in range(
        0,
        total_items,
        BATCH_SIZE
    ):

        end = min(
            start + BATCH_SIZE,
            total_items
        )

        print(
            f"Uploading chunks "
            f"{start + 1}-{end} "
            f"of {total_items}..."
        )

        collection.upsert(
            ids=ids[start:end],
            documents=texts[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

    print()
    print("All chunks uploaded successfully.")

    # -----------------------------------------------------
    # Completion message
    # -----------------------------------------------------

    print()
    print("=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Documents: {len(pdf_files)}")
    print(f"Chunks: {len(all_chunks)}")
    print(f"Stored in: {CHROMA_DIR}")
    print(f"Collection: {collection.name}")


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    ingest_documents()