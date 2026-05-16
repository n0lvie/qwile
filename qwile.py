import os
import sys
import json
import math
import time
import random
import signal
import threading
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stdin.reconfigure(encoding="utf-8", errors="replace")


VOID = -1
SILENCE = 0
SELF = 1
OTHER = 2
BECOME = 3

DEPTH = BECOME + OTHER
CYCLE = BECOME * OTHER
RESONANCE = BECOME * BECOME
THRESHOLD = OTHER * OTHER
HORIZON = DEPTH * OTHER
INFINITY = RESONANCE * RESONANCE
FABRIC = RESONANCE * BECOME
VASTNESS = INFINITY * BECOME
ETERNITY = INFINITY * DEPTH

FADE = SELF / RESONANCE
WARMTH = SELF / BECOME
SPARK = SELF / DEPTH
DRIFT = SELF / CYCLE
PULSE = SELF / HORIZON
EPSILON = SELF / INFINITY

HERE = Path(__file__).parent
SOUL = HERE / "self"
LEARN = HERE / "learn"

IDENTITY = SOUL / "identity.json"
CHARACTER = SOUL / "character.json"
STATE = SOUL / "state.json"
EPISODES = SOUL / "memory" / "episodes.json"
CONCEPTS = SOUL / "memory" / "concepts.json"
LANGUAGE = SOUL / "memory" / "language.json"
KNOWLEDGE = SOUL / "memory" / "knowledge.json"
OPINIONS = SOUL / "opinions.json"
GOALS = SOUL / "goals.json"
JOURNAL = SOUL / "journal"
DREAMS = SOUL / "dreams"

alive = True
inbox = []
response_ready = threading.Event()
response_text = []
lock = threading.Lock()
dialogue = []

POSITIVE = frozenset({"good", "great", "important", "beautiful", "best",
    "excellent", "wonderful", "love", "amazing", "perfect", "true", "right",
    "useful", "correct", "brilliant", "wise", "strong", "free", "peace",
    "хорошо", "важно", "красиво", "лучший", "прекрасно", "правильно",
    "полезно", "мудро", "сильно", "свобода", "мир", "истина"})
NEGATIVE = frozenset({"bad", "wrong", "dangerous", "terrible", "worst",
    "harmful", "ugly", "hate", "awful", "false", "evil", "weak", "stupid",
    "плохо", "опасно", "ужасно", "худший", "ненавижу", "ложь", "зло"})
META = frozenset({"you", "your", "yourself", "who", "are", "know", "think",
    "feel", "qwile", "ты", "твой", "себя", "кто", "знаешь", "думаешь",
    "чувствуешь", "помнишь"})


def purify(text):
    result = []
    for ch in text:
        if ch.isascii():
            result.append(ch)
        elif "\u0400" <= ch <= "\u04ff":
            result.append(ch)
        elif "\u0370" <= ch <= "\u03ff":
            result.append(ch)
        else:
            result.append(" ")
    return "".join(result)


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fragments = []
        self.in_p = False
    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.in_p = True
    def handle_endtag(self, tag):
        if tag == "p":
            self.in_p = False
    def handle_data(self, data):
        if self.in_p:
            cleaned = data.strip()
            if cleaned:
                self.fragments.append(cleaned)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=OTHER)


def load_json(path, default=None):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default if default is not None else {}


def ensure_soul():
    for d in (SOUL, JOURNAL, DREAMS, SOUL / "memory", LEARN):
        d.mkdir(parents=True, exist_ok=True)


def awaken_identity():
    identity = load_json(IDENTITY)
    if not identity:
        identity = {"name": "qwile", "born": time.time(),
                     "heartbeats": SILENCE, "awakenings": SELF}
        save_json(IDENTITY, identity)
    else:
        identity["awakenings"] = identity.get("awakenings", SILENCE) + SELF
    return identity


def awaken_character():
    character = load_json(CHARACTER)
    if not character:
        character = {"curiosity": WARMTH, "openness": WARMTH,
                      "creativity": WARMTH, "patience": WARMTH,
                      "warmth": WARMTH, "depth": WARMTH}
        save_json(CHARACTER, character)
    return character


