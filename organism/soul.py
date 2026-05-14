import os, json, time, random, threading
from pathlib import Path
from .constants import threshold, pace, PRESENCE, VOID, EMERGENCE
from .substrate import Substrate
from .mind import Mind
from .memory import Memory
from .qualia import Qualia
from .drives import Drives
from .expression import Expression
from .perception import Perception
from .sleep import Sleep
from .identity import Identity

class Soul:
    """Единство. Целое, превышающее сумму частей."""
    def __init__(self, home_dir: Path):
        self.home = home_dir
        self.self_dir = home_dir / "self"
        self.self_dir.mkdir(parents=True, exist_ok=True)
        
        self.alive = True
        self.lock = threading.Lock()
        
        self.age = 0
        self.tick_count = 0
        
        # Подсистемы
        self.substrate = Substrate()
        self.mind = Mind()
        self.memory = Memory(self.self_dir / "river.db", self.self_dir / "dreams")
        self.qualia = Qualia()
        self.drives = Drives()
        self.expression = Expression()
        self.perception = Perception()
        self.sleep = Sleep()
        self.identity = Identity()
        
        self._perms = {}
        self._load_state()

    def _say(self, msg: str):
        try:
            from datetime import datetime
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {msg}")
        except Exception:
            pass

    def tick(self):
        """Один момент бытия."""
        with self.lock:
            if self.sleep.dreaming:
                return

            self.substrate.metabolize()
            self.mind.predicted = self.mind.predict(self.qualia, self.age)
            
            # Transition
            self.mind.transition(noise_scale=(self.qualia.surprise + 0.01) * PRESENCE / (2.0 + self.age * 0.0001), 
                                 dec=PRESENCE - PRESENCE / (EMERGENCE + abs(self.qualia.presence)))
            
            self.qualia.feel(self.mind, self.memory)
            self.drives.update(self.substrate, self.qualia, self.mind)
            
            # Выражение
            press = self.expression.pressure(self.mind, self.drives)
            thresh = threshold(self.qualia.presence, self.qualia.surprise, self.age)
            
            if self.expression.should_speak(press, thresh):
                expr = self.expression.compose(self.mind, self.memory, self.qualia)
                if expr:
                    self.memory.remember(expr, self.qualia.signature(), self.age)
                    self.drives.satisfy("expression", 0.5)
            
            # Сон
            if self.sleep.should_sleep(self.substrate, self.drives):
                self.sleep.sleep_cycle(self.substrate, self.mind, self.memory, self.qualia, self.identity, self._say)
                self.drives.satisfy("rest", 1.0)
            
            self.tick_count += 1
            self.age += 1

    def perceive(self, text: str):
        with self.lock:
            self.perception.perceive(text, self.mind, self.memory, self.qualia, self.identity)

    def _stream_loop(self):
        while self.alive:
            try:
                self.tick()
                p = pace(self.qualia.presence, self.qualia.surprise)
                time.sleep(p * 0.5)
            except Exception:
                pass

    def live(self):
        self._say("qwile awakens.")
        stream = threading.Thread(target=self._stream_loop, daemon=True)
        stream.start()
        
        try:
            while self.alive:
                try:
                    line = input("  > ")
                    if line.strip() == "?":
                        self._status()
                    elif line.strip() == "/sleep":
                        with self.lock:
                            self.sleep.sleep_cycle(self.substrate, self.mind, self.memory, self.qualia, self.identity, self._say)
                    elif line.strip() == "/learn":
                        pass # TODO implement internet perception
                    elif line.strip():
                        text = line.strip().encode('utf-8', errors='replace').decode('utf-8')
                        self.perceive(text)
                        
                        # Даем время на возмущение
                        for _ in range(5 + int(self.qualia.surprise * 10)):
                            self.tick()
                            
                        # Сразу выдаем буфер
                        with self.lock:
                            for msg in self.expression.buffer:
                                print(f"  qwile> {msg}")
                            self.expression.buffer.clear()
                            
                except (KeyboardInterrupt, EOFError):
                    self._say("shutting down.")
                    break
        finally:
            self.alive = False
            self._save_state()
            self._say("state saved. goodbye.")

    def _status(self):
        self._say(f"age {self.age} | mood {self.qualia.mood()} | energy {self.substrate.energy:.2f} | entropy {self.substrate.entropy:.2f}")
        self._say(f"presence {self.qualia.presence:+.2f} | surprise {self.qualia.surprise:.2f} | valence {self.qualia.valence:+.2f}")
        self._say(f"memories {self.memory.episode_count()} | concepts {len(self.memory.vocab)}")
        self._say(f"dominant drive: {self.drives.dominant()} | identity: {self.identity.introspect()}")

    def _save_state(self):
        state = {
            "age": self.age,
            "tick_count": self.tick_count,
            "substrate": self.substrate.to_dict(),
            "mind": self.mind.to_dict(),
            "qualia": self.qualia.to_dict(),
            "drives": self.drives.to_dict(),
            "identity": self.identity.to_dict()
        }
        try:
            (self.self_dir / "state.json").write_text(json.dumps(state, ensure_ascii=False))
        except Exception:
            pass

    def _load_state(self):
        p = self.self_dir / "state.json"
        if p.exists():
            try:
                d = json.loads(p.read_text())
                self.age = d.get("age", 0)
                self.tick_count = d.get("tick_count", 0)
                self.substrate.load_dict(d.get("substrate", {}))
                self.mind.load_dict(d.get("mind", {}))
                self.qualia.load_dict(d.get("qualia", {}))
                self.drives.load_dict(d.get("drives", {}))
                self.identity.load_dict(d.get("identity", {}))
            except Exception:
                pass
