import os


def get_cursor_path_for_size(size):
    return os.path.join("assets", "images", f"cursor{int(size)}.png")
