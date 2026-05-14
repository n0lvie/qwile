PAIN = -1
VOID = 0
PRESENCE = 1
DUALITY = 2
EMERGENCE = 3

def threshold(presence: float, surprise: float, age: int) -> float:
    """Адаптивный порог — функция Триады и возраста."""
    return EMERGENCE + (abs(presence) * DUALITY) - (surprise * PRESENCE) + min(age * 0.0001, 1.0)

def pace(presence: float, surprise: float) -> float:
    """Скорость внутренних часов (меньше — быстрее)."""
    return PRESENCE / (PRESENCE + abs(presence) + surprise + 0.1)

def decay(presence: float, age: int) -> float:
    """Скорость угасания активаций."""
    return PRESENCE - PRESENCE / (EMERGENCE + abs(presence) + min(age * 0.0001, PRESENCE))
