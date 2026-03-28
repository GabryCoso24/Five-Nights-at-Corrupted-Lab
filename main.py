import pygame

from modules.game import Game


def main():
    pygame.init()
    game = Game(width=1920, height=1080)
    game.run()


if __name__ == "__main__":
    main()
