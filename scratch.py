import os
from sqlalchemy import create_engine, text
from config import Config

engine = create_engine(Config.DATABASE_URL)
with engine.connect() as conn:
    print("Dropping old documents table...")
    conn.execute(text("DROP TABLE IF EXISTS documents CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS chat_history CASCADE;"))
    conn.commit()
    
    print("Executing schema.sql...")
    with open('databases/schema.sql', 'r') as f:
        sql_commands = f.read().split(';')
        for cmd in sql_commands:
            if cmd.strip():
                try:
                    conn.execute(text(cmd))
                    conn.commit()
                except Exception as e:
                    print(f"Error executing command: {cmd}\n{e}")

print("Schema successfully recreated!")
