import os
import streamlit as st
from modelRag import RAGEngine
from mcp_client import MCPClient
from config import Config


# ── Page config ──────────────────────────
st.set_page_config(page_title="AI Knowledge Agent", layout="wide")

# ── Document selection (sidebar, always visible) ──
doc_dir = "./documents"
if not os.path.isdir(doc_dir):
    os.makedirs(doc_dir, exist_ok=True)
    files = []
else:
    files = os.listdir(doc_dir)

selected_file = st.sidebar.selectbox(
    "Select document",
    files if files else ["(no documents found)"],
    index=0,
)

# ── Skill selector (sidebar) ────────────
skill = st.sidebar.selectbox(
    "Select Skill (Tool)",
    ["answer_question", "search_documents", "summarize_document", "list_documents"],
    help="Choose which AI skill to invoke"
)

# ── Title ────────────────────────────────
title = "AI Knowledge Agent"
if selected_file and selected_file != "(no documents found)":
    title += f" — {selected_file}"
st.title(title)

# ── Initialize RAG & MCP clients ─────────
@st.cache_resource
def init_engine():
    return RAGEngine()

rag = init_engine()
client = MCPClient(Config.MCP_SERVER_URL)

# ── Message history ──────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# ── Chat input & processing ──────────────
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    response = ""
    docs = []

    # ── Route to the selected skill ──────
    # NOTE: mcp_client.MCPClient.call_tool raises RuntimeError when the
    # MCP server is unreachable or returns a non-JSON body. Catch that here
    # so the Streamlit app shows a helpful message instead of a raw stacktrace.
    try:
        if skill == "answer_question":
            result = client.call_tool("answer_question", {"query": prompt})
            response = result.get("answer", "")
            docs = result.get("sources", [])

        elif skill == "search_documents":
            result = client.call_tool("search_documents", {"query": prompt, "top_k": 5})
            docs = result if isinstance(result, list) else []
            response = f"Found {len(docs)} relevant document chunks."

        elif skill == "summarize_document":
            # Use the document selected in the sidebar
            doc_to_summarize = selected_file if selected_file and selected_file != "(no documents found)" else None

            if doc_to_summarize:
                with st.spinner(f"Summarising '{doc_to_summarize}'…"):
                    result = client.call_tool("summarize_document", {"filename": doc_to_summarize})
                    if isinstance(result, dict) and "error" in result:
                        response = result["error"]
                    elif isinstance(result, str):
                        response = result
                    else:
                        response = str(result) if result else "Summary unavailable."
            else:
                response = "No documents available to summarise."

        elif skill == "list_documents":
            result = client.call_tool("list_documents", {})
            if isinstance(result, list):
                doc_list = result
            elif isinstance(result, dict) and "documents" in result:
                doc_list = result["documents"]
            else:
                doc_list = ["No documents found"]
            response = f"Available documents: {doc_list}"
    except RuntimeError as e:
        response = f"⚠️ {e}"
        docs = []

    # ── Assistant response ───────────────
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

    # ── Sources expander ─────────────────
    if docs:
        with st.expander("Retrieved Sources"):
            st.write(docs)