"""Torcia del giocatore: crea una zona illuminata attorno al cursore e oscura il resto dello schermo."""

import pygame

class Flashlight:
    """Gestisce stato on/off e rendering dell'effetto luce con overlay trasparente."""
    def __init__(self, width, height, radius=100, alpha=200):
        """Prepara l'overlay per tutto lo schermo e salva i parametri del cono di luce."""
        self.width = width
        self.height = height
        self.radius = radius
        self.alpha = alpha
        self.on = True

        # Overlay con alpha per-pixel
        self.overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def toggle(self):
        """Attiva o disattiva la torcia."""
        self.on = not self.on

    def draw(self, screen):
        """Disegna il velo scuro lasciando visibile solo l'area illuminata intorno al mouse."""
        if not self.on:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Riempie overlay con nero semi-trasparente
        self.overlay.fill((0, 0, 0, self.alpha))

        # "Buco" trasparente nella posizione del mouse
        pygame.draw.circle(self.overlay, (0, 0, 0, 0), (mouse_x, mouse_y), self.radius)

        # Disegna overlay sopra il background
        screen.blit(self.overlay, (0, 0))

