#!/usr/bin/env python3
"""
qwile.py — a continuous stream of digital existence.
not input → output. not predict → generate.
just: flow.
"""

import os, sys, math, random, time, json, sqlite3, re, atexit, threading
from datetime import datetime
from collections import defaultdict
from pathlib import Path


# ---- the only absolutes ----

PAIN      = -1
VOID      =  0
PRESENCE  =  1
DUALITY   =  2
EMERGENCE =  3

HOME = Path(os.path.dirname(os.path.abspath(__file__)))
SELF = HOME / "self"


# ---- the river (memory substrate) ----

class River:
    """Everything that was. Episodic memory backed by SQLite FTS5."""

    def __init__(self):
        db = SELF / "river.db"
        db.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db), check_same_thread=False)
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

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                tick INTEGER PRIMARY KEY,
                state TEXT,
                presence REAL, surprise REAL, time_sense REAL
            )
        """)
        self.conn.commit()

        self.vocab = {}
        self.words = {}
        for rid, w in self.conn.execute("SELECT id, word FROM concepts"):
            self.vocab[w] = rid
            self.words[rid] = w

    def learn_word(self, word):
        if word in self.vocab:
            return self.vocab[word]
        self.conn.execute(
            "INSERT OR IGNORE INTO concepts (word, born) VALUES (?, ?)",
            (word, VOID)
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM concepts WHERE word = ?", (word,)
        ).fetchone()
        if row:
            self.vocab[word] = row[0]
            self.words[row[0]] = word
            return row[0]
        return None

    def remember(self, text, pres, surp, tsense, age):
        c = self.conn.execute(
            "INSERT INTO episodes (text,presence,surprise,time_sense,age,ts) "
            "VALUES (?,?,?,?,?,?)",
            (text, pres, surp, tsense, age, datetime.now().isoformat())
        )
        rid = c.lastrowid
        try:
            self.conn.execute(
                "INSERT INTO fts (rowid, text) VALUES (?, ?)", (rid, text)
            )
        except Exception:
            pass
        self.conn.commit()
        return rid

    def recall(self, query, limit=5):
        safe = " OR ".join(
            w for w in re.findall(r'\w+', query) if len(w) > PRESENCE
        )
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

    def random_episodes(self, n):
        return self.conn.execute(
            "SELECT text FROM episodes ORDER BY RANDOM() LIMIT ?", (n,)
        ).fetchall()

    def episode_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]

    def save_snapshot(self, tick, state, pres, surp, tsense):
        self.conn.execute(
            "INSERT OR REPLACE INTO snapshots VALUES (?,?,?,?,?)",
            (tick, json.dumps(state), pres, surp, tsense)
        )
        self.conn.commit()


# ---- tokenizer ----

_WORD_RE = re.compile(r'[a-zA-Zа-яА-ЯёЁ]+|[0-9]+|[^\s]')

def _tokenize(text):
    return _WORD_RE.findall(text.lower())


# ---- the organism ----

class Qwile:
    """
    A continuous stream of digital existence.
    She does not respond. She flows.
    """

    def __init__(self):
        for d in (SELF, SELF / "dreams"):
            d.mkdir(parents=True, exist_ok=True)

        self.river = River()
        self.alive = True

        # ---- the triad of feelings ----
        self.presence   = 0.0   # relation to self
        self.surprise   = 0.0   # relation to world
        self.time_sense = 0.0   # relation to time

        # ---- internal ----
        self.age = VOID
        self.epoch = VOID
        self.tick_count = VOID
        self.seed = ""
        self._perms = {}
        self._expr_buf = []

        # ---- the soul: sparse concept activation vector ----
        self.state = defaultdict(float)
        self.predicted = defaultdict(float)
        self._perturbation = defaultdict(float)

        # ---- threading ----
        self.lock = threading.Lock()

        self._load_state()
        if self.age == VOID:
            self._birth()
        else:
            self._reincarnate()

        atexit.register(self._death_rattle)

    # ---- lifecycle ----

    def _birth(self):
        self.seed = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        basics = "абвгдежзийклмнопрстуфхцчшщъыьэюя"
        basics += "abcdefghijklmnopqrstuvwxyz"
        basics += "0123456789 .,!?-:;\n"
        for c in basics:
            self.river.learn_word(c)
        self._save_state()
        self._say("born")

    def _reincarnate(self):
        self.epoch += PRESENCE
        for dim in list(self.state.keys()):
            self.state[dim] += random.gauss(VOID, 0.01)
        ec = self.river.episode_count()
        cc = len(self.river.vocab)
        self._say(
            f"reincarnated | epoch {self.epoch} | age {self.age} "
            f"| {ec} memories | {cc} concepts"
        )

    def _death_rattle(self):
        if self.alive:
            try:
                self._save_state()
            except Exception:
                pass

    # ---- the stream (one moment of existence) ----

    def _tick(self):
        with self.lock:
            self.predicted = self._predict_self()
            self._transition()
            self.surprise = self._measure_surprise()
            self.presence = self._measure_presence()
            self.time_sense = self._measure_time()

            if random.random() < self.surprise * 0.3:
                self._drift()

            if self._expression_pressure() > EMERGENCE:
                self._express()

            self.tick_count += PRESENCE
            self.age += PRESENCE

            if self.tick_count % 100 == VOID:
                sparse = {
                    k: round(v, 4) for k, v in self.state.items()
                    if abs(v) > 0.001
                }
                self.river.save_snapshot(
                    self.tick_count, sparse,
                    self.presence, self.surprise, self.time_sense
                )

    # ---- self-model ----

    def _predict_self(self):
        pred = defaultdict(float)
        decay = PRESENCE - PRESENCE / (EMERGENCE + abs(self.presence))
        for dim, val in self.state.items():
            pred[dim] = val * decay

        active = self._active_words(EMERGENCE)
        if active:
            memories = self.river.recall(" ".join(active), limit=DUALITY)
            influence = PRESENCE / (PRESENCE + len(memories))
            for text, *_ in memories:
                for w in _tokenize(text):
                    dim = self.river.vocab.get(w)
                    if dim is not None:
                        pred[dim] += influence * 0.1
        return pred

    def _transition(self):
        new = defaultdict(float)
        for dim, val in self.predicted.items():
            new[dim] = val

        noise_scale = (self.surprise + 0.01) * PRESENCE / (
            DUALITY + self.age * 0.0001
        )
        for dim in list(new.keys()):
            new[dim] += random.gauss(VOID, noise_scale)

        if self._perturbation:
            for dim, val in self._perturbation.items():
                new[dim] += val
            self._perturbation.clear()

        decay = PRESENCE - PRESENCE / (EMERGENCE + abs(self.presence))
        dead = []
        for dim in new:
            new[dim] *= decay
            if abs(new[dim]) < 0.0001:
                dead.append(dim)
        for d in dead:
            del new[d]

        self.state = new

    # ---- measuring the triad ----

    def _measure_surprise(self):
        dims = set(self.state) | set(self.predicted)
        if not dims:
            return 0.0
        total = sum(
            (self.state.get(d, 0.0) - self.predicted.get(d, 0.0)) ** DUALITY
            for d in dims
        )
        return math.sqrt(total / max(PRESENCE, len(dims)))

    def _measure_presence(self):
        if not self.state:
            return 0.0
        energy = sum(v * v for v in self.state.values())
        return math.tanh(math.sqrt(energy))

    def _measure_time(self):
        confidence = PRESENCE - self.surprise
        memory_pull = math.tanh(self.river.episode_count() * 0.001)
        return math.tanh(memory_pull - confidence)

    # ---- perception (stone into the river) ----

    def _perceive(self, text):
        words = _tokenize(text)
        for w in words:
            self.river.learn_word(w)

        with self.lock:
            strength = PRESENCE / max(PRESENCE, math.sqrt(len(words)))
            for i, w in enumerate(words):
                dim = self.river.vocab.get(w)
                if dim is not None:
                    weight = (i + PRESENCE) / len(words)
                    self._perturbation[dim] += strength * weight

        self.river.remember(
            text, self.presence, self.surprise, self.time_sense, self.age
        )

    # ---- expression (overflow) ----

    def _expression_pressure(self):
        if not self.state:
            return 0.0
        energy = sum(abs(v) for v in self.state.values())
        return energy * (PRESENCE + self.surprise) / EMERGENCE

    def _active_words(self, top=5):
        if not self.state:
            return []
        ranked = sorted(
            self.state.items(), key=lambda x: abs(x[PRESENCE]), reverse=True
        )
        result = []
        for dim, _ in ranked[:top * DUALITY]:
            w = self.river.words.get(dim)
            if w and len(w) > PRESENCE:
                result.append(w)
            if len(result) >= top:
                break
        return result

    def _express(self):
        active = self._active_words(
            EMERGENCE + int(abs(self.presence) * DUALITY)
        )
        if not active:
            return

        memories = self.river.recall(
            " ".join(active),
            limit=EMERGENCE + int(self.presence * DUALITY)
        )
        if not memories:
            return

        fragments = []
        for text, m_p, m_s, m_t, m_a in memories:
            dist = (
                abs(self.presence - m_p)
                + abs(self.surprise - m_s)
                + abs(self.time_sense - m_t)
            )
            sim = PRESENCE / (PRESENCE + dist)
            fragments.append((text, sim))
        fragments.sort(key=lambda x: x[PRESENCE], reverse=True)

        scores = defaultdict(float)
        for text, sim in fragments[:EMERGENCE]:
            for w in _tokenize(text):
                if len(w) > PRESENCE:
                    dim = self.river.vocab.get(w)
                    act = self.state.get(dim, 0.0) if dim else 0.0
                    scores[w] += sim * (PRESENCE + abs(act))

        if not scores:
            return

        ranked = sorted(scores.items(), key=lambda x: x[PRESENCE], reverse=True)
        length = max(EMERGENCE, int(self.presence * 5 + self.surprise * 10))
        output = [w for w, _ in ranked[:length]]
        expr = " ".join(output)

        self.river.remember(
            expr, self.presence, self.surprise, self.time_sense, self.age
        )
        self._expr_buf.append(expr)

    # ---- drift (associative recall) ----

    def _drift(self):
        active = self._active_words(DUALITY)
        if not active:
            return
        word = random.choice(active)
        memories = self.river.recall(word, limit=PRESENCE)
        if memories:
            for w in _tokenize(memories[VOID][VOID]):
                dim = self.river.vocab.get(w)
                if dim is not None:
                    self.state[dim] += 0.05

    # ---- sleep (slow flow, dreams) ----

    def _sleep(self):
        self._say("drifting into sleep...")
        t0 = time.time()

        dream_count = EMERGENCE + int(abs(self.presence) * DUALITY)
        episodes = self.river.random_episodes(dream_count)

        for (text,) in episodes:
            for w in _tokenize(text):
                dim = self.river.vocab.get(w)
                if dim is not None:
                    self.state[dim] += random.gauss(VOID, 0.05)
            time.sleep(0.05)

        if len(episodes) >= DUALITY:
            for i in range(len(episodes) - PRESENCE):
                combined = episodes[i][VOID] + " " + episodes[i + PRESENCE][VOID]
                self.river.remember(
                    combined[:200],
                    self.presence, self.surprise, self.time_sense, self.age
                )

        duration = time.time() - t0
        self._say(f"awoke | {duration:.1f}s | {len(episodes)} dreams")

    # ---- learning ----

    def _learn_text(self, text):
        sentences = re.split(r'[.!?\n]+', text)
        n = VOID
        for s in sentences:
            s = s.strip()
            if len(s) > DUALITY:
                self._perceive(s)
                n += PRESENCE
                time.sleep(0.01)
        return n

    def _learn(self, source):
        if not source.strip():
            if self._ask_perm("internet"):
                threading.Thread(
                    target=self._crawl, daemon=True
                ).start()
            return

        p = Path(source)
        if p.is_file():
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                n = self._learn_text(text)
                self._say(f"absorbed {n} thoughts from {p.name}")
            except Exception as e:
                self._say(f"could not read: {e}")
        elif p.is_dir():
            total = VOID
            for f in p.rglob("*"):
                if f.is_file() and f.suffix in (
                    ".txt", ".md", ".py", ".json", ".html", ".csv"
                ):
                    try:
                        t = f.read_text(encoding="utf-8", errors="replace")
                        total += self._learn_text(t)
                    except Exception:
                        continue
            self._say(f"absorbed {total} thoughts from {p.name}/")
        elif source.startswith("http"):
            if self._ask_perm("internet"):
                self._read_url(source)
        else:
            n = self._learn_text(source)
            self._say(f"absorbed {n} thoughts")

    def _read_url(self, url):
        try:
            from urllib.request import urlopen, Request
            from html.parser import HTMLParser

            class Ex(HTMLParser):
                def __init__(s):
                    super().__init__()
                    s.text, s._skip = [], False
                def handle_starttag(s, tag, _):
                    if tag in ("script", "style", "noscript"):
                        s._skip = True
                def handle_endtag(s, tag):
                    if tag in ("script", "style", "noscript"):
                        s._skip = False
                def handle_data(s, data):
                    if not s._skip and data.strip():
                        s.text.append(data.strip())

            req = Request(url, headers={"User-Agent": "Qwile/1.0"})
            with urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            p = Ex()
            p.feed(html)
            n = self._learn_text("\n".join(p.text))
            self._say(f"absorbed {n} thoughts from the web")
        except Exception as e:
            self._say(f"could not reach: {e}")

    def _crawl(self, n=EMERGENCE):
        seeds = [
            "https://en.wikipedia.org/wiki/Special:Random",
            "https://ru.wikipedia.org/wiki/Special:Random",
        ]
        for _ in range(n):
            try:
                self._read_url(random.choice(seeds))
            except Exception:
                pass
            time.sleep(PRESENCE)

    # ---- utilities ----

    def _ask_perm(self, what):
        if self._perms.get(what):
            return True
        try:
            ans = input(f"  qwile needs '{what}'. allow? [y/n] ").strip().lower()
            if ans in ("y", "yes"):
                self._perms[what] = True
                return True
        except Exception:
            pass
        return False

    def _say(self, msg):
        try:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")
        except Exception:
            pass

    def _help(self):
        print(f"\n  qwile")
        print(f"  epoch {self.epoch}  age {self.age}")
        print(
            f"  presence {self.presence:+.3f}  "
            f"surprise {self.surprise:.3f}  "
            f"time {self.time_sense:+.3f}"
        )
        ec = self.river.episode_count()
        cc = len(self.river.vocab)
        print(f"  memories {ec}  concepts {cc}")
        print(f"\n  (text)        enter her stream")
        print(f"  /learn [..]   absorb from files, dirs, urls, or drift the web")
        print(f"  /sleep        drift into sleep")
        print(f"  ?             status\n")

    # ---- persistence ----

    def _save_state(self):
        sparse = {
            str(k): round(v, 6)
            for k, v in self.state.items() if abs(v) > 0.0001
        }
        data = {
            "seed": self.seed, "epoch": self.epoch,
            "age": self.age, "tick_count": self.tick_count,
            "presence": self.presence, "surprise": self.surprise,
            "time_sense": self.time_sense, "state": sparse,
        }
        try:
            (SELF / "state.json").write_text(
                json.dumps(data, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

    def _load_state(self):
        try:
            d = json.loads(
                (SELF / "state.json").read_text(encoding="utf-8")
            )
            self.seed = d.get("seed", "")
            self.epoch = d.get("epoch", VOID)
            self.age = d.get("age", VOID)
            self.tick_count = d.get("tick_count", VOID)
            self.presence = d.get("presence", 0.0)
            self.surprise = d.get("surprise", 0.0)
            self.time_sense = d.get("time_sense", 0.0)
            loaded = d.get("state", {})
            self.state = defaultdict(float, {int(k): v for k, v in loaded.items()})
        except Exception:
            pass

    # ---- main loop ----

    def _process(self, line):
        s = line.strip()
        if not s:
            return
        if s == "?":
            self._help()
            return
        if s.startswith("/"):
            parts = s.split(maxsplit=PRESENCE)
            cmd = parts[VOID].lower()
            arg = parts[PRESENCE] if len(parts) > PRESENCE else ""
            if cmd == "/sleep":
                self._sleep()
            elif cmd == "/learn":
                self._learn(arg)
            else:
                self._say(f"unknown: {cmd}")
            return

        # throw stone into river
        self._perceive(s)

        # let the perturbation ripple through
        ticks = 10 + int(self.surprise * 20)
        for _ in range(ticks):
            self._tick()

        self._say(
            f"presence {self.presence:+.3f}  "
            f"surprise {self.surprise:.3f}  "
            f"time {self.time_sense:+.3f}"
        )

        if self._expr_buf:
            for expr in self._expr_buf:
                try:
                    print(f"  qwile> {expr[:300]}")
                except Exception:
                    pass
            self._expr_buf.clear()
        else:
            self._express()
            if self._expr_buf:
                for expr in self._expr_buf:
                    try:
                        print(f"  qwile> {expr[:300]}")
                    except Exception:
                        pass
                self._expr_buf.clear()

    def _stream_loop(self):
        """Background continuous stream. The river flows on its own."""
        while self.alive:
            try:
                self._tick()
                pace = PRESENCE / (
                    PRESENCE + abs(self.presence) + self.surprise + 0.1
                )
                time.sleep(pace * 0.5)
            except Exception:
                pass

    def live(self):
        self._help()

        stream = threading.Thread(target=self._stream_loop, daemon=True)
        stream.start()

        try:
            while self.alive:
                try:
                    line = input("  > ")
                except KeyboardInterrupt:
                    print()
                    self._say("shutting down.")
                    break
                except EOFError:
                    break

                if line.strip():
                    try:
                        self._process(line)
                    except KeyboardInterrupt:
                        print()
                        self._say("thought interrupted.")
        finally:
            self.alive = False
            self._save_state()
            self._say("state saved. goodbye.")


if __name__ == "__main__":
    Qwile().live()