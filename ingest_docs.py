import os
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from config import Config

# Initialize
engine = create_engine(Config.DATABASE_URL)
# model = SentenceTransformer(Config.EMBEDDING_MODEL)
self.model = SentenceTransformer(Config.EMBEDDING_MODEL)

def ingest_file(file_path):
    filename = os.path.basename(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple chunking (500 chars)
    chunks = [content[i:i+500] for i in range(0, len(content), 400)]
    
    for chunk in chunks:
        embedding = model.encode(chunk).tolist()
        # pgvector expects a string literal in the format '[0.1,0.2,...]'
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO documents (title, content, embedding) VALUES (:t, :c, CAST(:e AS vector))"),
                {"t": filename, "c": chunk, "e": embedding_str}
            )
            conn.commit()

# Run for all files in a folder
if __name__ == "__main__":
    for filename in os.listdir('./documents'):
        ingest_file(f'./documents/{filename}')
        print(f"Processed {filename}")