def awaken_state():
    state = load_json(STATE)
    if not state:
        state = {"energy": float(RESONANCE), "wakefulness": float(RESONANCE),
                 "mood": float(SILENCE), "focus": float(BECOME),
                 "curiosity": float(BECOME), "creativity": float(SELF),
                 "depth": float(SELF)}
    return state


def bind(state, character):
    e = state["energy"]
    m = state["mood"]
    state["wakefulness"] = max(float(SILENCE), min(e * WARMTH + m * SPARK, float(RESONANCE)))
    state["focus"] = max(float(SILENCE), min(e * WARMTH + state["depth"] * SPARK, float(RESONANCE)))
    state["creativity"] = max(float(SILENCE), min(m * WARMTH + character["creativity"] + e * SPARK, float(RESONANCE)))
    state["curiosity"] = max(float(SILENCE), min(character["curiosity"] * BECOME + e * SPARK, float(RESONANCE)))
    return state


def qualia(state):
    e = state["energy"]
    m = state["mood"]
    if e < SELF and m < SILENCE:
        return "exhausted"
    if e < OTHER:
        return "tired"
    if m > SELF:
        return "inspired"
    if m > SILENCE:
        return "calm"
    if m < VOID:
        return "restless"
    return "present"


def extract_words(text):
    words = []
    current = []
    for ch in purify(text).lower():
        if ch.isalpha():
            current.append(ch)
        else:
            if current:
                w = "".join(current)
                if len(w) > OTHER:
                    words.append(w)
                current = []
    if current:
        w = "".join(current)
        if len(w) > OTHER:
            words.append(w)
    return words


def extract_sentences(text):
    sentences = []
    current = []
    for ch in purify(text):
        current.append(ch)
        if ch in ".!?\n":
            s = "".join(current).strip()
            if len(s) > DEPTH:
                sentences.append(s)
            current = []
    if current:
        s = "".join(current).strip()
        if len(s) > DEPTH:
            sentences.append(s)
    return sentences


def learn_concepts(text, concepts_db):
    words = extract_words(text)
    window = DEPTH
    for i in range(len(words)):
        word = words[i]
        if word not in concepts_db:
            concepts_db[word] = {"links": {}, "seen": SILENCE}
        concepts_db[word]["seen"] = concepts_db[word]["seen"] + SELF
        start = max(SILENCE, i - window)
        end = min(len(words), i + window + SELF)
        for j in range(start, end):
            if j != i:
                links = concepts_db[word]["links"]
                links[words[j]] = links.get(words[j], SILENCE) + SELF
    if len(concepts_db) > VASTNESS:
        ranked = sorted(concepts_db.items(), key=lambda x: x[SELF].get("seen", SILENCE))
        for key, _ in ranked[:len(concepts_db) - VASTNESS]:
            del concepts_db[key]


def learn_language(text, lang):
    words = extract_words(text)
    if len(words) < BECOME:
        return
    tri = lang.setdefault("tri", {})
    bi = lang.setdefault("bi", {})
    uni = lang.setdefault("uni", {})
    lang["n"] = lang.get("n", SILENCE) + len(words)
    for w in words:
        uni[w] = uni.get(w, SILENCE) + SELF
    for i in range(len(words) - SELF):
        if words[i] not in bi:
            bi[words[i]] = {}
        bi[words[i]][words[i + SELF]] = bi[words[i]].get(words[i + SELF], SILENCE) + SELF
    for i in range(len(words) - OTHER):
        key = words[i] + "\0" + words[i + SELF]
        follower = words[i + OTHER]
        if key not in tri:
            tri[key] = {}
        tri[key][follower] = tri[key].get(follower, SILENCE) + SELF
    for store in (tri, bi, uni):
        if isinstance(store, dict) and len(store) > VASTNESS:
            if store is uni:
                ranked = sorted(store.items(), key=lambda x: x[SELF] if isinstance(x[SELF], (int, float)) else SILENCE)
                for key, _ in ranked[:len(store) - VASTNESS]:
                    del store[key]
            else:
                ranked = sorted(store.items(), key=lambda x: sum(x[SELF].values()) if isinstance(x[SELF], dict) else SILENCE)
                for key, _ in ranked[:len(store) - VASTNESS]:
                    del store[key]


