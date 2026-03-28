import os

import pygame


def load_enemy_sprites(folder=None):
    if folder is None:
        folder = os.path.join("assets", "images", "personaggi_cattivi")

    sprites = {}
    if not os.path.isdir(folder):
        return sprites

    valid_ext = {".png", ".jpg", ".jpeg", ".webp", ".jfif"}
    loaded_entries = []
    keyword_to_canonical = {
        "chugginton": "Chugginton",
        "linux": "Linux",
        "luca": "Luca",
        "mcqeen": "McQeen",
    }

    for filename in sorted(os.listdir(folder)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in valid_ext:
            continue

        # Usa il nome file come chiave custom e crea alias canonici quando possibile.
        stem = os.path.splitext(filename)[0]
        custom_name = stem.replace("_", " ").replace("-", " ").strip()

        full_path = os.path.join(folder, filename)
        try:
            surface = pygame.image.load(full_path).convert_alpha()
        except Exception:
            try:
                surface = pygame.image.load(full_path).convert()
            except Exception:
                continue

        if custom_name:
            sprites[custom_name] = surface

        lowered = stem.lower()
        for keyword, canonical in keyword_to_canonical.items():
            if keyword in lowered:
                sprites[canonical] = surface
                break

        loaded_entries.append(surface)

    return sprites
