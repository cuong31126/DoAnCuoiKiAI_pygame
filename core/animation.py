import os

import pygame

from settings import TILE_SIZE


class GIFAnimation:
    """Doc gif hoac thu muc frame png de tao animation loop."""

    def __init__(self, path=None, size=(TILE_SIZE, TILE_SIZE), frame_time=0.12, fallback_color=(255, 0, 255), alt_paths=None):
        self.size = size
        self.frame_time = frame_time
        self.timer = 0.0
        self.index = 0
        self.frames = []
        paths = [path] if path else []
        if alt_paths:
            paths.extend(alt_paths)

        for candidate in paths:
            self.frames = self._load_candidate(candidate)
            if self.frames:
                break

        if not self.frames:
            surf = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(surf, fallback_color, surf.get_rect(), border_radius=8)
            pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2, border_radius=8)
            self.frames = [surf]

    def _scale(self, image):
        return pygame.transform.scale(image.convert_alpha(), self.size)

    def _load_candidate(self, path):
        if not path or not os.path.exists(path):
            return []

        if os.path.isdir(path):
            files = sorted(
                os.path.join(path, name)
                for name in os.listdir(path)
                if name.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
            )
            return [self._scale(pygame.image.load(file)) for file in files]

        if path.lower().endswith(".gif"):
            frames = self._load_gif_with_pillow(path)
            if frames:
                return frames

        try:
            return [self._scale(pygame.image.load(path))]
        except pygame.error:
            return []

    def _load_gif_with_pillow(self, path):
        try:
            from PIL import Image, ImageSequence
        except ImportError:
            return []

        frames = []
        try:
            image = Image.open(path)
            for frame in ImageSequence.Iterator(image):
                rgba = frame.convert("RGBA")
                raw = rgba.tobytes()
                surf = pygame.image.fromstring(raw, rgba.size, "RGBA")
                frames.append(self._scale(surf))
        except Exception:
            return []
        return frames

    def reset(self):
        self.timer = 0.0
        self.index = 0

    def update(self, dt):
        if len(self.frames) <= 1:
            return
        self.timer += dt
        while self.timer >= self.frame_time:
            self.timer -= self.frame_time
            self.index = (self.index + 1) % len(self.frames)

    def get_frame(self, flip_x=False):
        frame = self.frames[self.index]
        if flip_x:
            return pygame.transform.flip(frame, True, False)
        return frame

    def draw(self, surface, pos, flip_x=False):
        surface.blit(self.get_frame(flip_x=flip_x), pos)
