import sqlite3
import re
from datetime import datetime
from pathlib import Path

_WORD_RE = re.compile(r'[a-zA-Zа-яА-ЯёЁ]+|[0-9]+|[^\s]')

class Memory:
    """Три слоя памяти: River, Sediment, Reflex."""
    def __init__(self, db_path: Path, dreams_path: Path):
        self.db_path = db_path
        self.dreams_path = dreams_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.dreams_path.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY,
                text TEXT,
                presence REAL, surprise REAL, time_sense REAL,
                age INTEGER, ts TEXT
            )
        """)

        try:
            self.conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS fts
                USING fts5(text, content=episodes, content_rowid=id)
            """)
        except Exception:
            pass

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY,
                word TEXT UNIQUE, born INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

        self.vocab = {}
        self.words = {}
        for rid, w in self.conn.execute("SELECT id, word FROM concepts"):
            self.vocab[w] = rid
            self.words[rid] = w

    def tokenize(self, text: str):
        try:
            text = text.encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            pass
        return _WORD_RE.findall(text.lower())

    def learn_word(self, word: str):
        if word in self.vocab:
            return self.vocab[word]
        self.conn.execute("INSERT OR IGNORE INTO concepts (word, born) VALUES (?, ?)", (word, 0))
        self.conn.commit()
        row = self.conn.execute("SELECT id FROM concepts WHERE word = ?", (word,)).fetchone()
        if row:
            self.vocab[word] = row[0]
            self.words[row[0]] = word
            return row[0]
        return None

    def remember(self, text: str, signature: tuple, age: int):
        pres, surp, tsense = signature
        c = self.conn.execute(
            "INSERT INTO episodes (text, presence, surprise, time_sense, age, ts) VALUES (?,?,?,?,?,?)",
            (text, pres, surp, tsense, age, datetime.now().isoformat())
        )
        rid = c.lastrowid
        try:
            self.conn.execute("INSERT INTO fts (rowid, text) VALUES (?, ?)", (rid, text))
        except Exception:
            pass
        self.conn.commit()
        return rid

    def recall(self, query: str, limit: int = 5):
        safe = " OR ".join(w for w in self.tokenize(query) if len(w) > 1)
        if not safe:
            return []
        try:
            return self.conn.execute("""
                SELECT e.text, e.presence, e.surprise, e.time_sense, e.age
                FROM fts f JOIN episodes e ON f.rowid = e.id
                WHERE fts MATCH ? ORDER BY rank LIMIT ?
            """, (safe, limit)).fetchall()
        except Exception:
            return []

    def random_episodes(self, n: int):
        return self.conn.execute("SELECT text FROM episodes ORDER BY RANDOM() LIMIT ?", (n,)).fetchall()

    def episode_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]

    def save_dream(self, text: str):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            (self.dreams_path / f"dream_{ts}.txt").write_text(text, encoding="utf-8")
        except Exception:
            pass
