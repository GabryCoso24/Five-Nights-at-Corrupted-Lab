"""Caricamento e normalizzazione di sprite e jumpscare, con nomi canonici per i personaggi."""

import os

import pygame


def _canonical_name_from_stem(stem):
    """Riconosce il nome canonico di un personaggio partendo dal nome file dell'asset."""
    keyword_to_canonical = {
        "chugginton": "Chugginton",
        "linux": "Linux",
        "luca": "Luca",
        "mcqeen": "McQeen",
    }
    lowered = stem.lower()
    for keyword, canonical in keyword_to_canonical.items():
        if keyword in lowered:
            return canonical
    return None


def load_enemy_sprites(folder=None):
    """Carica le immagini dei nemici e le espone sia col nome file sia con il nome canonico, quando disponibile."""
    if folder is None:
        folder = os.path.join("assets", "images", "personaggi_cattivi")

    sprites = {}
    if not os.path.isdir(folder):
        return sprites

    valid_ext = {".png", ".jpg", ".jpeg", ".webp", ".jfif"}
    loaded_entries = []
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

        canonical = _canonical_name_from_stem(stem)
        if canonical is not None:
            sprites[canonical] = surface

        loaded_entries.append(surface)

    return sprites


def load_jumpscare_assets(folder=None):
    """Raccoglie video, audio e frame di ogni jumpscare in una struttura pronta per il motore di gioco."""
    if folder is None:
        folder = os.path.join("assets", "jumpscares")

    jumpscares = {}
    if not os.path.isdir(folder):
        return jumpscares

    image_ext = {".png", ".jpg", ".jpeg", ".webp", ".jfif"}
    video_ext = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    audio_ext = {".wav", ".mp3", ".ogg", ".flac"}

    for entry in sorted(os.listdir(folder)):
        anim_folder = os.path.join(folder, entry)
        if not os.path.isdir(anim_folder):
            continue

        custom_name = entry.replace("_", " ").replace("-", " ").strip()
        canonical_name = _canonical_name_from_stem(entry)

        data = {
            "video": None,
            "audio": None,
            "frames": [],
        }

        for filename in sorted(os.listdir(anim_folder)):
            ext = os.path.splitext(filename)[1].lower()
            full_path = os.path.join(anim_folder, filename)

            if ext in video_ext and data["video"] is None:
                data["video"] = full_path
                continue

            if ext in audio_ext and data["audio"] is None:
                data["audio"] = full_path
                continue

            if ext in image_ext:
                try:
                    frame = pygame.image.load(full_path).convert_alpha()
                except Exception:
                    try:
                        frame = pygame.image.load(full_path).convert()
                    except Exception:
                        continue
                data["frames"].append(frame)

        if not data["video"] and not data["audio"] and not data["frames"]:
            continue

        keys = []
        if custom_name:
            keys.append(custom_name)
        if canonical_name:
            keys.append(canonical_name)

        for key in keys:
            jumpscares[key] = {
                "video": data["video"],
                "audio": data["audio"],
                "frames": list(data["frames"]),
            }

    return jumpscares


