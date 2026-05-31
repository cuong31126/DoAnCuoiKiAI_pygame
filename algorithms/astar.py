import heapq
from itertools import permutations

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

    best = None
    # 5 sinh vat nen duyet permutation van nhanh va de tin cay.
    for order in permutations(range(1, len(points))):
        current = 0
        steps = 0
        arrival = {}
        feasible = True
        for idx in order:
            steps += pair_costs[(current, idx)]
            arrival_seconds = steps * seconds_per_step
            creature = creatures[idx - 1]
            arrival[idx - 1] = arrival_seconds
            if arrival_seconds >= creature["timer"]:
                feasible = False
                break
            current = idx
        if not feasible:
            continue
        total_steps = steps + pair_costs[(current, 0)]
        if best is None or total_steps < best["steps"]:
            best = {
                "order": [idx - 1 for idx in order],
                "steps": total_steps,
                "arrival": arrival,
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
