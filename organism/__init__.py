from .soul import Soul

class Qwile:
    def __init__(self):
        import os
        from pathlib import Path
        self.soul = Soul(Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
    def live(self):
        self.soul.live()