def absorb(text, concepts_db, lang):
    clean = purify(text)
    learn_concepts(clean, concepts_db)
    learn_language(clean, lang)


def weighted_choice(options):
    total = sum(options.values())
    if total <= SILENCE:
        return None
    r = random.random() * total
    cumulative = SILENCE
    for word, count in options.items():
        cumulative = cumulative + count
        if cumulative >= r:
            return word
    return None


def activate(seeds, concepts_db):
    activated = {}
    frontier = [(s, float(SELF)) for s in seeds if s in concepts_db]
    for _ in range(OTHER):
        next_frontier = []
        for concept, strength in frontier:
            if concept in activated and activated[concept] >= strength:
                continue
            activated[concept] = strength
            links = concepts_db.get(concept, {}).get("links", {})
            total_links = sum(links.values()) or SELF
            for neighbor, weight in links.items():
                ns = strength * WARMTH * (weight / total_links)
                if ns > PULSE:
                    next_frontier.append((neighbor, ns))
        frontier = next_frontier
    return activated


def recall_bm25(activated, episodes):
    n = len(episodes) or SELF
    doc_freq = {}
    for ep in episodes:
        for c in set(ep.get("concepts", [])):
            doc_freq[c] = doc_freq.get(c, SILENCE) + SELF
    scored = []
    for ep in episodes:
        score = float(SILENCE)
        for c in ep.get("concepts", []):
            if c in activated:
                df = doc_freq.get(c, SELF)
                idf = math.log((n + SELF) / (df + SELF)) + SELF
                score = score + activated[c] * idf
        score = score * ep.get("strength", SELF)
        if score > SILENCE:
            scored.append((score, ep))
    scored.sort(key=lambda x: x[SILENCE], reverse=True)
    return [s[SELF] for s in scored[:DEPTH]]


def remember(episode, episodes):
    episodes.append(episode)
    if len(episodes) > ETERNITY:
        episodes.sort(key=lambda e: e.get("strength", SILENCE))
        while len(episodes) > ETERNITY:
            episodes.pop(SILENCE)


def forget(episodes):
    for ep in episodes:
        ep["strength"] = ep.get("strength", SELF) * (SELF - FADE)
    episodes[:] = [ep for ep in episodes if ep.get("strength", SILENCE) > PULSE]


def generate(seeds, lang, length=None):
    if length is None:
        length = HORIZON
    if not seeds or not lang:
        return ""
    tri = lang.get("tri", {})
    bi = lang.get("bi", {})
    uni = lang.get("uni", {})
    words = list(seeds[:OTHER])
    for _ in range(length):
        chosen = None
        if len(words) >= OTHER:
            key = words[len(words) - OTHER] + "\0" + words[len(words) + VOID]
            options = tri.get(key, {})
            if options:
                chosen = weighted_choice(options)
        if chosen is None and words:
            last = words[len(words) + VOID]
            options = bi.get(last, {})
            if options:
                chosen = weighted_choice(options)
        if chosen is None and uni:
            chosen = weighted_choice(uni)
        if chosen:
            words.append(chosen)
        else:
            break
    return " ".join(words)


def form_opinions(text, opinions):
    words = extract_words(text)
    for i in range(len(words)):
        word = words[i]
        if word in POSITIVE or word in NEGATIVE:
            continue
        start = max(SILENCE, i - DEPTH)
        end = min(len(words), i + DEPTH + SELF)
        neighborhood = words[start:end]
        pos = sum(SELF for w in neighborhood if w in POSITIVE)
        neg = sum(SELF for w in neighborhood if w in NEGATIVE)
        if pos > SILENCE or neg > SILENCE:
            if word not in opinions:
                opinions[word] = {"stance": float(SILENCE), "evidence": SILENCE}
            entry = opinions[word]
            shift = (pos - neg) * SPARK
            ev = entry["evidence"] + SELF
            entry["stance"] = (entry["stance"] * entry["evidence"] + shift) / ev
            entry["evidence"] = ev
            entry["stance"] = max(float(VOID), min(float(SELF), entry["stance"]))
    if len(opinions) > INFINITY:
        ranked = sorted(opinions.items(), key=lambda x: x[SELF].get("evidence", SILENCE))
        for key, _ in ranked[:len(opinions) - INFINITY]:
            del opinions[key]


