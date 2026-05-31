import os

import pygame

from settings import COLOR_GOLD, COLOR_WHITE, SCREEN_HEIGHT, SCREEN_WIDTH, SFX_VOLUME


ASSET_ALIASES = {
    "assets/ui/button.png": [
        "assets/FreeMix/FreeMix/ui/theme_mix/button/button.png",
        "assets/FreeMix/FreeMix/ui/theme_mix/button/button_blue.png",
    ],
    "assets/ui/panel.png": [
        "assets/FreeMix/FreeMix/ui/theme_mix/panel_blue.png",
        "assets/FreeMix/FreeMix/ui/theme_mix/panel_exterior.png",
    ],
    "assets/ui/narrator.png": [
        "assets/man1/Heroine base/Sprites/idle/player-idle-1.png",
        "assets/man1/Heroine base/Previews/idle.gif",
        "assets/man1/intro/intro1.jpg",
    ],
    "assets/fonts/fantasy_font.ttf": [
        "assets/FreeMix/FreeMix/ui/font_medium_9px.ttf",
    ],
    "assets/sounds/sfx/click.wav": [
        "assets/FreeMix/FreeMix/sfx/accept.wav",
    ],
    "assets/sounds/sfx/page_flip.wav": [
        "assets/FreeMix/FreeMix/sfx/menu_move.wav",
    ],
    "assets/sounds/sfx/rescue.wav": [
        "assets/FreeMix/FreeMix/sfx/powerup.wav",
    ],
    "assets/sounds/sfx/victory.wav": [
        "assets/FreeMix/FreeMix/sfx/bonus.wav",
    ],
    "assets/sounds/sfx/defeat.wav": [
        "assets/FreeMix/FreeMix/sfx/cancel.wav",
    ],
    "assets/sounds/music/menu_theme.mp3": [
        "assets/FreeMix/FreeMix/music/adventure.ogg",
    ],
    "assets/sounds/music/forest_theme.mp3": [
        "assets/FreeMix/FreeMix/music/tension.ogg",
    ],
    "assets/sounds/music/magical_theme.mp3": [
        "assets/FreeMix/FreeMix/music/majestic.ogg",
    ],
}


class AssetManager:
    """Quan ly asset va fallback de game khong crash khi thieu file."""

    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.fonts = {}

    def resolve(self, path):
        candidates = [path] + ASSET_ALIASES.get(path, [])
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return path

    def load_image(self, path, size=None, alpha=True, fallback_color=(80, 80, 110)):
        key = (path, size, alpha, fallback_color)
        if key in self.images:
            return self.images[key]

        resolved = self.resolve(path)
        image = None
        if os.path.exists(resolved):
            try:
                image = pygame.image.load(resolved)
                image = image.convert_alpha() if alpha else image.convert()
            except pygame.error:
                image = None

        if image is None:
            image = pygame.Surface(size or (80, 40), pygame.SRCALPHA)
            image.fill(fallback_color)
            pygame.draw.rect(image, (255, 255, 255), image.get_rect(), 2)

        if size:
            image = pygame.transform.smoothscale(image, size)

        self.images[key] = image
        return image

    def load_sound(self, path):
        if path in self.sounds:
            return self.sounds[path]
        resolved = self.resolve(path)
        sound = None
        if os.path.exists(resolved) and pygame.mixer.get_init():
            try:
                sound = pygame.mixer.Sound(resolved)
                sound.set_volume(SFX_VOLUME)
            except pygame.error:
                sound = None
        self.sounds[path] = sound
        return sound

    def font(self, size, bold=False):
        key = (size, bold)
        if key in self.fonts:
            return self.fonts[key]

        font_obj = None
        for family in ("Segoe UI", "Tahoma", "Verdana", "Arial"):
            try:
                font_obj = pygame.font.SysFont(family, size, bold=bold)
            except pygame.error:
                font_obj = None
            if font_obj is not None:
                break

        if font_obj is None:
            font_path = self.resolve("assets/fonts/fantasy_font.ttf")
            if os.path.exists(font_path):
                try:
                    font_obj = pygame.font.Font(font_path, size)
                except pygame.error:
                    font_obj = None

        if font_obj is None:
            font_obj = pygame.font.SysFont("arial", size, bold=bold)

        self.fonts[key] = font_obj
        return font_obj


assets = AssetManager()
CURRENT_UI_MOUSE_POS = None


def set_ui_mouse_pos(pos):
    global CURRENT_UI_MOUSE_POS
    CURRENT_UI_MOUSE_POS = pos


