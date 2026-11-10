"""Quiet overworld music, ducked beneath nearby arcade previews."""
import math
import pygame
from settigns import CURRENT_DIR


class AmbientMusic:
    def __init__(self):
        self.path = CURRENT_DIR / 'resources' / 'audio' / 'reverie.mp3'
        self.playing = False
        self.volume = 0.0
        self.enabled = pygame.mixer.get_init() is not None and self.path.exists()

    def update(self, dt, machine_volume=0.0):
        if not self.enabled:
            return
        if not self.playing:
            pygame.mixer.music.load(str(self.path))
            pygame.mixer.music.set_volume(0)
            pygame.mixer.music.play(-1)
            self.playing = True
        # Stay subtle, leaving room for footsteps and cabinet music.
        proximity = min(1.0, max(0.0, machine_volume / 0.08))
        target = 0.12 * (1 - 0.75 * proximity)
        self.volume += (target - self.volume) * (1 - math.exp(-2 * min(max(dt, 0), 0.1)))
        pygame.mixer.music.set_volume(self.volume)

    def stop(self):
        if self.playing:
            pygame.mixer.music.stop()
            self.playing = False
        self.volume = 0.0

