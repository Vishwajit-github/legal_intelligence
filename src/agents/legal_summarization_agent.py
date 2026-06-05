from langchain.agents import create_agent
from langchain_community.tools import tool

from config import model, concise_response_llm

from prompts import (
    LEGAL_SUMMARIZATION_AGENT_PROMPT
)


from src.tools.contract_summarizer_tool import summarize_contract_document

from src.tools.web_search_engine import (
    web_search_tool
)

from src.utils.agent_trace import trace_agent


@tool
def legal_summarization_agent(
    legal_input: str,
    action: str,
    user_query: str = "",
    input_type: str = ""
) -> str:
    """
    Legal Summarization Specialist.

    Use when:
    - summarizing contracts
    - summarizing legal agreements
    - simplifying legal language
    - executive summaries
    - client-friendly legal explanations
    - obligation summaries
    - clause summaries
    - policy summaries
    - law summaries
    - document overviews

    Inputs:
    - legal_input: uploaded legal document, contract, policy,
      agreement, legal text, or extracted content
    - action: 4-word meaningful term or phrase describing what the agent is
      looking for in this iteration.
    - user_query: specific summary request
    - input_type: optional hint such as contract, agreement,
      policy, law, legal_memo, nda, employment_contract

    Output:
    - concise or detailed legal summary
    - key obligations
    - major restrictions
    - important provisions
    - audience-appropriate explanation

    Output Format
    - Due to less token limit, you need to create bullet point based output
    - It should be created in order to achieve less token usage AND without information loss
    - So Structure needs to be more like point-based AND at the end ask Supervisor to summarise it in presentable ways.

    """

    print("\nCalling Agent: Legal Summarization Agent")

    prompt = f"""
Legal Input:
{legal_input}

Input Type:
{input_type or "auto-detect"}

User Query:
{user_query}
"""

    result = legal_summarization_specialist.invoke(
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
    
    print("\nFinished Agent: Legal Summarization Agent")
    trace_agent(
        "Legal Summarization Agent",
        prompt,
        final_output,
        action=action
    )

    return {
        "agent": "Legal Summarization Agent",
        "action": action,
        "input": prompt,
        "output": final_output
    }


legal_summarization_specialist = create_agent(
    model=model,
    tools=[
        summarize_contract_document
    ],
    system_prompt=LEGAL_SUMMARIZATION_AGENT_PROMPT,
)