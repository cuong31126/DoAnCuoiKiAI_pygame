import pygame

from core.scene_base import SceneBase
from core.ui import Button, assets, blur_surface, draw_panel, draw_text
from settings import COLOR_BG, COLOR_GOLD, COLOR_WHITE, SCREEN_HEIGHT, SCREEN_WIDTH


class MapSelect(SceneBase):
    """Man chon man choi."""

    def play_button_rect(self, card_rect):
        return pygame.Rect(card_rect.x + 60, card_rect.y + 169, 130, 27)

    def on_enter(self):
        # Tao giao dien chon 6 level va anh preview cho tung level
        self.bg = blur_surface(assets.load_image("assets/bg3.png", (SCREEN_WIDTH, SCREEN_HEIGHT), fallback_color=COLOR_BG), scale=0.14, passes=1)
        self.close_button = Button((1130, 16, 120, 38), "DONG", lambda: self.finish("main_menu"), (96, 38, 44), (142, 58, 66), 20)
        self.cards = []
        start_x = 155
        start_y = 150
        gap_x = 80
        gap_y = 55
        data = [
            ("LEVEL 1", "Basic delivery\nBFS DFS UCS", "map1", True, "DELIVERY", "assets/round1.png"),
            ("LEVEL 2", "Multi patient\nA* Greedy WA*", "map2", True, "ROUTING", "assets/round2.png"),
            ("LEVEL 3", "Battery plan\nLocal search", "map3", True, "BATTERY", "assets/round3.png"),
            ("LEVEL 4", "Dynamic halls\nRe-planning", "map4", True, "DYNAMIC", "assets/round4.png"),
            ("LEVEL 5", "Emergency CSP\nDeadlines", "map5", True, "CSP", "assets/round5.png"),
            ("LEVEL 6", "Crisis control\nGame search", "map6", True, "CRISIS", "assets/round6.png"),
        ]
        for i, item in enumerate(data):
            row = i // 3
            col = i % 3
            rect = pygame.Rect(
                start_x + col * (250 + gap_x),
                start_y + row * (200 + gap_y),
                250,
                200,
            )

            title, desc, target, unlocked, icon_text, preview_path = item
            preview_img = assets.load_image(
                preview_path,
                (210, 72),
                fallback_color=(60, 60, 80),
            )

            self.cards.append((rect, title, desc, target, unlocked, icon_text, preview_img))

    def handle_events(self, events):
        # Bat nut dong va nut choi cua tung level
        for event in events:
            if self.close_button.handle_event(event):
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.finish("main_menu")
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, _title, _desc, target, unlocked, _icon_text, _preview_img in self.cards:
                    play_rect = self.play_button_rect(rect)
                    if unlocked and play_rect.collidepoint(event.pos):
                        sound = assets.load_sound("assets/sounds/sfx/click.wav")
                        if sound:
                            sound.play()
                        self.finish(target)

    def update(self, dt):
        pass

    def draw(self):
        # Ve cac card level theo luoi 3x2
        self.screen.blit(self.bg, (0, 0))
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((8, 14, 24, 108))
        self.screen.blit(shade, (0, 0))

        header = pygame.Rect(0, 0, SCREEN_WIDTH, 72)
        pygame.draw.rect(self.screen, (12, 18, 32), header)
        pygame.draw.line(self.screen, (96, 124, 170), (0, 72), (SCREEN_WIDTH, 72), 2)
        draw_text(self.screen, "CHON MAN CHOI", 34, COLOR_GOLD, (35, 18), bold=True)
        self.close_button.draw(self.screen)

        for rect, title, desc, target, unlocked, icon_text, preview_img in self.cards:
            fill = (12, 18, 30) if unlocked else (24, 24, 32)
            border = (96, 124, 170) if unlocked else (102, 102, 114)
            draw_panel(self.screen, rect, fill, border, 228)

            preview_rect = pygame.Rect(rect.x + 20, rect.y + 13, 210, 72)
            self.screen.blit(preview_img, preview_rect.topleft)
            tint = pygame.Surface(preview_rect.size, pygame.SRCALPHA)
            tint.fill((8, 14, 24, 72))
            self.screen.blit(tint, preview_rect)
            pygame.draw.rect(self.screen, COLOR_WHITE, preview_rect, 2, border_radius=6)

            color = COLOR_GOLD if unlocked else (145, 150, 160)
            draw_text(self.screen, icon_text, 17, color, (rect.centerx, rect.y + 96), center=True, bold=True)
            draw_text(self.screen, title, 24, color, (rect.centerx, rect.y + 119), center=True, bold=True)

            for j, line in enumerate(desc.splitlines()):
                draw_text(
                    self.screen,
                    line,
                    15,
                    COLOR_WHITE if unlocked else (150, 150, 160),
                    (rect.centerx, rect.y + 134 + j * 17),
                    center=True,
                )

            if unlocked:
                play_rect = self.play_button_rect(rect)
                pygame.draw.rect(self.screen, (38, 98, 82), play_rect, border_radius=7)
                pygame.draw.rect(self.screen, COLOR_WHITE, play_rect, 2, border_radius=7)
                draw_text(self.screen, "CHOI", 20, COLOR_WHITE, play_rect.center, center=True, bold=True)
            else:
                draw_text(self.screen, "LOCKED", 22, (150, 150, 160), (rect.centerx, rect.y + 155), center=True, bold=True)
