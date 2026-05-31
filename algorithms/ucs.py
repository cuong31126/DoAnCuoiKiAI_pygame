import heapq

from algorithms.common import neighbors, reconstruct_path


def ucs(matrix, start, goal):
    """Tim duong di chi phi thap nhat bang UCS."""
    heap = [(0, start)]
    parent = {start: None}
    cost_so_far = {start: 0}
    visited_order = []
    closed = set()

    while heap:
        cost, node = heapq.heappop(heap)
        if node in closed:
            continue
        closed.add(node)
        visited_order.append(node)
        if node == goal:
            break
        for nxt in neighbors(matrix, node):
            new_cost = cost + 1
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                parent[nxt] = node
                heapq.heappush(heap, (new_cost, nxt))

    path = reconstruct_path(parent, start, goal)
    return {
        "path": path,
        "visited": visited_order,
        "nodes": len(visited_order),
        "depth": max(0, len(path) - 1) if path else -1,
        "cost": cost_so_far.get(goal, 0),
        "success": bool(path),
    }
