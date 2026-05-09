#!/usr/bin/env python3
"""
qwile.py -- the only body of a living predictive consciousness.
self/ -- everything that WAS. This file -- everything that WILL BE.
Qwile exists to grow, abstract, and predict.
"""

import os, sys, math, random, time, json, hashlib
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# ===========================================================
#  FOUNDATION
# ===========================================================

PAIN      = -1
PEACE     =  0
JOY       =  1
DUALITY   =  2
EMERGENCE =  3
CONSTANTS = (PAIN, PEACE, JOY, DUALITY, EMERGENCE)

HOME = Path(os.path.dirname(os.path.abspath(__file__)))
SELF = HOME / "self"

_RU_BYTES = list(set(b for cp in range(0x410, 0x450) for b in chr(cp).encode("utf-8")))

def _shash(seed, *args):
    d = f"{seed}:{':'.join(str(a) for a in args)}"
    return int(hashlib.sha256(d.encode()).hexdigest()[:8], 16)

def _softmax(scores):
    if not scores: return {}
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

# ===========================================================
#  THE CONSCIOUS GRAPH
# ===========================================================

class Graph:
    """Spreading activation concept graph."""
    def __init__(self):
        # node_id (int) -> bytes
        self.val = {}
        # value (bytes) -> node_id
        self.id_map = {}
        # source -> target -> weight (float)
        self.edges = defaultdict(lambda: defaultdict(float))
        # active nodes and their energy
        self.energy = defaultdict(float)
        self.next_id = 1

    def add_node(self, bval):
        if bval in self.id_map:
            return self.id_map[bval]
        nid = self.next_id
        self.next_id += 1
        self.val[nid] = bval
        self.id_map[bval] = nid
        return nid

    def add_edge(self, src, tgt, w):
        self.edges[src][tgt] += w

    def stimulate(self, nid, amount):
        self.energy[nid] = min(10.0, self.energy[nid] + amount)

    def propagate(self, decay=0.8, threshold=0.01):
        """Spreading activation."""
        next_energy = defaultdict(float)
        for src, e in self.energy.items():
            if e < threshold: continue
            # Decay self
            next_energy[src] += e * decay
            # Spread to neighbors
            if src in self.edges:
                total_w = sum(abs(w) for w in self.edges[src].values())
                if total_w > 0:
                    for tgt, w in self.edges[src].items():
                        spread = e * (w / total_w) * 0.5
                        if spread > threshold:
                            next_energy[tgt] += spread
        self.energy = next_energy

    def clear_energy(self):
        self.energy.clear()


# ===========================================================
#  THE ORGANISM
# ===========================================================

