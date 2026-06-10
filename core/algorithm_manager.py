from algorithms.adversarial import alpha_beta_search, expectimax_search, minimax_search
from algorithms.csp import backtracking_search, constraint_graph_search, min_conflicts_search
from algorithms.informed import (
    astar_route,
    constraint_propagation_search,
    greedy_route,
    online_replanning_astar,
    partial_observation_search,
    weighted_astar_route,
)
from algorithms.local_search import simple_hill_climbing, simulated_annealing, stochastic_hill_climbing
from algorithms.uninformed import bfs_search, dfs_search, ucs_search


class AlgorithmManager:
    """Dispatches the allowed algorithms for each level through one interface."""

    LEVEL_ALGORITHMS = {
        1: ["BFS", "DFS", "UCS"],
        2: ["A* Search", "Greedy Best-First", "Weighted A*"],
        3: ["Simple Hill Climbing", "Stochastic Hill Climbing", "Simulated Annealing"],
        4: ["Online Re-planning A*", "Partial Observation", "Constraint Propagation"],
        5: ["Backtracking Search", "Min-Conflicts", "Constraint Graph"],
        6: ["Minimax", "Alpha-Beta Pruning", "Expectimax"],
    }

    def __init__(self, hospital_map):
        self.hospital_map = hospital_map

    def set_map(self, hospital_map):
        self.hospital_map = hospital_map

    def get_algorithms(self, level=None):
        return list(self.LEVEL_ALGORITHMS.get(level or self.hospital_map.level, []))

    def run_algorithm(self, name, start=None, battery=None):
        hospital_map = self.hospital_map
        start = start or hospital_map.start
        battery = hospital_map.battery_limit if battery is None else battery
        tasks = hospital_map.remaining_tasks()
        if not tasks:
            return self._empty_success(name, start)

        if hospital_map.level == 1:
            goal = tasks[0].target
            if name == "BFS":
                return bfs_search(hospital_map, start, goal)
            if name == "DFS":
                return dfs_search(hospital_map, start, goal)
            return ucs_search(hospital_map, start, goal)

        if hospital_map.level == 2:
            if name == "A* Search":
                return astar_route(hospital_map, start, tasks)
            if name == "Greedy Best-First":
                return greedy_route(hospital_map, start, tasks)
            return weighted_astar_route(hospital_map, start, tasks)

        if hospital_map.level == 3:
            if name == "Simple Hill Climbing":
                return simple_hill_climbing(hospital_map, start, tasks)
            if name == "Stochastic Hill Climbing":
                return stochastic_hill_climbing(hospital_map, start, tasks)
            return simulated_annealing(hospital_map, start, tasks)

        if hospital_map.level == 4:
            goal = self._best_task(start, tasks).target
            if name == "Online Re-planning A*":
                return online_replanning_astar(hospital_map, start, goal)
            if name == "Partial Observation":
                return partial_observation_search(hospital_map, start, goal)
            return constraint_propagation_search(hospital_map, start, goal)

        if hospital_map.level == 5:
            if name == "Backtracking Search":
                return backtracking_search(hospital_map, start, tasks)
            if name == "Min-Conflicts":
                return min_conflicts_search(hospital_map, start, tasks)
            return constraint_graph_search(hospital_map, start, tasks)

        if name == "Minimax":
            return minimax_search(hospital_map, start, tasks, battery=battery)
        if name == "Alpha-Beta Pruning":
            return alpha_beta_search(hospital_map, start, tasks, battery=battery)
        return expectimax_search(hospital_map, start, tasks, battery=battery)

    def analyze_all(self, start=None, battery=None):
        return [self.run_algorithm(name, start=start, battery=battery) for name in self.get_algorithms()]

    def _best_task(self, start, tasks):
        def score(task):
            distance = abs(task.target[0] - start[0]) + abs(task.target[1] - start[1])
            deadline = task.deadline or 999
            return (deadline, distance - task.priority * 2)

        return min(tasks, key=score)

    def _empty_success(self, name, start):
        return {
            "name": name,
            "path": [start],
            "plan": [],
            "cost": 0,
            "path_length": 0,
            "nodes_expanded": 0,
            "runtime_ms": 0.0,
            "success": True,
            "message": "All tasks already complete.",
        }

