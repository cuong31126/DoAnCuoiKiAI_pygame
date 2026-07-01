from dataclasses import dataclass, field
from typing import List, Tuple


GridPos = Tuple[int, int]


@dataclass
class Obstacle:
    """Dynamic hallway obstacle that walks back and forth over a path."""

    name: str
    path: List[GridPos]
    index: int = 0  # lấy index vd vị trí 5,9 trong Obstacle("Nurse cart", [(5, 9), (5, 10), (5, 11), (5, 12)], tick_rate=0.48), của file map.py 
    direction: int = 1
    tick_rate: float = 0.55
    timer: float = 0.0
    start_index: int = field(init=False)

    def __post_init__(self):
        self.start_index = self.index

    @property
    def pos(self):
        return self.path[self.index] # ban đầu là path[0] = (5, 9) , 

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

# chạy giả lập hướng di chuyển của vật cản 
# áp dụng cho thuật toán and or search 
    def predicted_positions(self, steps=3):
        if not self.path:
            return []
        idx = self.index # sao chép chỉ số index ht của vật cản 
        direction = self.direction # sao chép hướng di chuyển của vật cản 
        positions = []  # ds chứa tọa độ dự án 
        for _ in range(steps):
            nxt = idx + direction # tính toán chỉ số ô tiếp theo giả định 
            # cơ chế quay đầu khi chạm biên : 
            if nxt < 0 or nxt >= len(self.path):
                # vật cản đi chạm vào tường tự động quay đầu ngược lại 
                direction *= -1
                nxt = idx + direction
            idx = nxt
            positions.append(self.path[idx]) # lưu tọa độ ô đó vào ds dự kiến 
        return positions
    
# Khởi tạo trạng thái tạm thời:
# idx = 2 (tọa độ tạm thời là (5, 5))
# direction = 1
# positions = []

# Vòng lặp 1 (Bước đi thứ 1):
# nxt = idx + direction 
# ⟹ nxt = 2 + 1 = 3.
# Kiểm tra chạm biên: if nxt < 0 or nxt >= len(self.path): (tương đương 3 < 0 hoặc 3 >= 3).

# Kết quả bước 1: positions = [(4, 5)], hướng đi hiện tại là đi lùi (-1).

# Vòng lặp 2 (Bước đi thứ 2):
# nxt = idx + direction 
# ⟹ nxt = 1 + (-1) = 0.
# Kiểm tra chạm biên: if 0 < 0 or 0 >= 3