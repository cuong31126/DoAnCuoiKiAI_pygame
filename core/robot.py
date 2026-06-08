from dataclasses import dataclass, field
from typing import List, Optional, Tuple


GridPos = Tuple[int, int]


@dataclass
class Robot:
    start: GridPos
    max_battery: int = 80
    position: GridPos = field(init=False)
    battery: int = field(init=False)
    score: int = 0
    collisions: int = 0
    charging_count: int = 0
    completed_tasks: List[str] = field(default_factory=list)
    path: List[GridPos] = field(default_factory=list)
    path_index: int = 0

    def __post_init__(self):
        self.reset()

    def reset(self):
        self.position = self.start
        self.battery = self.max_battery
        self.score = 0
        self.collisions = 0
        self.charging_count = 0
        self.completed_tasks = []
        self.path = []
        self.path_index = 0

    def set_path(self, path):
        self.path = list(path or [])
        self.path_index = 0
        if self.path:
            self.position = self.path[0]

    def next_cell(self) -> Optional[GridPos]:
        if self.path_index + 1 >= len(self.path):
            return None
        return self.path[self.path_index + 1]

    def step(self):
        nxt = self.next_cell()
        if nxt is None:
            return None
        self.path_index += 1
        self.position = nxt
        self.battery -= 1
        return nxt

    def charge(self):
        self.battery = self.max_battery
        self.charging_count += 1

