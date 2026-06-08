from collections import deque
import heapq
import time


def _result(name, path, visited, cost, success=True, message="Done"):
    return {
        "name": name,
        "path": path,
        "plan": [],
        "cost": cost,
        "path_length": max(0, len(path) - 1),
        "nodes_expanded": len(visited),
        "runtime_ms": 0.0,
        "success": success and bool(path),
        "message": message,
        "visited": visited,
    }


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


def _with_runtime(result, started):
    result["runtime_ms"] = (time.perf_counter() - started) * 1000
    return result


def bfs_search(hospital_map, start, goal):
    started = time.perf_counter()
    queue = deque([start])
    parent = {start: start}
    visited = []

    while queue:
        node = queue.popleft()
        visited.append(node)
        if node == goal:
            break
        for nxt in hospital_map.neighbors(node):
            if nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)

    path = _reconstruct(parent, start, goal)
    message = "BFS found the shortest path by number of steps." if path else "BFS could not reach the task."
    return _with_runtime(_result("BFS", path, visited, max(0, len(path) - 1), bool(path), message), started)


def dfs_search(hospital_map, start, goal, max_depth=90):
    started = time.perf_counter()
    stack = [(start, [start])]
    visited = []
    seen = set()
    path = []

    while stack:
        node, current_path = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        visited.append(node)
        if node == goal:
            path = current_path
            break
        if len(current_path) > max_depth:
            continue
        for nxt in reversed(list(hospital_map.neighbors(node))):
            if nxt not in seen:
                stack.append((nxt, current_path + [nxt]))

    message = "DFS found a path using depth-first exploration." if path else "DFS depth limit reached before success."
    return _with_runtime(_result("DFS", path, visited, max(0, len(path) - 1), bool(path), message), started)


def ucs_search(hospital_map, start, goal):
    started = time.perf_counter()
    heap = [(0, start)]
    parent = {start: start}
    cost_so_far = {start: 0}
    visited = []
    closed = set()

    while heap:
        cost, node = heapq.heappop(heap)
        if node in closed:
            continue
        closed.add(node)
        visited.append(node)
        if node == goal:
            break
        for nxt in hospital_map.neighbors(node):
            new_cost = cost + hospital_map.cell_cost(nxt)
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                parent[nxt] = node
                heapq.heappush(heap, (new_cost, nxt))

    path = _reconstruct(parent, start, goal)
    message = "UCS minimized weighted cell cost." if path else "UCS could not reach the task."
    return _with_runtime(_result("UCS", path, visited, cost_so_far.get(goal, 0), bool(path), message), started)

