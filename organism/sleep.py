import time
import random
from .constants import PRESENCE, DUALITY, EMERGENCE

class Sleep:
    """Сон. Консолидация, интеграция, сновидения."""
    def __init__(self):
        self.dreaming = False
        self.depth = 0.0

    def should_sleep(self, substrate, drives) -> bool:
        """Организм сам решает."""
        return substrate.is_critical() or drives.rest > 0.8

    def sleep_cycle(self, substrate, mind, memory, qualia, identity, log_cb):
        """Полный цикл сна."""
        self.dreaming = True
        self.depth = 1.0
        log_cb("drifting into sleep...")

        dream_count = EMERGENCE + int(abs(qualia.presence) * DUALITY)
        episodes = memory.random_episodes(dream_count)

        # Фаза сновидений и консолидации
        dreams = []
        for (text,) in episodes:
            for w in memory.tokenize(text):
                dim = memory.vocab.get(w)
                if dim is not None:
                    mind.perturb(dim, random.gauss(0, 0.05))
                    # Укрепление мировоззрения во сне
                    identity.update_worldview(dim, qualia.valence)
            dreams.append(text)
            time.sleep(0.05)

        # Консолидация (создание новых ассоциаций из случайных эпизодов)
        if len(episodes) >= DUALITY:
            for i in range(len(episodes) - PRESENCE):
                combined = episodes[i][0] + " " + episodes[i + PRESENCE][0]
                memory.remember(combined[:200], qualia.signature(), 0)

        identity.crystallize(memory, qualia)
        substrate.rest(0.5)

        self.dreaming = False
        self.depth = 0.0
        
        # Сохранение сна
        if dreams:
            dream_text = " ... ".join(dreams)[:500]
            memory.save_dream(dream_text)

        log_cb(f"awoke | {len(episodes)} dreams | identity: {identity.introspect()}")