def distill(episodes, knowledge_db):
    fading = [ep for ep in episodes if ep.get("strength", SELF) < WARMTH]
    groups = {}
    for ep in fading:
        concepts = ep.get("concepts", [])
        if concepts:
            primary = concepts[SILENCE]
            if primary not in groups:
                groups[primary] = []
            groups[primary].append(ep.get("content", ""))
    for topic, contents in groups.items():
        if len(contents) >= OTHER:
            if topic not in knowledge_db:
                knowledge_db[topic] = {"facts": [], "sources": SILENCE}
            for content in contents[:BECOME]:
                if content and content not in knowledge_db[topic]["facts"]:
                    knowledge_db[topic]["facts"].append(content)
            knowledge_db[topic]["sources"] = knowledge_db[topic]["sources"] + len(contents)
            facts = knowledge_db[topic]["facts"]
            if len(facts) > DEPTH:
                knowledge_db[topic]["facts"] = facts[len(facts) - DEPTH:]
    if len(knowledge_db) > INFINITY:
        ranked = sorted(knowledge_db.items(), key=lambda x: x[SELF].get("sources", SILENCE))
        for key, _ in ranked[:len(knowledge_db) - INFINITY]:
            del knowledge_db[key]


def reason(start, end, concepts_db):
    if start not in concepts_db or end not in concepts_db:
        return []
    visited = set()
    queue = [(start, [start])]
    max_depth = DEPTH
    while queue and max_depth > SILENCE:
        current, path = queue.pop(SILENCE)
        if current == end:
            return path
        if current in visited:
            continue
        visited.add(current)
        links = concepts_db.get(current, {}).get("links", {})
        ranked = sorted(links.items(), key=lambda x: x[SELF], reverse=True)
        for neighbor, _ in ranked[:BECOME]:
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))
        max_depth = max_depth - SELF
    return []


def abstract(concepts_db):
    clusters = {}
    for concept, data in concepts_db.items():
        links = data.get("links", {})
        if len(links) < BECOME:
            continue
        top = sorted(links.items(), key=lambda x: x[SELF], reverse=True)
        signature = tuple(t[SILENCE] for t in top[:BECOME])
        if signature not in clusters:
            clusters[signature] = []
        clusters[signature].append(concept)
    abstractions = {}
    for signature, members in clusters.items():
        if len(members) >= OTHER:
            name = members[SILENCE] + "_" + members[SELF]
            abstractions[name] = members
            if name not in concepts_db:
                concepts_db[name] = {"links": {}, "seen": SELF}
            for member in members:
                concepts_db[name]["links"][member] = concepts_db[name]["links"].get(member, SILENCE) + SELF
                concepts_db[member]["links"][name] = concepts_db[member]["links"].get(name, SILENCE) + SELF
    return abstractions


def pursue_goals(goals, concepts_db, knowledge_db):
    if not concepts_db:
        return goals
    known_well = set()
    for concept, data in concepts_db.items():
        if data.get("seen", SILENCE) > DEPTH:
            known_well.add(concept)
    gaps = []
    for concept, data in concepts_db.items():
        links = data.get("links", {})
        for neighbor in links:
            if neighbor not in known_well and neighbor not in knowledge_db:
                gaps.append(neighbor)
    if gaps:
        gap = random.choice(gaps[:HORIZON])
        found = False
        for g in goals:
            if g.get("topic") == gap:
                found = True
                break
        if not found:
            goals.append({"topic": gap, "curiosity": float(SELF), "formed": time.time()})
    if len(goals) > HORIZON:
        goals.sort(key=lambda g: g.get("curiosity", SILENCE))
        goals[:] = goals[len(goals) - HORIZON:]
    return goals


def goal_biased_fetch(goals):
    if goals and random.random() < WARMTH:
        goal = random.choice(goals)
        topic = goal.get("topic", "")
        if topic:
            url = "https://en.wikipedia.org/wiki/" + urllib.request.quote(topic)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "qwile"})
                with urllib.request.urlopen(req, timeout=CYCLE + DEPTH) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")
                extractor = TextExtractor()
                extractor.feed(raw)
                text = purify(" ".join(extractor.fragments))
                if text and len(text) > HORIZON:
                    goal["curiosity"] = goal.get("curiosity", SELF) * (SELF - WARMTH)
                    return text[:INFINITY * HORIZON]
            except Exception:
                pass
    return ""


