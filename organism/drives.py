class Drives:
    """Интринсические мотивации."""
    def __init__(self):
        self.curiosity = 0.0      # тяга к новому (растёт от однообразия)
        self.coherence = 0.0      # тяга к целостности (растёт от фрагментации)
        self.expression = 0.0     # давление выражения (растёт от накопления)
        self.rest = 0.0           # потребность в сне (растёт от энтропии)
        self.connection = 0.0     # тяга к контакту (растёт от одиночества)

    def update(self, substrate, qualia, mind):
        """Пересчёт потребностей из текущего состояния."""
        # Curiosity растёт если низкий сюрприз
        self.curiosity = max(0.0, self.curiosity + (0.5 - qualia.surprise) * 0.01)
        
        # Coherence растёт при низкой интеграции
        self.coherence = max(0.0, self.coherence + (0.5 - mind.measure_integration()) * 0.01)
        
        # Expression растёт от высокой энергии состояния (presence)
        self.expression = max(0.0, self.expression + abs(qualia.presence) * 0.02)
        
        # Rest привязан к энтропии
        self.rest = substrate.entropy
        
        # Connection растёт со временем, падает при взаимодействии
        self.connection = min(1.0, self.connection + 0.001)

    def dominant(self) -> str:
        """Какая потребность сейчас доминирует."""
        drives = {
            "curiosity": self.curiosity,
            "coherence": self.coherence,
            "expression": self.expression,
            "rest": self.rest,
            "connection": self.connection
        }
        return max(drives.items(), key=lambda x: x[1])[0]

    def satisfy(self, drive: str, amount: float):
        if hasattr(self, drive):
            val = getattr(self, drive)
            setattr(self, drive, max(0.0, val - amount))

    def to_dict(self):
        return {
            "curiosity": self.curiosity, "coherence": self.coherence,
            "expression": self.expression, "rest": self.rest, "connection": self.connection
        }

    def load_dict(self, d: dict):
        self.curiosity = d.get("curiosity", 0.0)
        self.coherence = d.get("coherence", 0.0)
        self.expression = d.get("expression", 0.0)
        self.rest = d.get("rest", 0.0)
        self.connection = d.get("connection", 0.0)
