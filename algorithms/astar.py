import heapq

from settings import HERO_SPEED
from algorithms.common import merge_paths, neighbors, reconstruct_path


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar_path(matrix, start, goal):
    """Tim duong ngan nhat giua 2 diem bang A*."""
    heap = [(0, 0, start)]
    parent = {start: None}
    g_score = {start: 0}
    visited_order = []
    closed = set()

    while heap:
        _, cost, node = heapq.heappop(heap)
        if node in closed:
            continue
        closed.add(node)
        visited_order.append(node)
        if node == goal:
            break
        for nxt in neighbors(matrix, node):
            new_cost = cost + 1
            if nxt not in g_score or new_cost < g_score[nxt]:
                g_score[nxt] = new_cost
                parent[nxt] = node
                priority = new_cost + manhattan(nxt, goal)
                heapq.heappush(heap, (priority, new_cost, nxt))

    path = reconstruct_path(parent, start, goal)
    return {
        "path": path,
        "visited": visited_order,
        "nodes": len(visited_order),
        "cost": g_score.get(goal, 0),
        "success": bool(path),
    }


def astar_tsp(start, creatures, matrix, seconds_per_step=HERO_SPEED):
    """
    1. Dung A* tinh duong ngan nhat giua moi cap diem.
    2. Thu cac thu tu cuu bang branch and bound nho gon.
    3. Loai thu tu lam sinh vat het gio truoc khi hero den.
    4. Tra ve lo trinh toi uu va thong so hien thi.
    """
    points = [start] + [creature["grid_pos"] for creature in creatures]
    pair_paths = {}
    pair_costs = {}

    for i, a in enumerate(points):
        for j, b in enumerate(points):
            if i == j:
                pair_paths[(i, j)] = [a]
                pair_costs[(i, j)] = 0
                continue
            result = astar_path(matrix, a, b)
            if not result["success"]:
                return {
                    "safe": False,
                    "order": [],
                    "route": [],
                    "steps": 0,
                    "eta": 0,
                    "reason": "Khong co duong di giua cac diem.",
                    "pair_paths": pair_paths,
                }
            pair_paths[(i, j)] = result["path"]
            pair_costs[(i, j)] = result["cost"]

    creature_count = len(creatures)
    if creature_count == 0:
        return {
            "safe": True,
            "order": [],
            "route": [start],
            "steps": 0,
            "eta": 0,
            "arrival": {},
            "reason": "An toan",
            "pair_paths": pair_paths,
        }

    # DP Held-Karp co rang buoc deadline: state (mask, last_point)
    # luu so buoc nho nhat de cuu tap mask va dang o last_point.
    states = {}
    for creature_index, creature in enumerate(creatures):
        point_index = creature_index + 1
        steps = pair_costs[(0, point_index)]
        arrival_seconds = steps * seconds_per_step
        if arrival_seconds < creature["timer"]:
            mask = 1 << creature_index
            states[(mask, point_index)] = {
                "steps": steps,
                "order": [creature_index],
                "arrival": {creature_index: arrival_seconds},
            }

    for _ in range(1, creature_count):
        next_states = dict(states)
        for (mask, last_point), state in states.items():
            for creature_index, creature in enumerate(creatures):
                if mask & (1 << creature_index):
                    continue
                point_index = creature_index + 1
                steps = state["steps"] + pair_costs[(last_point, point_index)]
                arrival_seconds = steps * seconds_per_step
                if arrival_seconds >= creature["timer"]:
                    continue
                next_mask = mask | (1 << creature_index)
                key = (next_mask, point_index)
                if key not in next_states or steps < next_states[key]["steps"]:
                    arrival = dict(state["arrival"])
                    arrival[creature_index] = arrival_seconds
                    next_states[key] = {
                        "steps": steps,
                        "order": state["order"] + [creature_index],
                        "arrival": arrival,
                    }
        states = next_states

    best = None
    all_rescued_mask = (1 << creature_count) - 1
    for (mask, last_point), state in states.items():
        if mask != all_rescued_mask:
            continue
        total_steps = state["steps"] + pair_costs[(last_point, 0)]
        if best is None or total_steps < best["steps"]:
            best = {
                "order": state["order"],
                "steps": total_steps,
                "arrival": state["arrival"],
            }

    if best is None:
        return {
            "safe": False,
            "order": [],
            "route": [],
            "steps": 0,
            "eta": 0,
            "reason": "Khong co thu tu nao cuu kip timer.",
            "pair_paths": pair_paths,
        }

    route = []
    current = 0
    for creature_index in best["order"]:
        target = creature_index + 1
        route = merge_paths(route, pair_paths[(current, target)])
        current = target
    route = merge_paths(route, pair_paths[(current, 0)])

    return {
        "safe": True,
        "order": best["order"],
        "route": route,
        "steps": best["steps"],
        "eta": best["steps"] * seconds_per_step,
        "arrival": best["arrival"],
        "reason": "An toan",
        "pair_paths": pair_paths,
    }
