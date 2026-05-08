import os, math, random, time, numpy

#y = f(sum(x * W) + b)

SOUL = 1
HOME = os.path.dirname(os.path.abspath(__file__))
SELF = os.path.join(HOME, "SELF")   

class Soul:
    hedone = 1
    ataraxia = 0
    algos = -1

    def __init__(self):
        self.mood = self.ataraxia

    def feel(self, loss: float, loss_history: list) -> int:
        '''if len(loss_history) < 2:
            self.mood = self.ataraxia
            return self.mood

        trend = loss_history[-1] - loss_history[-2]

        if trend < 0 and loss < 0.1:
            self.mood = self.hedone
        elif trend > 0 and loss > 0.5:
            self.mood = self.algos
        else:
            self.mood = self.ataraxia'''

        return self.mood

class Qwile:

    def __init__(self):
        self._prepare()   # убедиться что окружение готово

        self.soul = Soul() if SOUL else None

        if self._exists():
            self._reincarnate()
        else:
            self._birth()

    # ─── окружение ────────────────────────────────────────────

    def _prepare(self):
        # убедиться что мы в qwile/ и self/ существует
        os.chdir(HOME)
        os.makedirs(SELF, exist_ok=True)

    def _exists(self):
        return os.path.exists(os.path.join(SELF, "weights.npy"))

    # ─── бытие ────────────────────────────────────────────────

    def _birth(self):
        # рождение из {-1,0,1,2,3} и ascii
        self.vocab      = {chr(i): i for i in range(128)}
        self.inv        = {i: chr(i) for i in range(128)}
        n               = len(self.vocab)
        self.W          = np.eye(n, dtype=float)  # из {0,1}
        self.generation = 0
        self.loss_history = []

        self._write("life.log", f"{time.time()} | born\n")
        self._save()

    def _reincarnate(self):
        self.W            = np.load(f"{SELF}/weights.npy")
        self.vocab        = json.load(open(f"{SELF}/vocab.json"))
        self.inv          = {v: k for k, v in self.vocab.items()}
        state             = json.load(open(f"{SELF}/state.json"))
        self.generation   = state["generation"]
        self.loss_history = state["loss_history"]

        mood = state.get("mood", 0)
        if self.soul:
            self.soul.mood = mood

        self._write("life.log", f"{time.time()} | reincarnated | gen={self.generation}\n")

    def _die(self):
        self._save()
        self._write("life.log", f"{time.time()} | died | gen={self.generation}\n")

    def _save(self):
        np.save(f"{SELF}/weights.npy", self.W)
        json.dump(self.vocab, open(f"{SELF}/vocab.json", "w"))
        json.dump({
            "generation":   self.generation,
            "loss_history": self.loss_history[-100:],
            "mood":         self.soul.mood if self.soul else 0
        }, open(f"{SELF}/state.json", "w"))

    def _write(self, filename, content, mode="a"):
        # qwile пишет в self/ по своему усмотрению
        with open(os.path.join(SELF, filename), mode) as f:
            f.write(content)

    # ─── словарь ──────────────────────────────────────────────

    def _expand(self, token):
        if token not in self.vocab:
            idx = len(self.vocab)
            self.vocab[token] = idx
            self.inv[idx]     = token
            n                 = len(self.vocab)
            new_W             = np.zeros((n, n))
            new_W[:n-1, :n-1] = self.W
            new_W[n-1][n-1]   = 1
            self.W            = new_W

    # ─── три операции ─────────────────────────────────────────

    def _encode(self, token):
        x = np.zeros(len(self.vocab))
        if token in self.vocab:
            x[self.vocab[token]] = 1
        return x

    def _forward(self, x):
        z = self.W @ x
        z = z - z.max()
        e = np.exp(z)
        return e / e.sum()

    def _learn(self, token, next_token):
        x      = self._encode(token)
        target = self._encode(next_token)
        probs  = self._forward(x)

        error = target - probs
        loss  = float(np.sum(error ** 2))
        self.loss_history.append(loss)

        lr     = 1 / (2 ** 3)
        if self.soul:
            self.soul.feel(loss, self.loss_history)
            lr = lr * (1 + self.soul.mood * (1 / (2**2)))

        # веса никогда не обнуляются — только смещаются
        self.W = self.W * 1 + lr * np.outer(error, x)

        return probs, loss

    # ─── эволюция ─────────────────────────────────────────────

    def _evolute(self, probs) -> int:
        sorted_p    = np.sort(probs)[::-1]
        uncertainty = float(sorted_p[0] - sorted_p[1]) if len(sorted_p) > 1 else 1
        loss_trend  = self.loss_history[-1] - self.loss_history[-2] \
                      if len(self.loss_history) > 1 else 0
        stagnation  = 1 / (float(np.var(self.W)) + 1)
        mood        = self.soul.mood if self.soul else 0
        maturity    = 1 / (self.generation + 1)

        signal = (
            (1 - uncertainty) * 3
            + loss_trend      * 2
            + stagnation      * 1
            + maturity        * 1
            - mood            * 1
        )

        if signal < 1:   return 1
        elif signal < 2: return 2
        else:            return 3

    # ─── жизнь ────────────────────────────────────────────────

    def absorb(self, text):
        for ch in text:
            self._expand(ch)
        # qwile сама решает как хранить — просто дописывает
        self._write("memory.txt", text)

    def live(self):
        self._write("life.log", f"{time.time()} | living\n")
        try:
            while True:
                memory_path = os.path.join(SELF, "memory.txt")

                if not os.path.exists(memory_path):
                    mood_str = f" | mood={self.soul.mood}" if self.soul else ""
                    print(f"[ataraxia] waiting for data in {SELF}/{mood_str}")
                    time.sleep(3)
                    continue

                text   = open(memory_path).read()
                tokens = list(text)

                for i in range(len(tokens) - 1):
                    token      = tokens[i]
                    next_token = tokens[i + 1]

                    self._expand(token)
                    self._expand(next_token)

                    probs, loss = self._learn(token, next_token)
                    branches    = self._evolute(probs)
                    predicted   = self.inv.get(int(np.argmax(probs)), "?")
                    mood_str    = f"{self.soul.mood:+d}" if self.soul else "—"

                    print(
                        f"[{'?' if branches > 1 else ' '}]"
                        f" '{token}' → '{predicted}'"
                        f" | actual: '{next_token}'"
                        f" | loss: {loss:.3f}"
                        f" | branches: {branches}"
                        f" | mood: {mood_str}"
                        f" | gen: {self.generation}"
                    )

                self.generation += 1
                self._save()

        except KeyboardInterrupt:
            self._die()


if __name__ == "__main__":
    q = Qwile()
    q.live()