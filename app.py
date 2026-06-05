from contextlib import asynccontextmanager
from typing import Any, Dict, Optional
import uuid
import traceback
from pathlib import Path
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from graph.builder import graph
from src.utils.logger import get_chat_history

# =========================================================
# UPLOAD DIRECTORY
# =========================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# =========================================================
# RESPONSE SCHEMA
# =========================================================

class LegalResponse(BaseModel):
    request_id: str
    run_id: str
    status: str
    final_response: str
    validator: Optional[Dict[str, Any]] = None
    task_outputs: Optional[Any] = None


# =========================================================
# APP LIFECYCLE
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("\n" + "=" * 70)
    print("Starting Legal Intelligence AI API")
    print("=" * 70 + "\n")

    yield

    print("\n" + "=" * 70)
    print("Stopping Legal Intelligence AI API")
    print("=" * 70 + "\n")


app = FastAPI(
    title="Legal Intelligence AI API",
    description="Production-grade Legal Intelligence System using LangGraph + LangChain",
    version="1.0.0",
    lifespan=lifespan,
)

# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
async def root():
    return {
        "message": "Legal Intelligence AI API Running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


# =========================================================
# FILE TYPE DETECTION
# =========================================================

def get_file_type(file_path: str, mime_type: str = None):

    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return "pdf"

    if ext in [".doc", ".docx"]:
        return "word"

    if ext == ".txt":
        return "text"

    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        return "image"

    return "unknown"


# =========================================================
# LEGAL ANALYSIS ENDPOINT
# =========================================================

@app.post("/run", response_model=LegalResponse)
async def analyze_legal_query(
    user_query: str = Form(...),
    run_id: Optional[str] = Form(None),
    file: UploadFile = File(None),
):

    request_id = str(uuid.uuid4())
    run_id = run_id or str(uuid.uuid4())

    try:

        # =====================================================
        # SAVE FILE
        # =====================================================

        file_path = None
        file_mime_type = None

        if file:

            file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_path = str(file_path)
            file_mime_type = file.content_type

            print("\n📁 FILE SAVED:", file_path)

        # =====================================================
        # CHAT HISTORY
        # =====================================================

        history = get_chat_history(
            run_id=run_id,
            limit=6
        )

        # =====================================================
        # USER MESSAGE
        # =====================================================

        user_content = user_query

        if file_path:

            user_content += f"""

Legal document uploaded.

File path: {file_path}
File type: {get_file_type(file_path, file_mime_type)}

Legal Query: {user_query}
"""

        messages = history + [
            {
                "role": "user",
                "content": user_content,
            }
        ]

        # =====================================================
        # GRAPH STATE
        # =====================================================

        initial_state = {

            # SESSION
            "run_id": run_id,

            # USER INPUT
            "user_query": user_query,
            "messages": messages,

            # DOCUMENT INPUT
            "uploaded_file_path": file_path,
            "uploaded_file_type": (
                get_file_type(
                    file_path,
                    file_mime_type
                )
                if file_path
                else None
            ),
            "uploaded_file_mime_type": file_mime_type,

            # SUPERVISOR
            "supervisor_output": None,

            # VALIDATION
            "validation_result": None,
            "validation_risk_level": None,
            "is_valid": False,
            "iteration": 0,

            # AGENT OUTPUTS
            "used_agents": [],
            "agent_outputs": {},

            # FINAL OUTPUT
            "final_response": None,

            # CHAT HISTORY
            "chat_history": history,
        }

        # =====================================================
        # RUN GRAPH
        # =====================================================

        result = await graph.ainvoke(initial_state)

        # =====================================================
        # RESPONSE
        # =====================================================

        return LegalResponse(
            request_id=request_id,
            run_id=run_id,
            status="success",
            final_response=result.get(
                "final_response",
                "No response generated."
            ),
            validator=result.get(
                "validation_result"
            ),
            task_outputs=result.get(
                "agent_outputs"
            ),
        )

    except Exception as exc:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail={
                "request_id": request_id,
                "run_id": run_id,
                "status": "error",
                "message": str(exc),
            },
        )


# =========================================================
# DEBUG ENDPOINT
# =========================================================

@app.post("/legal/debug")
async def debug_workflow(
    user_query: str = Form(...),
    run_id: Optional[str] = Form(None),
):

    request_id = str(uuid.uuid4())
    run_id = run_id or str(uuid.uuid4())

    try:

        history = get_chat_history(
            run_id=run_id,
            limit=6
        )

        messages = history + [
            {
                "role": "user",
                "content": user_query
            }
        ]

        initial_state = {

            "run_id": run_id,
            "user_query": user_query,
            "messages": messages,

            "uploaded_file_path": None,
            "uploaded_file_type": None,
            "uploaded_file_mime_type": None,

            "supervisor_output": None,

            "validation_result": None,
            "validation_risk_level": None,
            "is_valid": False,
            "iteration": 0,

            "final_response": None,
            "used_agents": [],
            "agent_outputs": {},

            "chat_history": history,
        }

        result = await graph.ainvoke(initial_state)

        return {
            "request_id": request_id,
            "run_id": run_id,
            "status": "success",
            "graph_output": result,
        }

    except Exception as exc:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# =========================================================
# CHAT HISTORY
# =========================================================

@app.get("/history/{run_id}")
async def fetch_chat_history(run_id: str):

    try:

        history = get_chat_history(
            run_id=run_id,
            limit=50
        )

        return {
            "run_id": run_id,
            "history": history,
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )