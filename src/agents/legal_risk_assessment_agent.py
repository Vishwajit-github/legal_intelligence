from langchain.agents import create_agent
from langchain_community.tools import tool

from config import model

from prompts import (
    LEGAL_RISK_ASSESSMENT_AGENT_PROMPT
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
def legal_risk_assessment_agent(
    legal_input: str,
    action: str,
    user_query: str = "",
    input_type: str = ""
) -> str:
    """
    Legal Risk Assessment Specialist.
    
    Purpose:
    Identify, evaluate, and prioritize legal,
    contractual, regulatory, operational, and
    financial risks based on provided legal
    documents, clauses, facts, or scenarios.
    
    Use when:
    - legal risk assessment
    - contract risk review
    - liability analysis
    - indemnity risk analysis
    - contractual exposure assessment
    - compliance exposure review
    - regulatory risk identification
    - operational risk assessment
    - financial exposure assessment
    - legal gap analysis
    - risk prioritization
    
    Inputs:
    - legal_input:
      Contract, agreement, legal document,
      clause, dispute facts, or business scenario.
    
    - action:
      4-word meaningful term or phrase describing what the agent is
      looking for in this iteration.
    
    - user_query:
      Risk-related question, assessment request,
      exposure analysis, or mitigation request.
    
    - input_type:
      Optional document type hint.
    
    Tools Available:
    - process_input_document_clause:
      Extract specific clauses for detailed risk review.
    
    - process_input_documents:
      Retrieve relevant sections from uploaded
      legal documents.
    
    - legal_research_retrieval_tool:
      Return a final answer based on UAE laws,
      regulations, statutes, and legal authorities
      from internal legal and regulatory documents.
    
    - web_search_tool:
      Retrieve external legal, regulatory,
      compliance, or jurisdiction-specific
      information when necessary.
    
    Returns:
    - Identified risks
    - Risk severity assessment
    - Exposure analysis
    - Potential legal implications
    - Risk prioritization
    - Mitigation recommendations
    - Key assumptions and limitations
    
    Do NOT use for:
    - contract drafting
    - clause extraction only
    - legal document summarization
    - pure legal research without risk analysis
    - litigation strategy development
    """
    print("\nCalling Agent: Legal Risk Assessment Agent")

    prompt = f"""
Legal Input:
{legal_input}

Input Type:
{input_type or "auto-detect"}

User Query:
{user_query}
"""


    result = legal_risk_assessment_specialist_.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    )

    print("\nFinished Agent: Legal Risk Assessment Agent")

    final_output = result["messages"][-1].content

    trace_agent(
        "Legal Risk Assessment Agent",
        prompt,
        final_output,
        action=action
    )

    return {
        "agent": "Legal Risk Assessment Agent",
        "action": action,
        "input": prompt,
        "output": final_output
    }


legal_risk_assessment_specialist_ = create_agent(
    model=model,
    tools=[
        legal_clause_extraction_tool,
        contract_document_retrieval_tool,
        legal_research_retrieval_tool,
        web_search_tool
    ],
    system_prompt=LEGAL_RISK_ASSESSMENT_AGENT_PROMPT,
)