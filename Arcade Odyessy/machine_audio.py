"""Distance-controlled music previews for overworld arcade cabinets."""
import math
import pygame
from settigns import CURRENT_DIR


class MachineAudio:
    RADIUS = 650
    MAX_VOLUME = 0.08

    def __init__(self):
        self.tracks = {}
        self.volumes = {}
        self.failed = set()
        self.enabled = pygame.mixer.get_init() is not None
        if self.enabled:
            pygame.mixer.set_num_channels(max(16, pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(8)
        self.channels = {}

    def track_path(self, name):
        root = CURRENT_DIR.parent
        paths = (
            ('flappy', 'Flappy-Bird-Game-main/resourse_flappy/music/bgm_mario.mp3'),
            ('space', 'space shooter/audio/game_music.wav'),
            ('ninja', 'ninja_game/data/music.wav'),
            ('vampire', 'Vampire survivor/audio/music.wav'),
            ('platform', 'Platform/audio/music.wav'),
        )
        for keyword, path in paths:
            if keyword in name.lower():
                return root / path
        # These games have no soundtrack of their own; use the arcade theme.
        return root / 'Pixel-Runner-game-main/resources/audio/music.wav'

    def update(self, dt, player, machines):
        if not self.enabled:
            return
        nearest = None
        distance = self.RADIUS
        if player is not None and player.alive():
            for machine in machines:
                current = pygame.Vector2(player.rect.center).distance_to(machine.rect.center)
                if current < distance:
                    nearest, distance = machine, current
        blend = 1 - math.exp(-3 * max(0, min(dt, 0.1)))
        for machine in machines:
            target = 0.0
            if machine is nearest:
                proximity = 1 - distance / self.RADIUS
                proximity = proximity * proximity * (3 - 2 * proximity)
                target = self.MAX_VOLUME * proximity
            volume = self.volumes.get(machine, 0.0)
            volume += (target - volume) * blend
            self.volumes[machine] = volume
            if target > 0 and machine not in self.channels and machine not in self.failed:
                path = self.track_path(machine.name)
                try:
                    if path not in self.tracks:
                        self.tracks[path] = pygame.mixer.Sound(path)
                    channel = pygame.mixer.Channel(len(self.channels))
                    self.channels[machine] = channel
                except (pygame.error, FileNotFoundError):
                    self.failed.add(machine)
            channel = self.channels.get(machine)
            if channel is not None:
                channel.set_volume(volume)
                if target > 0 and not channel.get_busy():
                    channel.play(self.tracks[self.track_path(machine.name)], loops=-1)
                elif target == 0 and volume < 0.001:
                    channel.stop()
                    self.volumes[machine] = 0.0

    def stop(self):
        for channel in self.channels.values():
            channel.stop()
        self.volumes.clear()