def safe_render(font, text, color):
    """Render text va fallback neu font khong ho tro ky tu dac biet."""
    try:
        return font.render(text, True, color)
    except Exception:
        plain = text.encode("ascii", "ignore").decode("ascii") or "?"
        return font.render(plain, True, color)


def draw_text(surface, text, size, color, pos, center=False, bold=False, alpha=255):
    font = assets.font(size, bold)
    img = safe_render(font, text, color)
    if alpha < 255:
        img.set_alpha(alpha)
    rect = img.get_rect()
    rect.center = pos if center else rect.center
    if not center:
        rect.topleft = pos
    surface.blit(img, rect)
    return rect


def draw_glow_text(surface, text, size, pos, color=COLOR_GOLD):
    font = assets.font(size, bold=True)
    for radius, alpha in ((8, 45), (5, 70), (2, 120)):
        glow = safe_render(font, text, color)
        glow.set_alpha(alpha)
        rect = glow.get_rect(center=pos)
        for dx, dy in ((radius, 0), (-radius, 0), (0, radius), (0, -radius)):
            surface.blit(glow, rect.move(dx, dy))
    img = safe_render(font, text, color)
    surface.blit(img, img.get_rect(center=pos))


def draw_panel(surface, rect, fill=(20, 22, 45), border=(210, 210, 240), alpha=230):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((*fill, alpha))
    pygame.draw.rect(panel, border, panel.get_rect(), 2, border_radius=8)
    surface.blit(panel, rect.topleft)


def wrap_text(text, size, max_width, bold=False):
    font = assets.font(size, bold)
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        test = f"{current} {word}"
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_text_block(surface, lines, size, color, pos, line_gap=8, bold=False):
    x, y = pos
    cursor_y = y
    for line in lines:
        draw_text(surface, line, size, color, (x, cursor_y), bold=bold)
        cursor_y += size + line_gap
    return cursor_y


def format_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class Button:
    """Nut bam co hover, anh nen va am click."""

    def __init__(self, rect, text, callback, color=(70, 90, 150), hover_color=(100, 125, 205), text_size=24, image_path=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.text_size = text_size
        self.image_path = image_path
        self.enabled = True

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            sound = assets.load_sound("assets/sounds/sfx/click.wav")
            if sound:
                sound.play()
            if self.callback:
                self.callback()
            return True
        return False

    def draw(self, surface):
        mouse = CURRENT_UI_MOUSE_POS if CURRENT_UI_MOUSE_POS is not None else pygame.mouse.get_pos()
        hovered = self.enabled and self.rect.collidepoint(mouse)
        color = self.hover_color if hovered else self.color
        if not self.enabled:
            color = (70, 70, 80)

        if self.image_path:
            image = assets.load_image(self.image_path, self.rect.size, fallback_color=color)
            surface.blit(image, self.rect)
            tint = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            tint.fill((*color, 70 if hovered else 35))
            surface.blit(tint, self.rect)
        else:
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_WHITE if self.enabled else (130, 130, 140), self.rect, 2, border_radius=8)
        draw_text(surface, self.text, self.text_size, COLOR_WHITE if self.enabled else (160, 160, 170), self.rect.center, center=True, bold=True)


class ConfirmDialog:
    """Hop xac nhan dung cho nut ve menu."""

    def __init__(self, message, on_yes, on_no=None):
        self.message = message
        self.on_yes = on_yes
        self.on_no = on_no
        self.active = True
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        self.rect = pygame.Rect(cx - 230, cy - 120, 460, 240)
        self.yes_button = Button((cx - 160, cy + 45, 130, 44), "DONG Y", self._yes, (130, 40, 50), (180, 60, 70), 20)
        self.no_button = Button((cx + 30, cy + 45, 130, 44), "HUY", self._no, (70, 80, 100), (100, 115, 145), 20)

    def _yes(self):
        self.active = False
        if self.on_yes:
            self.on_yes()

    def _no(self):
        self.active = False
        if self.on_no:
            self.on_no()

    def handle_events(self, events):
        if not self.active:
            return False
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._no()
                return True
            if self.yes_button.handle_event(event) or self.no_button.handle_event(event):
                return True
        return True

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        surface.blit(overlay, (0, 0))
        draw_panel(surface, self.rect, (28, 28, 55), COLOR_WHITE, 245)
        draw_text(surface, "XAC NHAN", 30, COLOR_GOLD, (self.rect.centerx, self.rect.y + 45), center=True, bold=True)
        draw_text(surface, self.message, 22, COLOR_WHITE, (self.rect.centerx, self.rect.y + 100), center=True)
        self.yes_button.draw(surface)
        self.no_button.draw(surface)