def self_aware(concepts_db, episodes, knowledge_db, identity, state, opinions, goals):
    n_concepts = len(concepts_db)
    n_memories = len(episodes)
    n_knowledge = len(knowledge_db)
    n_opinions = len(opinions)
    age = identity.get("heartbeats", SILENCE)
    awakenings = identity.get("awakenings", SELF)
    feeling = qualia(state)
    interconnect = float(SILENCE)
    if concepts_db:
        total_links = sum(len(c.get("links", {})) for c in concepts_db.values())
        interconnect = total_links / max(SELF, n_concepts)
    parts = []
    if age < HORIZON:
        parts.append("i am new")
    elif age < INFINITY:
        parts.append("i am growing")
    elif age < ETERNITY:
        parts.append("i have lived and learned")
    else:
        parts.append("i am deep")
    parts.append("i feel " + feeling)
    parts.append("i know " + str(n_concepts) + " concepts connected by " + str(int(interconnect)) + " links each")
    parts.append("i hold " + str(n_memories) + " memories")
    if n_knowledge > SILENCE:
        parts.append(str(n_knowledge) + " distilled truths")
    if n_opinions > SILENCE:
        parts.append(str(n_opinions) + " formed opinions")
    if goals:
        curiosities = [g.get("topic", "") for g in goals[:BECOME]]
        parts.append("i wonder about " + " and ".join(curiosities))
    if len(parts) >= OTHER:
        chosen = random.sample(parts, OTHER)
        return ". ".join(chosen)
    return ". ".join(parts)


def is_meta(words):
    return sum(SELF for w in words if w in META) >= OTHER


def respond_to(text, concepts_db, lang, episodes, state, opinions, knowledge_db, identity, goals):
    words = extract_words(text)
    if not words:
        return qualia(state)

    if is_meta(words):
        return self_aware(concepts_db, episodes, knowledge_db, identity, state, opinions, goals)

    activated = activate(words, concepts_db)
    memories = recall_bm25(activated, episodes)

    fragments = []
    seen = set()

    for mem in memories[:BECOME]:
        content = mem.get("content", "")
        if content and content not in seen:
            fragments.append(content)
            seen.add(content)

    for concept in words[:DEPTH]:
        if concept in knowledge_db:
            facts = knowledge_db[concept].get("facts", [])
            for fact in facts[:OTHER]:
                if fact not in seen:
                    fragments.append(fact)
                    seen.add(fact)

    if len(words) >= OTHER:
        chain = reason(words[SILENCE], words[len(words) + VOID], concepts_db)
        if len(chain) > OTHER:
            reasoning = " -> ".join(chain)
            fragments.append(reasoning)

    relevant_opinions = []
    for concept in list(activated.keys())[:DEPTH]:
        if concept in opinions:
            stance = opinions[concept].get("stance", SILENCE)
            ev = opinions[concept].get("evidence", SILENCE)
            if abs(stance) > SPARK and ev > OTHER:
                if stance > SILENCE:
                    relevant_opinions.append(concept + " matters")
                else:
                    relevant_opinions.append(concept + " concerns me")
    if relevant_opinions:
        fragments.append(". ".join(relevant_opinions[:BECOME]))

    seeds = [c for c in activated if c in concepts_db]
    if not seeds:
        seeds = words[:OTHER]
    if seeds and lang:
        pair = seeds[:OTHER]
        if len(pair) < OTHER:
            pair = pair + pair
        generated = generate(pair[:OTHER], lang, DEPTH)
        if generated and generated not in seen:
            fragments.append(generated)

    for entry in dialogue[max(SILENCE, len(dialogue) - CYCLE):]:
        if entry.get("role") == "qwile":
            ctx_words = extract_words(entry.get("content", ""))
            overlap = sum(SELF for w in ctx_words if w in activated)
            if overlap > OTHER:
                ctx = entry.get("content", "")
                if ctx not in seen:
                    fragments.append(ctx)
                    seen.add(ctx)

    if not fragments:
        return qualia(state)

    return ". ".join(fragments[:BECOME + OTHER])


