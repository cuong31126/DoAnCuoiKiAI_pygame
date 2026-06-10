import unittest

from algorithms.astar import astar_path, astar_tsp
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.ucs import ucs
from algorithms.common import BLOCKED_VALUES


def assert_valid_path(testcase, matrix, path, start, goal):
    testcase.assertTrue(path)
    testcase.assertEqual(path[0], start)
    testcase.assertEqual(path[-1], goal)
    for row, col in path:
        testcase.assertNotIn(matrix[row][col], BLOCKED_VALUES)
    for current, nxt in zip(path, path[1:]):
        testcase.assertEqual(abs(current[0] - nxt[0]) + abs(current[1] - nxt[1]), 1)


class PathFindingTests(unittest.TestCase):
    def setUp(self):
        self.matrix = [
            [0, 0, 0, 0],
            [1, 1, 0, 1],
            [0, 0, 0, 0],
        ]
        self.start = (0, 0)
        self.goal = (2, 3)

    def test_solvers_return_valid_paths_on_non_default_grid_size(self):
        for solver in (bfs, dfs, ucs):
            with self.subTest(solver=solver.__name__):
                result = solver(self.matrix, self.start, self.goal)
                self.assertTrue(result["success"])
                assert_valid_path(self, self.matrix, result["path"], self.start, self.goal)

    def test_astar_returns_valid_path(self):
        result = astar_path(self.matrix, self.start, self.goal)
        self.assertTrue(result["success"])
        assert_valid_path(self, self.matrix, result["path"], self.start, self.goal)

    def test_start_equal_goal(self):
        for solver in (bfs, dfs, ucs, astar_path):
            with self.subTest(solver=solver.__name__):
                result = solver(self.matrix, self.start, self.start)
                self.assertTrue(result["success"])
                self.assertEqual(result["path"], [self.start])
                self.assertEqual(result["cost"], 0)

    def test_no_path(self):
        blocked = [
            [0, 1, 0],
            [1, 1, 0],
            [0, 0, 0],
        ]
        for solver in (bfs, dfs, ucs, astar_path):
            with self.subTest(solver=solver.__name__):
                result = solver(blocked, (0, 0), (2, 2))
                self.assertFalse(result["success"])
                self.assertEqual(result["path"], [])


class RescueRouteTests(unittest.TestCase):
    def test_astar_tsp_respects_timers_and_returns_to_base(self):
        matrix = [[0 for _ in range(5)] for _ in range(5)]
        start = (2, 2)
        creatures = [
            {"grid_pos": (0, 0), "timer": 10},
            {"grid_pos": (4, 4), "timer": 20},
            {"grid_pos": (0, 4), "timer": 20},
        ]

        result = astar_tsp(start, creatures, matrix, seconds_per_step=0.5)

        self.assertTrue(result["safe"])
        self.assertEqual(result["route"][0], start)
        self.assertEqual(result["route"][-1], start)
        self.assertEqual(sorted(result["order"]), [0, 1, 2])
        for creature_index, arrival in result["arrival"].items():
            self.assertLess(arrival, creatures[creature_index]["timer"])

    def test_astar_tsp_reports_unsafe_when_deadline_is_impossible(self):
        matrix = [[0 for _ in range(3)] for _ in range(3)]
        result = astar_tsp(
            (0, 0),
            [{"grid_pos": (2, 2), "timer": 0.5}],
            matrix,
            seconds_per_step=1.0,
        )

        self.assertFalse(result["safe"])
        self.assertEqual(result["route"], [])


if __name__ == "__main__":
    unittest.main()
