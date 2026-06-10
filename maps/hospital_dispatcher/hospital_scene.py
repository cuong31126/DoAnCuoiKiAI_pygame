import pygame

from core.algorithm_manager import AlgorithmManager
from core.animation import GIFAnimation
from core.game_manager import GameManager
from core.scene_base import SceneBase
from core.ui import Button, ConfirmDialog, assets, draw_panel, draw_text
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
    HERO_DRAW_SIZE,
    TILE_SIZE,
)
from ui.hud import HospitalHUD


CELL_COLORS = {
    0: (250, 250, 250),
    1: (0, 0, 0),
    2: (248, 224, 145),
    3: (118, 183, 232),
}

ALGORITHM_WAVE_COLORS = {
    "BFS": (68, 145, 255),
    "DFS": (165, 104, 255),
    "UCS": (45, 190, 176),
    "A* Search": (255, 170, 64),
    "Greedy Best-First": (255, 108, 108),
    "Weighted A*": (90, 205, 116),
    "Simple Hill Climbing": (255, 118, 178),
    "Stochastic Hill Climbing": (96, 210, 230),
    "Simulated Annealing": (255, 132, 64),
    "Online Re-planning A*": (255, 190, 74),
    "Partial Observation": (90, 170, 255),
    "Constraint Propagation": (130, 220, 140),
}


