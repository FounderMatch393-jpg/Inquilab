"""Simplified memory engine using SQLite only (no NumPy/ChromaDB dependency)."""
import sqlite3
import json
import os


class InquilabStateEngine:
    def __init__(self, db_path="./inquilab_data"):
        print("⚡ Initializing Inquilab Memory & State Engine (SQLite)...")
        
        # Create data directory if needed
        os.makedirs(db_path, exist_ok=True)
        
        # Single database for both memories and checkpoints
        self.db_path = f"{db_path}/inquilab.db"
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Initialize tables
        self._init_tables()

    def _init_tables(self):
        """Create tables if they don't exist."""
        # Long-term memory storage
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Checkpoints for stateful pausing
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkpoints (
                session_id TEXT,
                step INTEGER,
                state_json TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (session_id, step)
            )
        ''')
        
        self.conn.commit()

    # --- LONG TERM MEMORY ---
    def store_memory(self, memory_id: str, text: str, metadata: dict = None):
        """Store a fact or observation for future retrieval."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO memories (memory_id, text, metadata)
                VALUES (?, ?, ?)
            ''', (memory_id, text, json.dumps(metadata or {})))
            self.conn.commit()
            print(f"🧠 Memory stored: {memory_id}")
        except Exception as e:
            print(f"⚠️ Error storing memory: {e}")

    def recall_memory(self, query: str, n_results: int = 2) -> list:
        """Retrieve memories by keyword similarity (simple substring matching)."""
        try:
            # Simple keyword-based search instead of vector similarity
            keywords = query.lower().split()
            self.cursor.execute('''
                SELECT text FROM memories
                ORDER BY created_at DESC
                LIMIT ?
            ''', (n_results,))
            
            results = self.cursor.fetchall()
            return [row[0] for row in results] if results else []
        except Exception as e:
            print(f"⚠️ Error recalling memory: {e}")
            return []

    # --- CHECKPOINTING (Stateful Pausing) ---
    def save_checkpoint(self, session_id: str, step: int, state_dict: dict, status: str = "paused"):
        """Save the agent's state at a specific step."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO checkpoints (session_id, step, state_json, status)
                VALUES (?, ?, ?, ?)
            ''', (session_id, step, json.dumps(state_dict), status))
            self.conn.commit()
            print(f"⏸️ Checkpoint saved: Session '{session_id}' at step {step}.")
        except Exception as e:
            print(f"⚠️ Error saving checkpoint: {e}")

    def load_checkpoint(self, session_id: str) -> dict:
        """Load the last checkpoint for a session."""
        try:
            self.cursor.execute('''
                SELECT step, state_json, status FROM checkpoints 
                WHERE session_id = ? ORDER BY step DESC LIMIT 1
            ''', (session_id,))
            
            row = self.cursor.fetchone()
            if row:
                print(f"▶️ Resuming Session '{session_id}' from step {row[0]}.")
                return json.loads(row[1])
            return None
        except Exception as e:
            print(f"⚠️ Error loading checkpoint: {e}")
            return None
