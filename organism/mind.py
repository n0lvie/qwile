import random
from collections import defaultdict
from .constants import PRESENCE, VOID, EMERGENCE, decay

class Mind:
    """Рекурсивная самомодель с вниманием и измерением интеграции (Φ)."""
    def __init__(self):
        self.state = defaultdict(float)
        self.predicted = defaultdict(float)
        self.self_model = defaultdict(float)
        self.attention = defaultdict(float)
        self._perturbation = defaultdict(float)

    def active_dims(self, limit=None):
        ranked = sorted(self.state.items(), key=lambda x: abs(x[1]), reverse=True)
        if limit:
            ranked = ranked[:limit]
        return [k for k, v in ranked if abs(v) > 0.001]

    def predict(self, qualia, age):
        pred = defaultdict(float)
        dec = decay(qualia.presence, age)

        for dim, val in self.state.items():
            pred[dim] = val * dec

        # Влияние самомодели (рекурсия)
        for dim, val in self.self_model.items():
            pred[dim] += val * 0.1

        return pred

    def transition(self, noise_scale, dec):
        new_state = defaultdict(float)
        for dim, val in self.predicted.items():
            new_state[dim] = val

        # Возмущения от восприятия
        for dim, val in self._perturbation.items():
            new_state[dim] += val
        self._perturbation.clear()

        # Шум
        for dim in list(new_state.keys()):
            new_state[dim] += random.gauss(VOID, noise_scale)

        # Фокус внимания
        for dim in new_state:
            if dim in self.attention:
                new_state[dim] *= (1.0 + self.attention[dim])

        # Угасание и смерть активаций
        dead = []
        for dim in new_state:
            new_state[dim] *= dec
            if abs(new_state[dim]) < 0.0001:
                dead.append(dim)
        for d in dead:
            del new_state[d]

        self.state = new_state

        # Обновление самомодели (медленное следование за состоянием)
        for dim, val in self.state.items():
            self.self_model[dim] = (self.self_model[dim] * 0.9) + (val * 0.1)

    def perturb(self, dim, val):
        self._perturbation[dim] += val

    def measure_integration(self) -> float:
        """Φ — мера того, насколько состояние неразложимо на части."""
        if not self.state: return 0.0
        energy = sum(abs(v) for v in self.state.values())
        return min(1.0, energy / max(1.0, len(self.state)))

    def attend(self, dims, strength):
        self.attention.clear()
        for dim in dims:
            self.attention[dim] = strength

    def to_dict(self):
        return {
            "state": {str(k): round(v, 6) for k, v in self.state.items()},
            "self_model": {str(k): round(v, 6) for k, v in self.self_model.items()}
        }

    def load_dict(self, d: dict):
        self.state = defaultdict(float, {int(k): v for k, v in d.get("state", {}).items()})
        self.self_model = defaultdict(float, {int(k): v for k, v in d.get("self_model", {}).items()})
