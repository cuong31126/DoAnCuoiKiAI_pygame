import pygame

from core.ui import draw_panel, draw_text
from settings import COLOR_GOLD, COLOR_GREEN, COLOR_RED, COLOR_WHITE


class HospitalHUD:
    """Draws the dispatcher status panel and analysis table."""

    def draw_status(self, surface, rect, manager, selected_algorithm, result, state):
        robot = manager.robot
        hospital_map = manager.map
        draw_panel(surface, rect, (21, 26, 35), COLOR_WHITE, 235)
        draw_text(surface, "DISPATCH STATUS", 25, COLOR_GOLD, (rect.centerx, rect.y + 24), center=True, bold=True)

        path_found = "Yes" if result and result.get("success") else "No"
        lines = [
            f"Score: {robot.score}",
            f"Battery: {robot.battery}/{robot.max_battery}",
            f"Timer: {int(manager.elapsed)}/{int(hospital_map.time_limit)}s",
            f"Current task: {manager.current_task_label()}",
            f"Algorithm: {selected_algorithm}",
            f"Path found: {path_found}",
            f"Nodes expanded: {self._value(result, 'nodes_expanded')}",
            f"Path length: {self._value(result, 'path_length')}",
            f"Total cost: {self._value(result, 'cost')}",
            f"Runtime ms: {self._runtime(result)}",
            f"Re-plans: {manager.replan_count}",
            f"Collisions: {robot.collisions}",
            f"State: {state}",
        ]
        y = rect.y + 70
        for line in lines:
            draw_text(surface, line, 16, COLOR_WHITE, (rect.x + 20, y))
            y += 29

        if result:
            extra = self._extra_line(result)[:44]
            draw_text(surface, extra, 16, COLOR_GOLD, (rect.x + 20, rect.bottom - 78), bold=True)
            draw_text(surface, result.get("message", "")[:50], 15, COLOR_WHITE, (rect.x + 20, rect.bottom - 45))

    def draw_analysis(self, surface, rect, results):
        draw_panel(surface, rect, (20, 24, 36), COLOR_WHITE, 245)
        draw_text(surface, "ANALYZE ALGORITHMS", 27, COLOR_GOLD, (rect.centerx, rect.y + 30), center=True, bold=True)
        close_rect = pygame.Rect(rect.right - 64, rect.y + 12, 48, 32)
        pygame.draw.rect(surface, (140, 46, 54), close_rect, border_radius=6)
        draw_text(surface, "X", 21, COLOR_WHITE, close_rect.center, center=True, bold=True)

        headers = ["Algorithm", "Len", "Cost", "Nodes", "Runtime", "Extra"]
        xs = [rect.x + 30, rect.x + 285, rect.x + 355, rect.x + 425, rect.x + 505, rect.x + 610]
        for x, header in zip(xs, headers):
            draw_text(surface, header, 16, COLOR_GOLD, (x, rect.y + 82), bold=True)

        for i, result in enumerate(results[:6]):
            y = rect.y + 120 + i * 48
            status_color = COLOR_GREEN if result.get("success") else COLOR_RED
            row = [
                result.get("name", ""),
                str(result.get("path_length", 0)),
                str(round(result.get("cost", 0), 1)),
                str(result.get("nodes_expanded", 0)),
                f"{result.get('runtime_ms', 0):.2f}",
                self._extra_line(result),
            ]
            for x, value in zip(xs, row):
                color = status_color if x == xs[0] else COLOR_WHITE
                draw_text(surface, value, 15, color, (x, y), bold=x == xs[0])

        draw_text(surface, "ESC or X closes this table.", 16, COLOR_GOLD, (rect.centerx, rect.bottom - 32), center=True)
        return close_rect

    def _value(self, result, key):
        if not result:
            return 0
        return result.get(key, 0)

    def _runtime(self, result):
        if not result:
            return "0.00"
        return f"{result.get('runtime_ms', 0.0):.2f}"

    def _extra_line(self, result):
        if "score" in result and "charging_count" in result:
            return f"score {result['score']} / charge {result['charging_count']}"
        if "constraint_violations" in result:
            return f"violations {result['constraint_violations']} / score {result.get('score', 0)}"
        if "utility" in result:
            return f"{result.get('selected_action', '')} / U {result['utility']}"
        if "replan_count" in result:
            return f"replans {result.get('replan_count', 0)} / hits {result.get('collision_count', 0)}"
        return result.get("message", "")[:28]
