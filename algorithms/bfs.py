from collections import deque

from algorithms.common import neighbors, reconstruct_path


def bfs(matrix, start, goal):
    """Tim duong di ngan nhat bang BFS."""
    queue = deque([start])
    parent = {start: None}
    visited_order = []
    depth = {start: 0}

    while queue:
        node = queue.popleft()
        visited_order.append(node)
        if node == goal:
            break
        for nxt in neighbors(matrix, node):
            if nxt not in parent:
                parent[nxt] = node
                depth[nxt] = depth[node] + 1
                queue.append(nxt)

    path = reconstruct_path(parent, start, goal)
    return {
        "path": path,
        "visited": visited_order,
        "nodes": len(visited_order),
        "depth": depth.get(goal, -1),
        "cost": max(0, len(path) - 1),
        "success": bool(path),
    }
