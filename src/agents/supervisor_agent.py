from langchain.agents import create_agent
from langchain_community.tools import tool

from config import model

from prompts import (
    SUPERVISOR_PROMPT
)

from src.utils.agent_trace import trace_agent


# --------------------------------------------------
# SPECIALIST AGENTS
# --------------------------------------------------

from src.agents.legal_research_agent import (
    legal_research_agent
)

from src.agents.legal_clause_extraction_agent import (
    legal_clause_extraction_agent
)

from src.agents.legal_contract_intake_agent import (
    contract_analysis_agent
)

from src.agents.legal_compliance_agent import (
    legal_compliance_agent
)

from src.agents.litigation_strategy_agent import (
    litigation_strategy_agent
)

from src.agents.legal_summarization_agent import (
    legal_summarization_agent
)

from src.agents.legal_document_drafting_agent import (
    document_drafting_agent
)

from src.agents.legal_risk_assessment_agent import (
    legal_risk_assessment_agent
)

supervisor_agent = create_agent(
    model=model,
    tools=[
        legal_research_agent,
        legal_clause_extraction_agent,
        contract_analysis_agent,
        legal_compliance_agent,
        litigation_strategy_agent,
        legal_summarization_agent,
        document_drafting_agent,
        legal_risk_assessment_agent,
    ],
    system_prompt=SUPERVISOR_PROMPT,
)