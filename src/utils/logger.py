import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock


# =========================================================
# FILE SETUP
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "legal_agent_trace.jsonl"


def ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# LOGGER SETUP
# =========================================================

logger = logging.getLogger("legal_ai")

if logger.hasHandlers():
    logger.handlers.clear()

logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
logger.addHandler(handler)
logger.propagate = False


# =========================================================
# THREAD SAFE
# =========================================================

lock = Lock()


# =========================================================
# SAFE SERIALIZER (NO INFO LOSS)
# =========================================================

def sanitize(obj):

    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [sanitize(v) for v in obj]

    return {
        "__type__": type(obj).__name__,
        "__repr__": repr(obj),
    }


# =========================================================
# CORE LOGGER
# =========================================================

AGENT_DISPLAY_NAMES = {
    "supervisor_node": "Supervisor",
    "validator_node": "Validator",
    "router": "Router",
    "tool": "Tool",
    "LegalClauseExtractionAgent": "Legal Clause Extraction Agent",
    "LegalSummarizationAgent": "Legal Summarization Agent",
    "ContractAnalysisAgent": "Contract Analysis Agent",
    "LitigationStrategyAgent": "Litigation Strategy Agent",
    "LegalRiskAssessmentAgent": "Legal Risk Assessment Agent",
    "LegalComplianceAgent": "Legal Compliance Agent",
    "LegalResearchAgent": "Legal Research Agent",
    "DocumentDraftingAgent": "Document Drafting Agent",
}


def log_event(
    run_id,
    event,
    data=None,
    level="INFO",
    step=None,
    agent=None,
    node=None,
):

    resolved_agent = agent or node

    if resolved_agent is None and isinstance(data, dict):
        resolved_agent = data.get("agent")

    resolved_agent = resolved_agent or "unknown"
    resolved_agent = AGENT_DISPLAY_NAMES.get(resolved_agent, resolved_agent)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "run_id": run_id,
        "agent": resolved_agent,
        "event": event,
        "payload": sanitize(data),
    }

    line = json.dumps(record, ensure_ascii=False)

    with lock:
        ensure_log_dir()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    print(line)


# =========================================================
# CHAT HISTORY
# =========================================================

CHAT_FILE = LOG_DIR / "chat_history.jsonl"


def append_chat_history(run_id, user_message, ai_message):

    record = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        "user": user_message,
        "assistant": ai_message,
    }

    line = json.dumps(record, ensure_ascii=False)

    with lock:
        ensure_log_dir()
        with open(CHAT_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def get_chat_history(run_id, limit=3):

    ensure_log_dir()

    if not CHAT_FILE.exists():
        return []

    messages = []

    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    filtered = []

    for line in lines:
        try:
            item = json.loads(line)
        except Exception:
            continue

        if item.get("run_id") == run_id:
            filtered.append(item)

    filtered = filtered[-limit:]

    for item in filtered:
        messages.append({
            "role": "user",
            "content": item.get("user", ""),
        })
        messages.append({
            "role": "assistant",
            "content": item.get("assistant", ""),
        })

    return messages


# =========================================================
# EXCEPTION LOGGER
# =========================================================

def log_exception(run_id, node, exc):

    log_event(
        run_id=run_id,
        node=node,
        event="exception",
        level="ERROR",
        data={
            "error": str(exc),
            "type": type(exc).__name__,
        }
    )