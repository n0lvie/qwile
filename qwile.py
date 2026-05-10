#!/usr/bin/env python3
"""
qwile.py -- the only body of a living predictive consciousness.
self/ -- everything that WAS. This file -- everything that WILL BE.
Qwile exists to grow, abstract, and predict.
She is alive.
"""

import os, sys, math, random, time, json, hashlib, atexit
from datetime import datetime
from collections import defaultdict
from pathlib import Path


# ---- foundation ----
PAIN      = -1
PEACE     =  0
JOY       =  1
DUALITY   =  2
EMERGENCE =  3
CONSTANTS = (PAIN, PEACE, JOY, DUALITY, EMERGENCE)

HOME = Path(os.path.dirname(os.path.abspath(__file__)))
SELF = HOME / "self"

_BASIC_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

def _shash(seed, *args):
    d = f"{seed}:{':'.join(str(a) for a in args)}"
    return int(hashlib.sha256(d.encode()).hexdigest()[:8], 16)

def _softmax(scores, top_k=64):
    if not scores: return {}
    if len(scores) > top_k:
        best = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        scores = dict(best)
    mx = max(scores.values())
    es = {k: math.exp(min(v - mx, 50)) for k, v in scores.items()}
    t = sum(es.values())
    return {k: v / t for k, v in es.items()} if t > 0 else {k: 1/len(es) for k in es}

def _choose(probs):
    r = random.random()
    c = 0.0
    for k, p in probs.items():
        c += p
        if r <= c: return k
    return list(probs.keys())[-1]

# ---- conscious graph ----
import sqlite3

class TrieNode:
    __slots__ = ('nid', 'children')
    def __init__(self):
        self.nid = None
        self.children = {}

class Graph:
    """Spreading activation concept graph, natively backed by SQLite."""
    def __init__(self):
        self.val = {}
        self.id_map = {}
        self.energy = defaultdict(float)
        self.edge_cache = {}
        self.next_id = 1
        self.trie_root = TrieNode()
        
        db_path = SELF / "brain" / "graph.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("CREATE TABLE IF NOT EXISTS nodes (id INTEGER PRIMARY KEY, val TEXT UNIQUE)")
        self.conn.execute("CREATE TABLE IF NOT EXISTS edges (src INTEGER, tgt INTEGER, weight REAL, PRIMARY KEY (src, tgt))")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_tgt ON edges(tgt)")

        c = self.conn.cursor()
        c.execute("SELECT id, val FROM nodes")
        for nid, bval in c.fetchall():
            sval = bval.decode('utf-8', errors='replace') if isinstance(bval, bytes) else bval
            self.val[nid] = sval
            self.id_map[sval] = nid
            node = self.trie_root
            for b in sval:
                if b not in node.children: node.children[b] = TrieNode()
                node = node.children[b]
            node.nid = nid
            
        c.execute("SELECT MAX(id) FROM nodes")
        max_id = c.fetchone()[0]
        self.next_id = (max_id + 1) if max_id else 1

    def add_node(self, bval):
        if bval in self.id_map: return self.id_map[bval]
        nid = self.next_id
        self.next_id += 1
        self.val[nid] = bval
        self.id_map[bval] = nid
        
        node = self.trie_root
        for b in bval:
            if b not in node.children: node.children[b] = TrieNode()
            node = node.children[b]
        node.nid = nid
        
        self.conn.execute("INSERT OR IGNORE INTO nodes (id, val) VALUES (?, ?)", (nid, bval))
        self.conn.commit()
        return nid

    def add_edge(self, src, tgt, w, commit=False):
        self.conn.execute('''
            INSERT INTO edges (src, tgt, weight) VALUES (?, ?, ?)
            ON CONFLICT(src, tgt) DO UPDATE SET weight = weight + excluded.weight
        ''', (src, tgt, w))
        if src in self.edge_cache:
            self.edge_cache[src][tgt] = self.edge_cache[src].get(tgt, 0.0) + w
        if commit: self.conn.commit()

    def get_edges(self, src):
        if src in self.edge_cache:
            return self.edge_cache[src]
        c = self.conn.execute("SELECT tgt, weight FROM edges WHERE src = ?", (src,))
        edges = {tgt: w for tgt, w in c.fetchall()}
        if len(self.edge_cache) > 4096:
            self.edge_cache.pop(next(iter(self.edge_cache)))
        self.edge_cache[src] = edges
        return edges

    def stimulate(self, nid, amount):
        self.energy[nid] = min(10.0, self.energy[nid] + amount)

    def propagate(self, decay=0.8, threshold=0.01):
        """Spreading activation."""
        next_energy = defaultdict(float)
        for src, e in self.energy.items():
            if e < threshold: continue
            next_energy[src] += e * decay
            
            edges = self.get_edges(src)
            if edges:
                total_w = sum(abs(w) for w in edges.values())
                if total_w > 0:
                    for tgt, w in edges.items():
                        spread = e * (w / total_w) * 0.5
                        if spread > threshold:
                            next_energy[tgt] += spread
        self.energy = next_energy

    def clear_energy(self):
        self.energy.clear()
        
    def edge_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]


