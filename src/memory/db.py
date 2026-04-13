import sqlite3
import sqlite_vec
import struct
import os
from typing import List
from llama_cpp import Llama

class MemoryLayer:
    """
    Long-term Memory Storage utilizing sqlite-vec on edge disk.
    Designed to hold behavioral models, developer logic, and persona data.
    """
    def __init__(self, db_path: str = "data/db/memory.sqlite", embed_model_path: str = "models/nomic-embed-text-v1.5.Q4_K_M.gguf"):
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db = sqlite3.connect(db_path)
        try:
            self.db.enable_load_extension(True)
            sqlite_vec.load(self.db)
            self.db.enable_load_extension(False)
            self.vec_enabled = True
        except AttributeError:
            print("⚠️ macOS SIP/PYENV Vector Block Detected: sqlite3 lacks 'enable_load_extension'.")
            print("⚠️ Running MemoryLayer in Degraded SQL Mode (No Vector Search).")
            self.vec_enabled = False

        self.initialize_schema()
        
        if not os.path.exists(embed_model_path):
            raise FileNotFoundError(f"Embedding Model not found at {embed_model_path}. Run scripts/setup_models.py.")
            
        # Load the lightweight embedding model using Metal Backend
        self.embed_model = Llama(
            model_path=embed_model_path,
            embedding=True,
            n_gpu_layers=-1, 
            verbose=False
        )

    def initialize_schema(self):
        """Initialize all persistent tables and indexes used by memory and telemetry layers."""
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT
            )
        ''')

        self.db.execute('''
            CREATE TABLE IF NOT EXISTS reflection_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                reflection TEXT NOT NULL,
                score REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.db.execute('''
            CREATE TABLE IF NOT EXISTS system_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                agent_name TEXT NOT NULL,
                tokens_used INTEGER,
                execution_time_ms INTEGER,
                success_bool INTEGER NOT NULL,
                ram_spike REAL,
                task_type TEXT,
                error_class TEXT
            )
        ''')

        self.db.execute('''
            CREATE TABLE IF NOT EXISTS pattern_axioms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                axiom_text TEXT NOT NULL,
                scope TEXT,
                confidence REAL
            )
        ''')

        # nomic-embed-text-v1.5 outputs exactly 768 dimensions
        if self.vec_enabled:
            self.db.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_documents USING vec0(
                    id INTEGER PRIMARY KEY,
                    embedding float[768]
                )
            ''')
            self.db.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_pattern_axioms USING vec0(
                    id INTEGER PRIMARY KEY,
                    embedding float[768]
                )
            ''')

        self.db.execute("CREATE INDEX IF NOT EXISTS idx_reflection_logs_timestamp ON reflection_logs(timestamp DESC)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_system_telemetry_timestamp ON system_telemetry(timestamp DESC)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_system_telemetry_agent_name ON system_telemetry(agent_name)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_system_telemetry_task_type ON system_telemetry(task_type)")
        self.db.commit()

    def _serialize_f32(self, vector: List[float]) -> bytes:
        """Serializes Python floats into C-level contiguous 4-byte values for sqlite-vec."""
        return struct.pack(f'{len(vector)}f', *vector)

    def add_memory(self, text: str):
        """Generates embeddings and inserts data dynamically."""
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO documents (content) VALUES (?)", (text,))
        doc_id = cursor.lastrowid
        
        if self.vec_enabled:
            embedding_res = self.embed_model.create_embedding(text)
            embedding = embedding_res['data'][0]['embedding']
            cursor.execute(
                "INSERT INTO vec_documents(id, embedding) VALUES (?, ?)", 
                [doc_id, self._serialize_f32(embedding)]
            )
        self.db.commit()

    def search_memory(self, query: str, top_k: int = 3) -> List[str]:
        """Nearest-neighbor similarity search utilizing the edge DB or keyword search fallback."""
        cursor = self.db.cursor()
        
        if not self.vec_enabled:
            # Fallback to standard SQL text matching
            keywords = query.split()
            sql_query = "SELECT content FROM documents WHERE " + " OR ".join(["content LIKE ?"] * len(keywords)) + " LIMIT ?" # nosec
            search_params = [f"%{k}%" for k in keywords] + [top_k]
            results = cursor.execute(sql_query, search_params).fetchall()
            return [row[0] for row in results]
            
        emb_res = self.embed_model.create_embedding(query)
        embedding = emb_res['data'][0]['embedding']
        
        results = cursor.execute("""
            SELECT d.content 
            FROM vec_documents v 
            JOIN documents d ON v.id = d.id 
            WHERE v.embedding MATCH ? 
            ORDER BY distance 
            LIMIT ?
        """, [self._serialize_f32(embedding), top_k]).fetchall()
        
        return [row[0] for row in results]
