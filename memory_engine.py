import sqlite3
import json
import os
import math
import re
import hashlib
from collections import defaultdict

import chromadb


class StableHashEmbeddingFunction:
    """Deterministic embedding helper that avoids broken ONNX runtimes."""

    def __init__(self, dim: int = 32):
        self.dim = dim

    def embed_text(self, text: str):
        if text is None:
            text = ""
        tokens = re.findall(r"[a-zA-Z0-9]+", str(text).lower())
        if not tokens:
            return [0.0] * self.dim

        vec = [0.0] * self.dim
        counts = defaultdict(float)
        for token in tokens:
            token_hash = hashlib.md5(token.encode("utf-8")).digest()
            bucket = int.from_bytes(token_hash[:2], byteorder="big") % self.dim
            counts[bucket] += 1.0 + (len(token) * 0.05)

        for bucket, weight in counts.items():
            vec[bucket] = weight

        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return [0.0] * self.dim
        return [v / norm for v in vec]

    def embed_batch(self, texts):
        return [self.embed_text(text) for text in texts]


class InquilabStateEngine:
    def __init__(self, db_path="./inquilab_data"):
        print("⚡ Initializing Inquilab Memory & State Engine...")
        os.makedirs(db_path, exist_ok=True)
        
        # 1. Vector Memory (RAG) via ChromaDB
        # Uses a PersistentClient to keep embeddings securely stored on your local disk.
        self.chroma_client = chromadb.PersistentClient(path=f"{db_path}/vector_db")
        self.embedding_helper = StableHashEmbeddingFunction()
        self.memory_collection = self.chroma_client.get_or_create_collection(name="long_term_memory")
        
        # 2. Checkpointing (State) via SQLite
        # Creates a local database to track exactly where the agent is in a multi-step task.
        self.conn = sqlite3.connect(f"{db_path}/checkpoints.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkpoints (
                session_id TEXT,
                step INTEGER,
                state_json TEXT,
                status TEXT,
                PRIMARY KEY (session_id, step)
            )
        ''')
        self.conn.commit()

    # --- LONG TERM MEMORY (Agentic RAG) ---
    def store_memory(self, memory_id: str, text: str, metadata: dict = None):
        """Saves facts, user preferences, or successful code solutions for future runs."""
        self.memory_collection.add(
            documents=[text],
            embeddings=[self.embedding_helper.embed_text(text)],
            metadatas=[metadata or {}],
            ids=[memory_id]
        )
        print(f"🧠 Memory stored: {memory_id}")

    def recall_memory(self, query: str, n_results: int = 2) -> list:
        """Retrieves relevant past context to inject into the system prompt before reasoning."""
        query_embedding = [self.embedding_helper.embed_text(query)]
        results = self.memory_collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        return results["documents"][0] if results["documents"] else []

    # --- CHECKPOINTING (Stateful Pausing) ---
    def save_checkpoint(self, session_id: str, step: int, state_dict: dict, status: str = "paused"):
        """Freezes the agent's exact state so it can ask for human approval and resume later."""
        self.cursor.execute('''
            INSERT OR REPLACE INTO checkpoints (session_id, step, state_json, status)
            VALUES (?, ?, ?, ?)
        ''', (session_id, step, json.dumps(state_dict), status))
        self.conn.commit()
        print(f"⏸️ Checkpoint saved: Session '{session_id}' paused at step {step}.")

    def load_checkpoint(self, session_id: str) -> dict:
        """Restores the last known state to resume execution after a restart or approval."""
        self.cursor.execute('''
            SELECT step, state_json, status FROM checkpoints 
            WHERE session_id = ? ORDER BY step DESC LIMIT 1
        ''', (session_id,))
        row = self.cursor.fetchone()
        
        if row:
            print(f"▶️ Resuming Session '{session_id}' from step {row[0]}.")
            return json.loads(row[1])
        print("Observation: No previous state found.")
        return None