import os
import sys

import pygame

from modules.game import Game


def main():
    # In PyInstaller --onefile, bundled files are unpacked in _MEIPASS.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        os.chdir(sys._MEIPASS)

    pygame.init()
    game = Game(width=1920, height=1080)
    game.run()


if __name__ == "__main__":
    main()
