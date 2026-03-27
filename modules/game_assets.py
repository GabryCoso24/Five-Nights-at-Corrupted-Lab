import os

import pygame


def load_enemy_sprites(folder=None):
    if folder is None:
        folder = os.path.join("assets", "images", "personaggi_cattivi")

    sprites = {}
    if not os.path.isdir(folder):
        return sprites

    valid_ext = {".png", ".jpg", ".jpeg", ".webp", ".jfif"}
    for filename in os.listdir(folder):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_ext:
            continue

        key = os.path.splitext(filename)[0].lower()
        if "chugginton" in key:
            name = "Chugginton"
        elif "linux" in key:
            name = "Linux"
        elif "luca" in key:
            name = "Luca"
        else:
            continue

        full_path = os.path.join(folder, filename)
        try:
            sprites[name] = pygame.image.load(full_path).convert_alpha()
        except Exception:
            try:
                sprites[name] = pygame.image.load(full_path).convert()
            except Exception:
                pass

    return sprites
