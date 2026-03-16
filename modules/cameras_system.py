import pygame

from modules.ui_manager import add_graphic_element


class VideoCamere:
    def __init__(self, width, height, label_font, title_font):
        self.width = width
        self.height = height
        self.label_font = label_font
        self.title_font = title_font

        self.trigger_rect = pygame.Rect(24, self.height - 96, 220, 64)
        self.panel_rect = pygame.Rect(120, 70, self.width - 240, self.height - 140)
        self.is_open = False

    def set_trigger_rect(self, x, y, w, h):
        self.trigger_rect = pygame.Rect(x, y, w, h)
        return self.trigger_rect

    def set_panel_rect(self, x, y, w, h):
        self.panel_rect = pygame.Rect(x, y, w, h)
        return self.panel_rect

    def update_hover(self, mouse_pos):
        self.is_open = self.trigger_rect.collidepoint(mouse_pos)

    def queue_trigger(self):
        color = (64, 186, 227, 0.2) if self.is_open else (64, 186, 227, 0.2)
        add_graphic_element(
            rect=self.trigger_rect,
            text="CAM",
            color=color,
            font=self.label_font,
            text_color=(115, 216, 250, 0.5),
            border_radius=12,
            border_color=(35, 35, 35, 1),
            border_width=2,
            text_angle=90
        )

    def draw_overlay(self, surface):
        if not self.is_open:
            return

        shade = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 125))
        surface.blit(shade, (0, 0))

        pygame.draw.rect(surface, (30, 35, 40), self.panel_rect, border_radius=18)
        pygame.draw.rect(surface, (90, 105, 120), self.panel_rect, width=3, border_radius=18)

        title = self.title_font.render("SISTEMA CAMERE", True, (235, 235, 235))
        subtitle = self.label_font.render("Passa fuori dal pulsante per chiudere", True, (180, 190, 200))
        surface.blit(title, title.get_rect(center=(self.width // 2, self.panel_rect.top + 54)))
        surface.blit(subtitle, subtitle.get_rect(center=(self.width // 2, self.panel_rect.top + 98)))