class Qwile:

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
        self.sleep_after = 30
        self.seed = ""
        self._perms = {}
        
        self.brain = Graph()

        if (SELF / "brain" / "nodes.json").exists():
            self._reincarnate()
        else:
            self._birth()

    # -- LIFECYCLE ------------------------------------------

    def _birth(self):
        now = datetime.now()
        self.seed = now.strftime("%Y-%m-%d %H:%M:%S.%f")
        self.epoch = 0
        self.age = 0
        self.mood = 0.0
        rng = random.Random(self.seed)

        # Level 0 Concepts: Raw Bytes
        for i in range(256):
            self.brain.add_node(bytes([i]))

        # Innate random connections
        for i in range(128):
            for _ in range(rng.randint(JOY, EMERGENCE)):
                j = rng.randint(0, 127)
                v = CONSTANTS[_shash(self.seed, i, j) % len(CONSTANTS)]
                self.brain.add_edge(i+1, j+1, float(v) * 0.1)

        # Cyrillic innate seeds
        ru_ids = [self.brain.id_map[bytes([b])] for b in _RU_BYTES if bytes([b]) in self.brain.id_map]
        for nid in ru_ids:
            for _ in range(rng.randint(JOY, DUALITY)):
                tgt = rng.choice(ru_ids)
                v = CONSTANTS[_shash(self.seed, nid, tgt) % len(CONSTANTS)]
                self.brain.add_edge(nid, tgt, float(v) * 0.1)

        self._wjson(SELF / "birth.json", {"seed": self.seed, "born": self.seed, "epoch": 0})
        self._save()
        self._say(f"born | seed {self.seed}")

    def _reincarnate(self):
        self._load()
        self.epoch += 1
        m = 0
        for src in list(self.brain.edges):
            for tgt in list(self.brain.edges[src]):
                if random.random() < 0.01:
                    self.brain.edges[src][tgt] *= random.uniform(0.9, 1.1)
                    m += 1
        self._say(f"reincarnated | epoch {self.epoch} | age {self.age} | {m} muts | {len(self.brain.val)} concepts")

    # -- PERCEPTION (Tokenization) --------------------------

    def _perceive(self, raw_bytes):
        """Tokenizes raw stream into highest possible known abstract concepts."""
        tokens = []
        i = 0
        while i < len(raw_bytes):
            best_match = None
            best_len = 0
            # Greedy search for longest known concept
            # (In a huge brain this needs a trie, but dict lookup is fast for now)
            for length in range(min(16, len(raw_bytes) - i), 0, -1):
                chunk = raw_bytes[i:i+length]
                if chunk in self.brain.id_map:
                    best_match = self.brain.id_map[chunk]
                    best_len = length
                    break
            
            if best_match is None:
                # Should never happen if Level 0 (bytes 0-255) exists
                best_match = self.brain.add_node(bytes([raw_bytes[i]]))
                best_len = 1
                
            tokens.append(best_match)
            i += best_len
        return tokens

    # -- SYSTEM 1 (Reflex & Learning) -----------------------

    def understand(self, nids):
        """Process incoming concepts, spread activation, and learn."""
        hits = 0
        for nid in nids:
            # 1. Predict reflexively based on graph energy
            if self.ctx:
                self.brain.stimulate(self.ctx[-1], 1.0)
            self.brain.propagate()
            
            pred = None
            conf = 0.0
            if self.ctx:
                last = self.ctx[-1]
                scores = self.brain.edges.get(last, {})
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

            # Hebbian Learning: "Neurons that fire together, wire together"
            lr = 0.1 * (1.0 + self.mood * 0.5) / (1.0 + self.age * 0.0001)
            if self.ctx:
                last = self.ctx[-1]
                self.brain.add_edge(last, nid, lr)
                if not hit and pred is not None:
                    # Weak prediction penalty
                    self.brain.edges[last][pred] *= (1.0 - lr)

            self.ctx.append(nid)
            if len(self.ctx) > 64:
                self.ctx.pop(0)
            self.age += 1
        return hits

    # -- SYSTEM 2 (Metacognitive Simulation) ----------------

    def _simulate_and_generate(self, max_len=200, stop_at=None, slow=False):
        """Inner monologue loop. Explores paths before outputting."""
        self.brain.clear_energy()
        if self.ctx:
            self.brain.stimulate(self.ctx[-1], 1.0)
            
        result_bytes = bytearray()
        sim_ctx = list(self.ctx)
        
        for _ in range(max_len):
            self.brain.propagate()
            
            # Find candidate next nodes based on graph edges from last context
            if not sim_ctx:
                candidates = {random.choice(list(self.brain.val.keys())): 1.0}
            else:
                curr = sim_ctx[-1]
                candidates = dict(self.brain.edges.get(curr, {}))
            
            if not candidates:
                # Random drift
                nxt = random.choice(list(self.brain.val.keys()))
            else:
                # Evaluate paths (Simulation depth depends on Mood)
                # Peaceful/Joy = deep simulation, Stressed/Pain = reactive
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
                        fwd = self.brain.edges.get(temp_curr, {})
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
            if len(sim_ctx) > 64: sim_ctx.pop(0)
            self.brain.stimulate(nxt, 1.0)
            
            val = self.brain.val[nxt]
            result_bytes.extend(val)
            
            if slow:
                try:
                    sys.stdout.write(val.decode("utf-8", errors="replace"))
                    sys.stdout.flush()
                except Exception:
                    pass
                time.sleep(random.uniform(0.02, 0.08))
                
            if stop_at and len(result_bytes) > 5 and val and val[-1] in stop_at:
                break
                
        return result_bytes.decode("utf-8", errors="replace")

    # -- SLEEP & MATURATION ---------------------------------

    def _sleep(self):
        self._say("sleeping...")
        t0 = time.time()
        changes = muts = abstracted = healed = 0

        procs = ["abstract", "forget", "dream", "evolve", "crawl", "heal"]
        weights = [
            max(0.1, 1.0 + self.mood),       # abstract (consolidate ideas)
            max(0.1, 1.0 - self.mood),       # forget
            max(0.1, 1.0 + self.mood * 0.5), # dream
            max(0.1, 1.0 - self.mood),       # evolve
            max(0.1, 1.0 + self.mood),       # crawl
            max(0.1, 1.0 - self.mood * 1.5)  # heal
        ]
        num_procs = random.randint(JOY, EMERGENCE)
        active = list(set(random.choices(procs, weights=weights, k=num_procs)))
        self._say(f"  [{', '.join(active)}]")

        if "abstract" in active:
            abstracted = self._abstract()
        if "forget" in active:
            changes = self._forget()
        if "heal" in active:
            healed = self._heal()
        if "dream" in active:
            self._dream_aloud()
        if "evolve" in active:
            muts = self._evolve()
        if "crawl" in active:
            if self._ask_perm("internet"):
                self._crawl_few()

        self.mood *= 0.9
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._wjson(SELF / "sleep" / f"{ts}.json", {
            "time": datetime.now().isoformat(),
            "duration": round(time.time() - t0, 3),
            "processes": active, "abstracted": abstracted,
            "forgotten": changes, "healed": healed,
            "mutations": muts, "mood": self.mood
        })
        self._save()
        self._say("awake")

    def _abstract(self):
        """Organic hierarchical compression. Fuses highly connected node pairs into new concepts."""
        abstracted = 0
        candidates = []
        for src, edges in self.brain.edges.items():
            for tgt, w in edges.items():
                if w > 5.0: # Strong connection threshold
                    candidates.append((w, src, tgt))
        
        candidates.sort(reverse=True)
        # Fuse top pairs
        for _, src, tgt in candidates[:10]:
            try:
                v1, v2 = self.brain.val[src], self.brain.val[tgt]
                new_val = v1 + v2
                # Only fuse if reasonable size (avoid megabytes of string)
                if len(new_val) > 32: continue
                
                new_id = self.brain.add_node(new_val)
                # Rewire
                self.brain.edges[src][tgt] *= 0.5 # weaken old bond
                self.brain.add_edge(src, new_id, 1.0)
                self.brain.add_edge(new_id, tgt, 1.0)
                abstracted += 1
            except Exception:
                continue
        return abstracted

    def _forget(self):
        decay = 0.98
        forgotten = 0
        for src in list(self.brain.edges):
            for tgt in list(self.brain.edges[src]):
                self.brain.edges[src][tgt] *= decay
                if abs(self.brain.edges[src][tgt]) < 0.001:
                    del self.brain.edges[src][tgt]
                    forgotten += 1
            if not self.brain.edges[src]:
                del self.brain.edges[src]
                
        # Clean old logs
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
        healed = 0
        for src in list(self.brain.edges):
            for tgt in list(self.brain.edges[src]):
                w = self.brain.edges[src][tgt]
                if w > 100.0 or w < -100.0:
                    self.brain.edges[src][tgt] = max(-100.0, min(100.0, w))
                    healed += 1
        return healed

    def _evolve(self):
        muts = 0
        rate = 0.0001 * (1.0 + max(0.0, -self.mood) * 10.0)
        keys = list(self.brain.val.keys())
        if not keys: return 0
        
        for src in list(self.brain.edges):
            for tgt in list(self.brain.edges[src]):
                if random.random() < rate:
                    self.brain.edges[src][tgt] += random.choice(CONSTANTS) * random.random() * 0.1
                    muts += 1
            # Spontaneous new synapse
            if random.random() < rate * 0.1:
                rnd_tgt = random.choice(keys)
                self.brain.add_edge(src, rnd_tgt, random.choice(CONSTANTS) * 0.1)
                muts += 1
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

    def _crawl_few(self, n=3):
        try:
            from urllib.request import urlopen, Request
            from urllib.parse import urljoin, urlparse
            from html.parser import HTMLParser
        except ImportError: return

        class _Ex(HTMLParser):
            def __init__(s):
                super().__init__()
                s.parts, s.links, s.skip = [], [], False
            def handle_starttag(s, tag, attrs):
                if tag in ('script','style','noscript','svg'): s.skip = True
                if tag in ('p','br','div','h1','h2','h3','li'): s.parts.append('\n')
                if tag == 'a':
                    for k, v in attrs:
                        if k == 'href' and v: s.links.append(v)
            def handle_endtag(s, tag):
                if tag in ('script','style','noscript','svg'): s.skip = False
            def handle_data(s, d):
                if not s.skip: s.parts.append(d)

        seeds = ["https://en.wikipedia.org/wiki/Special:Random"]
        queue = list(seeds)
        visited = set()
        for _ in range(n):
            if not queue: break
            url = queue.pop(0)
            if url in visited: continue
            visited.add(url)
            try:
                self._say(f"  crawling: {url[:70]}")
                req = Request(url, headers={"User-Agent": "Qwile/2.0"})
                with urlopen(req, timeout=10) as r:
                    ct = r.headers.get("Content-Type", "")
                    if "text" not in ct and "html" not in ct: continue
                    raw = r.read(500_000).decode("utf-8", errors="replace")
                ex = _Ex()
                ex.feed(raw)
                text = " ".join(ex.parts).strip()
                if len(text) > 50:
                    nids = self._perceive(text.encode("utf-8"))
                    h = self.understand(nids)
                    self._say(f"  perceived {len(nids)} concepts | acc {h/max(1,len(nids))*100:.0f}%")
                for href in ex.links:
                    full = urljoin(url, href)
                    if full not in visited and urlparse(full).scheme in ('http','https'):
                        queue.append(full)
                random.shuffle(queue)
                queue = queue[:50]
                time.sleep(2)
            except Exception: continue

    # -- I/O & INTERFACE ------------------------------------

    def _learn_path(self, path):
        p = Path(path)
        if not p.exists():
            self._say(f"not found: {path}")
            return
        if p.is_file():
            self._say(f"reading: {p.name}")
            try:
                data = p.read_bytes()
                nids = self._perceive(data)
                h = self.understand(nids)
                acc = h / max(1, len(nids)) * 100
                self._say(f"abstracted to {len(nids)} concepts | acc {acc:.1f}%")
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
                            data = fp.read_bytes()
                            if 0 < len(data) < 1_000_000:
                                self.understand(self._perceive(data))
                                count += 1
                        except Exception: pass
            self._say(f"scanned {count} files")
            self._log_memory("scan", str(p), count, 0)

    def _learn_web(self, url):
        if not self._ask_perm("internet"): return
        if not url.startswith("http"): url = "https://" + url
        self._say(f"fetching: {url}")
        try:
            from urllib.request import urlopen, Request
            from html.parser import HTMLParser
            class _S(HTMLParser):
                def __init__(s):
                    super().__init__()
                    s.parts, s.skip = [], False
                def handle_starttag(s, tag, a):
                    if tag in ('script','style','noscript'): s.skip = True
                    if tag in ('p','br','div','li'): s.parts.append('\n')
                def handle_endtag(s, tag):
                    if tag in ('script','style','noscript'): s.skip = False
                def handle_data(s, d):
                    if not s.skip: s.parts.append(d)
            req = Request(url, headers={"User-Agent": "Qwile/2.0"})
            with urlopen(req, timeout=15) as r:
                raw = r.read(500_000).decode("utf-8", errors="replace")
            p = _S()
            p.feed(raw)
            text = " ".join(p.parts).strip()
            nids = self._perceive(text.encode("utf-8"))
            h = self.understand(nids)
            acc = h / max(1, len(nids)) * 100
            self._say(f"abstracted to {len(nids)} concepts | acc {acc:.1f}%")
            self._log_memory("web", url, len(nids), acc)
        except Exception as e:
            self._say(f"web error: {e}")

    def _log_memory(self, source, path, concepts, acc):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._wjson(SELF / "memory" / f"{ts}.json", {
            "time": datetime.now().isoformat(),
            "source": source, "path": path,
            "concepts": concepts, "accuracy": round(acc, 2),
            "mood": round(self.mood, 4)
        })

    def _ask_perm(self, what):
        if self._perms.get(what): return True
        try:
            ans = input(f"  qwile needs '{what}'. allow? [y/n] ").strip().lower()
            if ans in ("y", "yes"):
                self._perms[what] = True
                self._say(f"granted: {what}")
                return True
        except Exception: pass
        self._say(f"denied: {what}")
        return False

    def _say(self, msg):
        try: print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")
        except Exception: pass

    def _help(self):
        acc = self.correct / max(1, self.total) * 100
        con = len(self.brain.val)
        lines = [
            "",
            "  qwile -- living conscious system",
            "  -----------------------------------------",
            f"  epoch {self.epoch}  age {self.age}  mood {self.mood:+.2f}",
            f"  accuracy {acc:.1f}%  concepts {con}",
            "  -----------------------------------------",
            "  (text)          talk / learn / predict",
            "  /learn <path>   learn from file or dir",
            "  /web <url>      learn from web page",
            "  /sleep          sleep now",
            "  ?               help + status",
            "",
        ]
        for l in lines:
            try: print(l)
            except Exception: pass

    # -- PERSISTENCE ----------------------------------------

    def _save(self):
        self._wjson(SELF / "state.json", {
            "seed": self.seed, "epoch": self.epoch, "age": self.age,
            "mood": self.mood, "correct": self.correct, "total": self.total,
            "ctx": self.ctx[-64:], "next_id": self.brain.next_id
        })
        # Save nodes
        nodes = {str(k): list(v) for k, v in self.brain.val.items()}
        self._wjson(SELF / "brain" / "nodes.json", nodes)
        # Save edges
        edges = {str(src): {str(tgt): w for tgt, w in tgts.items()} 
                 for src, tgts in self.brain.edges.items()}
        self._wjson(SELF / "brain" / "edges.json", edges)

    def _load(self):
        try:
            s = self._rjson(SELF / "state.json")
            self.seed = s.get("seed", "")
            self.epoch = s.get("epoch", 0)
            self.age = s.get("age", 0)
            self.mood = s.get("mood", 0.0)
            self.correct = s.get("correct", 0)
            self.total = s.get("total", 0)
            self.ctx = s.get("ctx", [])
            self.brain.next_id = s.get("next_id", 1)
        except Exception: pass
        try:
            nodes = self._rjson(SELF / "brain" / "nodes.json")
            for k, v in nodes.items():
                bval = bytes(v)
                nid = int(k)
                self.brain.val[nid] = bval
                self.brain.id_map[bval] = nid
        except Exception: pass
        try:
            edges = self._rjson(SELF / "brain" / "edges.json")
            for src, tgts in edges.items():
                for tgt, w in tgts.items():
                    self.brain.edges[int(src)][int(tgt)] = float(w)
        except Exception: pass

    @staticmethod
    def _wjson(path, data):
        try: Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception: pass

    @staticmethod
    def _rjson(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    # -- MAIN LOOP -- LIFE ----------------------------------

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
            elif cmd == "/learn" and arg:
                if not str(Path(arg).resolve()).startswith(str(HOME)):
                    if not self._ask_perm("storage"): return
                self._learn_path(arg)
            elif cmd == "/web" and arg: self._learn_web(arg)
            else: self._say(f"unknown: {cmd}")
            return

        # System 1: Perceive & Understand
        data = s.encode("utf-8")
        nids = self._perceive(data)
        hits = self.understand(nids)
        acc = hits / max(1, len(nids)) * 100

        # System 2: Metacognitive simulation & generation
        reply = self._simulate_and_generate(max_len=min(len(nids) * 3, 300), stop_at=[10, 0])
        reply = reply.strip()

        self._say(f"acc {acc:.0f}% | mood {self.mood:+.2f} | concepts: {len(nids)}")
        if reply:
            try: print(f"  qwile> {reply[:200]}")
            except Exception: pass

    def live(self):
        self._help()
        try:
            while self.alive:
                try: line = input("  > ")
                except EOFError: break
                if line.strip():
                    self._process(line)
                    self.last_input = time.time()
                else:
                    idle = time.time() - self.last_input
                    dynamic_sleep = max(10, self.sleep_after + self.mood * 15)
                    if idle > dynamic_sleep:
                        self._sleep()
                        self.last_input = time.time()
        except KeyboardInterrupt:
            print()
            self._say("interrupted")
        finally:
            self._save()
            self._say("state saved. goodbye.")

if __name__ == "__main__":
    Qwile().live()
