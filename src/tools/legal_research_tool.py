import os
import re
import time
from pathlib import Path

from langchain_community.tools import tool
from langchain_community.vectorstores import Chroma
from config import embeddings, llm

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


# -----------------------------
# MAIN TOOL
# -----------------------------
@tool
def legal_research_retrieval_tool(query: str) -> str:
    """
    Input:
    User question with supporting details, within maximum 2 lines, with supporting information.

    Output: Context associated to User Question

    MULTI-CALL RESTRICTION:
    - If the agent considers calling this tool again,
      it MUST first verify that the new query is:
        (a) unrelated legal domain OR
        (b) missing entirely from previous retrieval

    
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

    for i, (doc, score) in enumerate(results):
        meta = doc.metadata or {}

        file_name = (
            meta.get("source_file")
            or os.path.basename(meta.get("source", meta.get("file_path", "unknown")))
        )
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

    retrieved_context = "\n\n".join(output_blocks)


    print(
        "✅ Returning LLM ANSWER FROM SEMANTIC RESULTS "
    )



    return retrieved_context