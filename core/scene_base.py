from abc import ABC

import pygame

from settings import (
    COLOR_BOTTOM_BAR,
    COLOR_GOLD,
    COLOR_TOP_BAR,
    COLOR_WHITE,
    GRID_OFFSET_X,
    GRID_OFFSET_Y,
    HERO_SPEED,
    NARRATOR_HEIGHT,
    NARRATOR_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEXT_SPEED,
    TILE_SIZE,
)


class SceneBase(ABC):
    """Lop co so cho moi man hinh trong game."""

    def __init__(self, screen, game_ref):
        self.screen = screen
        self.game = game_ref
        self.finished = False
        self.next_scene = None

    def on_enter(self):
        """Ham goi khi scene bat dau."""

    def on_exit(self):
        """Ham goi khi scene ket thuc."""

    def handle_events(self, events):
        """Xu ly danh sach su kien pygame."""

    def update(self, dt):
        """Cap nhat logic theo dt tinh bang giay."""

    def draw(self):
        """Ve scene len screen."""

    def finish(self, next_scene):
        """Bao cho game doi sang scene tiep theo."""
        self.finished = True
        self.next_scene = next_scene


class GridSceneBase(SceneBase):
    """Helper chung cho cac scene dung grid tile."""

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
        import pygame

        return pygame.Rect(SCREEN_WIDTH - 170, SCREEN_HEIGHT - 58, 138, 36)

    def ask_menu(self):
        from core.ui import ConfirmDialog

        self.confirm = ConfirmDialog("Ve menu chinh?", lambda: self.finish("main_menu"))


