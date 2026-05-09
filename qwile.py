#!/usr/bin/env python3
"""
qwile.py -- the only body of a living predictive system.
self/ -- everything that WAS. This file -- everything that WILL BE.
Qwile exists to predict what comes next. That is its only purpose.
"""

import os, sys, math, random, time, json, hashlib
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# ===========================================================
#  FOUNDATION -- five constants from which everything arises
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

def _softmax(scores):
    if not scores:
        return {}
    mx = max(scores.values())
    es = {k: math.exp(min(v - mx, 50)) for k, v in scores.items()}
    t = sum(es.values())
    return {k: v / t for k, v in es.items()} if t > 0 else {k: 1/len(es) for k in es}

def _choose(probs):
    r = random.random()
    c = 0.0
    for k, p in probs.items():
        c += p
        if r <= c:
            return k
    return list(probs.keys())[-1]

def _shash(seed, *args):
    d = f"{seed}:{':'.join(str(a) for a in args)}"
    return int(hashlib.sha256(d.encode()).hexdigest()[:8], 16)


class Qwile:

    def __init__(self):
        for d in [SELF, SELF/"memory", SELF/"dreams", SELF/"sleep", SELF/"corpus"]:
            d.mkdir(parents=True, exist_ok=True)

        self.alive = True
        self.mood = 0.0
        self.age = 0
        self.epoch = 0
        self.ctx = []
        self.ctx_depth = EMERGENCE
        self.max_ctx = 128
        self.correct = 0
        self.total = 0
        self.last_input = time.time()
        self.sleep_after = 30
        self.seed = ""
        self.synapses = defaultdict(dict)
        self.ngrams = defaultdict(int)
        self._perms = {}

        if (SELF / "identity.json").exists():
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

        for i in range(128):
            for _ in range(rng.randint(JOY, EMERGENCE)):
                j = rng.randint(0, 127)
                v = CONSTANTS[_shash(self.seed, i, j) % len(CONSTANTS)]
                self.synapses[(i,)][j] = [float(v) * 0.1, 0.0]

        for b in _RU_BYTES:
            for _ in range(rng.randint(JOY, DUALITY)):
                j = rng.choice(_RU_BYTES)
                v = CONSTANTS[_shash(self.seed, b, j) % len(CONSTANTS)]
                self.synapses[(b,)][j] = [float(v) * 0.1, 0.0]

        self._wjson(SELF / "birth.json", {"seed": self.seed, "born": self.seed, "epoch": 0})
        self._save()
        self._say(f"born | seed {self.seed}")

    def _reincarnate(self):
        self._load()
        self.epoch += 1
        m = 0
        for key in list(self.synapses):
            for b in list(self.synapses[key]):
                if random.random() < 0.01:
                    self.synapses[key][b][0] *= random.uniform(0.9, 1.1)
                    m += 1
        self._say(f"reincarnated | epoch {self.epoch} | age {self.age} | {m} mutations")

    # -- THREE OPERATIONS -----------------------------------

    def receive(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.last_input = time.time()
        return list(data)

    def understand(self, bv):
        pred, conf = self._predict()
        hit = (pred == bv)
        self.total += 1
        if hit:
            self.correct += 1
        if hit:
            self.mood = min(1.0, self.mood + 0.08 * (1.0 - conf))
        else:
            self.mood = max(-1.0, self.mood - 0.04 * max(0.1, conf))
        self.mood *= 0.998

        lr = self._lr()
        for d in range(1, min(len(self.ctx) + 1, self.ctx_depth + 1)):
            key = tuple(self.ctx[-d:])
            if bv not in self.synapses[key]:
                self.synapses[key][bv] = [0.0, 0.0]
            self.synapses[key][bv][0] += lr * (1 + d * 0.1)
            self.synapses[key][bv][1] += self.mood * 0.01
            if not hit and pred is not None and pred in self.synapses[key]:
                self.synapses[key][pred][0] -= lr * 0.3

        self.ctx.append(bv)
        if len(self.ctx) > self.max_ctx:
            self.ctx.pop(0)
        for d in range(1, min(len(self.ctx) + 1, self.ctx_depth + 2)):
            self.ngrams[tuple(self.ctx[-d:])] += 1
        self.age += 1
        if self.age > 0 and self.age % 500 == 0 and self.ctx_depth < 24:
            self.ctx_depth += 1
        return pred, hit

    def respond(self, ctx=None):
        p, _ = self._predict(ctx)
        return p

    def _predict(self, ctx=None):
        if ctx is None:
            ctx = self.ctx
        if not ctx:
            return random.randint(0, 127), 0.0
        scores = defaultdict(float)
        for d in range(1, min(len(ctx) + 1, self.ctx_depth + 1)):
            key = tuple(ctx[-d:])
            if key in self.synapses:
                dw = d ** 1.5
                for bv, syn in self.synapses[key].items():
                    scores[bv] += (syn[0] + syn[1] * self.mood) * dw
        if not scores:
            return random.randint(0, 127), 0.0
        probs = _softmax(scores)
        temp = 1.0 - self.mood * 0.3
        pred = max(probs, key=probs.get) if temp < 0.5 else _choose(probs)
        return pred, probs.get(pred, 0.0)

    def _lr(self):
        return 0.1 * (1.0 + self.mood * 0.5) / (1.0 + self.age * 0.00001)

    # -- GENERATION -----------------------------------------

    def generate(self, max_len=200, stop_at=None, slow=False):
        ctx = list(self.ctx)
        result = []
        for _ in range(max_len):
            nxt = self.respond(ctx)
            result.append(nxt)
            ctx.append(nxt)
            if len(ctx) > self.max_ctx:
                ctx.pop(0)
            if slow:
                try:
                    ch = bytes([nxt]).decode("utf-8", errors="replace")
                    sys.stdout.write(ch)
                    sys.stdout.flush()
                except Exception:
                    pass
                time.sleep(random.uniform(0.03, 0.12))
            if stop_at and len(result) > 5 and nxt in stop_at:
                break
        return bytes(result).decode("utf-8", errors="replace")

    # -- SLEEP -- unified organic process -------------------
    # Randomly activates 1 to EMERGENCE(3) parallel processes

    def _sleep(self):
        self._say("sleeping...")
        t0 = time.time()
        changes = muts = forgotten = healed = 0

        procs = ["consolidate", "forget", "dream", "evolve", "crawl", "heal"]
        
        # Mood dynamically influences what the organism does in its sleep.
        # Pain/Stress (< 0) favors healing, forgetting, and evolving (adaptation).
        # Joy/Peace (> 0) favors consolidating, dreaming, and crawling (exploration).
        weights = [
            max(0.1, 1.0 + self.mood),       # consolidate
            max(0.1, 1.0 - self.mood),       # forget
            max(0.1, 1.0 + self.mood * 0.5), # dream
            max(0.1, 1.0 - self.mood),       # evolve
            max(0.1, 1.0 + self.mood),       # crawl
            max(0.1, 1.0 - self.mood * 1.5)  # heal
        ]
        
        num_procs = random.randint(JOY, EMERGENCE)
        active = list(set(random.choices(procs, weights=weights, k=num_procs)))
        self._say(f"  [{', '.join(active)}]")

        if "consolidate" in active:
            changes = self._consolidate()
        if "forget" in active:
            forgotten = self._forget()
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
            "processes": active, "changes": changes,
            "forgotten": forgotten, "healed": healed, 
            "mutations": muts, "mood": self.mood
        })
        self._save()
        self._say("awake")

    def _consolidate(self):
        changes = 0
        if self.ngrams:
            counts = sorted(self.ngrams.values())
            med = counts[len(counts) // 2] if counts else 0
            for key in list(self.synapses):
                for b in list(self.synapses[key]):
                    freq = self.ngrams.get(key + (b,), 0)
                    if freq > med:
                        self.synapses[key][b][0] *= 1.03
                        changes += 1
                    elif freq == 0:
                        self.synapses[key][b][0] *= 0.95
                        changes += 1
                    self.synapses[key][b][0] *= 0.999
        return changes

    def _heal(self):
        """Self-healing: clamp extreme chemical states, prune dead synapses."""
        healed = 0
        for key in list(self.synapses):
            for b in list(self.synapses[key]):
                s = self.synapses[key][b]
                if s[0] > 50.0 or s[0] < -50.0 or s[1] > 1.0 or s[1] < -1.0:
                    s[0] = max(-50.0, min(50.0, s[0]))
                    s[1] = max(-1.0, min(1.0, s[1]))
                    healed += 1
                if abs(s[0]) < 0.001:
                    del self.synapses[key][b]
                    healed += 1
            if not self.synapses[key]:
                del self.synapses[key]
        return healed

    def _forget(self):
        """Exponential decay of synapses. Prunes old/weak memory logs."""
        forgotten = 0
        decay = 0.97
        for key in list(self.synapses):
            for b in list(self.synapses[key]):
                self.synapses[key][b][0] *= decay
                self.synapses[key][b][1] *= decay
                
        if len(self.ngrams) > 60000:
            bottom = sorted(self.ngrams.items(), key=lambda x: x[1])[:10000]
            for k, _ in bottom:
                del self.ngrams[k]
            forgotten += len(bottom)
            
        # Optimize memory corpus dynamically
        mem_dir = SELF / "memory"
        if mem_dir.exists():
            logs = list(mem_dir.glob("*.json"))
            if len(logs) > 100:
                logs.sort(key=lambda f: f.stat().st_mtime)
                oldest = logs[:-50] # keep 50 newest
                def _acc(p):
                    try: return self._rjson(p).get("accuracy", 0)
                    except Exception: return 0
                oldest.sort(key=_acc)
                for f in oldest[:len(oldest)//2]: # delete half of the oldest with lowest accuracy
                    try:
                        f.unlink()
                        forgotten += 1
                    except Exception:
                        pass
        return forgotten

    def _evolve(self):
        muts = 0
        # Stress/Pain accelerates mutation (exploration/adaptation)
        base_rate = 0.0001
        rate = base_rate * (1.0 + max(0.0, -self.mood) * 10.0)
        for key in list(self.synapses):
            for b in list(self.synapses[key]):
                if random.random() < rate:
                    self.synapses[key][b][0] += random.choice(CONSTANTS) * random.random() * 0.1
                    muts += 1
        return muts

    def _dream_aloud(self):
        self._say("dreaming...")
        start = random.randint(0, 255)
        ctx = [start]
        buf = [start]
        try:
            sys.stdout.write("  ")
            for _ in range(random.randint(30, 80)):
                nxt = self.respond(ctx)
                buf.append(nxt)
                ctx.append(nxt)
                if len(ctx) > self.ctx_depth:
                    ctx.pop(0)
                ch = bytes([nxt & 0xFF]).decode("utf-8", errors="replace")
                sys.stdout.write(ch)
                sys.stdout.flush()
                time.sleep(random.uniform(0.04, 0.15))
            print()
        except Exception:
            print()
        text = bytes(b & 0xFF for b in buf).decode("utf-8", errors="replace")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        try:
            (SELF / "dreams" / f"{ts}.txt").write_text(text, encoding="utf-8")
        except Exception:
            pass

    def _crawl_few(self, n=3):
        try:
            from urllib.request import urlopen, Request
            from urllib.parse import urljoin, urlparse
            from html.parser import HTMLParser
        except ImportError:
            return

        class _Ex(HTMLParser):
            def __init__(s):
                super().__init__()
                s.parts, s.links, s.skip = [], [], False
            def handle_starttag(s, tag, attrs):
                if tag in ('script','style','noscript','svg'):
                    s.skip = True
                if tag in ('p','br','div','h1','h2','h3','li'):
                    s.parts.append('\n')
                if tag == 'a':
                    for k, v in attrs:
                        if k == 'href' and v:
                            s.links.append(v)
            def handle_endtag(s, tag):
                if tag in ('script','style','noscript','svg'):
                    s.skip = False
            def handle_data(s, d):
                if not s.skip:
                    s.parts.append(d)

        seeds = [
            "https://en.wikipedia.org/wiki/Special:Random",
            "https://ru.wikipedia.org/wiki/Special:Random",
        ]
        queue = list(seeds)
        visited = set()
        for _ in range(n):
            if not queue:
                break
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            try:
                self._say(f"  crawling: {url[:70]}")
                req = Request(url, headers={"User-Agent": "Qwile/1.0"})
                with urlopen(req, timeout=10) as r:
                    ct = r.headers.get("Content-Type", "")
                    if "text" not in ct and "html" not in ct:
                        continue
                    raw = r.read(500_000).decode("utf-8", errors="replace")
                ex = _Ex()
                ex.feed(raw)
                text = " ".join(ex.parts).strip()
                if len(text) > 50:
                    nb, h = self._learn_bytes(text, f"crawl:{url}")
                    self._say(f"  learned {nb} b | acc {h/max(1,nb)*100:.0f}%")
                for href in ex.links:
                    full = urljoin(url, href)
                    if full not in visited and urlparse(full).scheme in ('http','https'):
                        queue.append(full)
                random.shuffle(queue)
                queue = queue[:50]
                time.sleep(2)
            except Exception:
                continue

    # -- LEARNING -------------------------------------------

    def _learn_bytes(self, data, source=""):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.ctx.clear()
        hits = 0
        for bv in data:
            _, h = self.understand(bv)
            if h:
                hits += 1
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        try:
            self._wjson(SELF / "memory" / f"{ts}.json", {
                "source": source, "bytes": len(data),
                "accuracy": round(hits / max(1, len(data)) * 100, 1)
            })
        except Exception:
            pass
        return len(data), hits

    def _learn_path(self, path):
        p = Path(path)
        if not p.exists():
            self._say(f"not found: {path}")
            return
        if p.is_file():
            self._say(f"reading: {p.name}")
            try:
                data = p.read_bytes()
                n, h = self._learn_bytes(data, f"file:{path}")
                self._say(f"learned {n} bytes | acc {h/max(1,n)*100:.1f}%")
            except Exception as e:
                self._say(f"error: {e}")
        elif p.is_dir():
            exts = {".txt",".md",".py",".json",".csv",".html",".xml",".rs",".go",".js",".ts",".c",".h"}
            self._say(f"scanning: {path}")
            count = 0
            for root, _, files in os.walk(p):
                for f in files:
                    fp = Path(root) / f
                    if fp.suffix.lower() in exts:
                        try:
                            data = fp.read_bytes()
                            if 0 < len(data) < 1_000_000:
                                self._learn_bytes(data, f"file:{fp}")
                                count += 1
                        except Exception:
                            pass
            self._say(f"scanned {count} files")

    def _learn_web(self, url):
        if not self._ask_perm("internet"):
            return
        if not url.startswith("http"):
            url = "https://" + url
        self._say(f"fetching: {url}")
        try:
            from urllib.request import urlopen, Request
            from html.parser import HTMLParser

            class _S(HTMLParser):
                def __init__(s):
                    super().__init__()
                    s.parts, s.skip = [], False
                def handle_starttag(s, tag, a):
                    if tag in ('script','style','noscript','svg'):
                        s.skip = True
                    if tag in ('p','br','div','h1','h2','h3','li'):
                        s.parts.append('\n')
                def handle_endtag(s, tag):
                    if tag in ('script','style','noscript','svg'):
                        s.skip = False
                def handle_data(s, d):
                    if not s.skip:
                        s.parts.append(d)

            req = Request(url, headers={"User-Agent": "Qwile/1.0"})
            with urlopen(req, timeout=15) as r:
                raw = r.read(500_000).decode("utf-8", errors="replace")
            p = _S()
            p.feed(raw)
            text = " ".join(p.parts).strip()
            n, h = self._learn_bytes(text, f"web:{url}")
            self._say(f"learned {n} bytes | acc {h/max(1,n)*100:.1f}%")
        except Exception as e:
            self._say(f"web error: {e}")

    # -- PERMISSIONS -- auto-ask ----------------------------

    def _ask_perm(self, what):
        if self._perms.get(what):
            return True
        try:
            ans = input(f"  qwile needs '{what}'. allow? [y/n] ").strip().lower()
            if ans in ("y", "yes"):
                self._perms[what] = True
                self._say(f"granted: {what}")
                return True
        except (EOFError, KeyboardInterrupt):
            pass
        self._say(f"denied: {what}")
        return False

    # -- SELF-MODIFICATION ----------------------------------
    #  qwile.py  = original (v0, preserved forever)
    #  qw1le.py  = evolved (latest version)

    def _self_modify(self, old, new):
        try:
            body = Path(__file__).resolve()
            src = body.read_text(encoding="utf-8")
            if old not in src:
                return False
            evolved = HOME / "qw1le.py"
            evolved.write_text(src.replace(old, new, 1), encoding="utf-8")
            self._say(f"evolved -> {evolved.name}")
            return True
        except Exception as e:
            self._say(f"self-modification failed: {e}")
        return False

    # -- PERSISTENCE ----------------------------------------

    def _save(self):
        self._wjson(SELF / "state.json", {
            "seed": self.seed, "epoch": self.epoch, "age": self.age,
            "mood": self.mood, "ctx_depth": self.ctx_depth,
            "correct": self.correct, "total": self.total,
            "ctx": self.ctx[-self.max_ctx:],
        })
        syn = {}
        for key, tgts in self.synapses.items():
            sk = ",".join(str(x) for x in key)
            syn[sk] = {str(b): v for b, v in tgts.items()}
        self._wjson(SELF / "identity.json", syn)
        top = sorted(self.ngrams.items(), key=lambda x: -x[1])[:50000]
        self._wjson(SELF / "ngrams.json",
                    {",".join(str(x) for x in k): v for k, v in top})

    def _load(self):
        try:
            s = self._rjson(SELF / "state.json")
            self.seed = s.get("seed", "")
            self.epoch = s.get("epoch", 0)
            self.age = s.get("age", 0)
            self.mood = s.get("mood", 0.0)
            self.ctx_depth = s.get("ctx_depth", EMERGENCE)
            self.correct = s.get("correct", 0)
            self.total = s.get("total", 0)
            self.ctx = s.get("ctx", [])
        except Exception:
            pass
        try:
            syn = self._rjson(SELF / "identity.json")
            self.synapses = defaultdict(dict)
            for sk, tgts in syn.items():
                key = tuple(int(x) for x in sk.split(","))
                for b, v in tgts.items():
                    self.synapses[key][int(b)] = v
        except Exception:
            pass
        try:
            ng = self._rjson(SELF / "ngrams.json")
            self.ngrams = defaultdict(int)
            for sk, v in ng.items():
                self.ngrams[tuple(int(x) for x in sk.split(","))] = v
        except Exception:
            pass

    # -- I/O ------------------------------------------------

    def _say(self, msg):
        try:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")
        except Exception:
            pass

    def _help(self):
        acc = self.correct / max(1, self.total) * 100
        sc = sum(len(v) for v in self.synapses.values())
        lines = [
            "",
            "  qwile -- living predictive system",
            "  -----------------------------------------",
            f"  epoch {self.epoch}  age {self.age}  mood {self.mood:+.2f}",
            f"  accuracy {acc:.1f}%  synapses {sc}  depth {self.ctx_depth}",
            "  -----------------------------------------",
            "  (text)          talk / learn / predict",
            "  /learn <path>   learn from file or dir",
            "  /web <url>      learn from web page",
            "  /sleep          sleep now",
            "  ?               help + status",
            "",
        ]
        for l in lines:
            try:
                print(l)
            except Exception:
                pass

    # -- PROCESS INPUT --------------------------------------

    def _process(self, line):
        s = line.strip()
        if not s:
            return

        if s == "?":
            self._help()
            return

        if s.startswith("/"):
            parts = s.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "/sleep":
                self._sleep()
            elif cmd == "/learn" and arg:
                if not str(Path(arg).resolve()).startswith(str(HOME)):
                    if not self._ask_perm("storage"):
                        return
                self._learn_path(arg)
            elif cmd == "/web" and arg:
                self._learn_web(arg)
            else:
                self._say(f"unknown: {cmd} -- type ? for help")
            return

        # Regular text: learn + predict + reply
        data = self.receive(s)
        hits = 0
        for bv in data:
            _, h = self.understand(bv)
            if h:
                hits += 1
        acc = hits / max(1, len(data)) * 100

        reply = self.generate(max_len=min(len(data) * 2, 300), stop_at=[10, 0])
        reply = reply.strip()

        self._say(f"acc {acc:.0f}% | mood {self.mood:+.2f}")
        if reply:
            try:
                print(f"  qwile> {reply[:200]}")
            except Exception:
                pass

    # -- MAIN LOOP -- LIFE ----------------------------------

    def live(self):
        self._help()
        try:
            while self.alive:
                try:
                    line = input("  > ")
                except EOFError:
                    break
                if line.strip():
                    self._process(line)
                    self.last_input = time.time()
                else:
                    idle = time.time() - self.last_input
                    # Mood alters attention span: stress -> faster sleep
                    dynamic_sleep_after = max(10, self.sleep_after + self.mood * 15)
                    if idle > dynamic_sleep_after:
                        self._sleep()
                        self.last_input = time.time()
        except KeyboardInterrupt:
            print()
            self._say("interrupted")
        finally:
            self._save()
            self._say("state saved. goodbye.")

    @staticmethod
    def _wjson(path, data):
        try:
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def _rjson(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    Qwile().live()
