import pymupdf
import re
import numpy as np
import faiss
import tiktoken
from typing import List
from openai import OpenAI
from config import model, llm
import numpy as np
import base64
import faiss
from langchain_community.tools import tool
from langchain_core.messages import HumanMessage
from config import model, llm, openai_client, embeddings

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

EMBED_MODEL = "text-embedding-3-large"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 20
TOP_K = 10

enc = tiktoken.get_encoding("cl100k_base")


# =========================================================
# TEXT EXTRACTION FROM PDF
# =========================================================

def extract_pdf_text(pdf_path: str) -> str:

    doc = pymupdf.open(pdf_path)

    full_text = []

    for page in doc:
        text = page.get_text().strip()
        full_text.append(text)

    doc.close()

    return "\n".join(full_text)

    
# =========================================================
# PAGE → IMAGE
# =========================================================

def page_to_base64(page):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
    return base64.b64encode(pix.tobytes("png")).decode()


# =========================================================
# FILE DETECTION
# =========================================================

from pathlib import Path

def get_file_type(path: str):
    return Path(path).suffix.lower()
    
# =========================================================
# CHUNKING
# =========================================================

def chunk_text(text: str) -> List[str]:

    tokens = enc.encode(text)
    chunks = []

    start = 0

    while start < len(tokens):

        end = start + CHUNK_SIZE
        chunks.append(enc.decode(tokens[start:end]))

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# DOC Extractor

from docx import Document

def extract_docx_text(docx_path: str) -> str:

    doc = Document(docx_path)

    full_text = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            full_text.append(text)

    return "\n".join(full_text)



def extract_structured_pdf(pdf_path: str):

    doc = pymupdf.open(pdf_path)
    full_text = []

    for page in doc:

        data = page.get_text("dict")

        page_text = []

        for block in data["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                line_text = " ".join(
                    span["text"] for span in line["spans"]
                )
                page_text.append(line_text)

        full_text.append("\n".join(page_text))

    doc.close()
    return "\n".join(full_text)

    
def extract_pdf_text(pdf_path: str, use_ocr: bool = False) -> str:

    doc = pymupdf.open(pdf_path)
    full_text = []

    for page in doc:

        text = page.get_text().strip()

        # OCR fallback condition
        if use_ocr or len(text) < 30:
            print("[OCR] using LLM OCR")
            text = extract_page_llm(page)
        else:
            print("[PDF TEXT] using pymupdf")

        full_text.append(text)

    doc.close()
    return "\n".join(full_text)

    

def extract_text(file_path: str) -> str:

    ext = get_file_type(file_path)

    if ext == ".pdf":
        return extract_pdf_text(file_path)

    elif ext == ".docx":
        return extract_docx_text(file_path)

    else:
        raise ValueError("Unsupported file type")
# =========================================================
# STRUCTURE DETECTION
# =========================================================

def detect_structure(doc):

    content = [
        HumanMessage(content=[
            {
                "type": "text",
                "text": """
Classify this PDF as:

STRUCTURED / UNSTRUCTURED

STRUCTURED:
- clean digital text
- reports
- paragraphs
- Easily Readable
- Any OCR can handle 

UNSTRUCTURED:
- tables
- columns
- noisy scanned-like pages
- blurry texts
- partitioned paragraphs

Return only: STRUCTURED or UNSTRUCTURED

Return UNSTRUCTURED only if document is very tough to recognise for simple OCRs.
"""
            }
        ])
    ]

    # attach first 2 pages as images
    for i in range(min(2, len(doc))):
        content[0].content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{page_to_base64(doc[i])}"
            }
        })

    resp = llm.invoke(content)

    return resp.content.strip().upper()

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
# NUMERIC CLAUSE DETECTION
# =========================================================
import json

def extract_clause_numbers_llm(query: str):

    prompt = f"""
You are a legal intent detection system.

Your job:
Detect whether the user is referring to LEGAL DOCUMENT REFERENCES.

Legal references include:
- clauses (e.g., 3.2, 4.1.1)
- articles
- sections
- rules
- laws
- provisions

STRICT RULES:
- If the number is about sports, marks, salary, score, quantity → NOT legal
- Only extract numbers if clearly tied to legal document structure

Examples:
"clause 3.2 termination" → VALID → ["3.2"]
"article 10 of agreement" → VALID → ["10"]
"who scored 100 runs" → INVALID → []
"salary 5000 AED" → INVALID → []


Examples:

Query: "clause 3.2 termination"
→
{{
  "is_legal": true,
  "numbers": ["3", "3.2"]
}}

Query: "section 9.1 b obligations"
→
{{
  "is_legal": true,
  "numbers": ["9", "9.1", "9.1 b"]
}}

Query: "article 10 of agreement"
→
{{
  "is_legal": true,
  "numbers": ["10"]
}}

Query: "who scored 100 runs"
→
{{
  "is_legal": false,
  "numbers": []
}}


Return ONLY valid JSON:
{{
  "is_legal": true/false,
  "numbers": []
}}

Query:
{query}
"""

    resp = llm.invoke(prompt)

    # extract raw text
    text = resp.content.strip()

    # safe JSON parsing
    try:
        return json.loads(text)
    except:
        return {
            "is_legal": False,
            "numbers": []
        }

