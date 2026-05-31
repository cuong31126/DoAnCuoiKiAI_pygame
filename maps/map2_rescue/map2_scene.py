import pygame

from algorithms.astar import astar_tsp
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
)


class Map2Scene(SceneBase):
    """Man 2: tram cuu ho ma thu."""

    def on_enter(self):
        self.game.play_music("assets/sounds/music/magical_theme.mp3")
        self.bg_intro = assets.load_image("assets/man2/BG2.png", (SCREEN_WIDTH, SCREEN_HEIGHT), fallback_color=(18, 20, 45))
        self.bg_game = assets.load_image("assets/man2/BG.png", (SCREEN_WIDTH, SCREEN_HEIGHT), fallback_color=(18, 42, 48))
        raw_narrator = assets.load_image("assets/man2/intro1.jpg", fallback_color=(80, 90, 130))
        bounds = raw_narrator.get_bounding_rect()
        if bounds.width and bounds.height:
            raw_narrator = raw_narrator.subsurface(bounds).copy()
        self.narrator = pygame.transform.smoothscale(raw_narrator, (NARRATOR_WIDTH - 32, NARRATOR_HEIGHT - 18))
        self.panel_img = assets.load_image("assets/ui/panel.png", (400, 540), fallback_color=(25, 30, 55))
        self.tile_grass = assets.load_image("assets/man1/dat1.png", (TILE_SIZE, TILE_SIZE), fallback_color=(45, 120, 70))
        self.stone = assets.load_image("assets/man2/Rock.png", (TILE_SIZE, TILE_SIZE), fallback_color=(80, 82, 90))

        hero_size = (HERO_DRAW_SIZE * 2, HERO_DRAW_SIZE)
        creature_size = (ENEMY_DRAW_SIZE, ENEMY_DRAW_SIZE)
        self.hero_idle = GIFAnimation("assets/man2/update_nv/idle_x4.gif", size=hero_size, frame_time=0.18, fallback_color=(80, 150, 255), alt_paths=["assets/man1/Heroine base/Previews/idle.gif"])
        self.hero_run = GIFAnimation("assets/man2/update_nv/run_x4.gif", size=hero_size, frame_time=0.1, fallback_color=(70, 210, 255), alt_paths=["assets/man2/update_nv/attack_x4.gif", "assets/man2/update_nv/Previews/run.gif"])
        self.hero_jump = GIFAnimation("assets/man2/update_nv/jump_x4.gif", size=hero_size, frame_time=0.12, fallback_color=(255, 220, 90), alt_paths=["assets/man2/update_nv/Previews/jump.gif"])
        self.creature_size = creature_size
        self.reset_scene(full=True)

    def reset_scene(self, full=False):
        self.matrix = self.build_matrix()
        self.base = (7, 10)
        self.story_script = [
            "Hoan ho! Nguoi da vuot qua Khu Rung Hon Mang.",
            "Gio day, mot thu thach moi dang cho don...",
            "Chao mung den voi TRAM CUU HO MA THU.",
            "",
            "Nhung sinh vat huyen thoai dang gap nan!",
            "Rong con dang mac ket trong da tam.",
            "Ran than bi thuong boi bay tho san bong toi.",
            "Chuon chuon khong lo dang kiet suc tren khong trung.",
            "Soi bac da lac dan trong rung toi.",
            "Nam linh hon dang dan mat di nang luong song.",
            "",
            "Moi sinh vat chi con mot khoang thoi gian ngan.",
            "Nguoi phai tim ra LO TRINH TOI UU de cuu tat ca,",
            "va dua chung ve TRAM BAO TON an toan!",
            "",
            "Hay nhu nha du hanh huyen thoai,",
            "nguoi tim ra con duong ngan nhat qua moi thanh pho!",
            "",
            "Nut [PHAN TICH] se giup nguoi xem lo trinh toi uu.",
            "Nhan ENTER de bat dau nhiem vu cuu ho...",
        ]
        self.story_script = [line for line in self.story_script if line]
        self.creatures = [
            {"name": "Rong", "icon": "RONG", "pos": (2, 2), "timer": 24, "gif": "assets/man2/update_nv/rong_fixed_128.gif", "color": (220, 90, 70)},
            {"name": "Ran", "icon": "RAN", "pos": (16, 2), "timer": 20, "gif": "assets/man2/update_nv/ran_fixed_128.gif", "color": (220, 220, 255)},
            {"name": "Chuon chuon", "icon": "CHUON", "pos": (17, 5), "timer": 30, "gif": "assets/man2/chuonchuon.gif", "color": (255, 160, 45)},
            {"name": "Soi", "icon": "SOI", "pos": (4, 11), "timer": 26, "gif": "assets/man2/update_nv/chosoi_fixed_128.gif", "color": (190, 205, 220)},
            {"name": "Nam linh hon", "icon": "NAM", "pos": (16, 12), "timer": 38, "gif": "assets/man2/nam_bi_benh.gif", "color": (70, 180, 110)},
        ]
        for creature in self.creatures:
            col, row = creature["pos"]
            creature["grid_pos"] = (row, col)
            creature["remaining"] = float(creature["timer"])
            creature["rescued"] = False
            creature["anim"] = GIFAnimation(creature["gif"], size=self.creature_size, frame_time=0.14, fallback_color=creature["color"])

        self.state = "INTRO" if full else "READY"
        self.hero_grid = self.base
        self.hero_pixel = self.grid_to_pixel(self.hero_grid)
        self.hero_mode = "idle"
        self.hero_flip = False
        self.route = []
        self.route_index = 0
        self.move_timer = 0.0
        self.elapsed = 0.0
        self.ai_result = None
        self.calc_timer = 0.0
        self.intro_line_index = 0
        self.intro_char_count = 0.0
        self.confirm = None
        self.static_grid = self.build_static_grid()
        self.buttons = self.build_buttons()

    def build_matrix(self):
        matrix = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        for col in range(1, 8):
            matrix[3][col] = 1
        for col in range(9, 18):
            matrix[4][col] = 1
        for col in range(2, 12):
            matrix[10][col] = 1
        for col in range(13, 19):
            matrix[11][col] = 1

        for row in range(0, 6):
            matrix[row][6] = 1
        for row in range(2, 12):
            matrix[row][13] = 1
        for row in range(6, 15):
            matrix[row][3] = 1
        for row in range(7, 15):
            matrix[row][17] = 1

        openings = [(3, 4), (4, 11), (10, 6), (11, 15), (1, 6), (8, 13), (9, 3), (12, 17), (7, 10)]
        for row, col in openings:
            matrix[row][col] = 0

        matrix[7][10] = 5
        return matrix

    def build_buttons(self):
        return [
            Button((330, 684, 140, 30), "BAT DAU", self.start_rescue, (45, 125, 85), (65, 175, 115), 18),
            Button((500, 684, 165, 30), "PHAN TICH", self.open_analysis, (95, 65, 145), (130, 90, 190), 17),
            Button((690, 684, 110, 30), "RESET", lambda: self.reset_scene(False), (100, 100, 110), (135, 135, 145), 18),
            Button((830, 684, 110, 30), "MENU", self.ask_menu, (130, 45, 55), (180, 65, 75), 18),
        ]

    def build_static_grid(self):
        surface = pygame.Surface((GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE), pygame.SRCALPHA)
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                surface.blit(self.tile_grass, rect)
                if self.matrix[row][col] == 1:
                    surface.blit(self.stone, rect)
                pygame.draw.rect(surface, (15, 25, 25, 95), rect, 1)
        return surface

    def grid_to_pixel(self, pos):
        row, col = pos
        return (GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE)

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

    def start_rescue(self):
        if self.state not in ("READY", "COMPLETED", "FAILED"):
            return
        self.ai_result = astar_tsp(self.base, self.creatures, self.matrix, HERO_SPEED)
        self.route = self.ai_result["route"]
        self.route_index = 0
        self.move_timer = 0.0
        self.hero_grid = self.base
        self.hero_pixel = self.grid_to_pixel(self.base)
        self.hero_mode = "idle"
        self.hero_flip = False
        for creature in self.creatures:
            creature["remaining"] = float(creature["timer"])
            creature["rescued"] = False
        self.elapsed = 0.0
        self.calc_timer = 0.0
        self.state = "AI_CALCULATING" if self.ai_result["safe"] else "FAILED"

    def open_analysis(self):
        if self.ai_result is None:
            self.ai_result = astar_tsp(self.base, self.creatures, self.matrix, HERO_SPEED)
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
                    close_rect = pygame.Rect(935, 122, 52, 34)
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
        for creature in self.creatures:
            creature["anim"].update(dt)
        self.hero_idle.update(dt)
        self.hero_run.update(dt)
        self.hero_jump.update(dt)

        if self.state == "INTRO":
            current_line = self.story_script[self.intro_line_index]
            self.intro_char_count = min(len(current_line), self.intro_char_count + TEXT_SPEED * dt)
            return

        if self.state in ("AI_CALCULATING", "HERO_RESCUING"):
            self.elapsed += dt
            self.update_creature_timers(dt)

        if self.state == "AI_CALCULATING":
            self.calc_timer += dt
            if self.calc_timer >= 0.4:
                self.state = "HERO_RESCUING"

        if self.state == "HERO_RESCUING":
            self.update_hero_move(dt)

    def update_creature_timers(self, dt):
        for creature in self.creatures:
            if creature["rescued"]:
                continue
            creature["remaining"] = max(0.0, creature["remaining"] - dt)
            if creature["remaining"] <= 0:
                sound = assets.load_sound("assets/sounds/sfx/defeat.wav")
                if sound:
                    sound.play()
                self.state = "FAILED"

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
        if not self.route:
            self.state = "FAILED"
            return

        self.check_rescue_at_current_cell()
        if self.route_index >= len(self.route) - 1:
            self.hero_mode = "idle"
            if all(creature["rescued"] for creature in self.creatures) and self.hero_grid == self.base:
                sound = assets.load_sound("assets/sounds/sfx/victory.wav")
                if sound:
                    sound.play()
                self.state = "COMPLETED"
            return

        start_node = self.route[self.route_index]
        end_node = self.route[self.route_index + 1]
        self.set_hero_direction(start_node, end_node)

        self.move_timer += dt
        progress = min(1.0, self.move_timer / HERO_SPEED)
        start_px = self.grid_to_pixel(start_node)
        end_px = self.grid_to_pixel(end_node)
        x = start_px[0] + (end_px[0] - start_px[0]) * progress
        y = start_px[1] + (end_px[1] - start_px[1]) * progress
        self.hero_pixel = (x, y)

        if progress >= 1.0:
            self.route_index += 1
            self.move_timer = 0.0
            self.hero_grid = self.route[self.route_index]
            self.check_rescue_at_current_cell()

    def check_rescue_at_current_cell(self):
        for creature in self.creatures:
            if not creature["rescued"] and self.hero_grid == creature["grid_pos"]:
                creature["rescued"] = True
                sound = assets.load_sound("assets/sounds/sfx/rescue.wav")
                if sound:
                    sound.play()

    def current_intro_lines(self):
        current = self.story_script[self.intro_line_index][: int(self.intro_char_count)]
        return (wrap_text(current, 24, 900) if current else [""])[:3]

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
        if self.confirm and self.confirm.active:
            self.confirm.draw(self.screen)

    def draw_intro(self):
        self.screen.blit(self.bg_intro, (0, 0))
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 95))
        self.screen.blit(shade, (0, 0))
        draw_text(self.screen, "TRAM CUU HO MA THU", 40, COLOR_GOLD, (SCREEN_WIDTH // 2, 86), center=True, bold=True)

        portrait_rect = pygame.Rect(18, SCREEN_HEIGHT - NARRATOR_HEIGHT - 18, NARRATOR_WIDTH, NARRATOR_HEIGHT)
        box_rect = pygame.Rect(235, SCREEN_HEIGHT - 260, 1015, 220)
        draw_panel(self.screen, portrait_rect, (25, 24, 45), COLOR_WHITE, 238)
        portrait_pos = self.narrator.get_rect(midbottom=(portrait_rect.centerx, portrait_rect.bottom - 6))
        self.screen.blit(self.narrator, portrait_pos)
        draw_panel(self.screen, box_rect, (18, 20, 40), COLOR_WHITE, 235)
        draw_text(self.screen, "Nguoi dan chuyen", 24, COLOR_GOLD, (box_rect.x + 28, box_rect.y + 18), bold=True)
        draw_text_block(self.screen, self.current_intro_lines(), 24, COLOR_WHITE, (box_rect.x + 28, box_rect.y + 56), line_gap=10)
        draw_text(self.screen, "ENTER: tiep tuc", 20, COLOR_GOLD, (box_rect.right - 170, box_rect.bottom - 34), bold=True)
        skip_rect = self.intro_skip_rect()
        pygame.draw.rect(self.screen, (130, 45, 55), skip_rect, border_radius=7)
        pygame.draw.rect(self.screen, COLOR_WHITE, skip_rect, 2, border_radius=7)
        draw_text(self.screen, "BO QUA", 17, COLOR_WHITE, skip_rect.center, center=True, bold=True)

    def draw_top_bar(self):
        pygame.draw.rect(self.screen, COLOR_TOP_BAR, (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.line(self.screen, (200, 200, 230), (0, 60), (SCREEN_WIDTH, 60), 1)
        draw_text(self.screen, "TRAM CUU HO MA THU", 28, COLOR_WHITE, (30, 15), bold=True)
        draw_text(self.screen, format_time(self.elapsed), 24, COLOR_WHITE, (1090, 17), bold=True)
        menu_rect = pygame.Rect(1200, 12, 60, 36)
        pygame.draw.rect(self.screen, (130, 45, 55), menu_rect, border_radius=7)
        pygame.draw.rect(self.screen, COLOR_WHITE, menu_rect, 2, border_radius=7)
        draw_text(self.screen, "MENU", 16, COLOR_WHITE, menu_rect.center, center=True, bold=True)

    def draw_grid(self):
        self.screen.blit(self.static_grid, (GRID_OFFSET_X, GRID_OFFSET_Y))
        self.draw_route_preview()
        self.draw_base()
        for creature in self.creatures:
            col, row = creature["pos"]
            pos = (GRID_OFFSET_X + col * TILE_SIZE, GRID_OFFSET_Y + row * TILE_SIZE)
            draw_pos = self.sprite_draw_pos(pos, creature["anim"].size)
            creature["anim"].draw(self.screen, draw_pos)
            if creature["rescued"]:
                badge = pygame.Rect(pos[0] + 21, pos[1] + 2, 17, 17)
                pygame.draw.circle(self.screen, COLOR_GREEN, badge.center, 9)
                draw_text(self.screen, "V", 14, COLOR_BLACK, badge.center, center=True, bold=True)
            else:
                draw_text(self.screen, str(int(creature["remaining"])), 14, COLOR_WHITE, (pos[0] + 3, pos[1] + 2), bold=True)
        self.draw_hero()
        pygame.draw.rect(self.screen, COLOR_WHITE, (GRID_OFFSET_X, GRID_OFFSET_Y, GRID_COLS * TILE_SIZE, GRID_ROWS * TILE_SIZE), 2)

    def draw_route_preview(self):
        if not self.ai_result or not self.ai_result.get("route"):
            return
        for pos in self.ai_result["route"]:
            row, col = pos
            rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE + 13, GRID_OFFSET_Y + row * TILE_SIZE + 13, 14, 14)
            pygame.draw.rect(self.screen, COLOR_GOLD, rect, border_radius=4)

    def draw_base(self):
        row, col = self.base
        rect = pygame.Rect(GRID_OFFSET_X + col * TILE_SIZE + 4, GRID_OFFSET_Y + row * TILE_SIZE + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        pygame.draw.rect(self.screen, (45, 95, 180), rect, border_radius=6)
        pygame.draw.rect(self.screen, COLOR_WHITE, rect, 2, border_radius=6)
        draw_text(self.screen, "BASE", 10, COLOR_WHITE, rect.center, center=True, bold=True)

    def draw_hero(self):
        if self.hero_mode == "jump":
            anim = self.hero_jump
        elif self.hero_mode == "run":
            anim = self.hero_run
        else:
            anim = self.hero_idle
        anim.draw(self.screen, self.sprite_draw_pos(self.hero_pixel, anim.size), flip_x=self.hero_flip)

    def draw_info_panel(self):
        rect = pygame.Rect(860, 80, 400, 540)
        self.screen.blit(self.panel_img, rect)
        tint = pygame.Surface(rect.size, pygame.SRCALPHA)
        tint.fill((12, 15, 32, 165))
        self.screen.blit(tint, rect)
        pygame.draw.rect(self.screen, COLOR_WHITE, rect, 2, border_radius=8)
        rescued = sum(1 for creature in self.creatures if creature["rescued"])
        draw_text(self.screen, "TRANG THAI", 30, COLOR_GOLD, (rect.centerx, rect.y + 32), center=True, bold=True)
        draw_text(self.screen, f"Da cuu: {rescued}/5", 24, COLOR_WHITE, (rect.x + 30, rect.y + 82), bold=True)
        for i, creature in enumerate(self.creatures):
            y = rect.y + 130 + i * 72
            label = f"{creature['name']} [{int(creature['remaining'])}s]"
            if creature["rescued"]:
                label += " OK"
            draw_text(self.screen, label, 19, COLOR_WHITE, (rect.x + 30, y), bold=True)
            bar_rect = pygame.Rect(rect.x + 30, y + 28, 250, 13)
            pygame.draw.rect(self.screen, (55, 55, 75), bar_rect, border_radius=5)
            ratio = creature["remaining"] / creature["timer"]
            fill = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.width * ratio), bar_rect.height)
            color = COLOR_GREEN if ratio > 0.45 else COLOR_RED
            pygame.draw.rect(self.screen, color, fill, border_radius=5)
            pygame.draw.rect(self.screen, COLOR_WHITE, bar_rect, 1, border_radius=5)
        draw_text(self.screen, f"Trang thai: {self.state}", 20, COLOR_GOLD, (rect.x + 30, rect.bottom - 50), bold=True)

    def draw_bottom_bar(self):
        pygame.draw.rect(self.screen, COLOR_BOTTOM_BAR, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        for button in self.buttons:
            button.draw(self.screen)

    def draw_analysis_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(280, 110, 720, 490)
        draw_panel(self.screen, rect, (22, 23, 48), COLOR_WHITE, 245)
        draw_text(self.screen, "PHAN TICH LO TRINH CUU HO", 29, COLOR_GOLD, (rect.centerx, rect.y + 38), center=True, bold=True)
        close_rect = pygame.Rect(rect.right - 65, rect.y + 12, 52, 34)
        pygame.draw.rect(self.screen, (130, 45, 55), close_rect, border_radius=6)
        draw_text(self.screen, "X", 22, COLOR_WHITE, close_rect.center, center=True, bold=True)

        result = self.ai_result or astar_tsp(self.base, self.creatures, self.matrix, HERO_SPEED)
        draw_text(self.screen, "Thuat toan: A* TSP", 23, COLOR_WHITE, (rect.x + 55, rect.y + 95), bold=True)
        if result["safe"]:
            route_names = ["BASE"] + [self.creatures[i]["icon"] for i in result["order"]] + ["BASE"]
            draw_text(self.screen, "Lo trinh toi uu:", 22, COLOR_GOLD, (rect.x + 55, rect.y + 145), bold=True)
            draw_text(self.screen, " -> ".join(route_names), 22, COLOR_WHITE, (rect.x + 55, rect.y + 178))
            draw_text(self.screen, f"Tong buoc di: {result['steps']}", 22, COLOR_WHITE, (rect.x + 55, rect.y + 235))
            draw_text(self.screen, f"Thoi gian du kien: {result['eta']:.1f}s", 22, COLOR_WHITE, (rect.x + 55, rect.y + 270))
            draw_text(self.screen, "Trang thai: AN TOAN", 22, COLOR_GREEN, (rect.x + 55, rect.y + 305), bold=True)
            y = rect.y + 350
            for i in result["order"]:
                arrival = result["arrival"].get(i, 0)
                creature = self.creatures[i]
                draw_text(self.screen, f"{creature['icon']} den luc {arrival:.1f}s / timer {creature['timer']}s", 19, COLOR_WHITE, (rect.x + 55, y))
                y += 25
        else:
            draw_text(self.screen, "Trang thai: KHONG AN TOAN", 22, COLOR_RED, (rect.x + 55, rect.y + 145), bold=True)
            draw_text(self.screen, result["reason"], 22, COLOR_WHITE, (rect.x + 55, rect.y + 185))
        draw_text(self.screen, "Nhan ESC hoac X de dong", 19, COLOR_GOLD, (rect.centerx, rect.bottom - 35), center=True)
