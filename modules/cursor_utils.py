"""Utility per selezione e gestione del cursore personalizzato."""

import os


def get_cursor_path_for_size(size):
    """Restituisce cursor path for size."""
    return os.path.join("assets", "images", f"cursor{int(size)}.png")


