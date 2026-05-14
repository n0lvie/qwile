import math
from .constants import PRESENCE, DUALITY

class Qualia:
    """Пятимерное пространство квалиа. Триада + валентность + возбуждение."""
    def __init__(self):
        self.presence = 0.0    # -1..1  отношение к себе
        self.surprise = 0.0    #  0..1  разрыв ожидание/реальность
        self.time_sense = 0.0  # -1..1  тяга прошлого vs вектор будущего
        self.valence = 0.0     # -1..1  боль/удовольствие
        self.arousal = 0.0     #  0..1  возбуждение/покой

    def feel(self, mind, memory):
        """Вычислить текущее квалиа из состояния."""
        # Surprise (разрыв предсказания)
        dims = set(mind.state) | set(mind.predicted)
        if dims:
            total_surp = sum((mind.state.get(d, 0.0) - mind.predicted.get(d, 0.0)) ** DUALITY for d in dims)
            self.surprise = math.sqrt(total_surp / max(PRESENCE, len(dims)))
        else:
            self.surprise = 0.0

        # Presence (энергия состояния)
        if mind.state:
            energy = sum(v * v for v in mind.state.values())
            self.presence = math.tanh(math.sqrt(energy))
        else:
            self.presence = 0.0

        # Time Sense (прошлое vs будущее)
        confidence = PRESENCE - self.surprise
        memory_pull = math.tanh(memory.episode_count() * 0.001)
        self.time_sense = math.tanh(memory_pull - confidence)

        # Arousal (возбуждение: комбинация сюрприза и энергии)
        self.arousal = min(1.0, (self.surprise + abs(self.presence)) / DUALITY)

        # Valence (валентность: насколько происходящее соответствует гомеостазу)
        # Если интеграция высокая - хорошо, если хаос - плохо
        integration = mind.measure_integration()
        self.valence = math.tanh((integration - 0.5) * DUALITY)

    def mood(self) -> str:
        """Текущее настроение — эмерджентное из квалиа."""
        if self.valence < -0.3 and self.arousal > 0.6: return "anxious"
        if self.valence > 0.3 and self.arousal > 0.6: return "excited"
        if self.valence < -0.3 and self.arousal < 0.4: return "melancholic"
        if self.valence > 0.3 and self.arousal < 0.4: return "serene"
        return "observant"

    def signature(self):
        """Уникальный отпечаток момента."""
        return (self.presence, self.surprise, self.time_sense)

    def to_dict(self):
        return {
            "presence": self.presence, "surprise": self.surprise,
            "time_sense": self.time_sense, "valence": self.valence, "arousal": self.arousal
        }

    def load_dict(self, d: dict):
        self.presence = d.get("presence", 0.0)
        self.surprise = d.get("surprise", 0.0)
        self.time_sense = d.get("time_sense", 0.0)
        self.valence = d.get("valence", 0.0)
        self.arousal = d.get("arousal", 0.0)