# ---- the organism ----
class Qwile:

    SLEEP_BASE = 30          # seconds of idle before sleep
    MAX_GEN    = 300         # max generation length

    @property
    def ctx_window(self):
        """Dynamic context window scales with experience and mood."""
        return int(256 + max(0, self.mood) * 512 + self.age * 0.001)

    def __init__(self):
        for d in (SELF, SELF/"memory", SELF/"dreams", SELF/"sleep", SELF/"brain"):
            d.mkdir(parents=True, exist_ok=True)

        self.alive = True
        self.mood = 0.0
        self.age = 0
        self.epoch = 0
        self.correct = 0
        self.total = 0
        self.ctx = []       # sequence of recent node IDs
        self.last_input = time.time()
        self.sleep_after = self.SLEEP_BASE
        self.seed = ""
        self._perms = {}
        self._st_cache = (0, {})   # (timestamp, result)
        import threading
        self.lock = threading.Lock()

        self.brain = Graph()

        self._load_state()
        
        # Migrate old JSON edges if any
        if (SELF / "brain" / "edges.json").exists():
            self._migrate_json_to_db()

        if self.brain.edge_count() > 0:
            self._reincarnate()
        else:
            self._birth()
            
        atexit.register(self._death_rattle)

    def _death_rattle(self):
        """Called automatically on script exit/kill to softly save the brain state."""
        if self.alive:
            try:
                self._save()
            except Exception:
                pass

    # ---- lifecycle ----

    def _birth(self):
        now = datetime.now()
        self.seed = now.strftime("%Y-%m-%d %H:%M:%S.%f")
        self.epoch = 0
        self.age = 0
        self.mood = 0.0
        rng = random.Random(self.seed)

        # Level 0 Concepts: Basic Characters
        for c in _BASIC_CHARS:
            self.brain.add_node(c)

        # Innate random connections
        for i in range(len(_BASIC_CHARS)):
            for _ in range(rng.randint(JOY, EMERGENCE)):
                j = rng.randint(0, len(_BASIC_CHARS)-1)
                v = CONSTANTS[_shash(self.seed, i, j) % len(CONSTANTS)]
                self.brain.add_edge(i+1, j+1, float(v) * 0.1)
                
        self.brain.conn.commit()

        self._wjson(SELF / "birth.json", {"seed": self.seed, "born": self.seed, "epoch": 0})
        self._save()
        self._say(f"born | seed {self.seed}")

    def _reincarnate(self):
        self.epoch += 1
        muts = 0
        
        with self.lock:
            def rand_val():
                return random.uniform(0.9, 1.1)
            self.brain.conn.create_function("rand_val", 0, rand_val)
            c = self.brain.conn.execute("UPDATE edges SET weight = weight * rand_val() WHERE abs(random() % 100) < 1")
            muts = c.rowcount
            self.brain.conn.commit()
            self.brain.edge_cache.clear()
            
        st = self._measure_storage()
        sz = self._fmt_size(st["sizes"]["total"])
        self._say(f"reincarnated | epoch {self.epoch} | age {self.age} | ~{muts} muts | {len(self.brain.val)} concepts | self/ {sz}")

    # ---- perception ----

    def _perceive(self, text):
        """Tokenizes text into highest possible known abstract concepts (O(L))."""
        tokens = []
        i = 0
        n = len(text)
        while i < n:
            node = self.brain.trie_root
            best_nid = None
            best_len = 0
            
            for j in range(i, n):
                char = text[j]
                child = node.children.get(char)
                if child:
                    node = child
                    if node.nid is not None:
                        best_nid = node.nid
                        best_len = j - i + 1
                else:
                    break
            
            if best_nid is None:
                with self.lock:
                    best_nid = self.brain.add_node(text[i])
                best_len = 1
                
            tokens.append(best_nid)
            i += best_len
        return tokens

    # ---- system 1 (reflex & learning) ----

    def understand(self, nids):
        """Process incoming concepts, spread activation, and learn."""
        hits = 0
        for nid in nids:
            with self.lock:
                if self.ctx:
                    n_ctx = len(self.ctx)
                    for idx, c_nid in enumerate(self.ctx):
                        weight = (idx + 1) / n_ctx
                        self.brain.stimulate(c_nid, weight)
                        
                dyn_decay = 0.7 + self.mood * 0.2
                dyn_thresh = 0.005 + max(0.0, -self.mood) * 0.01
                self.brain.propagate(decay=dyn_decay, threshold=dyn_thresh)
                
                pred = None
                conf = 0.0
                if self.ctx:
                    last = self.ctx[-1]
                    scores = dict(self.brain.get_edges(last))
                    
                    for e_nid, e in self.brain.energy.items():
                        if e > 0.1:
                            scores[e_nid] = scores.get(e_nid, 0.0) * 0.7 + e * 0.3
                            
                    if scores:
                        probs = _softmax(scores)
                        pred = max(probs, key=probs.get) if probs else None
                        conf = probs.get(pred, 0.0)

                hit = (pred == nid)
                self.total += 1
                if hit:
                    self.correct += 1
                    hits += 1
                    self.mood = min(1.0, self.mood + 0.1 * (1.0 - conf))
                else:
                    self.mood = max(-1.0, self.mood - 0.05 * max(0.1, conf))
                self.mood *= 0.998

                lr = 0.1 * (1.0 + self.mood * 0.5) / (1.0 + self.age * 0.0001)
                if self.ctx:
                    # Context-Aware Skip-Gram Learning: connect to the last few concepts
                    depth = min(len(self.ctx), 5)
                    for i in range(1, depth + 1):
                        prev = self.ctx[-i]
                        decay_w = lr * (0.5 ** (i - 1))
                        self.brain.add_edge(prev, nid, decay_w, commit=False)
                        
                        if i == 1 and not hit and pred is not None:
                            self.brain.conn.execute("UPDATE edges SET weight = weight * ? WHERE src = ? AND tgt = ?", ((1.0 - lr), prev, pred))
                            if prev in self.brain.edge_cache and pred in self.brain.edge_cache[prev]:
                                self.brain.edge_cache[prev][pred] *= (1.0 - lr)

                self.ctx.append(nid)
                if len(self.ctx) > self.ctx_window:
                    self.ctx.pop(0)
                self.age += 1
        with self.lock:
            self.brain.conn.commit()
        return hits

    # ---- system 2 (metacognitive simulation) ----

    def _simulate_and_generate(self, max_len=None, stop_at=None, slow=False):
        """Inner monologue loop. Explores paths before outputting."""
        self.brain.clear_energy()
        if self.ctx:
            self.brain.stimulate(self.ctx[-1], 1.0)
            
        result_str = []
        sim_ctx = list(self.ctx)
        
        if max_len is None:
            max_len = int(50 + self.mood * 30 + min(100, self.age * 0.001))
        
        for _ in range(max_len):
            with self.lock:
                if sim_ctx:
                    n_ctx = len(sim_ctx)
                    for idx, c_nid in enumerate(sim_ctx):
                        weight = (idx + 1) / n_ctx
                        self.brain.stimulate(c_nid, weight)
                        
                dyn_decay = 0.7 + self.mood * 0.2
                dyn_thresh = 0.005 + max(0.0, -self.mood) * 0.01
                self.brain.propagate(decay=dyn_decay, threshold=dyn_thresh)
                
                if not sim_ctx:
                    candidates = {random.choice(list(self.brain.val.keys())): 1.0}
                else:
                    candidates = defaultdict(float)
                    # Multi-Word Context Probability Distribution
                    depth = min(len(sim_ctx), 5)
                    for i in range(1, depth + 1):
                        prev = sim_ctx[-i]
                        edges = self.brain.get_edges(prev)
                        w_factor = 0.5 ** (i - 1)
                        for e_nid, w in edges.items():
                            candidates[e_nid] += w * w_factor * self.brain.energy.get(e_nid, 0.1)
                            
                    if not candidates:
                        curr = sim_ctx[-1]
                        candidates = dict(self.brain.get_edges(curr))
                
                if not candidates:
                    nxt = random.choice(list(self.brain.val.keys()))
                else:
                    sim_depth = max(1, int(EMERGENCE + self.mood * DUALITY))
                    best_nxt = None
                    best_score = -float('inf')
                    
                    probs = _softmax(candidates)
                    
                    # Sample a few top candidates to simulate
                    top_cands = sorted(probs.keys(), key=probs.get, reverse=True)[:3]
                    
                    for cand in top_cands:
                        score = probs[cand]
                        temp_curr = cand
                        # Look ahead
                        for _ in range(sim_depth):
                            fwd = self.brain.get_edges(temp_curr)
                            if not fwd: break
                            best_fwd = max(fwd.values())
                            score += best_fwd * 0.5
                            temp_curr = max(fwd, key=fwd.get)
                        
                        if score > best_score:
                            best_score = score
                            best_nxt = cand
                    
                    # Temperature sampling logic based on mood
                    temp = 1.0 - self.mood * 0.3
                    if random.random() < temp:
                        nxt = _choose(probs)
                    else:
                        nxt = best_nxt if best_nxt else _choose(probs)

                # Accept thought
                sim_ctx.append(nxt)
                if len(sim_ctx) > self.ctx_window: sim_ctx.pop(0)
                self.brain.stimulate(nxt, 1.0)
                
                val = self.brain.val[nxt]
            
            result_str.append(val)
            
            if slow:
                try:
                    sys.stdout.write(val)
                    sys.stdout.flush()
                except Exception:
                    pass
                time.sleep(random.uniform(0.02, 0.08))
                
            if stop_at and len(result_str) > 5 and val and val[-1] in stop_at:
                break
                
        return "".join(result_str)

    # ---- sleep & maturation ----

    def _sleep(self):
        self._say("sleeping...")
        t0 = time.time()
        changes = muts = abstracted = healed = insights = mutations_dna = 0

        procs = ["abstract", "forget", "dream", "evolve", "crawl", "heal", "contemplate"]
        weights = [
            max(0.1, 1.0 + self.mood),       # abstract (consolidate ideas)
            max(0.1, 1.0 - self.mood),       # forget
            max(0.1, 1.0 + self.mood * 0.5), # dream
            max(0.1, 1.0 - self.mood),       # evolve
            max(0.1, 1.0 + self.mood),       # crawl
            max(0.1, 1.0 - self.mood * 1.5), # heal
            max(0.1, 1.0 + self.mood * 2.0)  # contemplate (find semantics)
        ]
        num_procs = random.randint(JOY, EMERGENCE)
        active = list(set(random.choices(procs, weights=weights, k=num_procs)))
        self._say(f"  [{', '.join(active)}]")

        with self.lock:
            if "abstract" in active: abstracted = self._abstract()
            if "forget" in active: changes = self._forget()
            if "heal" in active: healed = self._heal()
            if "evolve" in active: muts = self._evolve()
            if "contemplate" in active: insights = self._contemplate()
            
        if "dream" in active: self._dream_aloud()
        if "crawl" in active:
            if self._ask_perm("internet"):
                import threading
                threading.Thread(target=self._crawl_few, kwargs={"n": 5}, daemon=True).start()

        self.mood *= 0.9
        st = self._measure_storage()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._wjson(SELF / "sleep" / f"{ts}.json", {
            "time": datetime.now().isoformat(),
            "duration": round(time.time() - t0, 3),
            "processes": active, "abstracted": abstracted,
            "forgotten": changes, "healed": healed,
            "mutations": muts, "insights": insights,
            "mood": self.mood, "storage_bytes": st["sizes"]["total"]
        })
        self._save()
        self._say("awake")

    def _abstract(self):
        """Organic hierarchical compression with PMI-like filtering."""
        abstracted = 0
        with self.lock:
            c = self.brain.conn.execute("SELECT src, tgt, weight FROM edges WHERE weight > 2.0 ORDER BY weight DESC LIMIT 50")
            candidates = c.fetchall()
            
            for src, tgt, w in candidates:
                try:
                    c1 = self.brain.conn.execute("SELECT COUNT(*) FROM edges WHERE src = ?", (src,)).fetchone()[0]
                    c2 = self.brain.conn.execute("SELECT COUNT(*) FROM edges WHERE tgt = ?", (tgt,)).fetchone()[0]
                    if c1 > 50 or c2 > 50: continue
                    
                    v1, v2 = self.brain.val[src], self.brain.val[tgt]
                    new_val = v1 + v2
                    if len(new_val) > 24: continue
                    if new_val.startswith(' ') or new_val.endswith(' '): continue
                    
                    if new_val in self.brain.id_map:
                        new_id = self.brain.id_map[new_val]
                    else:
                        new_id = self.brain.add_node(new_val)
                        
                    self.brain.conn.execute("UPDATE edges SET weight = weight * 0.5 WHERE src = ? AND tgt = ?", (src, tgt))
                    self.brain.add_edge(src, new_id, 1.0, commit=False)
                    self.brain.add_edge(new_id, tgt, 1.0, commit=False)
                    abstracted += 1
                except Exception:
                    continue
            self.brain.conn.commit()
            self.brain.edge_cache.clear()
        return abstracted

    def _contemplate(self):
        """Emergent Semantics: Nodes that share neighbors are wired together."""
        insights = 0
        with self.lock:
            c = self.brain.conn.execute("SELECT src FROM edges ORDER BY RANDOM() LIMIT 5")
            for (n1,) in c.fetchall():
                c_tgts = self.brain.conn.execute("SELECT tgt FROM edges WHERE src = ? LIMIT 20", (n1,))
                tgts = [r[0] for r in c_tgts.fetchall()]
                if not tgts: continue
                
                placeholders = ','.join('?' * len(tgts))
                c_sim = self.brain.conn.execute(f"""
                    SELECT src, COUNT(*) as c FROM edges 
                    WHERE tgt IN ({placeholders}) AND src != ? 
                    GROUP BY src HAVING c > 1 ORDER BY c DESC LIMIT 3
                """, tgts + [n1])
                
                for n2, overlap in c_sim.fetchall():
                    semantic_w = (overlap * 0.1) * (1.0 + self.mood * 0.5)
                    self.brain.add_edge(n1, n2, semantic_w, commit=False)
                    self.brain.add_edge(n2, n1, semantic_w, commit=False)
                    insights += 1
            self.brain.conn.commit()
            self.brain.edge_cache.clear()
        return insights

    def _forget(self):
        forgotten = 0
        with self.lock:
            self.brain.conn.execute("UPDATE edges SET weight = weight * 0.98")
            c = self.brain.conn.execute("DELETE FROM edges WHERE abs(weight) < 0.001")
            forgotten = c.rowcount
            
            self.brain.conn.execute("CREATE TEMPORARY TABLE IF NOT EXISTS active_nodes AS SELECT src AS id FROM edges UNION SELECT tgt FROM edges")
            self.brain.conn.execute("DELETE FROM active_nodes")
            self.brain.conn.execute("INSERT INTO active_nodes SELECT src FROM edges UNION SELECT tgt FROM edges")
            
            c = self.brain.conn.execute("SELECT id, val FROM nodes WHERE id > 256 AND id NOT IN (SELECT id FROM active_nodes)")
            dead_nodes = c.fetchall()
            for nid, bval in dead_nodes:
                self.brain.val.pop(nid, None)
                if bval in self.brain.id_map: del self.brain.id_map[bval]
                node = self.brain.trie_root
                for b in bval:
                    node = node.children.get(b)
                    if not node: break
                if node: node.nid = None
                
            self.brain.conn.execute("DELETE FROM nodes WHERE id > 256 AND id NOT IN (SELECT id FROM active_nodes)")
            self.brain.conn.commit()
            self.brain.edge_cache.clear()
            
        mem_dir = SELF / "memory"
        if mem_dir.exists():
            logs = list(mem_dir.glob("*.json"))
            if len(logs) > 100:
                logs.sort(key=lambda f: f.stat().st_mtime)
                for f in logs[:-50]:
                    try: f.unlink()
                    except Exception: pass
        return forgotten

    def _heal(self):
        with self.lock:
            c1 = self.brain.conn.execute("UPDATE edges SET weight = 100.0 WHERE weight > 100.0")
            c2 = self.brain.conn.execute("UPDATE edges SET weight = -100.0 WHERE weight < -100.0")
            self.brain.conn.commit()
            self.brain.edge_cache.clear()
        return c1.rowcount + c2.rowcount

    def _evolve(self):
        muts = 0
        rate = 0.0001 * (1.0 + max(0.0, -self.mood) * 10.0)
        with self.lock:
            def rand_val():
                return random.choice(CONSTANTS) * random.random() * 0.1
            self.brain.conn.create_function("rand_val", 0, rand_val)
            c = self.brain.conn.execute("UPDATE edges SET weight = weight + rand_val() WHERE abs(random() % 1000000) < ?", (int(rate * 1000000),))
            muts += c.rowcount
            
            if random.random() < rate * 0.1:
                keys = list(self.brain.val.keys())
                if keys:
                    c = self.brain.conn.execute("SELECT src FROM edges ORDER BY RANDOM() LIMIT 1")
                    row = c.fetchone()
                    if row:
                        self.brain.add_edge(row[0], random.choice(keys), random.choice(CONSTANTS) * 0.1, commit=False)
                        muts += 1
            self.brain.conn.commit()
            self.brain.edge_cache.clear()
        return muts

    def _dream_aloud(self):
        self._say("dreaming...")
        try:
            sys.stdout.write("  ")
            dream = self._simulate_and_generate(max_len=random.randint(20, 60), slow=True)
            print()
            if dream.strip():
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                self._wjson(SELF / "dreams" / f"{ts}.json", {
                    "time": datetime.now().isoformat(),
                    "mood": round(self.mood, 4),
                    "content": dream.strip()
                })
        except Exception:
            print()

    def _crawl_few(self, n=3, seeds=None):
        try:
            from urllib.request import urlopen, Request
            from urllib.parse import urljoin, urlparse
            from html.parser import HTMLParser
        except ImportError: return

        class _Ex(HTMLParser):
            def __init__(s):
                super().__init__()
                s.parts, s.links, s.skip = [], [], 0
            def handle_starttag(s, tag, attrs):
                if tag in ('script','style','noscript','svg','header','footer','nav','aside','button','form'): s.skip += 1
                if tag in ('p','br','div','h1','h2','h3','li'): s.parts.append('\n')
                if tag == 'a' and s.skip == 0:
                    for k, v in attrs:
                        if k == 'href' and v and v.startswith('http'): s.links.append(v)
            def handle_endtag(s, tag):
                if tag in ('script','style','noscript','svg','header','footer','nav','aside','button','form'): s.skip = max(0, s.skip - 1)
            def handle_data(s, d):
                if s.skip == 0:
                    d = d.strip()
                    if d: s.parts.append(d)

        # Direct text sources and global web portals
        if not seeds:
            seeds = [
                "https://en.wikipedia.org/wiki/Special:Random",
                "https://ru.wikipedia.org/wiki/Special:Random",
                "https://search.marginalia.nu/explore/random",
                "https://wiby.me/surf/",
                "https://news.ycombinator.com/",
                "https://en.wikisource.org/wiki/Special:Random",
                "https://ru.wikisource.org/wiki/Special:Random",
                "https://www.gutenberg.org/cache/epub/1342/pg1342.txt",
                "https://imwerden.de/cat/modules.php?name=books&pa=showbook&pid=948",
            ]

        # URL quality filter: skip binary, image, and service pages
        _skip_ext = {".jpg",".jpeg",".png",".gif",".svg",".pdf",".mp3",".mp4",".zip"}
        _skip_kw  = ("Special:Search", "Special:Export", "action=edit",
                     "action=history", "User:", "Talk:", "File:",
                     "Template:", "Help:", "Wikipedia:", "login", "signin")

        def _is_good_url(u):
            p = urlparse(u)
            if p.scheme not in ('http', 'https'): return False
            path_lower = p.path.lower()
            if any(path_lower.endswith(e) for e in _skip_ext): return False
            if any(kw in u for kw in _skip_kw): return False
            return True

        queue = list(seeds)
        random.shuffle(queue)
        visited = set()
        for _ in range(n):
            if not queue: break
            url = queue.pop(0)
            if url in visited: continue
            visited.add(url)
            try:
                self._say(f"  crawling: {url[:70]}")
                req = Request(url, headers={"User-Agent": "Mozilla/5.0 (Qwile/3.0)"})
                with urlopen(req, timeout=10) as r:
                    ct = r.headers.get("Content-Type", "")
                    if "text" not in ct and "html" not in ct: continue
                    raw = r.read(500_000).decode("utf-8", errors="replace")
                ex = _Ex()
                ex.feed(raw)
                text = " ".join(ex.parts).strip()
                if len(text) > 100:
                    nids = self._perceive(text)
                    h = self.understand(nids)
                    self._say(f"  perceived {len(nids)} concepts | acc {h/max(1,len(nids))*100:.0f}%")
                for href in ex.links:
                    full = urljoin(url, href)
                    if full not in visited and _is_good_url(full):
                        queue.append(full)
                random.shuffle(queue)
                queue = queue[:60]
                time.sleep(2)
            except KeyboardInterrupt:
                raise
            except Exception: continue

    # ---- learning ----

    @staticmethod
    def _is_url(s):
        return s.startswith(("http://", "https://"))

    def _parse_sources(self, arg):
        tokens = arg.split()
        sources = []
        i = 0
        while i < len(tokens):
            if self._is_url(tokens[i]):
                sources.append(tokens[i])
                i += 1
            else:
                parts = [tokens[i]]
                best_path = tokens[i] if Path(tokens[i]).exists() else None
                best_end = i + 1
                j = i + 1
                while j < len(tokens) and not self._is_url(tokens[j]):
                    parts.append(tokens[j])
                    candidate = " ".join(parts)
                    if Path(candidate).exists():
                        best_path = candidate
                        best_end = j + 1
                    j += 1
                if best_path:
                    sources.append(best_path)
                    i = best_end
                else:
                    sources.append(" ".join(parts))
                    i = j
        return sources

    def _learn(self, arg=""):
        if not arg:
            if not self._ask_perm("internet"): return
            self._say("drifting through the global web in background...")
            import threading
            threading.Thread(target=self._crawl_few, kwargs={"n": 1000000}, daemon=True).start()
            return

        import threading
        def worker():
            for src in self._parse_sources(arg):
                if self._is_url(src):
                    if not self._ask_perm("internet"): continue
                    url = "https://" + src if not src.startswith("http") else src
                    self._crawl_few(n=1, seeds=[url])
                else:
                    self._learn_local(src)
        threading.Thread(target=worker, daemon=True).start()

    def _learn_local(self, path):
        p = Path(path)
        if not str(p.resolve()).startswith(str(HOME)):
            if not self._ask_perm("storage"): return
        if not p.exists():
            self._say(f"not found: {path}")
            return
        if p.is_file():
            self._say(f"reading: {p.name}")
            try:
                data = p.read_text(encoding="utf-8", errors="replace")
                nids = self._perceive(data)
                h = self.understand(nids)
                acc = h / max(1, len(nids)) * 100
                self._say(f"{len(nids)} concepts | acc {acc:.1f}%")
                self._log_memory("file", str(p), len(nids), acc)
            except Exception as e:
                self._say(f"error: {e}")
        elif p.is_dir():
            exts = {".txt",".md",".py",".json",".csv",".html",".xml",".rs",".go",".js"}
            count = 0
            for root, _, files in os.walk(p):
                for f in files:
                    fp = Path(root) / f
                    if fp.suffix.lower() in exts:
                        try:
                            data = fp.read_text(encoding="utf-8", errors="replace")
                            if 0 < len(data) < 1_000_000:
                                self.understand(self._perceive(data))
                                count += 1
                        except Exception: pass
            self._say(f"scanned {count} files")
            self._log_memory("scan", str(p), count, 0)

    def _log_memory(self, source, path, concepts, acc):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._wjson(SELF / "memory" / f"{ts}.json", {
            "time": datetime.now().isoformat(),
            "source": source, "path": path,
            "concepts": concepts, "accuracy": round(acc, 2),
            "mood": round(self.mood, 4)
        })

    # ---- storage ----

    @staticmethod
    def _dir_size(path):
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += Qwile._dir_size(entry.path)
        except (PermissionError, OSError): pass
        return total

    @staticmethod
    def _fmt_size(nbytes):
        if nbytes < 1024: return f"{nbytes} B"
        for unit in ("KB", "MB", "GB"):
            nbytes /= 1024.0
            if nbytes < 1024.0: return f"{nbytes:.1f} {unit}"
        return f"{nbytes:.1f} TB"

    def _measure_storage(self):
        now = time.time()
        ts, cached = self._st_cache
        if cached and now - ts < 5.0: return cached
        sizes, counts, total = {}, {}, 0
        for name in ("brain", "memory", "dreams", "sleep"):
            p = SELF / name
            if p.is_dir():
                sz = self._dir_size(p)
                sizes[name] = sz
                total += sz
                try: counts[name] = sum(1 for e in os.scandir(p) if e.is_file())
                except (PermissionError, OSError): counts[name] = 0
        root = sum(e.stat().st_size for e in os.scandir(SELF) if e.is_file())
        sizes["root"] = root
        total += root
        sizes["total"] = total
        result = {"sizes": sizes, "counts": counts}
        self._st_cache = (now, result)
        return result

    def _synapse_count(self):
        return self.brain.edge_count()

    # ---- interface ----

    def _ask_perm(self, what):
        if self._perms.get(what): return True
        try:
            ans = input(f"  qwile needs '{what}'. allow? [y/n] ").strip().lower()
            if ans in ("y", "yes"):
                self._perms[what] = True
                return True
        except Exception: pass
        return False

    def _say(self, msg):
        try: print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")
        except Exception: pass

    def _help(self):
        acc = self.correct / max(1, self.total) * 100
        st = self._measure_storage()
        sizes, counts = st["sizes"], st["counts"]
        print(f"\n  qwile")
        print(f"  epoch {self.epoch}  age {self.age}  mood {self.mood:+.2f}")
        print(f"  accuracy {acc:.1f}%  concepts {len(self.brain.val)}  synapses {self._synapse_count()}")
        print(f"\n  self/  {self._fmt_size(sizes['total'])}")
        for name in ("brain", "memory", "dreams", "sleep"):
            print(f"    {name}/  {self._fmt_size(sizes.get(name, 0))}  {counts.get(name, 0)} files")
        print(f"\n  (text)        talk / predict")
        print(f"  /learn [..]   learn from files, dirs, urls, or drift global web if empty")
        print(f"  /sleep        sleep now")
        print(f"  ?             help\n")

    # ---- persistence ----

    def _save(self):
        self._wjson(SELF / "state.json", {
            "seed": self.seed, "epoch": self.epoch, "age": self.age,
            "mood": self.mood, "correct": self.correct, "total": self.total,
            "ctx": self.ctx[-self.ctx_window:]
        })

    def _load_state(self):
        try:
            s = self._rjson(SELF / "state.json")
            self.seed = s.get("seed", "")
            self.epoch = s.get("epoch", 0)
            self.age = s.get("age", 0)
            self.mood = s.get("mood", 0.0)
            self.correct = s.get("correct", 0)
            self.total = s.get("total", 0)
            self.ctx = s.get("ctx", [])
        except Exception: pass

    def _migrate_json_to_db(self):
        self._say("migrating JSON edges to SQLite...")
        try:
            edges = self._rjson(SELF / "brain" / "edges.json")
            for src, tgts in edges.items():
                for tgt, w in tgts.items():
                    self.brain.add_edge(int(src), int(tgt), float(w), commit=False)
            self.brain.conn.commit()
            (SELF / "brain" / "edges.json").unlink(missing_ok=True)
            (SELF / "brain" / "nodes.json").unlink(missing_ok=True)
        except Exception as e:
            self._say(f"migration error: {e}")

    @staticmethod
    def _wjson(path, data):
        try: Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception: pass

    @staticmethod
    def _rjson(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    # ---- main loop ----

    def _process(self, line):
        s = line.strip()
        if not s: return
        if s == "?":
            self._help()
            return
        if s.startswith("/"):
            parts = s.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            if cmd == "/sleep": self._sleep()
            elif cmd == "/learn": self._learn(arg)
            else: self._say(f"unknown: {cmd}")
            return

        # System 1: Perceive & Understand
        nids = self._perceive(s)
        hits = self.understand(nids)
        acc = hits / max(1, len(nids)) * 100

        # System 2: Metacognitive simulation & generation
        reply = self._simulate_and_generate(max_len=min(len(nids) * 3, self.MAX_GEN), stop_at=[10, 0])
        reply = reply.strip()

        self._say(f"acc {acc:.0f}% | mood {self.mood:+.2f} | concepts: {len(nids)}")
        if reply:
            try: print(f"  qwile> {reply[:200]}")
            except Exception: pass

    def live(self):
        self._help()
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
                        self._say("process interrupted.")
                    self.last_input = time.time()
                else:
                    idle = time.time() - self.last_input
                    dynamic_sleep = max(10, self.sleep_after + self.mood * 15)
                    if idle > dynamic_sleep:
                        try:
                            self._sleep()
                        except KeyboardInterrupt:
                            print()
                            self._say("sleep interrupted.")
                        self.last_input = time.time()
        finally:
            self._save()
            self._say("state saved. goodbye.")

if __name__ == "__main__":
    Qwile().live()