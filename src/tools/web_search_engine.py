from langchain_community.tools import tool
from config import embeddings, llm, model
@tool
def web_search_tool(query: str) -> str:
    """
    Search the web for legal, regulatory,
    compliance, or current information.
    """

    prompt = f"""
Perform a web search for the following query.

Query:
{query}

Requirements:
- Search the web.
- Use authoritative sources.
- Summarize findings.
- Include important legal or regulatory details.
- Mention sources when available.
"""

    result = model.invoke(prompt)

    return result.content