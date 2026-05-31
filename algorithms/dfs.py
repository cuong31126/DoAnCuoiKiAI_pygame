from settings import DFS_MAX_DEPTH
from algorithms.common import neighbors


def dfs(matrix, start, goal, max_depth=DFS_MAX_DEPTH):
    """Tim duong di bang DFS co gioi han do sau."""
    visited_order = []
    best_path = []

    def visit(node, path, seen, depth):
        nonlocal best_path
        visited_order.append(node)
        if node == goal:
            best_path = path[:]
            return True
        if depth >= max_depth:
            return False
        for nxt in neighbors(matrix, node):
            if nxt not in seen:
                seen.add(nxt)
                if visit(nxt, path + [nxt], seen, depth + 1):
                    return True
                seen.remove(nxt)
        return False

    visit(start, [start], {start}, 0)
    return {
        "path": best_path,
        "visited": visited_order,
        "nodes": len(visited_order),
        "depth": max(0, len(best_path) - 1) if best_path else -1,
        "cost": max(0, len(best_path) - 1),
        "success": bool(best_path),
    }
