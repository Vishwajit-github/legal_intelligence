from langchain.agents import create_agent
from langchain_community.tools import tool

from config import model

from prompts import (
    LITIGATION_STRATEGY_AGENT_PROMPT
)

from src.tools.legal_clause_extraction_tool import (
    legal_clause_extraction_tool
)

from src.tools.legal_document_retrieval_tool import  contract_document_retrieval_tool

from src.tools.legal_research_tool import (
    legal_research_retrieval_tool
)

from src.tools.web_search_engine import (
    web_search_tool
)

from src.utils.agent_trace import trace_agent


@tool
def litigation_strategy_agent(
    user_query: str,
    action: str,
) -> str:
    """
    Litigation Strategy Specialist.
    
    Purpose:
    Analyze disputes, claims, legal positions,
    evidence, timelines, and arguments to identify
    strengths, weaknesses, risks, and strategic
    considerations for potential litigation or
    formal legal proceedings.
    
    Use when:
    - dispute analysis
    - breach analysis
    - litigation preparation
    - evidentiary review
    - legal argument assessment
    - counterargument analysis
    - timeline reconstruction
    - claim evaluation
    - defense strategy review
    - contract dispute review
    - notice and demand analysis
    - legal position assessment
    
    Inputs:
    - legal_input:
      Contract, agreement, legal filing,
      dispute facts, correspondence,
      evidence, notices, or legal text.
    
    - user_query:
      Litigation-related question,
      dispute assessment, claim review,
      or strategy request.

    - action:
      4-word meaningful term or phrase describing what the agent is
      looking for in this iteration.
    
    - input_type:
      Optional hint such as contract,
      dispute, claim, lawsuit, notice,
      evidence, or correspondence.
    
    Tools Available:
    - process_input_document_clause: (When User provides input Document)
      Extract relevant clauses affecting
      rights, obligations, remedies,
      termination, liability, or dispute resolution.
    
    - process_input_documents: (When User provides input Document)
      Retrieve relevant sections from
      uploaded legal documents.
    
    - legal_research_retrieval_tool: (When it is necessary to look into UAE legal book)
      Return a final answer based on applicable UAE laws,
      legal provisions, and regulatory authorities.
    
    Returns:
    - dispute analysis
    - key legal issues
    - argument strengths
    - argument weaknesses
    - evidentiary assessment
    - potential counterarguments
    - timeline reconstruction
    - factual gaps
    - strategic considerations
    - assumptions and limitations
    
    Do NOT use for:
    - contract drafting
    - clause extraction only
    - legal compliance reviews
    - legal document summarization
    - pure legal research without dispute analysis
 
    """

    print("\nCalling Agent: Litigation Strategy Agent")

    prompt = f"""
User Query:
{user_query}
"""

    result = litigation_strategy_specialist.invoke(
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

    print("\nFinished Agent: Litigation Strategy Agent")
    
    trace_agent(
        "Litigation Strategy Agent",
        prompt,
        final_output,
        action=action
    )

    return {
        "agent": "Litigation Strategy Agent",
        "action": action,
        "input": prompt,
        "output": final_output
    }


litigation_strategy_specialist = create_agent(
    model=model,
    tools=[
        legal_clause_extraction_tool,
        contract_document_retrieval_tool,
        legal_research_retrieval_tool
    
    ],
    system_prompt=LITIGATION_STRATEGY_AGENT_PROMPT,
)