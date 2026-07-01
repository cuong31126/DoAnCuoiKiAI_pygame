import time
# Import các hàm dùng chung từ file common.py trong cùng thư mục
from .informed import _search, _runtime_result, manhattan

def and_or_search(hospital_map, start, goal):
    started = time.perf_counter()
    scenarios = [
        hospital_map.dynamic_positions(),
        hospital_map.predicted_dynamic_positions(steps=2),
        hospital_map.predicted_dynamic_positions(steps=5),
    ]
    avoid = set().union(*scenarios)
    result = _search(hospital_map, start, goal, "AND-OR Search", avoid=avoid)
    conditional_plan = {
        "or_node": "choose next robot move with lowest f = g + h",
        "and_nodes": len(scenarios),
        "avoided_cells": len(avoid),
    }
    return _runtime_result(
        "AND-OR Search",
        started,
        result["path"],
        ["conditional_plan"],
        result["cost"],
        result["nodes"] + len(scenarios),
        result["success"],
        "Builds a conditional plan over predicted obstacle outcomes.",
        result["visited"],
        {"conditional_plan": conditional_plan, "replan_count": 0, "collision_count": 0},
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





def _belief_after_action(hospital_map, belief, action):
    dr, dc = action
    next_belief = set()
    for row, col in belief:
        nxt = (row + dr, col + dc)
        next_belief.add(nxt if hospital_map.passable(nxt) else (row, col))
    return next_belief




def no_observation_search(hospital_map, start, goal):
    started = time.perf_counter()
    belief = {
        (row, col)
        for row in range(hospital_map.rows)
        for col in range(hospital_map.cols)
        if hospital_map.passable((row, col))
    }
    actions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
    coercion = []
    belief_trace = []

    for _ in range(40):
        if len(belief) <= 1:
            break
        candidates = [(_belief_after_action(hospital_map, belief, action), action) for action in actions]
        next_belief, action = min(candidates, key=lambda item: len(item[0]))
        if len(next_belief) >= len(belief):
            break
        belief = next_belief
        coercion.append(action)
        belief_trace.extend(list(belief)[:12])

    avoid = hospital_map.predicted_dynamic_positions(steps=3)
    result = _search(hospital_map, start, goal, "No Observation", avoid=avoid)
    visited = belief_trace + result["visited"]
    return _runtime_result(
        "No Observation",
        started,
        result["path"],
        ["coercion"] + [str(action) for action in coercion],
        result["cost"],
        result["nodes"] + len(belief_trace),
        result["success"],
        "Uses a blind belief state, then follows a robust route to the goal.",
        visited,
        {"belief_size": len(belief), "vision_radius": 0, "coercion_steps": len(coercion)},
    )
