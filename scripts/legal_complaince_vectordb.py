import os
import shutil
import sys
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env.example")

embeddings = OpenAIEmbeddings(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.core42.ai/v1"),
    model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
)


# =========================================================
# PATH SETUP
# =========================================================
DATA_PATH = ROOT_DIR / "data/legal_knowledge_base"
DB_PATH = ROOT_DIR / "data/vector_dbs/uae_legal_compliance_vector"
CHUNK_SIZE_TOKENS = 600
CHUNK_OVERLAP_TOKENS = 50


# =========================================================
# OPTIONAL CLEAN OLD DB (DEV ONLY)
# =========================================================
CLEAN_DB = True

if CLEAN_DB and DB_PATH.exists():
    print("🧹 Removing old vector DB...")
    shutil.rmtree(DB_PATH)


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