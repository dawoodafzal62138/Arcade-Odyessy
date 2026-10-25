import pygame
import os
from os import walk
from pathlib import Path
from random import randint, choice
from pytmx.util_pygame import load_pygame

BASE_DIR = Path(__file__).resolve().parent.parent

def join(*args):
    if args and os.path.isabs(args[0]):
        return os.path.join(*args)
    return str(BASE_DIR.joinpath(*args))

WIDTH, HEIGHT = 1280, 720
TILE_SIZE = 64