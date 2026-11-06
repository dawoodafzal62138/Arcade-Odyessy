from settigns import *


def import_image(path, alpha=True):
    path_str = str(path)
    return pygame.image.load(path_str).convert_alpha() if alpha else pygame.image.load(path_str).convert()


def import_folder(path, flip=False, color_key=None):
    frames = []
    path_str = str(path)
    for image_name in sorted(os.listdir(path_str)):
        if not image_name.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        image_path = os.path.join(path_str, image_name)
        img = pygame.image.load(image_path).convert_alpha()
        # img = pygame.transform.scale(img , (128,128))
        if flip:
            img = pygame.transform.flip(img, True, False)
            # img = pygame.transform.scale(img , (128,128))
        if color_key is not None:
            img.set_colorkey(color_key)
        frames.append(img)
    return frames
