import os
import sys

import pygame

from core.ui import assets, set_ui_mouse_pos
from settings import COLOR_BG, FPS, MUSIC_VOLUME, SCREEN_HEIGHT, SCREEN_WIDTH


class Game:
    """Quan ly cua so, vong lap chinh va chuyen scene."""

    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass

        pygame.display.set_caption("AI Quest: Labyrinth of Algorithms")
        self.window = pygame.display.set_mode(self.compute_window_size(), pygame.RESIZABLE)
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
        self.viewport = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.update_viewport()
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = None
        self.change_scene("main_menu")

    def compute_window_size(self):
        info = pygame.display.Info()
        max_w = max(960, info.current_w - 80)
        max_h = max(540, info.current_h - 120)
        scale = min(max_w / SCREEN_WIDTH, max_h / SCREEN_HEIGHT, 1.0)
        return (max(960, int(SCREEN_WIDTH * scale)), max(540, int(SCREEN_HEIGHT * scale)))

    def update_viewport(self):
        win_w, win_h = self.window.get_size()
        scale = min(win_w / SCREEN_WIDTH, win_h / SCREEN_HEIGHT)
        render_w = max(1, int(SCREEN_WIDTH * scale))
        render_h = max(1, int(SCREEN_HEIGHT * scale))
        offset_x = (win_w - render_w) // 2
        offset_y = (win_h - render_h) // 2
        self.viewport = pygame.Rect(offset_x, offset_y, render_w, render_h)

    def map_mouse_pos(self, pos):
        if not self.viewport.collidepoint(pos):
            return (-9999, -9999)
        x, y = pos
        rel_x = (x - self.viewport.x) / self.viewport.width
        rel_y = (y - self.viewport.y) / self.viewport.height
        return (int(rel_x * SCREEN_WIDTH), int(rel_y * SCREEN_HEIGHT))

    def normalize_events(self, events):
        mapped = []
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                self.update_viewport()
                continue
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                event_dict = event.dict.copy()
                event_dict["pos"] = self.map_mouse_pos(event.pos)
                mapped.append(pygame.event.Event(event.type, event_dict))
            else:
                mapped.append(event)
        return mapped

    def change_scene(self, scene_name):
        if self.scene:
            self.scene.on_exit()

        if scene_name == "main_menu":
            from scenes.main_menu import MainMenu

            self.scene = MainMenu(self.screen, self)
        elif scene_name == "map_select":
            from scenes.map_select import MapSelect

            self.scene = MapSelect(self.screen, self)
        elif scene_name == "map1":
            from maps.map1_forest.map1_scene import Map1Scene

            self.scene = Map1Scene(self.screen, self)
        elif scene_name == "map2":
            from maps.map2_rescue.map2_scene import Map2Scene

            self.scene = Map2Scene(self.screen, self)
        else:
            raise ValueError(f"Scene khong ton tai: {scene_name}")

        self.scene.on_enter()

    def play_music(self, path, loops=-1, volume=MUSIC_VOLUME):
        if not pygame.mixer.get_init():
            return
        resolved = assets.resolve(path)
        if not os.path.exists(resolved):
            return
        try:
            pygame.mixer.music.load(resolved)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)
        except pygame.error:
            pass

    def stop_music(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            raw_events = pygame.event.get()
            for event in raw_events:
                if event.type == pygame.QUIT:
                    self.running = False
            events = self.normalize_events(raw_events)
            set_ui_mouse_pos(self.map_mouse_pos(pygame.mouse.get_pos()))

            if self.scene:
                self.scene.handle_events(events)
                self.scene.update(dt)
                self.screen.fill(COLOR_BG)
                self.scene.draw()
                if self.scene.finished:
                    next_scene = self.scene.next_scene
                    self.scene.finished = False
                    self.change_scene(next_scene)

            self.window.fill((8, 8, 12))
            scaled = pygame.transform.smoothscale(self.screen, self.viewport.size)
            self.window.blit(scaled, self.viewport.topleft)
            pygame.display.flip()

        if self.scene:
            self.scene.on_exit()
        pygame.quit()
        sys.exit()
