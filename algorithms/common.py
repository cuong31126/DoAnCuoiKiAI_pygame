from settings import GRID_COLS, GRID_ROWS


BLOCKED_VALUES = {1, 2, 3, 4}


def in_bounds(pos):
    row, col = pos
    return 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS


def passable(matrix, pos):
    row, col = pos
    return matrix[row][col] not in BLOCKED_VALUES


def neighbors(matrix, pos):
    row, col = pos
    # Thu tu uu tien: phai, xuong, trai, len de duong di de nhin hon.
    for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        nxt = (row + dr, col + dc)
        if in_bounds(nxt) and passable(matrix, nxt):
            yield nxt


def reconstruct_path(parent, start, goal):
    if goal not in parent and goal != start:
        return []
    node = goal
    path = [node]
    while node != start:
        node = parent[node]
        path.append(node)
    path.reverse()
    return path


def merge_paths(first, second):
    if not first:
        return second[:]
    if not second:
        return first[:]
    return first + second[1:]
