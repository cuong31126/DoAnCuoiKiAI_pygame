from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

from core.obstacle import Obstacle
from core.patient import Patient
from core.task import Task


GridPos = Tuple[int, int]


@dataclass
class HospitalMap:
    level: int
    title: str
    grid: List[List[int]]
    start: GridPos
    tasks: List[Task]
    patients: List[Patient] = field(default_factory=list)
    charge_stations: List[GridPos] = field(default_factory=list)
    dynamic_obstacles: List[Obstacle] = field(default_factory=list)
    battery_limit: int = 80
    time_limit: float = 120.0
    vision_radius: int = 4

    @property
    def rows(self):
        return len(self.grid)

    @property
    def cols(self):
        return len(self.grid[0]) if self.grid else 0

    def in_bounds(self, pos: GridPos):
        row, col = pos
        return 0 <= row < self.rows and 0 <= col < self.cols

    def passable(self, pos: GridPos, extra_blocked: Optional[Iterable[GridPos]] = None):
        if not self.in_bounds(pos):
            return False
        if self.grid[pos[0]][pos[1]] == 1:
            return False
        if extra_blocked and pos in set(extra_blocked):
            return False
        return True

    def cell_cost(self, pos: GridPos):
        value = self.grid[pos[0]][pos[1]]
        if value == 2:
            return 5
        return 1

    def neighbors(self, pos: GridPos, extra_blocked: Optional[Iterable[GridPos]] = None):
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nxt = (pos[0] + dr, pos[1] + dc)
            if self.passable(nxt, extra_blocked):
                yield nxt

    def dynamic_positions(self) -> Set[GridPos]:
        return {obstacle.pos for obstacle in self.dynamic_obstacles}

    def predicted_dynamic_positions(self, steps=3) -> Set[GridPos]:
        positions = set(self.dynamic_positions())
        for obstacle in self.dynamic_obstacles:
            positions.update(obstacle.predicted_positions(steps))
        return positions

    def visible_cells(self, center: GridPos, radius: Optional[int] = None):
        radius = self.vision_radius if radius is None else radius
        visible = set()
        for row in range(center[0] - radius, center[0] + radius + 1):
            for col in range(center[1] - radius, center[1] + radius + 1):
                pos = (row, col)
                if self.in_bounds(pos) and abs(row - center[0]) + abs(col - center[1]) <= radius:
                    visible.add(pos)
        return visible

    def reset(self):
        for task in self.tasks:
            task.completed = False
        for obstacle in self.dynamic_obstacles:
            obstacle.reset()

    def remaining_tasks(self):
        return [task for task in self.tasks if not task.completed]


def _base_grid():
    rows, cols = 15, 20
    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    for col in range(2, 18):
        if col not in (5, 10, 15):
            grid[3][col] = 1
    for col in range(0, 16):
        if col not in (3, 8, 13):
            grid[7][col] = 1
    for col in range(4, 20):
        if col not in (6, 12, 17):
            grid[11][col] = 1
    for row in range(4, 11):
        if row not in (6, 9):
            grid[row][6] = 1
    for row in range(1, 7):
        if row not in (2, 5):
            grid[row][14] = 1
    for pos in ((2, 8), (2, 9), (4, 10), (5, 10), (8, 15), (9, 15), (13, 8), (13, 9)):
        grid[pos[0]][pos[1]] = 2
    return grid


def build_demo_level(level):
    grid = _base_grid()
    start = (1, 1)
    charge_stations = [(13, 1), (1, 18), (8, 10)]
    for station in charge_stations:
        grid[station[0]][station[1]] = 3

    if level == 1:
        tasks = [Task("T1", "Deliver medicine", (13, 18), priority=1)]
        title = "Level 1 - Basic Delivery"
        battery = 90
        time_limit = 90
        obstacles = []
    elif level == 2:
        tasks = [
            Task("T1", "Medicine A", (1, 17), priority=2),
            Task("T2", "Lab sample", (5, 18), priority=1),
            Task("T3", "Patient support", (10, 2), priority=3),
            Task("T4", "Medicine B", (13, 15), priority=2),
        ]
        title = "Level 2 - Multi Patient Delivery"
        battery = 100
        time_limit = 120
        obstacles = []
    elif level == 3:
        tasks = [
            Task("T1", "Ward A medicine", (1, 17), priority=2),
            Task("T2", "Lab tube", (13, 18), priority=2),
            Task("T3", "Patient lift", (10, 2), priority=3),
            Task("T4", "Sterile kit", (5, 18), priority=1),
        ]
        title = "Level 3 - Battery Optimization"
        battery = 30
        time_limit = 150
        obstacles = []
    elif level == 4:
        tasks = [
            Task("T1", "Deliver sample", (13, 18), priority=2),
            Task("T2", "Assist room", (1, 17), priority=1),
        ]
        title = "Level 4 - Dynamic Obstacles"
        battery = 90
        time_limit = 120
        obstacles = [
            Obstacle("Nurse cart", [(5, 9), (5, 10), (5, 11), (5, 12)], tick_rate=0.48),
            Obstacle("Patient", [(8, 12), (9, 12), (10, 12)], tick_rate=0.62),
            Obstacle("Bed", [(12, 16), (12, 17), (12, 18)], tick_rate=0.7),
        ]
    elif level == 5:
        tasks = [
            Task("E1", "Emergency drug", (5, 18), priority=5, deadline=24, urgent=True, reward=140),
            Task("T1", "Blood sample", (10, 2), priority=3, deadline=45, reward=110),
            Task("T2", "Routine meds", (13, 15), priority=2, deadline=75, reward=100),
            Task("T3", "Patient support", (1, 17), priority=1, deadline=85, reward=100),
        ]
        title = "Level 5 - Emergency Priority CSP"
        battery = 75
        time_limit = 110
        obstacles = []
    else:
        tasks = [
            Task("E1", "Emergency drug", (5, 18), priority=5, deadline=25, urgent=True, reward=150),
            Task("T1", "Lab sample", (13, 18), priority=3, deadline=70, reward=110),
            Task("T2", "Charge patient device", (10, 2), priority=2, deadline=90, reward=100),
            Task("T3", "Routine meds", (1, 17), priority=1, deadline=100, reward=100),
        ]
        title = "Level 6 - Hospital Crisis"
        battery = 55
        time_limit = 105
        obstacles = [
            Obstacle("Moving bed", [(5, 9), (5, 10), (5, 11), (5, 12)], tick_rate=0.48),
            Obstacle("Crowd", [(9, 11), (9, 12), (9, 13)], tick_rate=0.58),
        ]

    patients = [
        Patient(f"P{i + 1}", task.name, task.target, "care", task.priority)
        for i, task in enumerate(tasks)
    ]
    return HospitalMap(
        level=level,
        title=title,
        grid=grid,
        start=start,
        tasks=tasks,
        patients=patients,
        charge_stations=charge_stations,
        dynamic_obstacles=obstacles,
        battery_limit=battery,
        time_limit=time_limit,
        vision_radius=4,
    )