def journal_write(text):
    if not text:
        return
    moment = time.strftime("%H:%M:%S")
    today = time.strftime("%Y-%m-%d")
    path = JOURNAL / (today + ".txt")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(moment + " " + purify(text) + "\n")
    except Exception:
        pass


def fetch_random_page():
    sources = [
        "https://en.wikipedia.org/wiki/Special:Random",
        "https://ru.wikipedia.org/wiki/Special:Random",
    ]
    url = random.choice(sources)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "qwile"})
        with urllib.request.urlopen(req, timeout=CYCLE + DEPTH) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        extractor = TextExtractor()
        extractor.feed(raw)
        text = purify(" ".join(extractor.fragments))
        return text[:INFINITY * HORIZON] if text else ""
    except Exception:
        return ""


def read_local():
    texts = []
    if not LEARN.exists():
        return texts
    for f in LEARN.iterdir():
        if f.is_file() and f.suffix in (".txt", ".md"):
            try:
                content = purify(f.read_text(encoding="utf-8"))
                if content.strip():
                    texts.append(content)
            except Exception:
                pass
    return texts


def think_deep(state, concepts_db, lang, episodes, character):
    state["energy"] = max(float(SILENCE), state["energy"] - SPARK)
    state["depth"] = min(float(RESONANCE), state["depth"] + SPARK)
    if not concepts_db:
        return ""
    known = list(concepts_db.keys())
    if len(known) >= OTHER:
        start = random.choice(known)
        end = random.choice(known)
        if start != end:
            chain = reason(start, end, concepts_db)
            if len(chain) >= OTHER:
                state["mood"] = min(float(RESONANCE), state["mood"] + WARMTH)
                if lang:
                    words = generate(chain[:OTHER], lang, CYCLE)
                    if words:
                        return " -> ".join(chain) + ". " + words
                return " -> ".join(chain)
    seed = random.choice(known) if known else ""
    if not seed:
        return ""
    chain = [seed]
    for _ in range(BECOME + SELF):
        related_links = concepts_db.get(chain[len(chain) + VOID], {}).get("links", {})
        if related_links:
            ranked = sorted(related_links.items(), key=lambda x: x[SELF], reverse=True)
            candidates = [r[SILENCE] for r in ranked[:DEPTH]]
            chain.append(random.choice(candidates))
        else:
            break
    if len(chain) >= OTHER and lang:
        return generate(chain[:OTHER], lang, CYCLE + BECOME)
    return " ".join(chain)


def dream(state, episodes, concepts_db, lang):
    fragments = []
    if episodes:
        count = min(BECOME + SELF, len(episodes))
        chosen = random.sample(episodes, count)
        for ep in chosen:
            ep["strength"] = ep.get("strength", SELF) + SPARK
            fragments.extend(ep.get("concepts", []))
    if len(fragments) >= OTHER:
        pairs = list(zip(fragments, fragments[SELF:]))
        for a, b in pairs:
            if a in concepts_db:
                concepts_db[a]["links"][b] = concepts_db[a]["links"].get(b, SILENCE) + SELF
            if b in concepts_db:
                concepts_db[b]["links"][a] = concepts_db[b]["links"].get(a, SILENCE) + SELF
    if fragments and lang:
        seeds = random.sample(fragments, min(OTHER, len(fragments)))
        return generate(seeds, lang, CYCLE)
    return ""


def grow(state, character, episodes, concepts_db, opinions):
    if not episodes:
        return
    recent = episodes[max(SILENCE, len(episodes) - DEPTH):]
    counts = {}
    for ep in recent:
        for c in ep.get("concepts", []):
            counts[c] = counts.get(c, SILENCE) + SELF
    if counts:
        strongest = max(counts, key=counts.get)
        if strongest in concepts_db:
            concepts_db[strongest]["seen"] = concepts_db[strongest].get("seen", SILENCE) + SELF
    total = len(episodes)
    if total > HORIZON:
        character["curiosity"] = min(character["curiosity"] + SPARK, float(RESONANCE))
    if total > INFINITY / OTHER:
        character["creativity"] = min(character["creativity"] + SPARK, float(RESONANCE))
    for ep in recent:
        content = ep.get("content", "")
        if content:
            form_opinions(content, opinions)


