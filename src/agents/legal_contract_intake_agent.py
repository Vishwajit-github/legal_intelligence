from langchain.agents import create_agent
from langchain_community.tools import tool

from config import model

from prompts import (
    CONTRACT_ANALYSIS_AGENT_PROMPT
)

from src.tools.legal_document_retrieval_tool import  contract_document_retrieval_tool

from src.tools.web_search_engine import (
    web_search_tool
)

from src.utils.agent_trace import trace_agent


@tool
def contract_analysis_agent(user_legal_query: str, document_path: str, action: str) -> str:
    """
    Contract Analysis Specialist.
    
    Use when performing contract review, structural analysis, ambiguity detection, missing clause identification, consistency checks, or assessing overall contract quality and unusual provisions.
    
    Inputs:
    - user_legal_query: User query about provided document, within maximum 2 lines, with supporting information.
    - document_path: path of the attached document
    - action: 4-word meaningful term or phrase describing what the agent is
      looking for in this iteration.
    
    Output
    - Final Answer to the User Query
    
    Tools:
    - process_input_documents: retrieve relevant contract sections
    - web_search_tool: reference contract standards and best practices when needed

    Do Not Use more than once for same instance

    """

    print("\nCalling Agent: Contract Analysis Agent")

    prompt = f"""
    
User Query:
{user_legal_query}

Document Path={document_path}

"""
    result = contract_analysis_specialist_.invoke(
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
    
    print("\nFinished Agent: Contract Analysis Agent")
    trace_agent(
        "Contract Analysis Agent",
        prompt,
        final_output,
        action=action
    )

    return {
        "agent": "Contract Analysis Agent",
        "action": action,
        "input": prompt,
        "output": final_output
    }


# --------------------------------------------------
# SPECIALIST AGENT
# --------------------------------------------------

contract_analysis_specialist_ = create_agent(
    model=model,
    tools=[
        contract_document_retrieval_tool,
        web_search_tool
    ],
    system_prompt=CONTRACT_ANALYSIS_AGENT_PROMPT,
)