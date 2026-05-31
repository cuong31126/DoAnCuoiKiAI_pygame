import pygame

from core.scene_base import SceneBase
from core.ui import Button, assets, draw_panel, draw_text
from settings import COLOR_BG, COLOR_GOLD, COLOR_WHITE, SCREEN_HEIGHT, SCREEN_WIDTH


class MapSelect(SceneBase):
    """Man chon man choi."""

    def play_button_rect(self, card_rect):
        return pygame.Rect(card_rect.x + 60, card_rect.y + 150, 130, 36)

    def on_enter(self):
        self.bg = assets.load_image("assets/menu/bg2.png", (SCREEN_WIDTH, SCREEN_HEIGHT), fallback_color=COLOR_BG)
        self.close_button = Button((1130, 16, 120, 38), "DONG", lambda: self.finish("main_menu"), (120, 45, 55), (170, 65, 75), 20)
        self.cards = []
        start_x = 155
        start_y = 150
        gap_x = 80
        gap_y = 55
        data = [
            ("MAN 1", "Khu rung\nhon mang", "map1", True, "RUNG","assets/select/man1.png"),
            ("MAN 2", "Tram cuu\nho ma thu", "map2", True, "MA THU","assets/select/man2.png"),
            ("MAN 3", "(Khoa)", None, False, "KHOA","assets/select/man3.png"),
            ("MAN 4", "(Khoa)", None, False, "KHOA","assets/select/man4.png"),
            ("MAN 5", "(Khoa)", None, False, "KHOA","assets/select/man5.png"),
            ("MAN 6", "(Khoa)", None, False, "KHOA","assets/select/man6.png"),
        ]
        for i, item in enumerate(data):
            row = i // 3
            col = i % 3
            rect = pygame.Rect(
                start_x + col * (250 + gap_x),
                start_y + row * (200 + gap_y),
                250,
                200
            )

            title, desc, target, unlocked, icon_text, preview_path = item
            preview_img = assets.load_image(
                preview_path,
                (210, 80),
                fallback_color=(60, 60, 80)
            )

            self.cards.append((rect, title, desc, target, unlocked, icon_text, preview_img))

    def handle_events(self, events):
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
        self.screen.blit(self.bg, (0, 0))
        header = pygame.Rect(0, 0, SCREEN_WIDTH, 72)
        pygame.draw.rect(self.screen, (25, 25, 50), header)
        pygame.draw.line(self.screen, (180, 180, 210), (0, 72), (SCREEN_WIDTH, 72), 2)
        draw_text(self.screen, "CHON MAN CHOI", 34, COLOR_GOLD, (35, 18), bold=True)
        self.close_button.draw(self.screen)

        for rect, title, desc, target, unlocked, icon_text, preview_img in self.cards:
            fill = (24, 28, 48) if unlocked else (40, 40, 48)
            border = COLOR_WHITE if unlocked else (105, 105, 115)
            draw_panel(self.screen, rect, fill, border, 235)

            # Ảnh preview nhỏ
            preview_rect = pygame.Rect(rect.x + 20, rect.y + 15, 210, 80)
            self.screen.blit(preview_img, preview_rect.topleft)
            pygame.draw.rect(self.screen, COLOR_WHITE, preview_rect, 2, border_radius=6)

            color = COLOR_GOLD if unlocked else (145, 145, 150)
            draw_text(self.screen, icon_text, 18, color, (rect.centerx, rect.y + 105), center=True, bold=True)
            draw_text(self.screen, title, 26, color, (rect.centerx, rect.y + 130), center=True, bold=True)

            for j, line in enumerate(desc.splitlines()):
                draw_text(
                    self.screen,
                    line,
                    19,
                    COLOR_WHITE if unlocked else (150, 150, 160),
                    (rect.centerx, rect.y + 158 + j * 20),
                    center=True
                )

            if unlocked:
                play_rect = self.play_button_rect(rect)
                pygame.draw.rect(self.screen, (55, 120, 90), play_rect, border_radius=7)
                pygame.draw.rect(self.screen, COLOR_WHITE, play_rect, 2, border_radius=7)
                draw_text(self.screen, "CHOI", 20, COLOR_WHITE, play_rect.center, center=True, bold=True)
            else:
                draw_text(self.screen, "LOCKED", 22, (150, 150, 160), (rect.centerx, rect.y + 155), center=True, bold=True)
