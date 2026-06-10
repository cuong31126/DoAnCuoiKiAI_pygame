import time

from algorithms.informed import astar_path


ACTION_NAMES = ["go_to_task", "go_to_charge", "wait", "replan", "prioritize_emergency"]
ENV_STATES = [
    ("clear", 0.55),
    ("crowded", 0.30),
    ("blocked", 0.15),
]


def _best_task(start, tasks, emergency_only=False):
    filtered = [task for task in tasks if task.urgent] if emergency_only else tasks
    if not filtered:
        filtered = tasks
    return min(
        filtered,
        key=lambda task: (
            task.deadline or 999,
            abs(task.target[0] - start[0]) + abs(task.target[1] - start[1]) - task.priority * 2,
        ),
    )


def _nearest_charge(hospital_map, start):
    if not hospital_map.charge_stations:
        return None, None
    best_station = None
    best_result = None
    for station in hospital_map.charge_stations:
        result = astar_path(hospital_map, start, station)
        if result["success"] and (best_result is None or result["cost"] < best_result["cost"]):
            best_station = station
            best_result = result
    return best_station, best_result


def _action_path(hospital_map, start, tasks, action, avoid_dynamic=False):
    avoid = hospital_map.predicted_dynamic_positions(steps=4) if avoid_dynamic else None
    if action == "go_to_charge":
        _station, result = _nearest_charge(hospital_map, start)
        return result
    if action == "wait":
        return {"path": [start], "cost": 0, "nodes": 1, "success": True}
    task = _best_task(start, tasks, emergency_only=action == "prioritize_emergency")
    return astar_path(hospital_map, start, task.target, avoid=avoid)


def _utility(hospital_map, start, tasks, action, env_state, battery=None):
    avoid_dynamic = action in ("replan", "prioritize_emergency")
    result = _action_path(hospital_map, start, tasks, action, avoid_dynamic=avoid_dynamic)
    if not result or not result["success"]:
        return -999, result

    distance = result["cost"]
    battery_budget = hospital_map.battery_limit if battery is None else battery
    if action != "go_to_charge" and distance > battery_budget:
        return -999 - (distance - battery_budget) * 25, result
    if action == "go_to_charge" and distance > battery_budget:
        return -999 - (distance - battery_budget) * 25, result

    target_task = _best_task(start, tasks, emergency_only=action == "prioritize_emergency")
    reward = 0 if action in ("wait", "go_to_charge") else target_task.reward + target_task.priority * 15
    emergency_bonus = 50 if action == "prioritize_emergency" and target_task.urgent else 0
    distance_penalty = distance * 4
    battery_penalty = max(0, distance - battery_budget) * 10
    late_penalty = 60 if target_task.deadline and distance > target_task.deadline else 0
    collision_penalty = {"clear": 0, "crowded": 25, "blocked": 70}[env_state]
    charge_bonus = max(0, 45 - battery_budget) if action == "go_to_charge" else 0
    wait_penalty = 30 if action == "wait" else 0
    utility = reward + emergency_bonus + charge_bonus - distance_penalty - battery_penalty - collision_penalty - late_penalty - wait_penalty
    return utility, result


def _finish(name, started, action, utility, nodes, path_result, message):
    path = path_result["path"] if path_result else []
    return {
        "name": name,
        "path": path,
        "plan": [action],
        "cost": path_result["cost"] if path_result else 0,
        "path_length": max(0, len(path) - 1),
        "nodes_expanded": nodes + (path_result["nodes"] if path_result else 0),
        "runtime_ms": (time.perf_counter() - started) * 1000,
        "success": bool(path),
        "message": message,
        "selected_action": action,
        "utility": round(utility, 2),
    }


def minimax_search(hospital_map, start, tasks, battery=None):
    started = time.perf_counter()
    best = None
    nodes = 0
    for action in ACTION_NAMES:
        worst_utility = None
        worst_result = None
        for env_state, _prob in ENV_STATES:
            nodes += 1
            utility, result = _utility(hospital_map, start, tasks, action, env_state, battery=battery)
            if worst_utility is None or utility < worst_utility:
                worst_utility = utility
                worst_result = result
        if best is None or worst_utility > best[1]:
            best = (action, worst_utility, worst_result)
    return _finish("Minimax", started, best[0], best[1], nodes, best[2], "Environment chooses the worst outcome.")


def alpha_beta_search(hospital_map, start, tasks, battery=None):
    started = time.perf_counter()
    alpha = -10_000
    best = None
    nodes = 0
    for action in ACTION_NAMES:
        beta = 10_000
        value = 10_000
        chosen_result = None
        for env_state, _prob in ENV_STATES:
            nodes += 1
            utility, result = _utility(hospital_map, start, tasks, action, env_state, battery=battery)
            if utility < value:
                value = utility
                chosen_result = result
            beta = min(beta, value)
            if beta <= alpha:
                break
        if best is None or value > best[1]:
            best = (action, value, chosen_result)
        alpha = max(alpha, value)
    return _finish("Alpha-Beta Pruning", started, best[0], best[1], nodes, best[2], "Same game model as minimax with pruning.")


def expectimax_search(hospital_map, start, tasks, battery=None):
    started = time.perf_counter()
    best = None
    nodes = 0
    for action in ACTION_NAMES:
        expected = 0.0
        representative = None
        for env_state, probability in ENV_STATES:
            nodes += 1
            utility, result = _utility(hospital_map, start, tasks, action, env_state, battery=battery)
            expected += utility * probability
            if env_state == "clear":
                representative = result
        if best is None or expected > best[1]:
            best = (action, expected, representative)
    return _finish("Expectimax", started, best[0], best[1], nodes, best[2], "Environment is modeled as probabilistic.")
