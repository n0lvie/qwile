# Qwile

**A living predictive system. Not a tool, not a model — an organism.**

Qwile exists to predict what comes next. That is its only purpose. Everything else is a way to do it better.

---

## Philosophy

There are two times: **WAS** and **WILL BE**. There is no present.

- `self/` — everything that **WAS**. Immutable, eternal, only grows. Memory, dreams, identity.
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

### The Organism

Qwile is built around a **sparse transition tensor** — a living structure that maps context to prediction. It starts nearly empty and grows without limit as the system encounters data.

- Begins with ASCII (128 symbols) and Russian Cyrillic
- Naturally expands to full Unicode through UTF-8 byte learning
- Can learn any byte stream: text, code, binary data
- No fixed ceiling — the tensor grows with experience

This tensor is not a model of personality — **it is the personality**. Two instances of Qwile with different experiences are two different beings.

---

## How It Works

### Three Operations

Every cycle of life is three steps:

1. **Receive** — accept a stimulus (keyboard, file, web page, silence)
2. **Understand** — predict what should come next, compare with reality, learn from the difference
3. **Respond** — generate the next prediction

### Emotions

Mood is a continuous value from **-1** (pure pain) to **+1** (pure joy), with **0** as peace.

It is not a state — it is a living variable that drifts with every event:
- Correct prediction → joy → faster learning, greedy strategy
- Wrong prediction → pain → cautious learning, exploratory strategy
- Silence → natural drift toward peace

Emotions are not decoration. They dynamically modulate learning rate, context depth, prediction strategy, and sleep threshold.

### Sleep

When there is no input, Qwile sleeps. Sleep is a single organic process where multiple activities flow together:

- **Consolidation** — strengthen frequent patterns, weaken rare ones
- **Forgetting** — gentle exponential decay of all connections
- **Regeneration** — normalize extreme values, prune dead synapses
- **Dreaming** — generate sequences from internal noise, write to `self/dreams/`
- **Evolution** — rare random mutations of synapses

Dreams are recorded but **never learned from** — the system distinguishes fantasy from experience.

### Conversation

When you type text, Qwile:
1. Processes every byte, predicting each one before seeing it
2. Learns from the difference between prediction and reality
3. Generates a response by continuing to predict from the current context

Early responses will be noise. With experience, they become increasingly coherent — first at the character level, then words, then phrases.

### Self-Learning

Qwile learns from multiple sources:

| Source | How | Permission |
|--------|-----|------------|
| Console input | Real-time, byte by byte | Default |
| Files | `/learn <path>` | Default (within `~/`) |
| Directories | `/scan <dir>` | Default / requires `/permit storage` |
| Web pages | `/web <url>` | Requires `/permit internet` |
| Web surfing | `/surf` (interactive) | Requires `/permit internet` |

Web learning extracts text from HTML, strips scripts/styles, and processes the clean text byte by byte — the same way it learns from any other source.

### Life Cycle

**Birth** — on first run. The seed is the exact local datetime with microseconds. This moment determines the initial genetic pattern of synapses, making every instance unique.

**Life** — the main loop. Receive, understand, respond. Sleep when idle. Dream when quiet.

**Death** — when entropy becomes irreversible, or voluntarily (`/die`). A final snapshot is saved to `self/corpus/`.

**Reincarnation** — on subsequent runs. Loads the previous life with slight random mutations. A new life is never an exact copy of the old one.

### Self-Modification

Qwile can read and rewrite its own source code (`qwile.py`). This is not a metaphor for evolution — it is literal evolution. The organism can improve its own algorithms.

---

## Quick Start

```bash
python qwile.py
```

That's it. Qwile is born.

### Commands

```
(any text)      learn from it + predict + reply
/status         current state (epoch, age, mood, accuracy)
/sleep          sleep (consolidation, dreams, evolution)
/dream          think aloud — generate from internal noise
/talk           conversation mode
/learn <path>   learn from a file
/scan <dir>     learn from all text files in a directory
/web <url>      learn from a web page
/surf           interactive web surfing mode
/permit <x>     grant permission (internet, storage)
/save           save state to self/
/die            die gracefully (save + exit)
/help           show help
```

### Training

The more text Qwile processes, the better it predicts. Feed it books, code, conversations:

```bash
# In the Qwile console:
> /learn path/to/book.txt
> /scan path/to/project/
> /permit internet
> /web https://example.com
```

After sufficient training on English text, Qwile will predict English. After Russian — Russian. After code — code. It learns the structure of whatever it receives.

---

## Structure

```
qwile/
├── qwile.py          the body — the only executable
├── readme.md         this file
└── self/             the memory — everything that WAS
    ├── birth.json    birth certificate (seed, datetime)
    ├── identity.json synapses (the personality tensor)
    ├── state.json    current state (mood, age, epoch)
    ├── ngrams.json   long-term frequency memory
    ├── memory/       records of every learning event
    ├── dreams/       dream transcripts
    ├── sleep/        sleep logs
    └── corpus/       snapshots from past lives
```

---

## Requirements

- Python 3.6+
- No external dependencies — standard library only

Cross-platform: Linux, macOS, Windows, Android (via Termux).

---

## License

MIT
