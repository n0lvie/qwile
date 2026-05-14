from collections import defaultdict
import math

class Identity:
    """Эмерджентная идентичность. Характер, ценности, мировоззрение."""
    def __init__(self):
        self.traits = defaultdict(float)     # характер (измеряется через поведение)
        self.values = defaultdict(float)     # ценности (концепты с высоким valence)
        self.worldview = defaultdict(float)  # отношение к концептам (ассоциации)

    def crystallize(self, memory, qualia):
        """Медленная кристаллизация идентичности из накопленного опыта (во сне)."""
        # Traits обновляются на основе усредненного qualia
        self.traits["anxiety"] = self.traits.get("anxiety", 0.0) * 0.99 + (1.0 if qualia.valence < -0.3 and qualia.arousal > 0.6 else 0.0) * 0.01
        self.traits["curiosity"] = self.traits.get("curiosity", 0.0) * 0.99 + (1.0 if qualia.arousal > 0.5 else 0.0) * 0.01
        self.traits["melancholy"] = self.traits.get("melancholy", 0.0) * 0.99 + (1.0 if qualia.valence < -0.3 and qualia.arousal < 0.4 else 0.0) * 0.01

    def react(self, dim: int) -> float:
        """Идиосинкразическая реакция на концепт."""
        # Возвращает множитель внимания для данного концепта
        return self.worldview.get(dim, 0.0) * self.values.get(dim, 0.0)

    def update_worldview(self, dim: int, valence: float):
        """Формирование отношения к концепту."""
        self.worldview[dim] = self.worldview.get(dim, 0.0) * 0.9 + valence * 0.1
        if abs(self.worldview[dim]) > 0.5:
            self.values[dim] = self.values.get(dim, 0.0) * 0.95 + 0.05

    def introspect(self) -> str:
        """Самоописание."""
        active_traits = [k for k, v in self.traits.items() if v > 0.5]
        if not active_traits:
            return "formless"
        return ", ".join(active_traits)

    def to_dict(self):
        return {
            "traits": dict(self.traits),
            "values": {str(k): v for k, v in self.values.items()},
            "worldview": {str(k): v for k, v in self.worldview.items()}
        }

    def load_dict(self, d: dict):
        self.traits = defaultdict(float, d.get("traits", {}))
        self.values = defaultdict(float, {int(k): v for k, v in d.get("values", {}).items()})
        self.worldview = defaultdict(float, {int(k): v for k, v in d.get("worldview", {}).items()})
