import sqlite3
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# =========================================================
# PATH SETUP
# =========================================================
DATA_PATH = ROOT_DIR / "data/legal_knowledge_base"
DB_PATH = ROOT_DIR / "data/vector_dbs/uae_legal_compliance_vector"
CHUNK_SIZE_TOKENS = 600
CHUNK_OVERLAP_TOKENS = 50


def vector_db_exists(db_path: Path = DB_PATH) -> bool:
    """Return True when a persisted Chroma DB has indexed documents."""
    if not db_path.is_dir():
        return False

    chroma_sqlite = db_path / "chroma.sqlite3"
    if chroma_sqlite.is_file():
        try:
            with sqlite3.connect(f"file:{chroma_sqlite}?mode=ro", uri=True) as conn:
                row = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()
                return bool(row and row[0] > 0)
        except sqlite3.DatabaseError:
            return False

    legacy_files = [
        db_path / "chroma-collections.parquet",
        db_path / "chroma-embeddings.parquet",
    ]
    if all(path.is_file() for path in legacy_files):
        return True

    return False


def load_documents():
    from langchain_community.document_loaders import (
        PyPDFLoader,
        TextLoader,
        UnstructuredWordDocumentLoader,
    )

    # =========================================================
    # LOAD DOCUMENTS
    # =========================================================
    documents = []

    print("\n📂 Loading documents from:", DATA_PATH)

    for filepath in DATA_PATH.rglob("*"):
        if not filepath.is_file() or filepath.name.startswith("."):
            continue

        file = filepath.name
        suffix = filepath.suffix.lower()

        try:
            if suffix == ".pdf":
                loader = PyPDFLoader(str(filepath))
                docs = loader.load()

            elif suffix == ".docx":
                loader = UnstructuredWordDocumentLoader(str(filepath))
                docs = loader.load()

            elif suffix == ".txt":
                loader = TextLoader(str(filepath), encoding="utf-8")
                docs = loader.load()

            else:
                continue

            # -------------------------
            # FIXED METADATA (IMPORTANT)
            # -------------------------
            for d in docs:
                d.metadata = {
                    **(d.metadata or {}),
                    "source": file,
                    "file_path": str(filepath),
                }

            documents.extend(docs)

        except Exception as e:
            print(f"⚠️ Failed to load {file}: {e}")

    print(f"\n✅ Total documents loaded: {len(documents)}")

    return documents


def build_vector_db(clean_db: bool = True) -> Path:
    from langchain_community.vectorstores import Chroma
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    from config import embeddings

    # =========================================================
    # OPTIONAL CLEAN OLD DB (DEV ONLY)
    # =========================================================
    if clean_db and DB_PATH.exists():
        print("🧹 Removing old vector DB...")
        shutil.rmtree(DB_PATH)

    documents = load_documents()

    # =========================================================
    # VALIDATION CHECK
    # =========================================================
    if len(documents) == 0:
        raise ValueError("❌ No documents loaded. Check DATA_PATH or file formats.")

    # =========================================================
    # CHUNKING (TOKEN-AWARE)
    # =========================================================
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=CHUNK_SIZE_TOKENS,
        chunk_overlap=CHUNK_OVERLAP_TOKENS,
    )

    chunks = splitter.split_documents(documents)

    print(
        "✂️ Total chunks created: "
        f"{len(chunks)} "
        f"(chunk_size={CHUNK_SIZE_TOKENS} tokens, "
        f"overlap={CHUNK_OVERLAP_TOKENS} tokens)"
    )

    if len(chunks) == 0:
        raise ValueError("❌ Chunking failed. No chunks generated.")

    # =========================================================
    # VECTOR DB CREATION (CHROMA)
    # =========================================================
    print("⏳ This will take less than a minute...")
    print("\n🚀 Creating vector database...")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(DB_PATH),
    )

    # =========================================================
    # SAVE SAFELY (only if supported)
    # =========================================================
    try:
        vectorstore.persist()
    except Exception:
        pass

    # =========================================================
    # DONE
    # =========================================================
    print("\n🎉 VECTOR DB BUILD COMPLETE")
    print("📦 Location:", DB_PATH)
    print("🧠 Embeddings model:", getattr(embeddings, "model", "unknown"))
    print("📊 Total chunks indexed:", len(chunks))

    return DB_PATH


def ensure_vector_db() -> Path:
    if vector_db_exists():
        print(f"✅ Vector DB found: {DB_PATH}")
        return DB_PATH

    print(f"⚠️ Vector DB not found at {DB_PATH}")
    print("🔧 Building vector DB before application startup...")
    return build_vector_db(clean_db=DB_PATH.exists())


if __name__ == "__main__":
    build_vector_db(clean_db=True)
