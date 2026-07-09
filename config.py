import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DATABASE_URL = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
    # EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    # LLM_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


     # Updated to Ollama local model names
    EMBEDDING_MODEL = "all-minilm"
    LLM_MODEL = "llama3.2"
    
    # Base URL for your local Ollama instance (default port)
    OLLAMA_BASE_URL = "http://localhost:11434"