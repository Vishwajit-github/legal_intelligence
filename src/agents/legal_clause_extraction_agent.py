from langchain.agents import create_agent
from langchain_community.tools import tool

from config import model

from prompts import (
    LEGAL_CLAUSE_EXTRACTION_AGENT_PROMPT
)

from src.tools.legal_clause_extraction_tool import (
    legal_clause_extraction_tool
)


from src.tools.legal_research_tool import (
    legal_research_retrieval_tool
)

from src.tools.legal_clause_extraction_tool import legal_clause_extraction_tool

from src.utils.agent_trace import trace_agent


@tool
def legal_clause_extraction_agent(
    legal_input: str,
    action: str,
    user_query: str = "",
    input_type: str = ""
) -> str:
    """
    Legal Clause Extraction Specialist
    
    Purpose:
    Extract and identify legal clauses from contracts and legal documents.
    
    Use When:
    - Extracting clauses or provisions from documents
    - Finding specific contract language or sections
    - Identifying clause types (e.g., termination, indemnity, confidentiality)
    - Locating obligations, restrictions, or rights
    - Reviewing structure of legal agreements
    
    Supported Documents:
    - Contracts, agreements, policies, terms & conditions
    - Employment agreements, NDAs, vendor/service agreements
    - Other structured legal documents
    
    Inputs:
    - legal_input: document or extracted text
    - action: 4-word meaningful term or phrase describing what the agent is
      looking for in this iteration.
    - user_query: clause search or identification request
    - input_type (optional): contract type hint
    
    Output:
    - Extracted clauses
    - Clause headings and locations
    - Clause classification (e.g., termination, payment, IP)
    - Exact clause text excerpts
    
    Do NOT Use When:
    - Legal research or statutory interpretation is required
    - Compliance or risk analysis is needed
    - Litigation strategy or legal advice is required
    - Contract drafting or rewriting is required
    - General legal questions without a document
    
    Primary Tool:
    - process_input_document_clause
    
    Notes:
    - Preserve exact legal wording
    - Prefer extraction over summarization
    - Focus only on locating and classifying clauses
    
    """

    print("\nCalling Agent: Legal Clause Extraction Agent")

    prompt = f"""
Legal Input:
{legal_input}

Input Type:
{input_type or "auto-detect"}

User Query:
{user_query}
"""

    result = legal_clause_extraction_specialist_.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    )
    
    final_output = result["messages"][-1].content

    print("\nFinished Agent: Legal Clause Extraction Agent")

    trace_agent(
        "Legal Clause Extraction Agent",
        prompt,
        final_output,
        action=action
    )

    print("\nFinished Agent: Legal Clause Extraction Agent")
    
    return {
        "agent": "Legal Clause Extraction Agent",
        "action": action,
        "input": prompt,
        "output": final_output
    }


# --------------------------------------------------
# SPECIALIST AGENT
# --------------------------------------------------


legal_clause_extraction_specialist_ = create_agent(
    model=model,
    tools=[
        legal_research_retrieval_tool, legal_clause_extraction_tool
    ],
    system_prompt=LEGAL_CLAUSE_EXTRACTION_AGENT_PROMPT,
)