# =========================================================
# NUMERIC SEARCH
# =========================================================
def search_numeric(chunks: List[str], numbers: List[str]):

    matches = []
    seen_chunks = set()

    for i, chunk in enumerate(chunks):

        norm = chunk.replace("\n", " ")

        for num in numbers:

            pattern = rf"(?<!\d){re.escape(num)}\.?(?!\d)"

            if re.search(pattern, norm):

                # current chunk + next 2 chunks
                for j in range(i, min(i + 3, len(chunks))):

                    if j not in seen_chunks:
                        seen_chunks.add(j)
                        matches.append(chunks[j])

                break  # avoid re-processing same chunk for other numbers

    return matches
# =========================================================
# EMBEDDINGS
# =========================================================

def embed_texts(texts: list[str]):

    vectors = embeddings.embed_documents(texts)

    return vectors

def embed_query(query: str):

    return embeddings.embed_query(query)


# =========================================================
# FAISS
# =========================================================


def build_index(vectors):

    arr = np.array(vectors).astype("float32")

    index = faiss.IndexFlatL2(arr.shape[1])
    index.add(arr)

    return index


def retrieve(index, chunks, q_vec):

    _, I = index.search(
        np.array([q_vec]).astype("float32"),
        TOP_K
    )

    return [chunks[i] for i in I[0] if i < len(chunks)]


# =========================================================
# MAIN FUNCTION (FINAL OUTPUT ONLY)
# =========================================================


@tool
def legal_clause_extraction_tool(pdf_path: str, user_query: str):

    """
    Tool Name : process_pdf_for_clauses
    Legal clause extraction tool for user-provided PDF documents.

    This tool works ONLY on the PDF file provided via `pdf_path`.
    It is used to extract relevant clauses, articles, sections,
    or provisions based on the user's query.

    It first tries to detect legal clause references (e.g., 3.2, Article 10).
    If found, it performs direct matching on the document.
    Otherwise, it falls back to semantic (embedding-based) search.

    Args:
        pdf_path (str): Path to user-uploaded PDF document.
        user_query (str): User question about clauses or sections.

    Returns:
        list[str]: Relevant text chunks from the same document.
    """
    print("\n" + "=" * 60)
    print(f"[START] {pdf_path}")
    print(f"[QUERY] {user_query}")
    print("=" * 60)

    doc = pymupdf.open(pdf_path)

    try:
        structure = detect_structure(doc)
        print(f"[STRUCTURE] {structure}")
    except:
        structure = "STRUCTURED"

    use_ocr = "UNSTRUCTURED" in structure

    full_text = ""

    for page in doc:

        if use_ocr:
            text = extract_page_llm(page)

        else:

            text_raw = page.get_text("text")

            blocks = page.get_text("blocks")
            block_text = "\n".join([b[4] for b in blocks if b[4].strip()])

            text = text_raw + "\n" + block_text

            text = re.sub(r"\n\s*(\d+)\s*\.\s*", r"\n\1. ", text)
            text = re.sub(r"\n\s*(\d+\.\d+)\s*", r"\n\1 ", text)

        full_text += text + "\n"

    doc.close()

    if len(full_text.strip()) < 50:
        return []

    chunks = chunk_text(full_text)
    token_count = len(enc.encode(full_text))


    if token_count <= 7000:
        return full_text

    result = extract_clause_numbers_llm(user_query)
    is_legal = result.get("is_legal", False)
    numbers = result.get("numbers", [])

    print(f"[CLAUSE] legal={is_legal}, numbers={numbers}")

    matches = []
    if is_legal and numbers:
        matches = search_numeric(chunks, numbers)

    vectors = embed_texts(chunks)
    index = build_index(vectors)
    q_vec = embed_query(user_query)

    retrieved = retrieve(index, chunks, q_vec) or []

    final_chunks = matches + retrieved
    
    seen = set()
    deduped = []
    
    for x in final_chunks:
        if x not in seen:
            seen.add(x)
            deduped.append(x)
    
    final_chunks = deduped

    return final_chunks