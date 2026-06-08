import pygame

from core.scene_base import SceneBase
from core.ui import Button, assets, draw_glow_text, draw_text
from settings import COLOR_BG, COLOR_GOLD, COLOR_WHITE, SCREEN_HEIGHT, SCREEN_WIDTH


class MainMenu(SceneBase):
    """Man hinh bat dau cua game."""

    def on_enter(self):
        self.bg = assets.load_image("assets/menu/menu_bg.png", (SCREEN_WIDTH, SCREEN_HEIGHT), fallback_color=COLOR_BG)
        self.logo = assets.load_image("assets/menu/logo2.png", (190, 140), fallback_color=(50, 50, 90))
        self.buttons = [
            Button((540, 300, 200, 50), "BAT DAU", lambda: self.finish("map1"), (60, 95, 160), (90, 135, 220), 24, "assets/ui/button.png"),
            Button((540, 370, 200, 50), "CHON MAN", lambda: self.finish("map_select"), (60, 95, 160), (90, 135, 220), 23, "assets/ui/button.png"),
            Button((540, 440, 200, 50), "THOAT", self.game.quit, (120, 45, 55), (170, 65, 75), 24, "assets/ui/button.png"),
        ]
        self.game.play_music("assets/sounds/music/menu_theme.mp3")

    def on_exit(self):
        # Nhac se duoc scene tiep theo thay bang nhac moi neu can.
        pass

    def handle_events(self, events):
        for event in events:
            for button in self.buttons:
                if button.handle_event(event):
                    break

    def update(self, dt):
        pass

    def draw(self):
        self.screen.blit(self.bg, (0, 0))
        logo_rect = self.logo.get_rect(center=(SCREEN_WIDTH // 2, 105))
        self.screen.blit(self.logo, logo_rect)
        draw_glow_text(self.screen, "AI HOSPITAL", 66, (SCREEN_WIDTH // 2, 185), COLOR_GOLD)
        draw_text(self.screen, "DISPATCHER", 34, COLOR_WHITE, (SCREEN_WIDTH // 2, 240), center=True, alpha=220)
        for button in self.buttons:
            button.draw(self.screen)
        draw_text(
            self.screen,
            "Choose an AI algorithm and watch the medical robot dispatch tasks.",
            24,
            COLOR_WHITE,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 105),
            center=True,
            alpha=220,
        )
