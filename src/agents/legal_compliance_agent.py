from langchain.agents import create_agent
from langchain_community.tools import tool

from config import model

from prompts import (
    LEGAL_COMPLIANCE_AGENT_PROMPT
)

from src.tools.legal_clause_extraction_tool import legal_clause_extraction_tool
from src.tools.legal_document_retrieval_tool import  contract_document_retrieval_tool
from src.tools.legal_research_tool import legal_research_retrieval_tool
from src.tools.web_search_engine import web_search_tool
from src.utils.agent_trace import trace_agent

@tool
def legal_compliance_agent(
    legal_input: str,
    action: str,
    user_query: str = "",
    input_type: str = ""
) -> str:
    """

    Legal Compliance Specialist.
    
    Use when:
    - compliance reviews
    - regulatory assessments
    - UAE law compliance checks
    - labor law compliance
    - contract compliance analysis
    - policy compliance reviews
    - regulatory gap analysis
    - identifying missing legal obligations
    - comparing documents against legal requirements
    
    Inputs:
    - legal_input: contract, agreement, policy,
      legal document, regulatory document, or extracted text
    - action: 4-word meaningful term or phrase describing what the agent is
      looking for in this iteration.
    - user_query: compliance-related question
    - input_type: optional document type hint
    
    Outputs:
    - compliance findings
    - applicable regulations
    - compliance gaps
    - missing obligations
    - weak or missing provisions
    - regulatory observations
    - compliance recommendations
    
    Available Tools:
    - process_input_documents:
      Retrieve relevant sections from uploaded
      contracts, agreements, policies, and legal documents.
    
    - legal_research_retrieval_tool:
      Specilized to answer queries around UAE laws,
      regulations, legal articles, labor laws, criminal laws,
      constitutional provisions, and compliance obligations
      from internal legal and regulatory documents.
    
    - web_search_tool:
      Research external regulations, recent legal updates,
      regulatory guidance, and jurisdiction-specific
      compliance requirements not available in the internal
      legal knowledge base.
    
    Do NOT use when:
    - extracting clauses from documents
    - drafting contracts or legal documents
    - summarizing legal documents
    - researching laws without compliance analysis
    - performing litigation strategy analysis
    - performing legal risk assessment

    Keep the response concise and focused on actionable compliance findings.
    Maximum response length: 300 words unless the user explicitly requests detailed analysis.

    
    """

    print("\nCalling Agent: Legal Compliance Agent")

    prompt = f"""
Legal Input:
{legal_input}

Input Type:
{input_type or "auto-detect"}

User Query:
{user_query}
"""

    result = legal_compliance_specialist.invoke(
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

    print("\nFinished Agent: Legal Compliance Agent")
    
    trace_agent(
        "Legal Compliance Agent",
        prompt,
        final_output,
        action=action
    )

    return {
        "agent": "Legal Compliance Agent",
        "action": action,
        "input": prompt,
        "output": final_output
    }


legal_compliance_specialist = create_agent(
    model=model,
    tools=[
        contract_document_retrieval_tool,
        legal_research_retrieval_tool,
        legal_clause_extraction_tool,
    ],
    system_prompt=LEGAL_COMPLIANCE_AGENT_PROMPT,
)

