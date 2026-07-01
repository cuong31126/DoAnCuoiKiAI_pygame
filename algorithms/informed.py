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

# có tham số avoid cho thuật toán c4 gọi 
def _search(hospital_map, start, goal, name, weight=1.0, greedy=False, avoid=None):
    avoid = set(avoid or [])
    heap = [(0, 0, start)]
    parent = {start: start}
    g_score = {start: 0}
    visited = []
    closed = set()

    while heap:
        _, cost, node = heapq.heappop(heap)
        if node in closed:
            continue
        closed.add(node)
        visited.append(node)
        if node == goal:
            break
        for nxt in hospital_map.neighbors(node, avoid): # avoid c4 né các ô có vật cản động 
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


def ida_star_path(hospital_map, start, goal, avoid=None, max_iterations=180):
    avoid = set(avoid or [])
    threshold = manhattan(start, goal)
    visited = []
    best_path = []
    best_cost = 0
    iterations = 0

    def search(node, g_cost, limit, path, in_path):
        nonlocal best_path, best_cost
        f_cost = g_cost + manhattan(node, goal)
        if f_cost > limit:
            return f_cost
        visited.append(node)
        if node == goal:
            best_path = list(path)
            best_cost = g_cost
            return "FOUND"

        next_limit = float("inf")
        for nxt in hospital_map.neighbors(node, avoid):
            if nxt in in_path:
                continue
            in_path.add(nxt)
            path.append(nxt)
            result = search(nxt, g_cost + hospital_map.cell_cost(nxt), limit, path, in_path)
            if result == "FOUND":
                return "FOUND"
            if result < next_limit:
                next_limit = result
            path.pop()
            in_path.remove(nxt)
        return next_limit

    while iterations < max_iterations:
        iterations += 1
        result = search(start, 0, threshold, [start], {start})
        if result == "FOUND":
            return {
                "name": "IDA*",
                "path": best_path,
                "visited": visited,
                "cost": best_cost,
                "nodes": len(visited),
                "success": True,
                "iterations": iterations,
                "final_threshold": threshold,
            }
        if result == float("inf"):
            break
        threshold = result

    return {
        "name": "IDA*",
        "path": [],
        "visited": visited,
        "cost": 0,
        "nodes": len(visited),
        "success": False,
        "iterations": iterations,
        "final_threshold": threshold,
    }

# Điểm s = kc mahattan - độ ưu tiên * 3 + (0 nếu ko khẩn cấp, -8 nếu khẩn cấp)
# cái nào nhỏ nhất sẽ được chọn làm nhiệm vụ tiếp theo.

def _choose_next(current, tasks):
    return min(
        tasks,
        key=lambda task: manhattan(current, task.target) - task.priority * 3 + (0 if not task.urgent else -8),
    )

# từ hàm astar_route gọi qua hàm nà 
def _route(hospital_map, start, tasks, name, weight=1.0, greedy=False):
    started = time.perf_counter()
    current = start
    remaining = list(tasks)
    full_path = []
    full_visited = []
    plan = []
    total_cost = 0

    while remaining:
        task = _choose_next(current, remaining) # gọi hàm này để chon ra nhiệm vụ tiếp theo cần thực hiện 
        result = _search(hospital_map, current, task.target, name, weight=weight, greedy=greedy) # từ current đến nhiệm vụ vưa chọn 
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


def _route_with_solver(hospital_map, start, tasks, name, solver):
    started = time.perf_counter()
    current = start
    remaining = list(tasks)
    full_path = []
    full_visited = []
    plan = []
    total_cost = 0
    total_iterations = 0

    while remaining:
        task = _choose_next(current, remaining)
        result = solver(hospital_map, current, task.target)
        if not result["success"]:
            return _runtime_result(
                name,
                started,
                full_path,
                plan,
                total_cost,
                len(full_visited),
                False,
                f"Cannot reach {task.name}.",
                full_visited,
                {"iterations": total_iterations},
            )
        segment = result["path"]
        full_path = segment if not full_path else full_path + segment[1:]
        full_visited.extend(result["visited"])
        total_cost += result["cost"]
        total_iterations += result.get("iterations", 0)
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
        "Route built with iterative f-limit deepening.",
        full_visited,
        {"iterations": total_iterations},
    )


def astar_route(hospital_map, start, tasks):
    return _route(hospital_map, start, tasks, "A* Search", weight=1.0, greedy=False)


def ida_star_route(hospital_map, start, tasks):
    return _route_with_solver(hospital_map, start, tasks, "IDA*", ida_star_path)


def greedy_route(hospital_map, start, tasks):
    return _route(hospital_map, start, tasks, "Greedy Best-First", weight=1.0, greedy=True)


