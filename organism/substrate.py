from .constants import PRESENCE, VOID

class Substrate:
    """Энергетическая подсистема. Гомеостаз. Метаболизм."""
    def __init__(self):
        self.energy = 1.0  # 0.0 .. 1.0
        self.entropy = 0.0 # Растёт без сна

    def metabolize(self):
        """Один цикл метаболизма. Трата энергии, накопление энтропии."""
        self.consume(0.001)
        self.entropy = min(1.0, self.entropy + 0.002)

    def consume(self, amount: float):
        """Потребление энергии на действие."""
        self.energy = max(0.0, self.energy - amount)

    def rest(self, amount: float):
        """Восстановление во сне."""
        self.energy = min(1.0, self.energy + amount)
        self.entropy = max(0.0, self.entropy - amount * 1.5)

    def is_critical(self) -> bool:
        """Организм на грани — принудительный сон."""
        return self.energy < 0.1 or self.entropy > 0.9

    def to_dict(self):
        return {"energy": self.energy, "entropy": self.entropy}

    def load_dict(self, d: dict):
        self.energy = d.get("energy", 1.0)
        self.entropy = d.get("entropy", 0.0)