class BaseMapScene(GridSceneBase):
    """Base scene cho cac map co intro, hero, top bar va bottom bar giong nhau."""

    title = ""
    intro_speaker = "Nguoi dan chuyen"
    intro_title_size = 40
    intro_text_size = 22
    intro_line_gap = 30
    intro_max_lines = 7
    hero_path_attr = "hero_path"
    hero_index_attr = "hero_index"

    def skip_intro(self):
        self.state = "READY"
        self.intro_line_index = len(self.story_script) - 1
        self.intro_char_count = float(len(self.story_script[-1]))

    def handle_intro_input(self):
        from core.ui import assets

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

    def current_intro_lines(self, max_lines=None):
        from core.ui import wrap_text

        limit = max_lines or self.intro_max_lines
        current = self.story_script[self.intro_line_index][: int(self.intro_char_count)]
        lines = wrap_text(current, 24, 900) if current else [""]
        return lines[:limit]

    def top_menu_rect(self):
        return pygame.Rect(1200, 12, 60, 36)

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
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and getattr(self, "analysis_close_rect", None)
                    and self.analysis_close_rect.collidepoint(event.pos)
                ):
                    self.state = "READY"
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.top_menu_rect().collidepoint(event.pos):
                    self.ask_menu()
                    return

            for button in self.buttons:
                if button.handle_event(event):
                    break

    def update_intro(self, dt):
        current_line = self.story_script[self.intro_line_index]
        self.intro_char_count = min(len(current_line), self.intro_char_count + TEXT_SPEED * dt)

    def update_hero_animations(self, dt):
        for attr in ("hero_idle", "hero_run", "hero_jump", "hero_attack"):
            anim = getattr(self, attr, None)
            if anim:
                anim.update(dt)

    def set_hero_direction(self, current, nxt):
        dr = nxt[0] - current[0]
        dc = nxt[1] - current[1]
        self.hero_mode = "jump" if dr < 0 else "run"
        if dc < 0:
            self.hero_flip = True
        elif dc > 0:
            self.hero_flip = False

    def update_hero_move(self, dt):
        path = getattr(self, self.hero_path_attr)
        if not path:
            self.on_empty_hero_path()
            return

        self.before_hero_step()
        index = getattr(self, self.hero_index_attr)
        if index >= len(path) - 1:
            self.on_hero_route_finished()
            return

        start_node = path[index]
        end_node = path[index + 1]
        self.set_hero_direction(start_node, end_node)

        self.move_timer += dt
        progress = min(1.0, self.move_timer / HERO_SPEED)
        start_px = self.grid_to_pixel(start_node)
        end_px = self.grid_to_pixel(end_node)
        x = start_px[0] + (end_px[0] - start_px[0]) * progress
        y = start_px[1] + (end_px[1] - start_px[1]) * progress
        self.hero_pixel = (x, y)

        if progress >= 1.0:
            index += 1
            setattr(self, self.hero_index_attr, index)
            self.move_timer = 0.0
            self.hero_grid = path[index]
            self.on_hero_reached_cell()

    def on_empty_hero_path(self):
        self.state = "READY"

    def before_hero_step(self):
        pass

    def on_hero_route_finished(self):
        self.hero_mode = "idle"

    def on_hero_reached_cell(self):
        pass

    def draw(self):
        if self.state == "INTRO":
            self.draw_intro()
            return
        self.screen.blit(self.bg_game, (0, 0))
        self.draw_top_bar()
        self.draw_grid()
        self.draw_info_panel()
        self.draw_bottom_bar()
        self.draw_scene_overlays()
        if self.state == "ANALYSIS":
            self.draw_analysis_overlay()
        if self.confirm and self.confirm.active:
            self.confirm.draw(self.screen)

    def draw_intro(self):
        from core.ui import draw_panel, draw_text

        self.screen.blit(self.bg_intro, (0, 0))
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 95))
        self.screen.blit(shade, (0, 0))
        draw_text(
            self.screen,
            self.title,
            self.intro_title_size,
            COLOR_GOLD,
            (SCREEN_WIDTH // 2, 86),
            center=True,
            bold=True,
        )

        portrait_rect = pygame.Rect(18, SCREEN_HEIGHT - NARRATOR_HEIGHT - 18, NARRATOR_WIDTH, NARRATOR_HEIGHT)
        box_rect = pygame.Rect(235, SCREEN_HEIGHT - 260, 1015, 220)
        draw_panel(self.screen, portrait_rect, (25, 24, 45), COLOR_WHITE, 238)
        portrait_pos = self.narrator.get_rect(midbottom=(portrait_rect.centerx, portrait_rect.bottom - 6))
        self.screen.blit(self.narrator, portrait_pos)

        draw_panel(self.screen, box_rect, (18, 20, 40), COLOR_WHITE, 235)
        draw_text(self.screen, self.intro_speaker, 24, COLOR_GOLD, (box_rect.x + 28, box_rect.y + 18), bold=True)

        y = box_rect.y + 56
        for line in self.current_intro_lines():
            if y + self.intro_line_gap > box_rect.bottom - 44:
                break
            draw_text(self.screen, line, self.intro_text_size, COLOR_WHITE, (box_rect.x + 28, y))
            y += self.intro_line_gap

        draw_text(self.screen, "ENTER: tiep tuc", 20, COLOR_GOLD, (box_rect.right - 170, box_rect.bottom - 34), bold=True)
        skip_rect = self.intro_skip_rect()
        pygame.draw.rect(self.screen, (130, 45, 55), skip_rect, border_radius=7)
        pygame.draw.rect(self.screen, COLOR_WHITE, skip_rect, 2, border_radius=7)
        draw_text(self.screen, "BO QUA", 17, COLOR_WHITE, skip_rect.center, center=True, bold=True)

    def draw_top_bar(self):
        from core.ui import draw_text, format_time

        pygame.draw.rect(self.screen, COLOR_TOP_BAR, (0, 0, SCREEN_WIDTH, 60))
        pygame.draw.line(self.screen, (200, 200, 230), (0, 60), (SCREEN_WIDTH, 60), 1)
        draw_text(self.screen, self.title, 28, COLOR_WHITE, (30, 15), bold=True)
        draw_text(self.screen, format_time(self.elapsed), 24, COLOR_WHITE, (1090, 17), bold=True)
        menu_rect = self.top_menu_rect()
        pygame.draw.rect(self.screen, (130, 45, 55), menu_rect, border_radius=7)
        pygame.draw.rect(self.screen, COLOR_WHITE, menu_rect, 2, border_radius=7)
        draw_text(self.screen, "MENU", 16, COLOR_WHITE, menu_rect.center, center=True, bold=True)

    def draw_bottom_bar(self):
        pygame.draw.rect(self.screen, COLOR_BOTTOM_BAR, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        for button in self.buttons:
            button.draw(self.screen)

    def draw_hero(self):
        if self.hero_mode == "jump":
            anim = self.hero_jump
        elif self.hero_mode == "run":
            anim = self.hero_run
        elif self.hero_mode == "attack" and hasattr(self, "hero_attack"):
            anim = self.hero_attack
        else:
            anim = self.hero_idle
        anim.draw(self.screen, self.sprite_draw_pos(self.hero_pixel, anim.size), flip_x=self.hero_flip)

    def draw_scene_overlays(self):
        pass
