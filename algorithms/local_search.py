import math
import random
import time

from algorithms.informed import astar_path


RNG = random.Random(42)


def _merge(first, second):
    if not first:
        return list(second)
    if not second:
        return list(first)
    return list(first) + list(second)[1:]


def _nearest_charge(hospital_map, pos):
    best = None
    for station in hospital_map.charge_stations:
        result = astar_path(hospital_map, pos, station)
        if result["success"] and (best is None or result["cost"] < best["cost"]):
            best = {"station": station, "path": result["path"], "cost": result["cost"], "nodes": result["nodes"]}
    return best


def _evaluate(hospital_map, start, tasks, order):
    current = start
    battery = hospital_map.battery_limit
    route = []
    plan = []
    total_distance = 0
    nodes = 0
    charges = 0
    score = 0
    elapsed_steps = 0
    success = True
    message = "Plan evaluated."

    for index in order:
        task = tasks[index]
        direct = astar_path(hospital_map, current, task.target)
        nodes += direct["nodes"]
        if not direct["success"]:
            success = False
            message = f"Cannot reach {task.name}."
            break

        if direct["cost"] > battery:
            charge = _nearest_charge(hospital_map, current)
            if not charge or charge["cost"] > battery:
                success = False
                message = "Battery cannot reach task or charger."
                break
            route = _merge(route, charge["path"])
            total_distance += charge["cost"]
            elapsed_steps += charge["cost"]
            nodes += charge["nodes"]
            plan.append("CHARGE")
            charges += 1
            battery = hospital_map.battery_limit
            current = charge["station"]
            direct = astar_path(hospital_map, current, task.target)
            nodes += direct["nodes"]
            if not direct["success"] or direct["cost"] > battery:
                success = False
                message = "Task still unreachable after charging."
                break

        route = _merge(route, direct["path"])
        total_distance += direct["cost"]
        elapsed_steps += direct["cost"]
        battery -= direct["cost"]
        current = task.target
        plan.append(task.task_id)
        late_penalty = 50 if task.urgent and task.deadline and elapsed_steps > task.deadline else 0
        score += task.reward + task.priority * 10 - late_penalty

    objective = score - total_distance * 2 - charges * 8
    if not success:
        objective -= 500
    return {
        "order": list(order),
        "path": route,
        "plan": plan,
        "distance": total_distance,
        "nodes": nodes,
        "charges": charges,
        "score": score,
        "objective": objective,
        "success": success,
        "message": message,
    }


def _neighbors(order):
    if len(order) < 2:
        return [order]
    items = []
    for i in range(len(order) - 1):
        candidate = list(order)
        candidate[i], candidate[i + 1] = candidate[i + 1], candidate[i]
        items.append(candidate)
    return items


def _finish(name, started, evaluation, iterations):
    return {
        "name": name,
        "path": evaluation["path"],
        "plan": evaluation["plan"],
        "cost": evaluation["distance"],
        "path_length": max(0, len(evaluation["path"]) - 1),
        "nodes_expanded": evaluation["nodes"] + iterations,
        "runtime_ms": (time.perf_counter() - started) * 1000,
        "success": evaluation["success"],
        "message": evaluation["message"],
        "score": evaluation["score"],
        "distance": evaluation["distance"],
        "charging_count": evaluation["charges"],
        "objective": round(evaluation["objective"], 2),
    }


def _initial_order(tasks):
    return [
        i
        for i, _task in sorted(
            enumerate(tasks),
            key=lambda item: (item[1].deadline or 999, -item[1].priority),
        )
    ]


def simple_hill_climbing(hospital_map, start, tasks):
    started = time.perf_counter()
    current = _initial_order(tasks)
    best = _evaluate(hospital_map, start, tasks, current)
    iterations = 0

    improved = True
    while improved and iterations < 50:
        improved = False
        for candidate_order in _neighbors(current):
            iterations += 1
            candidate = _evaluate(hospital_map, start, tasks, candidate_order)
            if candidate["objective"] > best["objective"]:
                current = candidate_order
                best = candidate
                improved = True
                break

    return _finish("Simple Hill Climbing", started, best, iterations)


def stochastic_hill_climbing(hospital_map, start, tasks):
    started = time.perf_counter()
    current = _initial_order(tasks)
    best = _evaluate(hospital_map, start, tasks, current)
    iterations = 0

    for _ in range(90):
        iterations += 1
        candidate_order = list(current)
        a, b = RNG.sample(range(len(candidate_order)), 2)
        candidate_order[a], candidate_order[b] = candidate_order[b], candidate_order[a]
        candidate = _evaluate(hospital_map, start, tasks, candidate_order)
        if candidate["objective"] >= best["objective"] or RNG.random() < 0.15:
            current = candidate_order
            if candidate["objective"] > best["objective"]:
                best = candidate

    return _finish("Stochastic Hill Climbing", started, best, iterations)


def simulated_annealing(hospital_map, start, tasks):
    started = time.perf_counter()
    current_order = _initial_order(tasks)
    current = _evaluate(hospital_map, start, tasks, current_order)
    best = current
    temperature = 40.0
    iterations = 0

    while temperature > 0.5 and iterations < 120:
        iterations += 1
        candidate_order = list(current_order)
        a, b = RNG.sample(range(len(candidate_order)), 2)
        candidate_order[a], candidate_order[b] = candidate_order[b], candidate_order[a]
        candidate = _evaluate(hospital_map, start, tasks, candidate_order)
        delta = candidate["objective"] - current["objective"]
        if delta > 0 or RNG.random() < math.exp(delta / max(temperature, 0.01)):
            current_order = candidate_order
            current = candidate
            if current["objective"] > best["objective"]:
                best = current
        temperature *= 0.92

    return _finish("Simulated Annealing", started, best, iterations)

