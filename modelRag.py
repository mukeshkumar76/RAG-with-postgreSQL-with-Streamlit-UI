import os
from sqlalchemy import create_engine, text
# Optional: Remove sentence_transformers if you want Ollama to do the embedding work, 
# or keep it if you want to run sentence_transformers locally on CPU/GPU.
from sentence_transformers import SentenceTransformer
from config import Config
import ollama  # Import the official ollama package

def before_llm(user_query):
    print("User asked:", user_query)
    if len(user_query) < 3:
        raise ValueError("Question too short")

class RAGEngine:
    DOCUMENTS_DIR = "./documents"
    
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        
        # FIX 1: If using SentenceTransformer, keep the Hugging Face path 
        # (e.g., 'sentence-transformers/all-MiniLM-L6-v2'). 
        # If you changed Config.EMBEDDING_MODEL to 'all-minilm' for Ollama, 
        # use: self.ollama_emb_model = Config.EMBEDDING_MODEL
        # self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.ollama_emb_model = Config.EMBEDDING_MODEL

        # FIX 2: Initialize the Ollama Client correctly using your config URL
        self.client = ollama.Client(host=Config.OLLAMA_BASE_URL)
        
    def hybrid_search(self, query: str, top_k: int = 5):
        # FIX 3: Fixed 'model.encode' to 'self.model.encode'
        embedding = self.model.encode(query).tolist()
        
        # Alternatively, if you want OLLAMA to generate the embedding instead of SentenceTransformer:
        # response = self.client.embed(model=Config.EMBEDDING_MODEL, input=query)
        # embedding = response['embeddings'][0]

        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        with self.engine.connect() as conn:
            stmt = text("""
                SELECT content, 
                (embedding <=> CAST(:embedding AS vector)) as dist 
                FROM documents 
                ORDER BY dist LIMIT :top_k
            """)
            result = conn.execute(stmt, {"embedding": embedding_str, "top_k": top_k})
            return [row[0] for row in result.fetchall()]

    def generate_response(self, query: str, context: list):
        before_llm(query)
        prompt = f"Context: {' '.join(context)}\n\nQuestion: {query}"
        
        # FIX 4: Corrected the Ollama client call layout
        completion = self.client.chat(
            model=Config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        # FIX 5: Ollama response dictionary parsing layout
        return completion['message']['content']
    
    def summarize_document(self, filename: str):
        content = None

        with self.engine.connect() as conn:
            stmt = text("SELECT content FROM documents WHERE title = :fname LIMIT 1")
            result = conn.execute(stmt, {"fname": filename})
            row = result.fetchone()
            if row:
                content = row[0]

        if not content:
            file_path = os.path.join(self.DOCUMENTS_DIR, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

        if not content:
            return {"error": f"Document '{filename}' not found"}

        prompt = f"Summarize the following document:\n\n{content[:8000]}"
        
        # FIX 6: Corrected the Ollama client call layout here too
        completion = self.client.chat(
            model=Config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return completion['message']['content']

    def list_documents(self):
        docs = []
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT DISTINCT title FROM documents"))
            docs = [row[0] for row in result.fetchall() if row[0] is not None]
        if not docs:
            if os.path.isdir(self.DOCUMENTS_DIR):
                docs = [f for f in os.listdir(self.DOCUMENTS_DIR) if os.path.isfile(os.path.join(self.DOCUMENTS_DIR, f))]
        return docs