import os
import sys
from pathlib import Path
import pygame
from settigns import WIDTH, HEIGHT, CURRENT_DIR

# Modular game displays
from ninja_display import NinjaDisplay
from tiny_titan_display import TinyTitanDisplay
from platform_display import PlatformDisplay
from flappy_bird_display import FlappyBirdDisplay
from pong_display import PongDisplay
from vampire_survivor_display import VampireSurvivorDisplay
from space_shooter_display import SpaceShooterDisplay
from pixel_runner_display import PixelRunnerDisplay




# =========================================================================
# FACTORY: MATCHES EXACT GAME FOLDER NAMES
# =========================================================================
def get_display(game_name):
    """
    Returns the appropriate game display matching the folder names:
    - 'ninja_game' -> NinjaDisplay (ninja_display.py)
    - 'Tiny titan' -> TinyTitanDisplay (tiny_titan_display.py)
    - 'Platform' -> PlatformDisplay (platform_display.py)
    - 'Flappy-Bird-Game-main' -> FlappyBirdDisplay (flappy_bird_display.py)
    - 'Pong' -> PongDisplay (pong_display.py)
    - 'Vampire survivor' -> VampireSurvivorDisplay (vampire_survivor_display.py)
    - 'Pixel-Runner-game-main'
    - 'space shooter'
    """
    clean = (game_name or "").strip().lower()

    if "ninja" in clean:
        return NinjaDisplay(game_name)
    elif "titan" in clean or "tiny" in clean:
        return TinyTitanDisplay(game_name)
    elif "platform" in clean:
        return PlatformDisplay(game_name)
    elif "flappy" in clean:
        return FlappyBirdDisplay(game_name)
    elif "pong" in clean:
        return PongDisplay(game_name)
    elif "vampire" in clean:
        return VampireSurvivorDisplay(game_name)
    elif "pixel" in clean or "runner" in clean:
        return PixelRunnerDisplay(game_name)
    elif "space" in clean or ("shooter" in clean and "vampire" not in clean):
        return SpaceShooterDisplay(game_name)
    else:
        return NinjaDisplay(game_name)
