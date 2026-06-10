"""Cau hinh chung cho AI Hospital Dispatcher."""

import os

# Kich thuoc cua so game
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Grid
TILE_SIZE = 40
GRID_COLS = 20
GRID_ROWS = 15

# Vi tri grid tren man hinh
GRID_OFFSET_X = 30
GRID_OFFSET_Y = 80

# FPS
FPS = 60

# Mau sac
COLOR_BG = (15, 15, 35)
COLOR_TOP_BAR = (25, 25, 50)
COLOR_BOTTOM_BAR = (25, 25, 50)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GOLD = (255, 215, 0)
COLOR_RED = (255, 50, 50)
COLOR_GREEN = (50, 255, 50)
COLOR_BLUE = (50, 50, 255)

# Toc do
HERO_SPEED = 0.22
VISUALIZE_SPEED = 0.03
TEXT_SPEED = 30

# Am luong
MUSIC_VOLUME = 0.05
SFX_VOLUME = 0.22

# Gioi han DFS
DFS_MAX_DEPTH = 80

# Duong dan goc project va asset chuan
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = "assets"

# Kich thuoc ve sprite. Hero x4 co khung 2:1 nen width se duoc tinh = HERO_DRAW_SIZE * 2.
HERO_DRAW_SIZE = 64
ENEMY_DRAW_SIZE = 60
NARRATOR_WIDTH = 220
NARRATOR_HEIGHT = 300
