import pygame

from algorithms.bfs import bfs
from algorithms.common import merge_paths
from algorithms.dfs import dfs
from algorithms.ucs import ucs
from core.animation import GIFAnimation
from core.scene_base import SceneBase
from core.ui import (
    Button,
    ConfirmDialog,
    assets,
    draw_panel,
    draw_text,
    draw_text_block,
    format_time,
    wrap_text,
)
from settings import (
    COLOR_BLACK,
    COLOR_BLUE,
    COLOR_BOTTOM_BAR,
    COLOR_GOLD,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_TOP_BAR,
    COLOR_WHITE,
    ENEMY_DRAW_SIZE,
    GRID_COLS,
    GRID_OFFSET_X,
    GRID_OFFSET_Y,
    GRID_ROWS,
    HERO_DRAW_SIZE,
    HERO_SPEED,
    NARRATOR_HEIGHT,
    NARRATOR_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_SPEED,
    TILE_SIZE,
    VISUALIZE_SPEED,
)


class Map1Scene(SceneBase):
    """Man 1: khu rung hon mang."""

    def on_enter(self):
        self.game.play_music("assets/sounds/music/forest_theme.mp3")
        self.bg_intro = assets.load_image("assets/man1/rung.png", (SCREEN_WIDTH, SCREEN_HEIGHT), fallback_color=(10, 18, 24))
        self.bg_game = assets.load_image("assets/man1/rung.png", (SCREEN_WIDTH, SCREEN_HEIGHT), fallback_color=(12, 35, 28))
        raw_narrator = assets.load_image("assets/man1/intro/intro1.jpg", fallback_color=(80, 90, 130))
        bounds = raw_narrator.get_bounding_rect()
        if bounds.width and bounds.height:
            raw_narrator = raw_narrator.subsurface(bounds).copy()
        self.narrator = pygame.transform.smoothscale(raw_narrator, (NARRATOR_WIDTH - 32, NARRATOR_HEIGHT - 18))
        self.panel_img = assets.load_image("assets/man1/back.png", (400, 540), fallback_color=(25, 30, 55))
        self.tile_grass = assets.load_image("assets/man1/Plants/Plant_1.png", (TILE_SIZE, TILE_SIZE), fallback_color=(48, 125, 55))
        self.stones = {
            1: assets.load_image("assets/man1/dat2.png", (TILE_SIZE, TILE_SIZE), fallback_color=(85, 85, 90)),
            2: assets.load_image("assets/man1/dat4.png", (TILE_SIZE, TILE_SIZE), fallback_color=(75, 78, 86)),
            3: assets.load_image("assets/man1/dat1.png", (TILE_SIZE, TILE_SIZE), fallback_color=(95, 90, 80)),
            4: assets.load_image("assets/man1/dat3.png", (TILE_SIZE, TILE_SIZE), fallback_color=(70, 70, 82)),
        }
        self.key_img = assets.load_image("assets/sprites/items/old_key.png", (TILE_SIZE, TILE_SIZE), fallback_color=(230, 180, 30))
        self.gate_locked = assets.load_image("assets/sprites/items/stone_gate_locked.png", (TILE_SIZE, TILE_SIZE), fallback_color=(95, 95, 105))
        self.gate_open = assets.load_image("assets/sprites/items/stone_gate_open.png", (TILE_SIZE, TILE_SIZE), fallback_color=(90, 130, 115))

        actor_size = (HERO_DRAW_SIZE * 2, HERO_DRAW_SIZE)
        enemy_size = (ENEMY_DRAW_SIZE, ENEMY_DRAW_SIZE)
        self.hero_idle = GIFAnimation("assets/man2/update_nv/idle_x4.gif", size=actor_size, frame_time=0.18, fallback_color=(80, 150, 255), alt_paths=["assets/man1/Heroine base/Previews/idle.gif"])
        self.hero_run = GIFAnimation("assets/man2/update_nv/run_x4.gif", size=actor_size, frame_time=0.1, fallback_color=(70, 210, 255), alt_paths=["assets/man2/update_nv/attack_x4.gif", "assets/man2/update_nv/Previews/run.gif"])
        self.hero_jump = GIFAnimation("assets/man2/update_nv/jump_x4.gif", size=actor_size, frame_time=0.12, fallback_color=(255, 220, 90), alt_paths=["assets/man2/update_nv/Previews/jump.gif"])
        self.hero_attack = GIFAnimation(
            "assets/man2/update_nv/attack_x4.gif",
            size=actor_size,
            frame_time=0.09,
            fallback_color=(255, 180, 90),
            alt_paths=[
                "assets/man1/attack_x4.gif",
                "assets/man1/Heroine base/Previews/attack.gif",
                "assets/man1/Heroine base/Spritesheets/attack.png",
            ],
        )
        self.monster_anims = {
            "slime": GIFAnimation("assets/man1/slime-preview.gif", size=enemy_size, frame_time=0.16, fallback_color=(60, 220, 80)),
            "goblin": GIFAnimation("assets/man1/ogre-idle.gif", size=enemy_size, frame_time=0.15, fallback_color=(190, 90, 45)),
        }
        self.monster_attack_anims = {
            "slime": GIFAnimation(
                "assets/man1/slime-attack.gif",
                size=enemy_size,
                frame_time=0.1,
                fallback_color=(120, 255, 120),
                alt_paths=["assets/man1/slime-preview.gif"],
            ),
            "goblin": GIFAnimation(
                "assets/man1/ogre-attack.gif",
                size=enemy_size,
                frame_time=0.1,
                fallback_color=(230, 100, 55),
                alt_paths=["assets/man1/ogre-idle.gif"],
            ),
        }
        self.reset_scene(full=True)

    def reset_scene(self, full=False):
        self.matrix = [
            [5, 0, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 2, 2, 0, 2, 0, 4, 4, 4, 4, 0, 3, 0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 4, 0, 3, 0, 0, 0, 1, 0],
            [1, 1, 1, 1, 0, 2, 2, 2, 2, 2, 0, 0, 4, 0, 3, 3, 3, 0, 1, 0],
            [0, 0, 0, 1, 0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0],
            [0, 3, 0, 1, 1, 1, 1, 0, 0, 2, 2, 2, 2, 2, 2, 0, 3, 3, 3, 1],
            [0, 3, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [0, 3, 3, 3, 3, 0, 1, 1, 1, 1, 1, 1, 0, 4, 4, 4, 4, 4, 4, 1],
            [0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 1, 0, 4, 6, 0, 0, 4, 0, 1],
            [1, 1, 0, 0, 3, 3, 3, 3, 3, 0, 0, 1, 0, 4, 4, 4, 0, 4, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 3, 0, 0, 1, 0, 0, 0, 4, 0, 4, 4, 0],
            [0, 1, 1, 1, 1, 1, 0, 0, 3, 0, 0, 1, 1, 1, 0, 4, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 4, 4, 4, 4, 0],
            [0, 2, 2, 2, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 7],
        ]
        self.monsters = [
            {"type": "slime", "pos": (3, 5)},
            {"type": "slime", "pos": (10, 3)},
            {"type": "goblin", "pos": (15, 8)},
            {"type": "slime", "pos": (5, 11)},
            {"type": "goblin", "pos": (2, 5)},
        ]
        for monster in self.monsters:
            col, row = monster["pos"]
            monster["grid_pos"] = (row, col)
            monster["defeated"] = False
        self.story_script = [
            "Chao mung nguoi, hoi nguoi hoc viec...",
            "Day la Khu Rung Hon Mang - thu thach dau tien.",
            "Suong mu day dac che khuat moi loi di.",
            "Quai vat an nap trong bui ram, san sang chan duong.",
            "",
            "Nhiem vu cua nguoi: TIM CHIA KHOA CO.",
            "Sau do, mo CONG DA o goc sau khu rung.",
            "",
            "Ba phuong phap co xua se dan loi cho nguoi:",
            "BFS - Lan toa nhu song, tim moi ngoc ngach...",
            "DFS - Di thang den cung, roi quay lui thu loi khac...",
            "UCS - Luon chon con duong it ton suc nhat...",
            "",
            "Hay chon cach cua nguoi, va bat dau hanh trinh!",
            "Nhan ENTER de buoc vao khu rung...",
        ]
        self.story_script = [line for line in self.story_script if line]
        self.state = "INTRO" if full else "READY"
        self.start = (0, 0)
        self.key_pos = (8, 14)
        self.gate_pos = (14, 19)
        self.hero_grid = self.start
        self.hero_pixel = self.grid_to_pixel(self.hero_grid)
        self.hero_path = []
        self.hero_index = 0
        self.move_timer = 0.0
        self.visited = []
        self.visual_index = 0
        self.visual_timer = 0.0
        self.path = []
        self.algorithm_name = "Chua chon"
        self.algorithm_color = COLOR_GREEN
        self.stats = {"nodes": 0, "depth": 0, "cost": 0, "success": False}
        self.has_key = False
        self.elapsed = 0.0
        self.analysis_results = None
        self.confirm = None
        self.hero_mode = "idle"
        self.hero_flip = False
        self.hero_attacks_left = 1
        self.attack_timer = 0.0
        self.attack_duration = 0.55
        self.attack_target = None
        self.monster_attack_timer = 0.0
        self.monster_attack_duration = 0.8
        self.killing_monster = None
        self.intro_line_index = 0
        self.intro_char_count = 0.0
        self.static_grid = self.build_static_grid()
        self.buttons = self.build_buttons()

    def build_buttons(self):
        return [
            Button((30, 684, 90, 30), "BFS", lambda: self.start_algorithm("BFS"), (40, 125, 75), (65, 175, 105), 18),
            Button((130, 684, 90, 30), "DFS", lambda: self.start_algorithm("DFS"), (140, 50, 55), (190, 70, 80), 18),
            Button((230, 684, 90, 30), "UCS", lambda: self.start_algorithm("UCS"), (55, 80, 160), (80, 110, 215), 18),
            Button((340, 684, 165, 30), "PHAN TICH", self.open_analysis, (95, 65, 145), (130, 90, 190), 17),
            Button((520, 684, 110, 30), "RESET", lambda: self.reset_scene(False), (100, 100, 110), (135, 135, 145), 18),
            Button((645, 684, 110, 30), "MENU", self.ask_menu, (130, 45, 55), (180, 65, 75), 18),
        ]

    def build_static_grid(self):
        surface = pygame.Surface((GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE), pygame.SRCALPHA)
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                value = self.matrix[row][col]
                rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                surface.blit(self.tile_grass, rect)
                if value in self.stones:
                    surface.blit(self.stones[value], rect)
                pygame.draw.rect(surface, (15, 25, 25, 95), rect, 1)
        return surface

    def grid_to_pixel(self, pos):
        row, col = pos
        return (GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE)

    def actor_draw_pos(self, grid_pos):
        return self.grid_to_pixel(grid_pos)

    def sprite_draw_pos(self, cell_pixel, sprite_size):
        x, y = cell_pixel
        return (
            int(x + TILE_SIZE / 2 - sprite_size[0] / 2),
            int(y + TILE_SIZE - sprite_size[1] + 4),
        )

    def intro_skip_rect(self):
        return pygame.Rect(SCREEN_WIDTH - 170, SCREEN_HEIGHT - 58, 138, 36)

    def skip_intro(self):
        self.state = "READY"
        self.intro_line_index = len(self.story_script) - 1
        self.intro_char_count = float(len(self.story_script[-1]))

    def run_solver(self, name, start, goal):
        if name == "BFS":
            return bfs(self.matrix, start, goal)
        if name == "DFS":
            return dfs(self.matrix, start, goal)
        return ucs(self.matrix, start, goal)

    def make_route_result(self, name):
        first = self.run_solver(name, self.start, self.key_pos)
        second = self.run_solver(name, self.key_pos, self.gate_pos) if first["success"] else {"path": [], "visited": [], "nodes": 0, "depth": -1, "cost": 0, "success": False}
        path = merge_paths(first["path"], second["path"])
        visited = first["visited"] + second["visited"]
        return {
            "path": path,
            "visited": visited,
            "nodes": first["nodes"] + second["nodes"],
            "depth": max(first["depth"], second["depth"]),
            "cost": first["cost"] + second["cost"],
            "success": first["success"] and second["success"],
        }

    def start_algorithm(self, name):
        if self.state not in ("READY", "COMPLETED"):
            return
        colors = {"BFS": COLOR_GREEN, "DFS": COLOR_RED, "UCS": COLOR_BLUE}
        result = self.make_route_result(name)
        self.algorithm_name = name
        self.algorithm_color = colors[name]
        self.stats = result
        self.path = result["path"]
        self.visited = result["visited"]
        self.visual_index = 0
        self.visual_timer = 0.0
        self.hero_grid = self.start
        self.hero_pixel = self.grid_to_pixel(self.hero_grid)
        self.hero_path = []
        self.hero_index = 0
        self.move_timer = 0.0
        self.has_key = False
        self.elapsed = 0.0
        self.hero_mode = "idle"
        self.hero_attacks_left = 1
        self.attack_timer = 0.0
        self.attack_target = None
        self.monster_attack_timer = 0.0
        self.killing_monster = None
        for monster in self.monsters:
            monster["defeated"] = False
        self.state = "VISUALIZING" if result["visited"] else "READY"

    def open_analysis(self):
        self.analysis_results = {name: self.make_route_result(name) for name in ("BFS", "DFS", "UCS")}
        self.state = "ANALYSIS"

    def ask_menu(self):
        self.confirm = ConfirmDialog("Ve menu chinh?", lambda: self.finish("main_menu"))

    def handle_intro_input(self):
        full_line = self.story_script[self.intro_line_index]
        if self.intro_char_count < len(full_line):
            self.intro_char_count = float(len(full_line))
            return
        if self.intro_line_index >= len(self.story_script) - 1:
            self.state = "READY"
            return
        sound = assets.load_sound("assets/sounds/sfx/page_flip.wav")
        if sound:
            sound.play()
        self.intro_line_index += 1
        self.intro_char_count = 0.0

    def handle_events(self, events):
        if self.confirm and self.confirm.active:
            self.confirm.handle_events(events)
            return

        for event in events:
            if self.state == "INTRO":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.handle_intro_input()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.intro_skip_rect().collidepoint(event.pos):
                        self.skip_intro()
                continue

            if self.state == "ANALYSIS":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "READY"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    close_rect = pygame.Rect(908, 122, 52, 34)
                    if close_rect.collidepoint(event.pos):
                        self.state = "READY"
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                top_menu = pygame.Rect(1200, 12, 60, 36)
                if top_menu.collidepoint(event.pos):
                    self.ask_menu()
                    return

            for button in self.buttons:
                if button.handle_event(event):
                    break

    def update(self, dt):
        for anim in self.monster_anims.values():
            anim.update(dt)
        for anim in self.monster_attack_anims.values():
            anim.update(dt)
        self.hero_idle.update(dt)
        self.hero_run.update(dt)
        self.hero_jump.update(dt)
        self.hero_attack.update(dt)

        if self.state == "INTRO":
            current_line = self.story_script[self.intro_line_index]
            self.intro_char_count = min(len(current_line), self.intro_char_count + TEXT_SPEED * dt)
            return

        self.elapsed += dt

        if self.state == "VISUALIZING":
            self.visual_timer += dt
            while self.visual_timer >= VISUALIZE_SPEED and self.visual_index < len(self.visited):
                self.visual_timer -= VISUALIZE_SPEED
                self.visual_index += 1
            if self.visual_index >= len(self.visited):
                if self.path:
                    self.hero_path = self.path
                    self.hero_index = 0
                    self.move_timer = 0.0
                    self.state = "HERO_MOVING"
                else:
                    self.state = "READY"

        if self.state == "HERO_MOVING":
            self.update_hero_move(dt)

        if self.state == "HERO_ATTACKING":
            self.update_hero_attack(dt)

        if self.state == "MONSTER_ATTACKING":
            self.update_monster_attack(dt)

    def set_hero_direction(self, current, nxt):
        dr = nxt[0] - current[0]
        dc = nxt[1] - current[1]
        if dr < 0:
            self.hero_mode = "jump"
        else:
            self.hero_mode = "run"
        if dc < 0:
            self.hero_flip = True
        elif dc > 0:
            self.hero_flip = False

    def update_hero_move(self, dt):
        if not self.hero_path or self.hero_index >= len(self.hero_path) - 1:
            self.state = "COMPLETED"
            self.hero_grid = self.gate_pos
            self.hero_pixel = self.grid_to_pixel(self.hero_grid)
            self.hero_mode = "idle"
            return

        start_node = self.hero_path[self.hero_index]
        end_node = self.hero_path[self.hero_index + 1]
        self.set_hero_direction(start_node, end_node)

        self.move_timer += dt
        progress = min(1.0, self.move_timer / HERO_SPEED)
        start_px = self.grid_to_pixel(start_node)
        end_px = self.grid_to_pixel(end_node)
        x = start_px[0] + (end_px[0] - start_px[0]) * progress
        y = start_px[1] + (end_px[1] - start_px[1]) * progress
        self.hero_pixel = (x, y)

        if progress >= 1.0:
            self.hero_index += 1
            self.move_timer = 0.0
            self.hero_grid = self.hero_path[self.hero_index]
            monster = self.monster_at(self.hero_grid)
            if monster:
                if self.hero_attacks_left > 0:
                    self.start_attack(monster)
                else:
                    self.start_monster_attack(monster)
                return
            if self.hero_grid == self.key_pos:
                self.has_key = True
            if self.hero_grid == self.gate_pos:
                self.state = "COMPLETED"
                self.hero_mode = "idle"

    def monster_at(self, grid_pos):
        for monster in self.monsters:
            if not monster["defeated"] and monster["grid_pos"] == grid_pos:
                return monster
        return None

    def start_attack(self, monster):
        self.attack_target = monster
        self.attack_timer = 0.0
        self.hero_attacks_left -= 1
        self.hero_mode = "attack"
        self.hero_attack.reset()
        sound = assets.load_sound("assets/FreeMix/FreeMix/sfx/punch.wav")
        if sound:
            sound.play()
        self.state = "HERO_ATTACKING"

    def update_hero_attack(self, dt):
        self.attack_timer += dt
        if self.attack_timer < self.attack_duration:
            return
        if self.attack_target:
            self.attack_target["defeated"] = True
        self.attack_target = None
        self.hero_mode = "idle"
        if self.hero_grid == self.key_pos:
            self.has_key = True
        if self.hero_grid == self.gate_pos:
            self.state = "COMPLETED"
        else:
            self.state = "HERO_MOVING"

    def start_monster_attack(self, monster):
        self.killing_monster = monster
        self.monster_attack_timer = 0.0
        self.hero_mode = "idle"
        attack_anim = self.monster_attack_anims.get(monster["type"])
        if attack_anim:
            attack_anim.reset()
        sound = assets.load_sound("assets/sounds/sfx/defeat.wav")
        if sound:
            sound.play()
        self.state = "MONSTER_ATTACKING"

    def update_monster_attack(self, dt):
        self.monster_attack_timer += dt
        if self.monster_attack_timer >= self.monster_attack_duration:
            self.state = "GAME_OVER"

    def current_intro_lines(self, max_lines=3):
        current = self.story_script[self.intro_line_index][: int(self.intro_char_count)]
        lines = wrap_text(current, 24, 900) if current else [""]
        return lines[:3]
    
        lines = []
        
        # Gom TẤT CẢ các dòng đã qua + dòng hiện tại
        for line in self.story_script[: self.intro_line_index]:
            wrapped = wrap_text(line, 22, 930) if line else [""]  # 22 là font size
            lines.extend(wrapped)
        
        # Thêm dòng hiện tại (đang chạy chữ)
        current = self.story_script[self.intro_line_index][: int(self.intro_char_count)]
        wrapped_current = wrap_text(current, 22, 930) if current else [""]
        lines.extend(wrapped_current)
        
        # Chỉ lấy max_lines dòng CUỐI CÙNG
        return lines[-max_lines:] if len(lines) > max_lines else lines

    def draw(self):
        if self.state == "INTRO":
            self.draw_intro()
            return
        self.screen.blit(self.bg_game, (0, 0))
        self.draw_top_bar()
        self.draw_grid()
        self.draw_info_panel()
        self.draw_bottom_bar()
        if self.state == "ANALYSIS":
            self.draw_analysis_overlay()
        if self.state == "GAME_OVER":
            self.draw_game_over_overlay()
        if self.confirm and self.confirm.active:
            self.confirm.draw(self.screen)

    def draw_intro(self):
        self.screen.blit(self.bg_intro, (0, 0))
        
        # Lớp phủ tối
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 95))
        self.screen.blit(shade, (0, 0))
        
        # Tiêu đề
        draw_text(self.screen, "KHU RUNG HON MANG", 46, COLOR_GOLD, 
                (SCREEN_WIDTH // 2, 86), center=True, bold=True)

        # ── VẼ NGƯỜI DẪN TRUYỆN ──
        portrait_rect = pygame.Rect(18, SCREEN_HEIGHT - NARRATOR_HEIGHT - 18, 
                                    NARRATOR_WIDTH, NARRATOR_HEIGHT)
        draw_panel(self.screen, portrait_rect, (25, 24, 45), COLOR_WHITE, 238)
        portrait_pos = self.narrator.get_rect(
            midbottom=(portrait_rect.centerx, portrait_rect.bottom - 6)
        )
        self.screen.blit(self.narrator, portrait_pos)

        # ── VẼ TEXT BOX ──
        box_rect = pygame.Rect(235, SCREEN_HEIGHT - 260, 1015, 220)
        draw_panel(self.screen, box_rect, (18, 20, 40), COLOR_WHITE, 235)
        draw_text(self.screen, "LON SODA", 24, COLOR_GOLD, 
                (box_rect.x + 28, box_rect.y + 18), bold=True)

        # ── VẼ CHỮ TRONG TEXT BOX (CÓ GIỚI HẠN) ──
        lines = self.current_intro_lines(max_lines=7)  # Tối đa 7 dòng
        
        # Tạo 1 surface con để clip chữ (cắt phần thừa)
        text_area = pygame.Rect(box_rect.x + 20, box_rect.y + 50, 
                                box_rect.width - 50, box_rect.height - 70)
        
        # Vẽ từng dòng
        y = text_area.y
        for line in lines:
            if y + 30 > text_area.bottom:  # ← KIỂM TRA KHÔNG VƯỢT QUÁ ĐÁY
                break
            draw_text(self.screen, line, 22, COLOR_WHITE, (text_area.x + 8, y))
            y += 30  # Khoảng cách giữa các dòng

        # Nút ENTER
        draw_text(self.screen, "ENTER ĐỂ TIẾP TỤC", 20, COLOR_GOLD, 
                (box_rect.right - 170, box_rect.bottom - 34), bold=True)
        skip_rect = self.intro_skip_rect()
        pygame.draw.rect(self.screen, (130, 45, 55), skip_rect, border_radius=7)
        pygame.draw.rect(self.screen, COLOR_WHITE, skip_rect, 2, border_radius=7)
        draw_text(self.screen, "BO QUA", 17, COLOR_WHITE, skip_rect.center, center=True, bold=True)

    def draw_top_bar(self):
        pygame.draw.rect(self.screen, COLOR_TOP_BAR, (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.line(self.screen, (200, 200, 230), (0, 60), (SCREEN_WIDTH, 60), 1)
        draw_text(self.screen, "KHU RUNG HON MANG", 28, COLOR_WHITE, (30, 15), bold=True)
        draw_text(self.screen, format_time(self.elapsed), 24, COLOR_WHITE, (1090, 17), bold=True)
        menu_rect = pygame.Rect(1200, 12, 60, 36)
        pygame.draw.rect(self.screen, (130, 45, 55), menu_rect, border_radius=7)
        pygame.draw.rect(self.screen, COLOR_WHITE, menu_rect, 2, border_radius=7)
        draw_text(self.screen, "MENU", 16, COLOR_WHITE, menu_rect.center, center=True, bold=True)

    def draw_grid(self):
        self.screen.blit(self.static_grid, (GRID_OFFSET_X, GRID_OFFSET_Y))
        self.draw_visited_and_path()
        if not self.has_key:
            self.screen.blit(self.key_img, self.grid_to_pixel(self.key_pos))
        self.screen.blit(self.gate_open if self.has_key else self.gate_locked, self.grid_to_pixel(self.gate_pos))

        for monster in self.monsters:
            if monster["defeated"]:
                continue
            col, row = monster["pos"]
            if self.state == "MONSTER_ATTACKING" and monster is self.killing_monster:
                anim = self.monster_attack_anims[monster["type"]]
            else:
                anim = self.monster_anims[monster["type"]]
            cell_pos = (GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE)
            anim.draw(self.screen, self.sprite_draw_pos(cell_pos, anim.size))

        self.draw_hero()
        pygame.draw.rect(self.screen, COLOR_WHITE, (GRID_OFFSET_X, GRID_OFFSET_Y, GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE), 2)

    def draw_hero(self):
        if self.hero_mode == "jump":
            anim = self.hero_jump
        elif self.hero_mode == "run":
            anim = self.hero_run
        elif self.hero_mode == "attack":
            anim = self.hero_attack
        else:
            anim = self.hero_idle
        anim.draw(self.screen, self.sprite_draw_pos(self.hero_pixel, anim.size), flip_x=self.hero_flip)

    def draw_visited_and_path(self):
        overlay_color = (*self.algorithm_color, 95)
        for pos in self.visited[: self.visual_index]:
            row, col = pos
            rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill(overlay_color)
            self.screen.blit(surf, rect)
        if self.state in ("HERO_MOVING", "HERO_ATTACKING", "MONSTER_ATTACKING", "GAME_OVER", "COMPLETED"):
            for pos in self.path:
                row, col = pos
                rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE + 11, GRID_OFFSET_Y + row * TILE_SIZE + 11, 18, 18)
                pygame.draw.rect(self.screen, COLOR_GOLD, rect, border_radius=5)

    def draw_info_panel(self):
        rect = pygame.Rect(860, 80, 400, 540)
        self.screen.blit(self.panel_img, rect)
        tint = pygame.Surface(rect.size, pygame.SRCALPHA)
        tint.fill((12, 15, 32, 165))
        self.screen.blit(tint, rect)
        pygame.draw.rect(self.screen, COLOR_WHITE, rect, 2, border_radius=8)
        draw_text(self.screen, "THONG TIN", 30, COLOR_GOLD, (rect.centerx, rect.y + 32), center=True, bold=True)
        lines = [
            f"Thuat toan: {self.algorithm_name}",
            f"Nodes: {self.stats.get('nodes', 0)}",
            f"Do sau: {self.stats.get('depth', 0)}",
            f"Duong di: {max(0, len(self.path) - 1)} buoc",
            f"Key: {'Da nhat' if self.has_key else 'Chua co'}",
            f"Luot danh: {self.hero_attacks_left}/1",
            f"Trang thai: {'Khong tim thay' if not self.stats.get('success') and self.algorithm_name != 'Chua chon' else self.state}",
        ]
        for i, line in enumerate(lines):
            draw_text(self.screen, line, 21, COLOR_WHITE, (rect.x + 30, rect.y + 95 + i * 39))

    def draw_game_over_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(390, 210, 500, 220)
        draw_panel(self.screen, rect, (35, 18, 25), COLOR_RED, 245)
        draw_text(self.screen, "GAME OVER", 46, COLOR_RED, (rect.centerx, rect.y + 55), center=True, bold=True)
        draw_text(self.screen, "Hero da het luot danh va bi quai vat ha guc.", 21, COLOR_WHITE, (rect.centerx, rect.y + 112), center=True)
        draw_text(self.screen, "Bam RESET de thu lai hoac MENU de thoat.", 20, COLOR_GOLD, (rect.centerx, rect.y + 158), center=True)

    def draw_bottom_bar(self):
        pygame.draw.rect(self.screen, COLOR_BOTTOM_BAR, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        for button in self.buttons:
            button.draw(self.screen)

    def draw_analysis_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(300, 110, 680, 470)
        draw_panel(self.screen, rect, (22, 23, 48), COLOR_WHITE, 245)
        draw_text(self.screen, "PHAN TICH THUAT TOAN", 31, COLOR_GOLD, (rect.centerx, rect.y + 38), center=True, bold=True)
        close_rect = pygame.Rect(rect.right - 72, rect.y + 12, 52, 34)
        pygame.draw.rect(self.screen, (130, 45, 55), close_rect, border_radius=6)
        draw_text(self.screen, "X", 22, COLOR_WHITE, close_rect.center, center=True, bold=True)
        headers = ["Thuat toan", "Nodes", "Do sau", "Duong di", "Trang thai"]
        xs = [rect.x + 55, rect.x + 245, rect.x + 355, rect.x + 465, rect.x + 575]
        for x, header in zip(xs, headers):
            draw_text(self.screen, header, 18, COLOR_GOLD, (x, rect.y + 105), bold=True)
        for r, name in enumerate(("BFS", "DFS", "UCS")):
            data = self.analysis_results[name]
            y = rect.y + 150 + r * 62
            status = "OK" if data["success"] else "FAIL"
            row = [name, str(data["nodes"]), str(data["depth"]), str(max(0, len(data["path"]) - 1)), status]
            for x, value in zip(xs, row):
                draw_text(self.screen, value, 20, COLOR_WHITE, (x, y))
        notes = [
            "BFS: tim ngan nhat theo so buoc tren grid.",
            "DFS: gioi han do sau 80, du suc cho ban do hien tai.",
            "UCS: toi uu chi phi, hop voi grid co chi phi deu.",
            "Nhan ESC hoac X de dong.",
        ]
        for i, note in enumerate(notes):
            draw_text(self.screen, note, 19, COLOR_WHITE, (rect.x + 55, rect.y + 355 + i * 28))
