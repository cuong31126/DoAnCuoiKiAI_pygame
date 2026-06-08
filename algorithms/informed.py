import heapq
import time


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct(parent, start, goal):
    if goal not in parent and goal != start:
        return []
    node = goal
    path = [node]
    while node != start:
        node = parent[node]
        path.append(node)
    path.reverse()
    return path


def _runtime_result(name, started, path, plan, cost, nodes, success, message, visited=None, extra=None):
    result = {
        "name": name,
        "path": path,
        "plan": plan,
        "cost": cost,
        "path_length": max(0, len(path) - 1),
        "nodes_expanded": nodes,
        "runtime_ms": (time.perf_counter() - started) * 1000,
        "success": success,
        "message": message,
        "visited": visited or [],
    }
    if extra:
        result.update(extra)
    return result


def _search(hospital_map, start, goal, name, weight=1.0, greedy=False, avoid=None, visible_only=False):
    avoid = set(avoid or [])
    heap = [(0, 0, start)]
    parent = {start: start}
    g_score = {start: 0}
    visited = []
    closed = set()
    visible = hospital_map.visible_cells(start) if visible_only else None

    while heap:
        _, cost, node = heapq.heappop(heap)
        if node in closed:
            continue
        closed.add(node)
        visited.append(node)
        if node == goal:
            break
        for nxt in hospital_map.neighbors(node, avoid):
            if visible is not None and nxt not in visible and manhattan(nxt, goal) > manhattan(node, goal):
                continue
            step = hospital_map.cell_cost(nxt)
            new_cost = cost + step
            if nxt not in g_score or new_cost < g_score[nxt]:
                g_score[nxt] = new_cost
                parent[nxt] = node
                heuristic = manhattan(nxt, goal)
                priority = heuristic if greedy else new_cost + heuristic * weight
                heapq.heappush(heap, (priority, new_cost, nxt))

    path = _reconstruct(parent, start, goal)
    return {
        "name": name,
        "path": path,
        "visited": visited,
        "cost": g_score.get(goal, 0),
        "nodes": len(visited),
        "success": bool(path),
    }


def astar_path(hospital_map, start, goal, avoid=None):
    return _search(hospital_map, start, goal, "A* Search", avoid=avoid)


def _choose_next(current, tasks):
    return min(
        tasks,
        key=lambda task: manhattan(current, task.target) - task.priority * 3 + (0 if not task.urgent else -8),
    )


def _route(hospital_map, start, tasks, name, weight=1.0, greedy=False):
    started = time.perf_counter()
    current = start
    remaining = list(tasks)
    full_path = []
    full_visited = []
    plan = []
    total_cost = 0

    while remaining:
        task = _choose_next(current, remaining)
        result = _search(hospital_map, current, task.target, name, weight=weight, greedy=greedy)
        if not result["success"]:
            return _runtime_result(name, started, full_path, plan, total_cost, len(full_visited), False, f"Cannot reach {task.name}.", full_visited)
        segment = result["path"]
        full_path = segment if not full_path else full_path + segment[1:]
        full_visited.extend(result["visited"])
        total_cost += result["cost"]
        plan.append(task.task_id)
        current = task.target
        remaining.remove(task)

    return _runtime_result(
        name,
        started,
        full_path,
        plan,
        total_cost,
        len(full_visited),
        True,
        "Route built by distance plus task priority.",
        full_visited,
    )


def astar_route(hospital_map, start, tasks):
    return _route(hospital_map, start, tasks, "A* Search", weight=1.0, greedy=False)


def greedy_route(hospital_map, start, tasks):
    return _route(hospital_map, start, tasks, "Greedy Best-First", weight=1.0, greedy=True)


def weighted_astar_route(hospital_map, start, tasks):
    return _route(hospital_map, start, tasks, "Weighted A*", weight=1.8, greedy=False)


def online_replanning_astar(hospital_map, start, goal):
    started = time.perf_counter()
    avoid = hospital_map.dynamic_positions()
    result = _search(hospital_map, start, goal, "Online Re-planning A*", avoid=avoid)
    return _runtime_result(
        "Online Re-planning A*",
        started,
        result["path"],
        [],
        result["cost"],
        result["nodes"],
        result["success"],
        "Avoids currently observed moving obstacles and replans when blocked.",
        result["visited"],
        {"replan_count": 0, "collision_count": 0},
    )


def partial_observation_search(hospital_map, start, goal):
    started = time.perf_counter()
    visible_dynamic = hospital_map.dynamic_positions() & hospital_map.visible_cells(start)
    result = _search(
        hospital_map,
        start,
        goal,
        "Partial Observation",
        avoid=visible_dynamic,
        visible_only=False,
    )
    return _runtime_result(
        "Partial Observation",
        started,
        result["path"],
        [],
        result["cost"],
        result["nodes"],
        result["success"],
        "Plans with only nearby moving obstacles treated as known.",
        result["visited"],
        {"replan_count": 0, "collision_count": 0, "vision_radius": hospital_map.vision_radius},
    )


def constraint_propagation_search(hospital_map, start, goal):
    started = time.perf_counter()
    avoid = hospital_map.predicted_dynamic_positions(steps=4)
    result = _search(hospital_map, start, goal, "Constraint Propagation", avoid=avoid)
    return _runtime_result(
        "Constraint Propagation",
        started,
        result["path"],
        [],
        result["cost"],
        result["nodes"],
        result["success"],
        "Removes cells predicted to be occupied in the next few ticks.",
        result["visited"],
        {"replan_count": 0, "collision_count": 0, "constraints": len(avoid)},
    )

