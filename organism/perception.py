import math
from .constants import PRESENCE

class Perception:
    """Восприятие как многослойная интеграция."""
    def perceive(self, text: str, mind, memory, qualia, identity) -> int:
        words = memory.tokenize(text)
        if not words:
            return 0

        # Учим новые слова
        for w in words:
            memory.learn_word(w)

        strength = PRESENCE / max(PRESENCE, math.sqrt(len(words)))
        
        # Передаем возмущения в Mind
        for i, w in enumerate(words):
            dim = memory.vocab.get(w)
            if dim is not None:
                weight = (i + PRESENCE) / len(words)
                # Учет идиосинкразии (identity)
                idio_mult = 1.0 + abs(identity.react(dim))
                mind.perturb(dim, strength * weight * idio_mult)

        # Сохранение в эпизодической памяти
        memory.remember(text, qualia.signature(), memory.episode_count())
        return len(words)
