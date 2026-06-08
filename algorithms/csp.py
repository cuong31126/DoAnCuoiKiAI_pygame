from itertools import permutations
import random
import time

from algorithms.informed import astar_path


RNG = random.Random(7)


def _merge(first, second):
    if not first:
        return list(second)
    if not second:
        return list(first)
    return list(first) + list(second)[1:]


def _evaluate_order(hospital_map, start, tasks, order):
    current = start
    route = []
    total_cost = 0
    elapsed = 0
    battery = hospital_map.battery_limit
    violations = 0
    nodes = 0
    score = 0
    plan = []
    dangerous = hospital_map.predicted_dynamic_positions(steps=4)

    for index in order:
        task = tasks[index]
        result = astar_path(hospital_map, current, task.target, avoid=dangerous)
        nodes += result["nodes"]
        if not result["success"]:
            violations += 4
            continue
        route = _merge(route, result["path"])
        total_cost += result["cost"]
        elapsed += result["cost"]
        battery -= result["cost"]
        if battery < 0:
            violations += 2
        if task.deadline and elapsed > task.deadline:
            violations += 3 if task.urgent else 1
        if task.target in dangerous:
            violations += 1
        score += task.reward + task.priority * 12
        current = task.target
        plan.append(task.task_id)

    for left, right in zip(order, order[1:]):
        if tasks[left].priority < tasks[right].priority and tasks[right].urgent:
            violations += 1

    score -= violations * 40 + total_cost
    return {
        "order": list(order),
        "path": route,
        "plan": plan,
        "cost": total_cost,
        "nodes": nodes,
        "violations": violations,
        "score": score,
        "success": bool(route) and violations == 0,
    }


def _finish(name, started, evaluation, expanded, message):
    return {
        "name": name,
        "path": evaluation["path"],
        "plan": evaluation["plan"],
        "cost": evaluation["cost"],
        "path_length": max(0, len(evaluation["path"]) - 1),
        "nodes_expanded": evaluation["nodes"] + expanded,
        "runtime_ms": (time.perf_counter() - started) * 1000,
        "success": bool(evaluation["path"]),
        "message": message,
        "constraint_violations": evaluation["violations"],
        "score": evaluation["score"],
    }


def _best_by_constraints(candidates):
    return min(candidates, key=lambda item: (item["violations"], -item["score"], item["cost"]))


def backtracking_search(hospital_map, start, tasks):
    started = time.perf_counter()
    order_domain = range(len(tasks))
    best = None
    expanded = 0

    def backtrack(prefix, remaining):
        nonlocal best, expanded
        expanded += 1
        if not remaining:
            evaluation = _evaluate_order(hospital_map, start, tasks, prefix)
            if best is None or (evaluation["violations"], -evaluation["score"]) < (best["violations"], -best["score"]):
                best = evaluation
            return
        for index in sorted(remaining, key=lambda i: (tasks[i].deadline or 999, -tasks[i].priority)):
            backtrack(prefix + [index], [item for item in remaining if item != index])

    backtrack([], list(order_domain))
    message = "Perfect CSP plan found." if best and best["violations"] == 0 else "No perfect plan; selected lowest-conflict order."
    return _finish("Backtracking Search", started, best, expanded, message)


def min_conflicts_search(hospital_map, start, tasks):
    started = time.perf_counter()
    order = list(range(len(tasks)))
    RNG.shuffle(order)
    best = _evaluate_order(hospital_map, start, tasks, order)
    expanded = 0

    for _ in range(160):
        expanded += 1
        if best["violations"] == 0:
            break
        a, b = RNG.sample(range(len(order)), 2)
        candidate_order = list(order)
        candidate_order[a], candidate_order[b] = candidate_order[b], candidate_order[a]
        candidate = _evaluate_order(hospital_map, start, tasks, candidate_order)
        if (candidate["violations"], -candidate["score"]) <= (best["violations"], -best["score"]):
            order = candidate_order
            best = candidate

    message = "Min-conflicts reduced violations by local swaps."
    return _finish("Min-Conflicts", started, best, expanded, message)


def constraint_graph_search(hospital_map, start, tasks):
    started = time.perf_counter()
    expanded = 0
    ranked = sorted(range(len(tasks)), key=lambda i: (tasks[i].deadline or 999, -tasks[i].priority))
    candidates = [_evaluate_order(hospital_map, start, tasks, ranked)]
    expanded += 1

    for a, b in permutations(range(len(tasks)), 2):
        if tasks[a].priority > tasks[b].priority:
            candidate = list(ranked)
            if candidate.index(a) > candidate.index(b):
                ia, ib = candidate.index(a), candidate.index(b)
                candidate[ia], candidate[ib] = candidate[ib], candidate[ia]
                candidates.append(_evaluate_order(hospital_map, start, tasks, candidate))
                expanded += 1

    best = _best_by_constraints(candidates)
    message = "Constraint graph ranked tasks by deadline, priority, battery and danger constraints."
    return _finish("Constraint Graph", started, best, expanded, message)

