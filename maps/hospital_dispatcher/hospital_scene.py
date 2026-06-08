import pygame

from core.algorithm_manager import AlgorithmManager
from core.game_manager import GameManager
from core.scene_base import SceneBase
from core.ui import Button, ConfirmDialog, draw_panel, draw_text
from settings import (
    COLOR_BOTTOM_BAR,
    COLOR_GOLD,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_TOP_BAR,
    COLOR_WHITE,
    GRID_OFFSET_X,
    GRID_OFFSET_Y,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SIZE,
)
from ui.hud import HospitalHUD


CELL_COLORS = {
    0: (226, 232, 236),
    1: (70, 79, 88),
    2: (248, 224, 145),
    3: (118, 183, 232),
}


class HospitalScene(SceneBase):
    """Shared playable scene for all six AI Hospital Dispatcher levels."""

    def __init__(self, screen, game_ref, level):
        super().__init__(screen, game_ref)
        self.level = max(1, min(6, level))

    def on_enter(self):
        self.game.play_music("assets/sounds/music/chill.ogg")
        self.manager = GameManager(self.level)
        self.algorithm_manager = AlgorithmManager(self.manager.map)
        self.hud = HospitalHUD()
        self.selected_algorithm = self.algorithm_manager.get_algorithms()[0]
        self.result = None
        self.analysis_results = []
        self.analysis_close_rect = None
        self.state = "READY"
        self.move_timer = 0.0
        self.step_seconds = 0.16
        self.confirm = None
        self.buttons = self.build_buttons()

    def build_buttons(self):
        buttons = []
        x = 24
        for name in self.algorithm_manager.get_algorithms():
            color = (42, 130, 96) if name == self.selected_algorithm else (55, 83, 132)
            hover = (66, 170, 126) if name == self.selected_algorithm else (78, 115, 178)
            buttons.append(Button((x, 684, 150, 30), self.short_label(name), lambda n=name: self.select_algorithm(n), color, hover, 13))
            x += 158
        buttons.extend(
            [
                Button((520, 684, 82, 30), "RUN", self.run_selected, (43, 128, 80), (66, 172, 109), 17),
                Button((612, 684, 118, 30), "ANALYZE", self.open_analysis, (93, 68, 148), (127, 94, 194), 16),
                Button((742, 684, 92, 30), "RESET", self.reset_level, (92, 96, 107), (125, 131, 145), 16),
                Button((846, 684, 92, 30), "LEVELS", lambda: self.finish("map_select"), (70, 93, 124), (94, 124, 164), 15),
                Button((950, 684, 82, 30), "MENU", self.ask_menu, (132, 48, 56), (178, 68, 78), 16),
            ]
        )
        return buttons

    def short_label(self, name):
        labels = {
            "Greedy Best-First": "Greedy",
            "Simple Hill Climbing": "Hill Climb",
            "Stochastic Hill Climbing": "Stochastic HC",
            "Simulated Annealing": "Annealing",
            "Online Re-planning A*": "Replan A*",
            "Partial Observation": "Partial Obs",
            "Constraint Propagation": "Constraints",
            "Backtracking Search": "Backtracking",
            "Alpha-Beta Pruning": "Alpha-Beta",
        }
        return labels.get(name, name)

    def select_algorithm(self, name):
        self.selected_algorithm = name
        self.buttons = self.build_buttons()
        self.manager.status_message = f"Selected {name}"

    def reset_level(self):
        self.manager.reset()
        self.algorithm_manager.set_map(self.manager.map)
        self.selected_algorithm = self.algorithm_manager.get_algorithms()[0]
        self.result = None
        self.analysis_results = []
        self.state = "READY"
        self.move_timer = 0.0
        self.buttons = self.build_buttons()

    def run_selected(self):
        if self.state == "ANALYSIS":
            return
        self.result = self.algorithm_manager.run_algorithm(self.selected_algorithm, self.manager.robot.position)
        self.manager.status_message = self.result.get("message", "")
        if self.result.get("success") and self.result.get("path"):
            self.manager.robot.set_path(self.result["path"])
            self.state = "RUNNING" if len(self.result["path"]) > 1 else "READY"
        else:
            self.state = "READY"

    def open_analysis(self):
        self.analysis_results = self.algorithm_manager.analyze_all(start=self.manager.robot.position)
        self.state = "ANALYSIS"

    def ask_menu(self):
        self.confirm = ConfirmDialog("Return to main menu?", lambda: self.finish("main_menu"))

    def handle_events(self, events):
        if self.confirm and self.confirm.active:
            self.confirm.handle_events(events)
            return

        for event in events:
            if self.state == "ANALYSIS":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "READY"
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and self.analysis_close_rect
                    and self.analysis_close_rect.collidepoint(event.pos)
                ):
                    self.state = "READY"
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.run_selected()
                elif event.key == pygame.K_ESCAPE:
                    self.ask_menu()

            for button in self.buttons:
                if button.handle_event(event):
                    break

    def update(self, dt):
        moved = False
        if self.state in ("READY", "RUNNING"):
            for obstacle in self.manager.map.dynamic_obstacles:
                moved = obstacle.update(dt) or moved

        if self.state != "RUNNING":
            return

        self.manager.elapsed += dt
        if self.manager.elapsed >= self.manager.map.time_limit:
            self.state = "FAILED"
            self.manager.status_message = "Time limit reached."
            return
        if moved and self.future_path_blocked():
            self.replan_from_current("Moving obstacle blocked the path.")
            return

        self.move_timer += dt
        if self.move_timer < self.step_seconds:
            return
        self.move_timer = 0.0
        self.step_robot()

    def future_path_blocked(self):
        dynamic = self.manager.map.dynamic_positions()
        future = self.manager.robot.path[self.manager.robot.path_index + 1 :]
        return any(pos in dynamic for pos in future[:5])

    def step_robot(self):
        robot = self.manager.robot
        nxt = robot.next_cell()
        if nxt is None:
            self.handle_path_finished()
            return

        if nxt in self.manager.map.dynamic_positions():
            robot.collisions += 1
            robot.score -= 20
            self.replan_from_current("Collision risk detected; re-planning.")
            return

        robot.step()
        if robot.position in self.manager.map.charge_stations:
            robot.charge()
            self.manager.status_message = "Battery charged."
        completed = self.manager.mark_task_if_reached()
        if completed:
            self.manager.status_message = f"Completed {completed.name}."

        if robot.battery <= 0:
            self.state = "FAILED"
            self.manager.status_message = "Battery depleted."
            return

        if completed and self.manager.all_tasks_done():
            self.state = "COMPLETED"
            self.manager.status_message = "All hospital tasks complete."
            return

        if completed and self.manager.map.level in (4, 6):
            self.replan_from_current("Next task selected after completion.")

    def handle_path_finished(self):
        if self.manager.all_tasks_done():
            self.state = "COMPLETED"
            self.manager.status_message = "All hospital tasks complete."
        elif self.manager.map.remaining_tasks():
            self.replan_from_current("Path finished; planning next task.")
        else:
            self.state = "READY"

    def replan_from_current(self, message):
        self.manager.replan_count += 1
        self.manager.status_message = message
        self.result = self.algorithm_manager.run_algorithm(self.selected_algorithm, self.manager.robot.position)
        if self.result.get("success") and len(self.result.get("path", [])) > 1:
            self.manager.robot.set_path(self.result["path"])
            self.state = "RUNNING"
        else:
            self.state = "FAILED"

    def draw(self):
        self.screen.fill((13, 18, 25))
        self.draw_top_bar()
        self.draw_grid()
        self.draw_legend()
        self.hud.draw_status(
            self.screen,
            pygame.Rect(858, 80, 398, 540),
            self.manager,
            self.selected_algorithm,
            self.result,
            self.state,
        )
        self.draw_bottom_bar()
        if self.state in ("COMPLETED", "FAILED"):
            self.draw_end_overlay()
        if self.state == "ANALYSIS":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 145))
            self.screen.blit(overlay, (0, 0))
            self.analysis_close_rect = self.hud.draw_analysis(self.screen, pygame.Rect(210, 104, 860, 500), self.analysis_results)
        if self.confirm and self.confirm.active:
            self.confirm.draw(self.screen)

    def draw_top_bar(self):
        pygame.draw.rect(self.screen, COLOR_TOP_BAR, (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.line(self.screen, (190, 200, 216), (0, 60), (SCREEN_WIDTH, 60), 1)
        draw_text(self.screen, "AI Hospital Dispatcher", 27, COLOR_GOLD, (30, 14), bold=True)
        draw_text(self.screen, self.manager.map.title, 22, COLOR_WHITE, (395, 18), bold=True)
        draw_text(self.screen, self.manager.status_message, 17, COLOR_WHITE, (820, 21))

    def draw_grid(self):
        hospital_map = self.manager.map
        path = set(self.result.get("path", [])) if self.result else set()
        visited = set((self.result or {}).get("visited", [])[:90])
        for row in range(hospital_map.rows):
            for col in range(hospital_map.cols):
                value = hospital_map.grid[row][col]
                rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, CELL_COLORS.get(value, CELL_COLORS[0]), rect)
                if (row, col) in visited:
                    pygame.draw.rect(self.screen, (143, 178, 214), rect.inflate(-10, -10), border_radius=6)
                if (row, col) in path:
                    pygame.draw.rect(self.screen, COLOR_GOLD, rect.inflate(-18, -18), border_radius=5)
                pygame.draw.rect(self.screen, (122, 135, 148), rect, 1)

        for station in hospital_map.charge_stations:
            self.draw_cell_badge(station, "CHG", (32, 99, 175))
        self.draw_cell_badge(hospital_map.start, "START", (34, 137, 97))
        for task in hospital_map.tasks:
            color = COLOR_GREEN if task.completed else ((210, 52, 68) if task.urgent else (96, 74, 180))
            self.draw_task(task, color)
        for obstacle in hospital_map.dynamic_obstacles:
            self.draw_obstacle(obstacle.pos)
        self.draw_robot(self.manager.robot.position)
        pygame.draw.rect(
            self.screen,
            COLOR_WHITE,
            (GRID_OFFSET_X, GRID_OFFSET_Y, hospital_map.cols * TILE_SIZE, hospital_map.rows * TILE_SIZE),
            2,
        )

    def draw_cell_badge(self, pos, label, color):
        row, col = pos
        rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE + 4, GRID_OFFSET_Y + row * TILE_SIZE + 8, TILE_SIZE - 8, TILE_SIZE - 16)
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_WHITE, rect, 1, border_radius=6)
        draw_text(self.screen, label, 9, COLOR_WHITE, rect.center, center=True, bold=True)

    def draw_task(self, task, color):
        row, col = task.target
        center = (GRID_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2, GRID_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(self.screen, color, center, 15)
        pygame.draw.circle(self.screen, COLOR_WHITE, center, 15, 2)
        draw_text(self.screen, task.task_id, 11, COLOR_WHITE, center, center=True, bold=True)
        if task.deadline and not task.completed:
            draw_text(self.screen, str(int(task.deadline)), 10, COLOR_RED, (center[0] - 14, center[1] - 27), bold=True)

    def draw_obstacle(self, pos):
        row, col = pos
        rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE + 7, GRID_OFFSET_Y + row * TILE_SIZE + 7, TILE_SIZE - 14, TILE_SIZE - 14)
        pygame.draw.rect(self.screen, (218, 96, 52), rect, border_radius=7)
        pygame.draw.rect(self.screen, COLOR_WHITE, rect, 2, border_radius=7)
        draw_text(self.screen, "!", 18, COLOR_WHITE, rect.center, center=True, bold=True)

    def draw_robot(self, pos):
        row, col = pos
        center = (GRID_OFFSET_X + col * TILE_SIZE + TILE_SIZE // 2, GRID_OFFSET_Y + row * TILE_SIZE + TILE_SIZE // 2)
        pygame.draw.circle(self.screen, (31, 168, 204), center, 17)
        pygame.draw.circle(self.screen, COLOR_WHITE, center, 17, 2)
        pygame.draw.rect(self.screen, (12, 54, 75), pygame.Rect(center[0] - 7, center[1] - 5, 14, 10), border_radius=3)
        pygame.draw.circle(self.screen, COLOR_WHITE, (center[0] - 5, center[1] - 1), 2)
        pygame.draw.circle(self.screen, COLOR_WHITE, (center[0] + 5, center[1] - 1), 2)

    def draw_legend(self):
        rect = pygame.Rect(30, 44, 800, 28)
        labels = [
            ("floor", CELL_COLORS[0]),
            ("wall", CELL_COLORS[1]),
            ("weighted", CELL_COLORS[2]),
            ("charge", CELL_COLORS[3]),
            ("path", COLOR_GOLD),
            ("dynamic", (218, 96, 52)),
        ]
        x = rect.x
        for label, color in labels:
            pygame.draw.rect(self.screen, color, (x, rect.y + 8, 14, 14), border_radius=3)
            draw_text(self.screen, label, 13, COLOR_WHITE, (x + 20, rect.y + 5))
            x += 116

    def draw_bottom_bar(self):
        pygame.draw.rect(self.screen, COLOR_BOTTOM_BAR, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        for button in self.buttons:
            button.draw(self.screen)

    def draw_end_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(360, 230, 560, 190)
        border = COLOR_GREEN if self.state == "COMPLETED" else COLOR_RED
        title = "LEVEL COMPLETE" if self.state == "COMPLETED" else "MISSION FAILED"
        draw_panel(self.screen, rect, (22, 26, 38), border, 245)
        draw_text(self.screen, title, 34, border, (rect.centerx, rect.y + 48), center=True, bold=True)
        draw_text(self.screen, self.manager.status_message, 21, COLOR_WHITE, (rect.centerx, rect.y + 96), center=True)
        draw_text(self.screen, "Use RESET, LEVELS, or MENU to continue.", 18, COLOR_GOLD, (rect.centerx, rect.y + 138), center=True)