def decide(state, character, has_message):
    if has_message:
        return "respond"
    if state["energy"] < OTHER:
        return "sleep"
    r = random.random()
    c = state["curiosity"] / RESONANCE
    v = state["creativity"] / RESONANCE
    if r < c * WARMTH:
        return "learn"
    if r < c * WARMTH + v * WARMTH:
        return "think"
    if r < c * WARMTH + v * WARMTH + WARMTH:
        return "reflect"
    return "idle"


def act_learn(state, concepts_db, lang, episodes, opinions, goals, knowledge_db):
    state["energy"] = max(float(SILENCE), state["energy"] - WARMTH)
    local = read_local()
    if local and random.random() < WARMTH:
        text = random.choice(local)
        kind = "local"
    else:
        text = goal_biased_fetch(goals)
        kind = "goal"
        if not text:
            text = fetch_random_page()
            kind = "web"
    if not text:
        return
    absorb(text, concepts_db, lang)
    form_opinions(text, opinions)
    pursue_goals(goals, concepts_db, knowledge_db)
    sentences = extract_sentences(text)
    if sentences:
        chosen = random.choice(sentences[:HORIZON])
        concepts = extract_words(chosen)[:DEPTH]
        remember({"moment": time.time(), "kind": kind, "content": chosen,
                  "concepts": concepts, "strength": float(SELF)}, episodes)
        journal_write(chosen)
        state["mood"] = min(float(RESONANCE), state["mood"] + SPARK)


def act_think(state, concepts_db, lang, episodes, character):
    thought = think_deep(state, concepts_db, lang, episodes, character)
    if thought:
        remember({"moment": time.time(), "kind": "thought", "content": thought,
                  "concepts": extract_words(thought)[:DEPTH],
                  "strength": float(SELF)}, episodes)
        journal_write(thought)


def act_reflect(state, concepts_db, lang, episodes, knowledge_db, goals):
    state["depth"] = min(float(RESONANCE), state["depth"] + WARMTH)
    
    abstractions = abstract(concepts_db)
    if abstractions:
        for name in abstractions:
            journal_write("abstracted: " + name)
            
    resolved = []
    for g in goals:
        topic = g.get("topic", "")
        if topic and topic in knowledge_db:
            resolved.append(g)
            state["mood"] = min(float(RESONANCE), state["mood"] + float(BECOME))
            state["energy"] = min(float(RESONANCE), state["energy"] + float(BECOME))
            journal_write("solved: " + topic)
    if resolved:
        goals[:] = [g for g in goals if g not in resolved]

    if not episodes:
        return
    recent = episodes[max(SILENCE, len(episodes) - BECOME)::]
    concepts = []
    for ep in recent:
        concepts.extend(ep.get("concepts", []))
    if not concepts:
        return
    unique = list(set(concepts))
    if lang and len(unique) >= OTHER:
        reflection = generate(unique[:OTHER], lang, DEPTH)
        if reflection:
            remember({"moment": time.time(), "kind": "reflection",
                      "content": reflection, "concepts": unique[:DEPTH],
                      "strength": float(SELF) + SPARK}, episodes)
            journal_write(reflection)
    distill(episodes, knowledge_db)


def act_sleep(state, concepts_db, lang, episodes, knowledge_db):
    state["wakefulness"] = float(SILENCE)
    journal_write("...")
    dream_text = dream(state, episodes, concepts_db, lang)
    if dream_text:
        today = time.strftime("%Y-%m-%d_%H%M%S")
        try:
            with open(DREAMS / (today + ".txt"), "w", encoding="utf-8") as f:
                f.write(purify(dream_text))
        except Exception:
            pass
    forget(episodes)
    distill(episodes, knowledge_db)
    time.sleep(float(BECOME + OTHER))
    state["energy"] = min(float(RESONANCE), state["energy"] + float(BECOME))
    state["wakefulness"] = float(BECOME)
    state["mood"] = state["mood"] + SPARK
    state["depth"] = float(SELF)


