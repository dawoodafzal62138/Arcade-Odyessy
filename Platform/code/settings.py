from pathlib import Path
import pygame
from os import walk
from os.path import join
from pytmx.util_pygame import load_pygame
import os



CURRENT_PATH = Path(__file__).parent.parent.resolve()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280,720
TILE_SIZE = 64 
FRAMERATE = 60
BG_COLOR = '#fcdfcd'
