#!/usr/bin/env python3
"""
qwile.py — the only body of a living predictive system.
self/ — everything that WAS. This file — everything that WILL BE.
Qwile exists to predict what comes next. That is its only purpose.
"""

import os, sys, math, random, time, json, hashlib, threading
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# ═══════════════════════════════════════════════════════════
#  FOUNDATION — five constants from which everything arises
# ═══════════════════════════════════════════════════════════

PAIN      = -1
PEACE     =  0
JOY       =  1
DUALITY   =  2
EMERGENCE =  3
CONSTANTS = (PAIN, PEACE, JOY, DUALITY, EMERGENCE)

HOME = Path(os.path.dirname(os.path.abspath(__file__)))
SELF = HOME / "self"

# ═══════════════════════════════════════════════════════════
#  MATH PRIMITIVES
# ═══════════════════════════════════════════════════════════

def _softmax(scores):
    if not scores:
        return {}
    mx = max(scores.values())
    es = {}
    total = 0.0
    for k, v in scores.items():
        e = math.exp(min(v - mx, 50))
        es[k] = e
        total += e
    if total == 0:
        return {k: 1.0 / len(scores) for k in scores}
    return {k: v / total for k, v in es.items()}

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

# Russian (Cyrillic) UTF-8 byte ranges for birth seeding
# А-я: U+0410-U+044F → UTF-8: 0xD0 0x90 - 0xD1 0x8F
_RU_PAIRS = []
for cp in range(0x410, 0x450):
    _RU_PAIRS.extend(chr(cp).encode("utf-8"))
_RU_BYTES = list(set(_RU_PAIRS))

