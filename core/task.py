from dataclasses import dataclass
from typing import Optional, Tuple


GridPos = Tuple[int, int]


@dataclass
class Task:
    """A hospital delivery/support task on the grid."""

    task_id: str
    name: str
    target: GridPos
    priority: int = 1
    deadline: Optional[float] = None
    reward: int = 100
    urgent: bool = False
    completed: bool = False

    def display_name(self):
        tag = "URG" if self.urgent else f"P{self.priority}"
        return f"{self.name} [{tag}]"