class HospitalScene(SceneBase):
    """Shared playable scene for all six AI Hospital Dispatcher levels."""

    def __init__(self, screen, game_ref, level):
        super().__init__(screen, game_ref)
        self.level = max(1, min(6, level))

    def on_enter(self):
        # Khoi tao level hien tai, algorithm manager va HUD cho man choi
        self.game.play_music("assets/sounds/music/chill.ogg")
        self.manager = GameManager(self.level)
        self.algorithm_manager = AlgorithmManager(self.manager.map)
        self.hud = HospitalHUD()
        self.load_visual_assets()
        self.selected_algorithm = self.algorithm_manager.get_algorithms()[0]
        self.result = None
        self.analysis_results = []
        self.analysis_close_rect = None
        self.state = "READY"
        self.move_timer = 0.0
        self.step_seconds = 0.16
        self.wave_elapsed = 0.0
        self.wave_nodes_per_second = 34
        self.hero_flip = False
        self.confirm = None
        self.buttons = self.build_buttons()

    def load_visual_assets(self):
        # Tai asset benh vien mot lan, chi thay doi cach ve khong doi ma tran
        tile_size = (TILE_SIZE, TILE_SIZE)
        self.weighted_img = assets.load_image("assets/coin.png", tile_size, fallback_color=CELL_COLORS[2])
        self.charge_img = assets.load_image("assets/benhvien/room_iv_stand_g.png", (28, 36), fallback_color=CELL_COLORS[3])
        self.start_img = assets.load_image("assets/benhvien/lab_automation_robot.png", (28, 28), fallback_color=(34, 137, 97))
        self.task_imgs = [
            assets.load_image("assets/benhvien/room_bed_h.png", (34, 24), fallback_color=(96, 74, 180)),
            assets.load_image("assets/benhvien/room_bed_v.png", (24, 34), fallback_color=(96, 74, 180)),
            assets.load_image("assets/benhvien/room_bed_meal.png", (34, 28), fallback_color=(96, 74, 180)),
        ]
        hero_size = (HERO_DRAW_SIZE * 5 // 2, HERO_DRAW_SIZE * 5 // 4)
        self.hero_idle = GIFAnimation(
            "assets/man1/Heroine base/Previews/idle.gif",
            size=hero_size,
            frame_time=0.14,
            fallback_color=(31, 168, 204),
        )
        self.hero_run = GIFAnimation(
            "assets/man1/Heroine base/Previews/run.gif",
            size=hero_size,
            frame_time=0.08,
            fallback_color=(31, 168, 204),
        )
        self.obstacle_img = assets.load_image("assets/vatcan.png", (34, 34), fallback_color=(136, 98, 214))

    def build_buttons(self):
        # Tao day nut chay thuat toan, analyze, reset, level va menu
        buttons = []
        x = 24
        for name in self.algorithm_manager.get_algorithms():
            color = (42, 130, 96) if name == self.selected_algorithm else (55, 83, 132)
            hover = (66, 170, 126) if name == self.selected_algorithm else (78, 115, 178)
            buttons.append(Button((x, 684, 150, 30), self.short_label(name), lambda n=name: self.select_algorithm(n), color, hover, 13))
            x += 158
        stop_label = "RESUME" if self.state == "PAUSED" else "STOP"
        buttons.extend(
            [
                Button((520, 684, 82, 30), "RUN", self.run_selected, (43, 128, 80), (66, 172, 109), 17),
                Button((612, 684, 82, 30), stop_label, self.stop_selected, (145, 58, 68), (190, 78, 88), 15),
                Button((704, 684, 118, 30), "ANALYZE", self.open_analysis, (93, 68, 148), (127, 94, 194), 16),
                Button((834, 684, 92, 30), "RESET", self.reset_level, (92, 96, 107), (125, 131, 145), 16),
                Button((938, 684, 92, 30), "LEVELS", lambda: self.finish("map_select"), (70, 93, 124), (94, 124, 164), 15),
                Button((1042, 684, 82, 30), "MENU", self.ask_menu, (132, 48, 56), (178, 68, 78), 16),
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
        # Doi thuat toan dang duoc chon va cap nhat nut
        self.selected_algorithm = name
        self.buttons = self.build_buttons()
        self.manager.status_message = f"Selected {name}"

    def reset_level(self):
        # Reset lai trang thai man choi ve luc bat dau
        self.manager.reset()
        self.algorithm_manager.set_map(self.manager.map)
        self.selected_algorithm = self.algorithm_manager.get_algorithms()[0]
        self.result = None
        self.analysis_results = []
        self.state = "READY"
        self.move_timer = 0.0
        self.wave_elapsed = 0.0
        self.hero_flip = False
        self.buttons = self.build_buttons()

    def run_selected(self):
        # Chay thuat toan dang chon tu vi tri hien tai cua robot
        if self.state == "ANALYSIS":
            return
        if self.state == "RUNNING":
            self.manager.status_message = "Already running. Press STOP to pause."
            return
        if self.state == "PAUSED":
            self.state = "RUNNING" if self.manager.robot.next_cell() else "READY"
            self.manager.status_message = "Resumed."
            self.buttons = self.build_buttons()
            return
        self.result = self.algorithm_manager.run_algorithm(
            self.selected_algorithm,
            self.manager.robot.position,
            battery=self.manager.robot.battery,
        )
        self.wave_elapsed = 0.0
        self.manager.status_message = self.result.get("message", "")
        if self.result.get("success") and self.result.get("path"):
            self.manager.robot.set_path(self.result["path"])
            self.state = "RUNNING" if len(self.result["path"]) > 1 else "READY"
        else:
            self.state = "READY"
        self.buttons = self.build_buttons()

    def stop_selected(self):
        if self.state == "RUNNING":
            self.state = "PAUSED"
            self.manager.status_message = "Paused."
            self.buttons = self.build_buttons()
            return
        if self.state == "PAUSED":
            self.state = "RUNNING" if self.manager.robot.next_cell() else "READY"
            self.manager.status_message = "Resumed." if self.state == "RUNNING" else "No remaining path."
            self.buttons = self.build_buttons()

    def open_analysis(self):
        # Chay tat ca thuat toan de so sanh ket qua
        self.analysis_results = self.algorithm_manager.analyze_all(
            start=self.manager.robot.position,
            battery=self.manager.robot.battery,
        )
        self.state = "ANALYSIS"

    def ask_menu(self):
        self.confirm = ConfirmDialog("Return to main menu?", lambda: self.finish("main_menu"))

    def handle_events(self, events):
        # Xu ly phim, click nut va bang phan tich
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
                elif event.key == pygame.K_s:
                    self.stop_selected()
                elif event.key == pygame.K_ESCAPE:
                    self.ask_menu()

            for button in self.buttons:
                if button.handle_event(event):
                    break

    def update(self, dt):
        # Cap nhat vat can dong, timer va buoc di cua robot
        moved = False
        if self.state != "ANALYSIS" and self.state != "PAUSED" and self.result and self.result.get("visited"):
            self.wave_elapsed += dt

        if self.state in ("READY", "RUNNING"):
            self.hero_idle.update(dt)
            self.hero_run.update(dt)
            for anim in getattr(self, "obstacle_anims", []):
                anim.update(dt)
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

        self.set_hero_direction(robot.position, nxt)
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
        self.result = self.algorithm_manager.run_algorithm(
            self.selected_algorithm,
            self.manager.robot.position,
            battery=self.manager.robot.battery,
        )
        self.wave_elapsed = 0.0
        if self.result.get("success") and len(self.result.get("path", [])) > 1:
            self.manager.robot.set_path(self.result["path"])
            self.state = "RUNNING"
        else:
            self.state = "FAILED"
        self.buttons = self.build_buttons()

    def draw(self):
        # Ve toan bo man choi: bang tren, grid, HUD va cac overlay
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
        # Ve thanh thong tin tren cung cua level
        pygame.draw.rect(self.screen, COLOR_TOP_BAR, (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.line(self.screen, (190, 200, 216), (0, 60), (SCREEN_WIDTH, 60), 1)
        draw_text(self.screen, "AI Hospital Dispatcher", 27, COLOR_GOLD, (30, 14), bold=True)
        draw_text(self.screen, self.manager.map.title, 22, COLOR_WHITE, (395, 18), bold=True)
        draw_text(self.screen, self.manager.status_message, 17, COLOR_WHITE, (820, 21))

    def draw_grid(self):
        # Ve luoi benh vien, task, vat can dong va duong di
        hospital_map = self.manager.map
        path = set(self.result.get("path", [])) if self.result else set()
        visited_order = (self.result or {}).get("visited", [])
        visible_count = min(len(visited_order), int(self.wave_elapsed * self.wave_nodes_per_second))
        visited = {cell: index for index, cell in enumerate(visited_order[:visible_count])}
        for row in range(hospital_map.rows):
            for col in range(hospital_map.cols):
                value = hospital_map.grid[row][col]
                rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                self.draw_tile(rect, value, row, col)
                if (row, col) in visited:
                    self.draw_wave_cell(rect, visible_count - visited[(row, col)])
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
            self.draw_obstacle(obstacle)
        self.draw_robot(self.manager.robot.position)
        pygame.draw.rect(
            self.screen,
            COLOR_WHITE,
            (GRID_OFFSET_X, GRID_OFFSET_Y, hospital_map.cols * TILE_SIZE, hospital_map.rows * TILE_SIZE),
            2,
        )

    def draw_wave_cell(self, rect, age):
        color = ALGORITHM_WAVE_COLORS.get(self.selected_algorithm, (143, 178, 214))
        alpha = max(54, 168 - age * 3)
        fill = pygame.Surface(rect.size, pygame.SRCALPHA)
        fill.fill((*color, alpha))
        self.screen.blit(fill, rect)
        pygame.draw.rect(self.screen, color, rect.inflate(-8, -8), 2, border_radius=6)

    def draw_tile(self, rect, value, row, col):
        if value == 1:
            pygame.draw.rect(self.screen, CELL_COLORS[1], rect)
            return
        elif value == 2:
            image = self.weighted_img
        elif value == 3:
            pygame.draw.rect(self.screen, CELL_COLORS[0], rect)
            tint = pygame.Surface(rect.size, pygame.SRCALPHA)
            tint.fill((84, 146, 178, 46))
            self.screen.blit(tint, rect)
            return
        else:
            pygame.draw.rect(self.screen, CELL_COLORS[0], rect)
            return
        self.screen.blit(image, rect)
        tint = pygame.Surface(rect.size, pygame.SRCALPHA)
        if value == 2:
            tint.fill((240, 196, 92, 78))
        self.screen.blit(tint, rect)
        if value == 2:
            pygame.draw.rect(self.screen, (240, 196, 92), rect.inflate(-26, -26), border_radius=5)
            draw_text(self.screen, "5", 10, COLOR_WHITE, (rect.right - 10, rect.y + 10), center=True, bold=True)

    def set_hero_direction(self, current, nxt):
        dc = nxt[1] - current[1]
        if dc < 0:
            self.hero_flip = True
        elif dc > 0:
            self.hero_flip = False

    def draw_cell_badge(self, pos, label, color):
        row, col = pos
        cell_rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        icon = self.charge_img if label == "CHG" else self.start_img
        icon_rect = icon.get_rect(center=cell_rect.center)
        self.screen.blit(icon, icon_rect)
        halo = pygame.Surface(cell_rect.size, pygame.SRCALPHA)
        halo.fill((color[0], color[1], color[2], 38))
        self.screen.blit(halo, cell_rect)
        rect = pygame.Rect(cell_rect.centerx - 18, cell_rect.bottom - 16, 36, 14)
        if label == "CHG":
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            draw_text(self.screen, label, 8, COLOR_WHITE, rect.center, center=True, bold=True)
            return
        if label == "START":
            pygame.draw.rect(self.screen, color, rect, 2, border_radius=6)
            draw_text(self.screen, label, 7, COLOR_WHITE, rect.center, center=True, bold=True)
            return
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_WHITE, rect, 1, border_radius=6)
        draw_text(self.screen, label, 9, COLOR_WHITE, rect.center, center=True, bold=True)

    def draw_task(self, task, color):
        row, col = task.target
        rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        image = self.task_imgs[sum(ord(char) for char in task.task_id) % len(self.task_imgs)]
        image_rect = image.get_rect(center=rect.center)
        self.screen.blit(image, image_rect)
        badge = pygame.Rect(rect.x + 4, rect.y + 4, 24, 14)
        pygame.draw.rect(self.screen, color, badge, border_radius=5)
        pygame.draw.rect(self.screen, COLOR_WHITE, badge, 1, border_radius=5)
        draw_text(self.screen, task.task_id, 9, COLOR_WHITE, badge.center, center=True, bold=True)
        if task.deadline and not task.completed:
            draw_text(self.screen, str(int(task.deadline)), 10, COLOR_RED, (rect.right - 8, rect.y + 5), center=True, bold=True)

    def draw_obstacle(self, obstacle):
        pos = obstacle.pos
        row, col = pos
        rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        sprite_rect = self.obstacle_img.get_rect(center=(rect.centerx, rect.bottom - 14))
        self.screen.blit(self.obstacle_img, sprite_rect)
        pygame.draw.rect(self.screen, (218, 96, 52), rect.inflate(-24, -24), 2, border_radius=6)
        draw_text(self.screen, "!", 12, COLOR_WHITE, (rect.right - 10, rect.y + 8), center=True, bold=True)

    def draw_robot(self, pos):
        row, col = pos
        rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        anim = self.hero_run if self.state == "RUNNING" else self.hero_idle
        draw_pos = (int(rect.centerx - anim.size[0] / 2), int(rect.bottom - anim.size[1] + 12))
        anim.draw(self.screen, draw_pos, flip_x=self.hero_flip)

    def draw_legend(self):
        # Giai thich mau sac/ky hieu tren luoi
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
        # Ve thanh nut dieu khien o duoi man hinh
        pygame.draw.rect(self.screen, COLOR_BOTTOM_BAR, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        for button in self.buttons:
            button.draw(self.screen)

    def draw_end_overlay(self):
        border = COLOR_GREEN if self.state == "COMPLETED" else COLOR_RED
        title = "LEVEL COMPLETE" if self.state == "COMPLETED" else "MISSION FAILED"
        rect = pygame.Rect(860, 82, 390, 104)
        draw_panel(self.screen, rect, (18, 22, 34), border, 232)
        draw_text(self.screen, title, 24, border, (rect.x + 18, rect.y + 14), bold=True)
        draw_text(self.screen, self.manager.status_message, 18, COLOR_WHITE, (rect.x + 18, rect.y + 50))
        

