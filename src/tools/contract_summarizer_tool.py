import pymupdf
import base64
import numpy as np
import faiss
import tiktoken

from typing import List
from openai import OpenAI
from langchain_community.tools import tool

from config import model, embeddings, openai_client


# =========================================================
# CONFIG
# =========================================================

client = openai_client

MODEL_NAME = model
EMBED_MODEL = "text-embedding-3-large"

CHUNK_SIZE = 800
TOP_K = 3
TOKEN_THRESHOLD = 6000

enc = tiktoken.get_encoding("cl100k_base")


# =========================================================
# PAGE → IMAGE
# =========================================================

def page_to_base64(page):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
    return base64.b64encode(pix.tobytes("png")).decode()


# =========================================================
# STRUCTURE DETECTION
# =========================================================

def detect_structure(doc):

    content = [{
        "type": "text",
        "text": """
Classify this PDF as:

STRUCTURED / UNSTRUCTURED

STRUCTURED:
- clean digital text
- reports
- paragraphs
- very plain text 

UNSTRUCTURED:
- tables
- forms
- columns
- scanned-like pages

Return Unstructured ONLY if open source OCR will definitely fail for given page structure.
"""
    }]

    for i in range(min(2, len(doc))):
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{page_to_base64(doc[i])}"
            }
        })

    resp = openai_client.chat.completions.create(
        model="gpt-5.1",
        temperature=0,
        messages=[{"role": "user", "content": content}],
    )

    return resp.choices[0].message.content.strip().upper()


# =========================================================
# OCR PAGE EXTRACTION
# =========================================================

def extract_page_llm(page):

    img = page_to_base64(page)

    resp = openai_client.chat.completions.create(
        model="gpt-5.1",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all readable text from this medical page. Preserve structure."
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img}"}
                    }
                ],
            }
        ],
    )

    return resp.choices[0].message.content.strip()


# =========================================================
# TOKEN HELPERS
# =========================================================

def count_tokens(text: str) -> int:
    return len(enc.encode(text))


def chunk_text(text: str) -> List[str]:
    tokens = enc.encode(text)
    return [
        enc.decode(tokens[i:i + CHUNK_SIZE])
        for i in range(0, len(tokens), CHUNK_SIZE)
    ]


# =========================================================
# EMBEDDINGS + FAISS
# =========================================================

def embed(texts: List[str]):
    return client.embeddings.create(
        model=EMBED_MODEL,
        input=texts
    ).data


def embed_query(q: str):
    return client.embeddings.create(
        model=EMBED_MODEL,
        input=[q]
    ).data[0].embedding


def build_index(vectors):
    arr = np.array([v.embedding for v in vectors]).astype("float32")
    index = faiss.IndexFlatL2(arr.shape[1])
    index.add(arr)
    return index


def retrieve(index, chunks, q_vec):
    _, I = index.search(np.array([q_vec]).astype("float32"), TOP_K)
    return [chunks[i] for i in I[0] if i < len(chunks)]


# =========================================================
# DIRECT ANSWER
# =========================================================


def answer_direct(question: str, doc: str, system_prompt: str = None):

    system_prompt = """
Answer only using the supplied document content.

"""

    messages = [
        ("system", system_prompt),
        ("user", f"""
Imagine that user query passed to retriever and retriever returned top K chunks and these chunks will be passed as iinput to you , not the whole document. So you have access to whole document. Do Not pretend that you dont have the document

DOCUMENT:
{doc}

QUESTION:
{question}
""")
    ]

    resp = model.invoke(messages)

    return resp.content
    
# =========================================================
# MAIN PIPELINE
# =========================================================
@tool
def summarize_contract_document(pdf_path: str, concise_user_query: str):
    """
    Legal Document Summarizer Tool.

    This tool processes legal PDFs and generates relevant summary or structured content.

    --------------------------
    INPUTS
    --------------------------
    pdf_path : str
        Document Path on local to the legal document PDF file.

    concise_user_query : str
        User query with supporting details, inside 1 line ONLY.

    --------------------------
    WHEN TO USE THIS TOOL
    --------------------------
    Use this tool when:
    - User uploads or references legal documents (PDF, contracts, agreements)
    - You need summarised version of the contract
  
    DO NOT USE WHEN:
    - No document is provided
    - Question is general legal knowledge (use legal_research_tool instead)
    - Only drafting or rewriting is required

    """
    question=concise_user_query
    print("\n" + "="*80)
    print(f"[START] Processing PDF: {pdf_path}")
    print("="*80)
    
    print("\n==============================")
    print(f"🔍 Incoming Query: {question}")
    print("==============================")

    doc = pymupdf.open(pdf_path)

    print(f"[INFO] Pages in document: {len(doc)}")

    if len(doc) == 0:
        print("[ERROR] Empty PDF")
        return "Empty PDF"

    # -----------------------------------------------------
    # STEP 1: STRUCTURE DETECTION
    # -----------------------------------------------------

    print("\n[STEP 1] Detecting structure...")

    try:
        structure = detect_structure(doc)
        print(f"[STRUCTURE RESULT] {structure}")
    except Exception as e:
        print(f"[ERROR] Structure detection failed: {e}")
        return str(e)

    use_ocr = "UNSTRUCTURED" in structure or "SCANNED" in structure

    print(f"[DECISION] use_ocr = {use_ocr}")

    # -----------------------------------------------------
    # STEP 2: EXTRACTION
    # -----------------------------------------------------

    print("\n[STEP 2] Extracting text page-by-page...")

    full_text = ""

    for i, page in enumerate(doc):

        try:
            text = page.get_text().strip()
            

            if len(text) < 30:
                text = extract_page_llm(page)

            elif use_ocr:
                text = extract_page_llm(page)

            else:
                print("[MODE] PyMuPDF used")

        except Exception as e:
            print(f"[ERROR] Page extraction failed: {e}")
            text = ""

        full_text += text + "\n"

    doc.close()

    print("\n[INFO] Full text length:", len(full_text))

    if len(full_text.strip()) < 50:
        print("[ERROR] No meaningful text extracted")
        return "No meaningful text extracted"

    # -----------------------------------------------------
    # STEP 3: RETURN DOCUMENT OR CHUNKS
    # -----------------------------------------------------
    
    token_count = count_tokens(full_text)
    
    print(f"\n[TOKEN COUNT] {token_count}")
    
    
    # =====================================================
    # SMALL DOCUMENT
    # =====================================================
    
    if token_count <= TOKEN_THRESHOLD:
    
        print("[MODE] FULL DOCUMENT")
    
        return full_text
    
    # =====================================================
    # LARGE DOCUMENT
    # =====================================================
    
    print("[MODE] RETRIEVAL MODE")
    
    chunks = chunk_text(full_text)
    
    print(f"[INFO] Total chunks: {len(chunks)}")
    
    vectors = embed(chunks)
    
    print("[INFO] Embeddings created")
    
    index = build_index(vectors)
    
    q_vec = embed_query(question)
    
    top_chunks = retrieve(
        index=index,
        chunks=chunks,
        q_vec=q_vec
    )
    
    print(f"[TOP K] Retrieved {len(top_chunks)} chunks")
    
    return top_chunks