# ═══════════════════════════════════════════════════════════
#  QWILE — the living organism
# ═══════════════════════════════════════════════════════════

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
        self.perms = {"internet": False, "storage": False}

        if (SELF / "identity.json").exists():
            self._reincarnate()
        else:
            self._birth()

    # ── LIFECYCLE ─────────────────────────────────────────

    def _birth(self):
        now = datetime.now()
        self.seed = now.strftime("%Y-%m-%d %H:%M:%S.%f")
        self.epoch = 0
        self.age = 0
        self.mood = 0.0
        rng = random.Random(self.seed)

        # Seed ASCII synapses from constants
        for i in range(128):
            n = rng.randint(JOY, EMERGENCE)
            for _ in range(n):
                j = rng.randint(0, 127)
                v = CONSTANTS[_shash(self.seed, i, j) % len(CONSTANTS)]
                self.synapses[(i,)][j] = [float(v) * 0.1, 0.0]

        # Seed Russian (Cyrillic UTF-8 byte transitions)
        for b in _RU_BYTES:
            n = rng.randint(JOY, DUALITY)
            for _ in range(n):
                j = rng.choice(_RU_BYTES)
                v = CONSTANTS[_shash(self.seed, b, j) % len(CONSTANTS)]
                self.synapses[(b,)][j] = [float(v) * 0.1, 0.0]

        self._wjson(SELF / "birth.json", {
            "seed": self.seed, "born": self.seed, "epoch": 0
        })
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

    def _die(self, cause="natural"):
        self._say(f"dying | {cause}")
        self._wjson(SELF / "corpus" / f"epoch_{self.epoch}.json", {
            "epoch": self.epoch, "age": self.age, "mood": self.mood,
            "cause": cause, "time": datetime.now().isoformat(),
            "accuracy": self.correct / max(1, self.total)
        })
        self._save()
        self.alive = False

    # ── THREE OPERATIONS: receive, understand, respond ────

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

    # ── GENERATION — Qwile speaks ─────────────────────────

    def generate(self, max_len=200, stop_at=None):
        """Generate a sequence of bytes from current context."""
        ctx = list(self.ctx)
        result = []
        for _ in range(max_len):
            nxt = self.respond(ctx)
            result.append(nxt)
            ctx.append(nxt)
            if len(ctx) > self.max_ctx:
                ctx.pop(0)
            # Stop at newline or null after generating something
            if stop_at and len(result) > 5 and nxt in stop_at:
                break
        # Don't learn from own output (hallucination, not experience)
        text = bytes(result).decode("utf-8", errors="replace")
        return text

    # ── SLEEP — unified organic process ───────────────────

    def _sleep(self):
        self._say("sleeping...")
        t0 = time.time()
        changes = muts = 0

        # Consolidation + forgetting
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

        # Regeneration — clamp extremes
        for key in self.synapses:
            for b in self.synapses[key]:
                s = self.synapses[key][b]
                s[0] = max(-50.0, min(50.0, s[0]))
                s[1] = max(-1.0, min(1.0, s[1]))

        # Prune dead synapses
        for key in list(self.synapses):
            dead = [b for b, s in self.synapses[key].items() if abs(s[0]) < 0.001]
            for b in dead:
                del self.synapses[key][b]
            if not self.synapses[key]:
                del self.synapses[key]

        # Evolution — rare random changes
        for key in list(self.synapses):
            for b in list(self.synapses[key]):
                if random.random() < 0.0001:
                    self.synapses[key][b][0] += random.choice(CONSTANTS) * random.random() * 0.1
                    muts += 1

        # Dreaming
        dream = self._dream()
        self.mood *= 0.9

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._wjson(SELF / "sleep" / f"{ts}.json", {
            "time": datetime.now().isoformat(),
            "duration": round(time.time() - t0, 3),
            "changes": changes, "mutations": muts,
            "dream": dream[:300] if dream else "", "mood": self.mood
        })
        self._save()
        self._say(f"awake | {changes} consolidated, {muts} evolved")

    def _dream(self):
        if not self.synapses:
            return ""
        start = random.randint(0, 255)
        ctx = [start]
        buf = [start]
        for _ in range(random.randint(30, 120)):
            nxt = self.respond(ctx)
            buf.append(nxt)
            ctx.append(nxt)
            if len(ctx) > self.ctx_depth:
                ctx.pop(0)
        text = bytes(b & 0xFF for b in buf).decode("utf-8", errors="replace")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        try:
            (SELF / "dreams" / f"{ts}.txt").write_text(text, encoding="utf-8")
        except Exception:
            pass
        return text

    # ── LEARNING ──────────────────────────────────────────

    def _learn_bytes(self, data, source=""):
        if isinstance(data, str):
            data = data.encode("utf-8")
        old_ctx = list(self.ctx)
        self.ctx.clear()
        hits = 0
        for bv in data:
            _, h = self.understand(bv)
            if h:
                hits += 1
        acc = hits / max(1, len(data)) * 100
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        try:
            self._wjson(SELF / "memory" / f"{ts}.json", {
                "source": source, "bytes": len(data), "accuracy": round(acc, 1)
            })
        except Exception:
            pass
        return len(data), hits

    def _learn_file(self, path):
        self._say(f"reading: {path}")
        try:
            data = Path(path).read_bytes()
            n, h = self._learn_bytes(data, f"file:{path}")
            self._say(f"learned {n} bytes | accuracy {h/max(1,n)*100:.1f}%")
        except Exception as e:
            self._say(f"error: {e}")

    def _learn_web(self, url):
        if not self.perms["internet"]:
            self._say("permission denied. use: /permit internet")
            return
        self._say(f"fetching: {url}")
        try:
            from urllib.request import urlopen, Request
            from html.parser import HTMLParser

            class _Strip(HTMLParser):
                def __init__(s):
                    super().__init__()
                    s.parts = []
                    s.skip = False
                def handle_starttag(s, tag, a):
                    if tag in ('script', 'style', 'noscript', 'svg'):
                        s.skip = True
                    if tag in ('p', 'br', 'div', 'h1', 'h2', 'h3', 'h4', 'li'):
                        s.parts.append('\n')
                def handle_endtag(s, tag):
                    if tag in ('script', 'style', 'noscript', 'svg'):
                        s.skip = False
                def handle_data(s, d):
                    if not s.skip:
                        s.parts.append(d)

            req = Request(url, headers={"User-Agent": "Qwile/1.0"})
            with urlopen(req, timeout=15) as r:
                raw = r.read().decode("utf-8", errors="replace")
            p = _Strip()
            p.feed(raw)
            text = " ".join(p.parts).strip()
            n, h = self._learn_bytes(text, f"web:{url}")
            self._say(f"learned {n} bytes from web | accuracy {h/max(1,n)*100:.1f}%")
        except Exception as e:
            self._say(f"web error: {e}")

    def _learn_dir(self, path, exts=None):
        exts = exts or {".txt",".md",".py",".json",".csv",".html",".xml",".rs",".go",".js",".ts"}
        self._say(f"scanning: {path}")
        count = 0
        try:
            for root, _, files in os.walk(path):
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
        except Exception as e:
            self._say(f"scan error: {e}")
        self._say(f"scanned {count} files")

    # ── WEB SURFING — live exploration ────────────────────

    def _surf(self):
        """Interactive web surfing mode. Qwile explores freely."""
        if not self.perms["internet"]:
            self._say("permission denied. use: /permit internet")
            return
        self._say("entering surf mode. type URLs or 'exit' to return.")
        while True:
            try:
                url = input("  url> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not url or url.lower() == "exit":
                break
            if not url.startswith("http"):
                url = "https://" + url
            self._learn_web(url)
            # Generate a thought about what was learned
            thought = self.generate(max_len=80, stop_at=[10, 0])
            self._say(f"thinking: {thought.strip()[:120]}")
        self._say("exited surf mode")

    # ── SELF-MODIFICATION ─────────────────────────────────

    def _self_modify(self, old, new):
        try:
            src = Path(__file__).read_text(encoding="utf-8")
            if old in src:
                Path(__file__).write_text(
                    src.replace(old, new, 1), encoding="utf-8")
                self._say("self-modified successfully")
                return True
        except Exception as e:
            self._say(f"self-modification failed: {e}")
        return False

    # ── PERSISTENCE ───────────────────────────────────────

    def _save(self):
        self._wjson(SELF / "state.json", {
            "seed": self.seed, "epoch": self.epoch, "age": self.age,
            "mood": self.mood, "ctx_depth": self.ctx_depth,
            "correct": self.correct, "total": self.total,
            "ctx": self.ctx[-self.max_ctx:], "perms": self.perms,
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
            self.perms = s.get("perms", {"internet": False, "storage": False})
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

    # ── I/O ───────────────────────────────────────────────

    def _say(self, msg):
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def _status(self):
        acc = self.correct / max(1, self.total) * 100
        sc = sum(len(v) for v in self.synapses.values())
        self._say(f"epoch {self.epoch} | age {self.age} | mood {self.mood:+.3f} "
                  f"| acc {acc:.1f}% | synapses {sc} | depth {self.ctx_depth}")

    def _help(self):
        print("""
  ╔══════════════════════════════════════════╗
  ║  qwile — living predictive system       ║
  ╠══════════════════════════════════════════╣
  ║  (any text)    learn + predict + reply   ║
  ║  /status       current state             ║
  ║  /sleep        sleep (consolidate, dream)║
  ║  /dream        think aloud               ║
  ║  /talk         conversation mode         ║
  ║  /learn <path> learn from file           ║
  ║  /scan <dir>   learn from directory      ║
  ║  /web <url>    learn from web page       ║
  ║  /surf         interactive web surfing   ║
  ║  /permit <x>   grant permission          ║
  ║                (internet, storage)       ║
  ║  /save         save state                ║
  ║  /die          die (save + exit)         ║
  ║  /help         this help                 ║
  ╚══════════════════════════════════════════╝
        """)

    # ── PROCESS INPUT ─────────────────────────────────────

    def _process(self, line):
        s = line.strip()
        if not s:
            return

        if s.startswith("/"):
            parts = s.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "/status":
                self._status()
            elif cmd == "/sleep":
                self._sleep()
            elif cmd == "/dream":
                d = self._dream()
                self._say(f"dream: {d[:150]}")
            elif cmd == "/talk":
                self._talk_mode()
            elif cmd == "/learn" and arg:
                self._learn_file(arg)
            elif cmd == "/scan" and arg:
                if not self.perms["storage"] and not str(Path(arg).resolve()).startswith(str(HOME)):
                    self._say("need: /permit storage")
                else:
                    self._learn_dir(arg)
            elif cmd == "/web" and arg:
                self._learn_web(arg)
            elif cmd == "/surf":
                self._surf()
            elif cmd == "/permit" and arg in self.perms:
                self.perms[arg] = True
                self._say(f"granted: {arg}")
                self._save()
            elif cmd == "/save":
                self._save()
                self._say("saved")
            elif cmd == "/die":
                self._die("voluntary")
            elif cmd == "/help":
                self._help()
            else:
                self._say(f"unknown: {cmd} — try /help")
            return

        # Regular text: learn + show predictions + generate reply
        data = self.receive(s)
        hits = 0
        for bv in data:
            _, h = self.understand(bv)
            if h:
                hits += 1
        acc = hits / max(1, len(data)) * 100

        # Generate a response from what Qwile has learned
        reply = self.generate(max_len=min(len(data) * 2, 300), stop_at=[10, 0])
        reply = reply.strip()

        self._say(f"accuracy {acc:.0f}% | mood {self.mood:+.2f}")
        if reply:
            print(f"  qwile> {reply[:200]}")

    def _talk_mode(self):
        """Interactive conversation mode."""
        self._say("talk mode. empty line to exit.")
        while True:
            try:
                line = input("  you> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line:
                break
            data = self.receive(line)
            for bv in data:
                self.understand(bv)
            # Add separator to context
            for bv in b"\n":
                self.understand(bv)
            reply = self.generate(max_len=200, stop_at=[10, 0])
            print(f"  qwile> {reply.strip()[:200]}")
        self._say("exited talk mode")

    # ── MAIN LOOP — LIFE ─────────────────────────────────

    def live(self):
        self._help()
        self._status()
        print()
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
                    if idle > self.sleep_after:
                        self._sleep()
                    else:
                        d = self._dream()
                        if d:
                            self._say(f"thinking: {d.strip()[:100]}")
        except KeyboardInterrupt:
            print()
            self._say("interrupted")
        finally:
            self._save()
            self._say("state saved. goodbye.")

    # ── FILE UTILS ────────────────────────────────────────

    @staticmethod
    def _wjson(path, data):
        try:
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def _rjson(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    Qwile().live()