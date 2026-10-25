import pygame
from pathlib import Path
import os


base_path = str(Path(__file__).parent.parent.resolve() / "data/images")


def load_image(image_path):
    img = pygame.image.load(str(base_path + image_path)).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    images = []
    for image_name in sorted(os.listdir(base_path + path)):
        images.append(load_image(path + "/" + image_name))
    return images

class Animations:
    def __init__(self, images , image_dur = 5, loop = True):
        self.images = images
        self.image_duration = image_dur
        self.loop = loop
        
        self.frame = 0
        self.done = False

    def copy(self):
        return Animations(self.images, self.image_duration, self.loop)

    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.image_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.image_duration * len(self.images) - 1)
            if self.frame >= self.image_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        return self.images[int(self.frame // self.image_duration)]