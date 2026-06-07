# run.py (enhanced version)

import uvicorn
from scripts.legal_complaince_vectordb import ensure_vector_db

if __name__ == "__main__":
    ensure_vector_db()

    print("\n" + "=" * 60)
    print("   Healthcare Multi-Agent System Starting")
    print("   Port: 8000")
    print("=" * 60 + "\n")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )