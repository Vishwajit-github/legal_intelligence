import os
import re
import time
from pathlib import Path

from langchain_community.tools import tool
from langchain_community.vectorstores import Chroma
from config import embeddings, llm
from typing import Optional, List

DATA_PATH = str(
    Path(__file__).resolve().parents[2]
    / "data/vector_dbs/uae_legal_compliance_vector"
)


legal_compliance_vectorstore = Chroma(
    persist_directory=DATA_PATH,
    embedding_function=embeddings
)


# -----------------------------
# Extract article number
# -----------------------------
def extract_article_number(query: str):
    match = re.search(r"(?:article|art)\s*(\d+)", query.lower())
    return match.group(1) if match else None


# -----------------------------
# SAFE regex builder (FIXED VERSION)
# -----------------------------
def build_article_pattern(article_no: str):
    """
    Prevents 1 matching 10/100/1102 etc.
    Supports:
    - Article 1
    - Article (1)
    - Article.1
    """
    return rf"\bart(?:icle|\.)?\s*[\(\.]?\s*{article_no}\s*[\)\.]?\b"


def search_numeric(chunks: List[str], regex_pattern):

    matches = []
    seen_chunks = set()

    numbers=list(set(numbers))

    print("NUMBERS", numbers)

    for i, chunk in enumerate(chunks):

        norm = chunk.replace("\n", " ")

        for num in numbers:

            print("NUM", num)

            pattern = rf"\b{re.escape(num)}\b"

            if re.search(pattern, norm):

                for j in range(i, min(i + 3, len(chunks))):

                    if j not in seen_chunks:
                        seen_chunks.add(j)

                        print(f"\n📄 Result | Type=Numeric | Chunk={j} | Matched={num}")

                        matches.append(chunks[j])

                break

    return matches

import json

def extract_legal_regex_llm(document_text: str,  articles: list[str] | None = None):

    prompt = f"""
You are a legal text pattern extraction system.

Your Job is only to return regex pattern associated with articles, clause or section specific numbers.
You will be provided with numbers specific to clause or articles also,

Legal references include:
- Articles (e.g., Article 10, Art. 10)
- Clauses (e.g., Clause 3.2, Cl. 3.2)
- Sections (e.g., Section 5, Sec. 5)

OR it can be any other wordings used instead of article, clauses. Like Law as well. So you need to analyze what words are there in Text and what articles need to extract and then create regex that can help me to extract chunks of relevant sections.

STRICT RULES:
- Do NOT explain anything
- Do NOT return text
- Do NOT guess formats not present in the document
- Return ONLY valid JSON
- Regex must be Python-compatible

Keep Simple Regex , if there are multiple articles then make sure regex handles all.

---

Return format:

{{
  "regex":"<your regex output>"
}}



---

Text:
{document_text}

Articles/Clauses Need to extract
{articles}
"""

    resp = llm.invoke(prompt)
    text = resp.content.strip()

    try:
        return json.loads(text)
    except Exception:
        return {"regex":""
        }
        
# -----------------------------
# MAIN TOOL
# -----------------------------
@tool
def legal_research_retrieval_tool(query: str, articles: Optional[List[str]] = None) -> str:
    """

     Args:
        query: User question with supporting details, within maximum 2 lines, with supporting information.
        articles: List of article numbers or clause numbers that explicitely mentioned by user OR articles that need to search. This can contain like Parts, Sections, Chapters etc. The naming can be different , not necessarily 'article' always.

     Output: Context associated to User Question

    MULTI-CALL RESTRICTION:
    - If the agent considers calling this tool again,
      it MUST first verify that the new query is:
        (a) missing entirely from previous retrieval

    
    Do Not Call this tool again for similar kind of question or rephrased question, ensuring we follow optimized practices.
    """

    start_time = time.time()
   
    print("\n==============================")
    print(f"🔍 Incoming Query: {query}")
    print("==============================")

    print("🔎 SEMANTIC MODE ACTIVATED")

    retrieval_start = time.time()
    results = legal_compliance_vectorstore.similarity_search_with_relevance_scores(
        query, k=3
    )

    print(
        "📦 Retrieved "
        f"{len(results)} semantic results in {round(time.time() - retrieval_start, 4)}s"
    )

    if not results:
        return "No relevant legal or compliance documents found."

    output_blocks = []
    all_file_names=[]
    for i, (doc, score) in enumerate(results):
        meta = doc.metadata or {}

        file_name = (
            meta.get("source_file")
            or os.path.basename(meta.get("source", meta.get("file_path", "unknown")))
        )

        all_file_names.append(file_name)
        page = meta.get("page", "NA")

        print(f"\n📄 Result {i} | File={file_name} | Page={page} | Score={score}")

        output_blocks.append(f"""
----------------------------------------
Document {i+1}
📄 File: {file_name}
📑 Page: {page}
⭐ Score: {round(score, 3)}
----------------------------------------

{doc.page_content}
""")

    regex_pattern=extract_legal_regex_llm(output_blocks)
    
    matches = []
    all_file_names=list(set(all_file_names))
    print(f"Articles {articles}")
    
        # =========================================================
    # STEP 3: REGEX + ARTICLE MODE (IF PROVIDED)
    # =========================================================
    if articles:

        print("\n==============================")
        print("🔎 REGEX EXTRACTION MODE")
        print("==============================")

        # Convert semantic context → text for regex generation
        context_text = "\n".join(output_blocks)

        # 3.1 Get regex from LLM
        regex_response = extract_legal_regex_llm(context_text, articles)
        regex_pattern = regex_response.get("regex", "")

        print(f"[DEBUG] Generated Regex: {regex_pattern}")

        # =====================================================
        # STEP 4: FETCH ALL CHUNKS FROM RELEVANT FILES
        # =====================================================
        all_docs = []

        for file_name in all_file_names:

            print(f"\n📂 Fetching file: {file_name}")

            docs = legal_compliance_vectorstore.get(
                where={"source": file_name},
                include=["documents"]
            )

            if docs and "documents" in docs:
                print(f"[DEBUG] Retrieved {len(docs['documents'])} chunks")
                all_docs.extend(docs["documents"])
            else:
                print(f"[WARNING] No docs found for {file_name}")

        chunks = all_docs

        # =====================================================
        # STEP 5: APPLY REGEX SEARCH
        # =====================================================
        print("\n🔍 Running regex-based search...")

        matches = []

        if regex_pattern:

            pattern = re.compile(regex_pattern, re.IGNORECASE)

            for i, chunk in enumerate(chunks):

                if pattern.search(chunk):

                    print(f"📄 Regex Match Found in Chunk {i}")

                    matches.append(chunk)

        print(f"\n✅ REGEX MATCHES FOUND: {len(matches)}")

        # =====================================================
        # STEP 6: MERGE RESULTS
        # =====================================================
        output_blocks = matches + output_blocks


    print(
        "✅ Returning SEMANTIC RESULTS "
    )



    return output_blocks