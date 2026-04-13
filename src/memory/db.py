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
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)
        
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT
            )
        ''')
        
        # nomic-embed-text-v1.5 outputs exactly 768 dimensions
        self.db.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS vec_documents USING vec0(
                id INTEGER PRIMARY KEY,
                embedding float[768]
            )
        ''')
        self.db.commit()
        
        if not os.path.exists(embed_model_path):
            raise FileNotFoundError(f"Embedding Model not found at {embed_model_path}. Run scripts/setup_models.py.")
            
        # Load the lightweight embedding model using Metal Backend
        self.embed_model = Llama(
            model_path=embed_model_path,
            embedding=True,
            n_gpu_layers=-1, 
            verbose=False
        )

    def _serialize_f32(self, vector: List[float]) -> bytes:
        """Serializes Python floats into C-level contiguous 4-byte values for sqlite-vec."""
        return struct.pack(f'{len(vector)}f', *vector)

    def add_memory(self, text: str):
        """Generates embeddings and inserts data dynamically."""
        embedding_res = self.embed_model.create_embedding(text)
        embedding = embedding_res['data'][0]['embedding']
        
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO documents (content) VALUES (?)", (text,))
        doc_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO vec_documents(id, embedding) VALUES (?, ?)", 
            [doc_id, self._serialize_f32(embedding)]
        )
        self.db.commit()

    def search_memory(self, query: str, top_k: int = 3) -> List[str]:
        """Nearest-neighbor similarity search utilizing the edge DB."""
        emb_res = self.embed_model.create_embedding(query)
        embedding = emb_res['data'][0]['embedding']
        
        cursor = self.db.cursor()
        results = cursor.execute("""
            SELECT d.content 
            FROM vec_documents v 
            JOIN documents d ON v.id = d.id 
            WHERE v.embedding MATCH ? 
            ORDER BY distance 
            LIMIT ?
        """, [self._serialize_f32(embedding), top_k])
        
        return [row[0] for row in results]
