from fastapi import FastAPI, Body
from modelRag import RAGEngine
import os
import uvicorn
from config import Config
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI()
rag = RAGEngine()

# ──────────────────────────────────────────
# SKILL 1: search_documents (existing)
# ──────────────────────────────────────────
@app.post("/tools/search_documents")
def search_documents(data: Dict[str, Any] = Body(...)):
    """Hybrid search across documents."""
    query = data.get("query", "")
    top_k = data.get("top_k", 5)
    return rag.hybrid_search(query, top_k)

# ──────────────────────────────────────────
# SKILL 2: answer_question (RAG-based Q&A)
# ──────────────────────────────────────────
@app.post("/tools/answer_question")
def answer_question(data: Dict[str, Any] = Body(...)):
    """Answer a question using retrieved documents as context."""
    query = data.get("query", "")
    docs = rag.hybrid_search(query, top_k=3)
    try:
        answer = rag.generate_response(query, docs)
    except ValueError as e:
        return {"answer": str(e), "sources": []}
    except Exception as e:
        return {"answer": f"Error generating response: {str(e)}", "sources": []}
    return {"answer": answer, "sources": docs}

# ──────────────────────────────────────────
# SKILL 3: summarize_document
# ──────────────────────────────────────────
@app.post("/tools/summarize_document")
def summarize_document(data: Dict[str, Any] = Body(...)):
    """Summarize the content of a document by filename."""
    filename = data.get("filename", "")
    return rag.summarize_document(filename)

# ──────────────────────────────────────────
# SKILL 4: list_documents
# ──────────────────────────────────────────
@app.post("/tools/list_documents")
def list_documents(data: Dict[str, Any] = Body(default={})):
    """List all available indexed documents."""
    return rag.list_documents()

if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)