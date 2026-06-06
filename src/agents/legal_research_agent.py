import time
from langchain.agents import create_agent

from langchain_community.tools import tool

from src.tools.legal_research_tool import (
    legal_research_retrieval_tool
)
from config import model

from prompts import (
    LEGAL_RESEARCH_AGENT_PROMPT
)
from src.utils.agent_trace import trace_agent


legal_research_specialist_ = create_agent(
    model=model,
    tools=[
        legal_research_retrieval_tool
    ],
    system_prompt=LEGAL_RESEARCH_AGENT_PROMPT,
)

@tool
def legal_research_agent(user_legal_query: str, action: str) -> str:
    """
    Legal Research Specialist.

    Use when the user needs legal research,
    legal authority lookup, statutory interpretation,
    regulatory analysis, legal citations,
    or legal framework explanations.

    Typical use cases:
    - Research UAE laws and regulations
    - Find relevant statutes and legal provisions
    - Explain articles, sections, clauses, or legal concepts
    - Identify legal obligations under specific laws
    - Research labor laws, criminal laws, civil laws,
      commercial laws, and regulatory frameworks

    Inputs:
    - user_legal_query:
      User legal research question, within maximum 2 lines, with supporting information.
    - action:
      4-word meaningful term or phrase describing what the agent is
      looking for in this iteration.

    Output
    - Retrived Legal Document content specific to User query.

    This agent does NOT:
    - extract contract clauses
    - analyze contract structure
    - perform litigation strategy
    - draft legal documents
    - perform legal risk scoring
    - certify legal compliance

    Do Not Use more than once for same instance

    """

    start_time = time.time()
    print("\nCalling Agent: Legal Research Agent")

    prompt = f"""
User Query:
{user_legal_query}

 
"""

    result = legal_research_specialist_.invoke(
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
    
    print("\nFinished Agent: Legal Research Agent")
    
    trace_agent(
        "Legal Research Agent",
        prompt,
        final_output,
        evidence={
            "latency_sec": round(time.time() - start_time, 4),
            "mode": "direct_retrieval",
        },
        action=action,
    )

    return {
        "agent": "Legal Research Agent",
        "action": action,
        "input": prompt,
        "output": final_output
    }


