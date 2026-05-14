from collections import defaultdict
from .constants import PRESENCE, EMERGENCE

class Expression:
    """Речь как переполнение с грамматической кристаллизацией."""
    def __init__(self):
        self.buffer = []

    def pressure(self, mind, drives) -> float:
        """Давление выражения — функция внутреннего состояния и мотиваций."""
        if not mind.state:
            return 0.0
        energy = sum(abs(v) for v in mind.state.values())
        return (energy * PRESENCE + drives.expression) / EMERGENCE

    def compose(self, mind, memory, qualia) -> str:
        """Собрать высказывание из резонирующих фрагментов памяти."""
        active = mind.active_dims(limit=EMERGENCE + 2)
        if not active:
            return ""

        words = [memory.words.get(d) for d in active if memory.words.get(d)]
        if not words:
            return ""

        query = " ".join(words)
        memories = memory.recall(query, limit=EMERGENCE + 2)
        if not memories:
            return ""

        fragments = []
        for text, m_p, m_s, m_t, m_a in memories:
            # Насколько это воспоминание резонирует с текущим квалиа
            dist = abs(qualia.presence - m_p) + abs(qualia.surprise - m_s) + abs(qualia.time_sense - m_t)
            sim = PRESENCE / (PRESENCE + dist)
            fragments.append((text, sim))
        
        fragments.sort(key=lambda x: x[1], reverse=True)

        scores = defaultdict(float)
        for text, sim in fragments[:EMERGENCE]:
            for w in memory.tokenize(text):
                if len(w) > 1:
                    dim = memory.vocab.get(w)
                    act = mind.state.get(dim, 0.0) if dim else 0.0
                    scores[w] += sim * (PRESENCE + abs(act))

        if not scores:
            return ""

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        length = max(EMERGENCE, int(abs(qualia.presence) * 5 + qualia.surprise * 10))
        output = [w for w, _ in ranked[:length]]
        
        expr = " ".join(output)
        self.buffer.append(expr)
        return expr

    def should_speak(self, pressure: float, threshold: float) -> bool:
        return pressure > threshold
