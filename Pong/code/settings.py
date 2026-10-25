import pygame
from os.path import join

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720 
SIZE = {'paddle': (40,200), 'ball': (30,30)}
POS = {'player': (WINDOW_WIDTH - 50, WINDOW_HEIGHT / 2), 'opponent': (50, WINDOW_HEIGHT / 2)}
SPEED = {'player': 500, 'opponent': 250, 'ball': 150}
COLORS = {
    'paddle1': '#ee322c',
    'paddle1 shadow': '#b12521',
    'paddle2': "#1d20d8",
    'paddle2 shadow': '#b12521',
    'ball': '#ee622c',
    'ball shadow': '#c14f24',
    'bg': '#002633'
}