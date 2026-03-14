import pygame

class Flashlight:
    def __init__(self, width, height, radius=100, alpha=200):
        self.width = width
        self.height = height
        self.radius = radius
        self.alpha = alpha
        self.on = True

        # Overlay con alpha per-pixel
        self.overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def toggle(self):
        self.on = not self.on

    def draw(self, screen):
        if not self.on:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Riempie overlay con nero semi-trasparente
        self.overlay.fill((0, 0, 0, self.alpha))

        # "Buco" trasparente nella posizione del mouse
        pygame.draw.circle(self.overlay, (0, 0, 0, 0), (mouse_x, mouse_y), self.radius)

        # Disegna overlay sopra il background
        screen.blit(self.overlay, (0, 0))