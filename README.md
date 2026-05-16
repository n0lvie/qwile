# qwile

A digital organism script that learns, thinks, and remembers.

## Description

`qwile` is a Python-based autonomous agent designed to simulate a form of "digital soul". It can:
- **Learn**: Scrape information from Wikipedia or read local text files to expand its concepts and language model.
- **Remember**: Maintain an episodic memory of what it has heard, thought, or reflected upon.
- **Think**: Generate thoughts and reflections based on its learned concepts.
- **Sleep & Dream**: Process its memories, distill knowledge, and "dream" to strengthen concept links.
- **Interact**: Respond to user messages based on its internal state, character, and memories.

## Structure

- `qwile.py`: The main logic of the organism.
- `self/`: (Ignored by git) Contains the organism's state, memory, and personal data (identity, character, opinions, journal, dreams).
- `learn/`: (Ignored by git) A directory where you can place text files for the organism to read and learn from.

## Requirements

- Python 3.x
- No external dependencies (uses standard libraries only).

## Usage

Run the script:
```bash
python qwile.py
```

The organism will initialize its "soul" in the `self/` directory upon the first run.
