import pygame
from pathlib import Path
import os 
from os.path import join
from pytmx.util_pygame import load_pygame

WIDTH, HEIGHT = 1920, 1080

# Tile scaling:
# Reduced by 50% from 0.5 to 0.25 (TILE_SIZE is now 128px)
ORIGINAL_TILE_SIZE = 512
TILE_SCALE = 0.25
TILE_SIZE = int(ORIGINAL_TILE_SIZE * TILE_SCALE)

# Player scaling:
# Reduced by 50%
PLAYER_SCALE = 0.60

FRAMERATE = 60
PLAYER_SIZE = (64*4, 96*4)
CURRENT_DIR = Path(__file__).parent.resolve()

