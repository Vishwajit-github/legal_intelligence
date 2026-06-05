from langchain.agents import create_agent
from langchain_community.tools import tool

from config import model

from prompts import (
    DOCUMENT_DRAFTING_AGENT_PROMPT
)

from src.tools.web_search_engine import web_search_tool

from src.utils.agent_trace import trace_agent


@tool
def document_drafting_agent(
    legal_input: str,
    action: str,
    user_query: str = "",
    input_type: str = ""
) -> str:
    """
    Legal Document Drafting Specialist.
    
    Purpose:
    Draft legal documents, clauses, templates, amendments,
    memorandums, and agreement language based on user
    requirements and applicable legal context.
    
    Use when:
    - NDA drafting
    - contract drafting
    - agreement creation
    - legal memo drafting
    - amendment drafting
    - vendor agreements
    - SaaS agreements
    - employment clauses
    - confidentiality clauses
    - custom legal templates
    - clause rewriting or improvement
    
    Inputs:
    - legal_input:
      Existing contract, clause, requirements,
      business context, or drafting instructions.
    
    - action:
      4-word meaningful term or phrase describing what the agent is
      looking for in this iteration.
    
    - user_query:
      Drafting request, modifications, jurisdiction,
      parties, obligations, or document requirements.
    
    - input_type:
      Optional document type hint.
    
    Tools Available:
    - web_search_tool:
      Retrieve drafting guidance, legal references,
      public templates, or jurisdiction-specific
      drafting considerations when needed.
    
    Returns:
    - Drafted legal language
    - Structured legal document sections
    - Draft clauses
    - Assumptions and missing information when applicable
    
    Do NOT use for:
    - compliance audits
    - legal research
    - clause extraction
    - litigation analysis
    - legal risk assessment
    """

    print("\nCalling Agent: Document Drafting Agent")

    prompt = f"""
Legal Input:
{legal_input}

Input Type:
{input_type or "auto-detect"}

User Query:
{user_query}
"""

    result = document_drafting_specialist_.invoke(
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

    print("\nFinished Agent: Document Drafting Agent")

    trace_agent(
        "Document Drafting Agent",
        prompt,
        final_output,
        action=action
    )

    return {
        "agent": "Document Drafting Agent",
        "action": action,
        "input": prompt,
        "output": final_output
    }


# --------------------------------------------------
# SPECIALIST AGENT
# --------------------------------------------------

document_drafting_specialist_ = create_agent(
    model=model,
    tools=[
        web_search_tool
    ],
    system_prompt=DOCUMENT_DRAFTING_AGENT_PROMPT,
)