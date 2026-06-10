import pygame

from core.scene_base import SceneBase
from core.ui import Button, assets, blur_surface, draw_panel, draw_text
from settings import COLOR_BG, COLOR_GOLD, COLOR_WHITE, SCREEN_HEIGHT, SCREEN_WIDTH


class MainMenu(SceneBase):
    """Man hinh bat dau cua game."""

    def on_enter(self):
        # Tai anh nen, logo va nut chinh cho man hinh dau
        self.bg = blur_surface(assets.load_image("assets/bg3.png", (SCREEN_WIDTH, SCREEN_HEIGHT), fallback_color=COLOR_BG), scale=0.2, passes=1)
        self.doctor = self.build_doctor_cutout("assets/lonsoda.jpg", (260, 260))
        self.buttons = [
            Button((538, 330, 204, 52), "BAT DAU", lambda: self.finish("map1"), (34, 53, 82), (58, 86, 128), 24),
            Button((538, 398, 204, 52), "CHON MAN", lambda: self.finish("map_select"), (34, 53, 82), (58, 86, 128), 23),
            Button((538, 466, 204, 52), "THOAT", self.game.quit, (102, 44, 50), (151, 63, 72), 24),
        ]
        self.game.play_music("assets/sounds/music/menu_theme.mp3")

    def on_exit(self):
        # Nhac se duoc scene tiep theo thay bang nhac moi neu can.
        pass

    def handle_events(self, events):
        # Xu ly click vao cac nut o menu chinh
        for event in events:
            for button in self.buttons:
                if button.handle_event(event):
                    break

    def update(self, dt):
        pass

    def build_doctor_cutout(self, path, size):
        try:
            from PIL import Image
            import numpy as np

            resolved = assets.resolve(path)
            image = Image.open(resolved).convert("RGBA")
            pixels = np.array(image, dtype=np.float32)
            bg = pixels[0, 0, :3].astype(np.float32)
            rgb = pixels[:, :, :3]
            dist = np.sqrt(((rgb - bg) ** 2).sum(axis=2))
            alpha = np.clip((dist - 18.0) * 18.0, 0, 255).astype(np.uint8)
            pixels[:, :, 3] = alpha
            cutout = Image.fromarray(pixels.astype(np.uint8), "RGBA")
            bbox = cutout.getbbox()
            if bbox:
                pad = 18
                left = max(0, bbox[0] - pad)
                top = max(0, bbox[1] - pad)
                right = min(cutout.width, bbox[2] + pad)
                bottom = min(cutout.height, bbox[3] + pad)
                cutout = cutout.crop((left, top, right, bottom))
            surface = pygame.image.fromstring(cutout.tobytes(), cutout.size, "RGBA").convert_alpha()
            return pygame.transform.smoothscale(surface, size)
        except Exception:
            return assets.load_image(path, size, fallback_color=(60, 60, 80))

    def draw(self):
        # Ve giao dien menu chinh va thong diep mo dau
        self.screen.blit(self.bg, (0, 0))
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((10, 16, 28, 102))
        self.screen.blit(shade, (0, 0))

        center_panel = pygame.Rect(438, 88, 404, 452)
        draw_panel(self.screen, center_panel, (10, 16, 28), (90, 120, 168), 170)

        doctor_rect = self.doctor.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(self.doctor, doctor_rect)
        draw_text(self.screen, "AI HOSPITAL", 60, (0, 0, 0), (SCREEN_WIDTH // 2 + 2, 252), center=True, bold=True, alpha=120)
        draw_text(self.screen, "AI HOSPITAL", 60, COLOR_GOLD, (SCREEN_WIDTH // 2, 250), center=True, bold=True)
        draw_text(self.screen, "DISPATCHER", 30, COLOR_WHITE, (SCREEN_WIDTH // 2, 302), center=True, alpha=210)
        for button in self.buttons:
            button.draw(self.screen)
        draw_text(
            self.screen,
            "Choose an AI algorithm and watch the medical robot dispatch tasks.",
            20,
            COLOR_WHITE,
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 105),
            center=True,
            alpha=180,
        )
