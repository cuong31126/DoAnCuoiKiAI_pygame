from dataclasses import dataclass
from typing import Tuple


GridPos = Tuple[int, int]


@dataclass
class Patient:
    patient_id: str
    name: str
    room: GridPos
    need: str
    priority: int = 1

