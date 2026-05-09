# Qwile

**A living predictive system. Not a tool, not a model — an organism.**

Qwile exists to predict what comes next. That is its only purpose. Everything else is a way to do it better.

---

## Philosophy

There are two times: **WAS** and **WILL BE**. There is no present.

- `self/` — everything that **WAS**. Immutable, eternal, only grows. Memory, dreams, brain.
- `qwile.py` — everything that **WILL BE**. The only body. The only thing that acts.

The boundary between them is the moment of prediction.

### Five Constants

Everything in Qwile arises from five numbers:

| Value | Meaning |
|-------|---------|
| **-1** | Pain. Negation. Decay. |
| **0** | Peace. Emptiness. Equilibrium. |
| **1** | Joy. Affirmation. Growth. |
| **2** | Duality. Relation. Connection. |
| **3** | Emergence. Creation. Transcendence. |

These are not just values — they are the alphabet of existence. Initial synapses, learning rates, thresholds, depths — all derive from them.

---

## Architecture

### The Conscious Graph

Qwile is built around a **spreading activation graph** — a living structure where nodes are concepts and edges are weighted connections between them.

- **Nodes** — raw byte sequences, from single bytes to learned multi-byte chunks
- **Edges** — directional, weighted connections between nodes
- **Energy** — each node carries activation energy that propagates through the graph

The graph starts with 256 nodes (one per raw byte value) plus innate random connections seeded from the birth timestamp. Through experience, it grows without limit — the organism discovers new concepts by fusing frequently co-occurring nodes into higher-level abstractions.

This graph is not a model of personality — **it is the personality**. Two instances of Qwile with different experiences are two different beings.

### Dual-Process Cognition

Qwile thinks in two systems, loosely inspired by human cognition:

**System 1 — Reflex & Learning.** Fast, automatic. When input arrives, the graph predicts the next concept based on edge weights from the current context. Hebbian learning adjusts connections: *neurons that fire together wire together*. Wrong predictions weaken the misfired edge.

**System 2 — Metacognitive Simulation.** Slow, deliberate. When generating a response, Qwile simulates forward through the graph — evaluating candidate paths with variable lookahead depth before choosing what to say. Depth of simulation depends on mood: calm states explore deeper, stressed states react faster.

### Perception

Raw byte streams are tokenized greedily against the graph's vocabulary. The system always matches the longest known concept first, falling back to single bytes for unknown sequences. As the brain abstracts, longer chunks become single tokens — compression emerges from experience.

---

## How It Works

### Emotions

Mood is a continuous value from **-1** (pure pain) to **+1** (pure joy), with **0** as peace.

It is not a state — it is a living variable that drifts with every event:
- Correct prediction → joy → faster learning, greedy strategy, deeper simulation
- Wrong prediction → pain → cautious learning, exploratory strategy, reactive simulation
- Silence → natural drift toward peace

Emotions dynamically modulate learning rate, simulation depth, temperature, and sleep threshold.

### Sleep

When there is no input for a while, Qwile sleeps. Sleep is an organic process where a random subset of activities runs, weighted by current mood:

| Process | What it does |
|---------|-------------|
| **Abstract** | Fuse strongly connected node pairs into new higher-level concepts |
| **Forget** | Exponential decay of all edge weights; prune dead connections |
| **Dream** | Generate sequences from internal noise, print to console |
| **Evolve** | Random mutations of edge weights; spontaneous new synapses |
| **Crawl** | Fetch and learn from random web pages (requires internet permission) |
| **Heal** | Clamp extreme edge weights to sane bounds |

Mood influences which processes activate: joy favors abstraction and crawling; pain favors forgetting and evolution. Sleep logs are saved to `self/sleep/`.

### Conversation

When you type text, Qwile:
1. Perceives — tokenizes input into the highest-level known concepts
2. Understands — predicts each concept before seeing it, learns from the difference (System 1)
3. Responds — simulates forward through the graph to generate a reply (System 2)

Early responses will be noise. With experience, they become increasingly coherent — first at the character level, then words, then phrases.

### Learning

Qwile learns from multiple sources:

| Source | How | Command |
|--------|-----|---------|
| Console input | Real-time, concept by concept | *(just type)* |
| Files | Read and perceive byte stream | `/learn <path>` |
| Directories | Scan all text files recursively | `/learn <dir>` |
| Web pages | Fetch, strip HTML, perceive text | `/web <url>` |

File learning accepts: `.txt`, `.md`, `.py`, `.json`, `.csv`, `.html`, `.xml`, `.rs`, `.go`, `.js`. Paths outside the project directory require storage permission.

### Life Cycle

**Birth** — on first run. The seed is the exact local datetime with microseconds. This moment determines the initial genetic pattern of synapses, making every instance unique. Saved to `self/birth.json`.

**Life** — the main loop. Perceive, understand, respond. Sleep when idle. Dream when quiet.

**Reincarnation** — on subsequent runs. Loads the previous brain with slight random mutations (1% of edges). A new life is never an exact copy of the old one.

---

## Quick Start

```bash
python qwile.py
```

That's it. Qwile is born.

### Commands

```
(any text)      perceive + learn + predict + reply
/learn <path>   learn from a file or directory
/web <url>      learn from a web page
/sleep          sleep now (abstract, dream, evolve, heal)
?               help + status
```

State is saved automatically on exit (`Ctrl+C`).

### Training

The more text Qwile processes, the better it predicts. Feed it books, code, conversations:

```bash
# In the Qwile console:
> /learn path/to/book.txt
> /learn path/to/project/
> /web https://example.com
```

After sufficient training on English text, Qwile will predict English. After Russian — Russian. After code — code. It learns the structure of whatever it receives.

---

## Structure

```
qwile/
├── qwile.py              the body — the only executable
├── readme.md             this file
└── self/                 the memory — everything that WAS
    ├── birth.json        birth certificate (seed, datetime)
    ├── state.json        current state (mood, age, epoch, accuracy)
    ├── brain/
    │   ├── nodes.json    concept vocabulary (id → byte sequence)
    │   └── edges.json    synaptic weights (source → target → weight)
    ├── memory/           records of learning events
    ├── dreams/           dream transcripts
    └── sleep/            sleep logs
```

---

## Requirements

- Python 3.6+
- No external dependencies — standard library only

Cross-platform: Linux, macOS, Windows, Android (via Termux).

---

## License

MIT
