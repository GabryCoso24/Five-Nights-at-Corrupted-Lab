import pygame

from modules.game import Game


def main():
    pygame.init()
    game = Game(width=1280, height=720)
    game.run()


if __name__ == "__main__":
    main()
