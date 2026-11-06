
from settings import * 

def import_image(path, alpha=True):
    return pygame.image.load(path).convert_alpha() if alpha else pygame.image.load(path).convert()


def import_folder(path):
    
    frames = []
    for image_name in sorted(os.listdir(path)):
        frames.append(pygame.image.load(path + "/" + image_name).convert_alpha())
    return frames

