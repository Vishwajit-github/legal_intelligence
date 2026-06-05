import time
from src.utils.logger import log_event


# -----------------------------------
# SAFE IMPORT WRAPPER
# -----------------------------------
def safe_import(path, name):
    try:
        module = __import__(path, fromlist=[name])
        return getattr(module, name)
    except Exception as e:
        print(f"[AGENT LOAD ERROR] {name}: {e}")
        return None


# -----------------------------------
# IMPORT LEGAL AGENTS
# -----------------------------------

legal_research_agent_ = safe_import(
    "agents.legal_research_agent",
    "legal_research_agent"
)

legal_clause_extraction_agent_ = safe_import(
    "agents.legal_clause_extraction_agent",
    "legal_clause_extraction_agent"
)

contract_analysis_agent_ = safe_import(
    "agents.contract_analysis_agent",
    "contract_analysis_agent"
)

legal_compliance_agent_ = safe_import(
    "agents.legal_compliance_agent",
    "legal_compliance_agent"
)

litigation_strategy_agent_ = safe_import(
    "agents.litigation_strategy_agent",
    "litigation_strategy_agent"
)

legal_summarization_agent_ = safe_import(
    "agents.legal_summarization_agent",
    "legal_summarization_agent"
)

document_drafting_agent_ = safe_import(
    "agents.document_drafting_agent",
    "document_drafting_agent"
)

legal_risk_assessment_agent_ = safe_import(
    "agents.legal_risk_assessment_agent",
    "legal_risk_assessment_agent"
)


# -----------------------------------
# AGENT WRAPPER
# -----------------------------------
def trace_agent_call(
    run_id,
    agent_name,
    agent_fn,
    input_payload
):

    start_time = time.time()

    log_event(
        run_id,
        "agent_call_start",
        {
            "agent": agent_name,
            "input": str(input_payload)
        }
    )

    try:

        if agent_fn is None:
            raise ValueError(
                f"Agent not found: {agent_name}"
            )

        result = agent_fn.invoke(
            input_payload
        )

        output = (
            result.content
            if hasattr(result, "content")
            else str(result)
        )

        latency = round(
            time.time() - start_time,
            4
        )

        log_event(
            run_id,
            "agent_call_end",
            {
                "agent": agent_name,
                "output": output,
                "latency_sec": latency,
                "status": "success"
            }
        )

        return result

    except Exception as e:

        latency = round(
            time.time() - start_time,
            4
        )

        log_event(
            run_id,
            "agent_call_error",
            {
                "agent": agent_name,
                "error": str(e),
                "latency_sec": latency,
                "status": "error"
            }
        )

        return None


# -----------------------------------
# WRAPPED ACCESSOR
# -----------------------------------
def get_agent(
    agent_name,
    run_id=None
):

    agent = AGENT_REGISTRY.get(
        agent_name
    )

    if agent is None:
        return None

    def wrapped(input_payload):

        return trace_agent_call(
            run_id=run_id,
            agent_name=agent_name,
            agent_fn=agent,
            input_payload=input_payload
        )

    return wrapped


# -----------------------------------
# LEGAL AGENT REGISTRY
# -----------------------------------
AGENT_REGISTRY = {

    "legal_research_agent":
        legal_research_agent_,

    "legal_clause_extraction_agent":
        legal_clause_extraction_agent_,

    "contract_analysis_agent":
        contract_analysis_agent_,

    "legal_compliance_agent":
        legal_compliance_agent_,

    "litigation_strategy_agent":
        litigation_strategy_agent_,

    "legal_summarization_agent":
        legal_summarization_agent_,

    "document_drafting_agent":
        document_drafting_agent_,

    "legal_risk_assessment_agent":
        legal_risk_assessment_agent_,
}