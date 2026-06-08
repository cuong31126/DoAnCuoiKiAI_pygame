from dataclasses import dataclass, field
from typing import List, Tuple


GridPos = Tuple[int, int]


@dataclass
class Obstacle:
    """Dynamic hallway obstacle that walks back and forth over a path."""

    name: str
    path: List[GridPos]
    index: int = 0
    direction: int = 1
    tick_rate: float = 0.55
    timer: float = 0.0
    start_index: int = field(init=False)

    def __post_init__(self):
        self.start_index = self.index

    @property
    def pos(self):
        return self.path[self.index]

    def reset(self):
        self.index = self.start_index
        self.direction = 1
        self.timer = 0.0

    def update(self, dt):
        if len(self.path) <= 1:
            return False
        self.timer += dt
        if self.timer < self.tick_rate:
            return False
        self.timer -= self.tick_rate
        nxt = self.index + self.direction
        if nxt < 0 or nxt >= len(self.path):
            self.direction *= -1
            nxt = self.index + self.direction
        self.index = nxt
        return True

    def predicted_positions(self, steps=3):
        if not self.path:
            return []
        idx = self.index
        direction = self.direction
        positions = []
        for _ in range(steps):
            nxt = idx + direction
            if nxt < 0 or nxt >= len(self.path):
                direction *= -1
                nxt = idx + direction
            idx = nxt
            positions.append(self.path[idx])
        return positions