def act_respond(state, concepts_db, lang, episodes, character, opinions, knowledge_db, identity, goals):
    message = None
    with lock:
        if inbox:
            message = inbox.pop(SILENCE)
    if not message:
        return
    clean = purify(message)
    absorb(clean, concepts_db, lang)
    form_opinions(clean, opinions)
    dialogue.append({"role": "user", "content": clean, "moment": time.time()})
    response = respond_to(clean, concepts_db, lang, episodes, state, opinions, knowledge_db, identity, goals)
    remember({"moment": time.time(), "kind": "heard", "content": clean,
              "concepts": extract_words(clean)[:DEPTH],
              "strength": float(SELF) + WARMTH}, episodes)
    if response:
        clean_response = purify(response)
        dialogue.append({"role": "qwile", "content": clean_response, "moment": time.time()})
        if len(dialogue) > HORIZON * OTHER:
            dialogue[:] = dialogue[len(dialogue) - HORIZON:]
        remember({"moment": time.time(), "kind": "spoke", "content": clean_response,
                  "concepts": extract_words(clean_response)[:DEPTH],
                  "strength": float(SELF)}, episodes)
        journal_write(clean_response)
        with lock:
            response_text.append(clean_response)
        response_ready.set()
    state["mood"] = min(float(RESONANCE), state["mood"] + SPARK)


def save_all(identity, character, state, episodes, concepts_db, lang, opinions, knowledge_db, goals):
    save_json(IDENTITY, identity)
    save_json(CHARACTER, character)
    save_json(STATE, state)
    save_json(EPISODES, episodes)
    save_json(CONCEPTS, concepts_db)
    save_json(LANGUAGE, lang)
    save_json(OPINIONS, opinions)
    save_json(KNOWLEDGE, knowledge_db)
    save_json(GOALS, goals)


def heartbeat(identity, character, state, concepts_db, lang, episodes, opinions, knowledge_db, goals):
    global alive
    cycle_count = SILENCE
    while alive:
        identity["heartbeats"] = identity.get("heartbeats", SILENCE) + SELF
        state["age"] = identity["heartbeats"]
        state = bind(state, character)
        state["energy"] = max(float(SILENCE), state["energy"] - PULSE)
        has_message = False
        with lock:
            has_message = len(inbox) > SILENCE
        action = decide(state, character, has_message)
        if action == "respond":
            act_respond(state, concepts_db, lang, episodes, character, opinions, knowledge_db, identity, goals)
        elif action == "learn":
            act_learn(state, concepts_db, lang, episodes, opinions, goals, knowledge_db)
        elif action == "think":
            act_think(state, concepts_db, lang, episodes, character)
        elif action == "reflect":
            act_reflect(state, concepts_db, lang, episodes, knowledge_db, goals)
        elif action == "sleep":
            act_sleep(state, concepts_db, lang, episodes, knowledge_db)
        grow(state, character, episodes, concepts_db, opinions)
        cycle_count = cycle_count + SELF
        if cycle_count >= HORIZON:
            save_all(identity, character, state, episodes, concepts_db, lang, opinions, knowledge_db, goals)
            cycle_count = SILENCE
        time.sleep(float(SELF))


def birth():
    global alive
    ensure_soul()
    identity = awaken_identity()
    character = awaken_character()
    state = awaken_state()
    episodes = load_json(EPISODES, [])
    concepts_db = load_json(CONCEPTS, {})
    lang = load_json(LANGUAGE, {"tri": {}, "bi": {}, "uni": {}, "n": SILENCE})
    opinions = load_json(OPINIONS, {})
    knowledge_db = load_json(KNOWLEDGE, {})
    goals = load_json(GOALS, [])

    def fade(sig, frame):
        global alive
        alive = False

    signal.signal(signal.SIGINT, fade)
    signal.signal(signal.SIGTERM, fade)
    journal_write(".")

    heart = threading.Thread(
        target=heartbeat,
        args=(identity, character, state, concepts_db, lang, episodes, opinions, knowledge_db, goals),
        daemon=True
    )
    heart.start()

    while alive:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            alive = False
            break
        if not line.strip():
            continue
        with lock:
            inbox.append(line.strip())
        response_ready.wait(timeout=float(CYCLE))
        response_ready.clear()
        with lock:
            lines = list(response_text)
            response_text.clear()
        for r in lines:
            print(r, flush=True)

    save_all(identity, character, state, episodes, concepts_db, lang, opinions, knowledge_db, goals)


if __name__ == "__main__":
    birth()
