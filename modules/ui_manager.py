import pygame


class UIManager:
    def __init__(self):
        self._queue = []

    def add_rect_text(
        self,
        *,
        rect,
        text,
        color,
        font,
        text_color=(25, 25, 25),
        border_radius=10,
        border_color=(40, 40, 40),
        border_width=2,
        text_angle=0,
    ):
        self._queue.append(
            {
                "type": "rect_text",
                "rect": rect,
                "text": text,
                "color": color,
                "font": font,
                "text_color": text_color,
                "border_radius": border_radius,
                "border_color": border_color,
                "border_width": border_width,
                "text_angle": text_angle,
            }
        )

    def draw(self, surface):
        for item in self._queue:
            if item["type"] != "rect_text":
                continue

            rect = item["rect"]
            if not isinstance(rect, pygame.Rect):
                try:
                    rect = pygame.Rect(rect)
                except Exception:
                    continue
            fill_color = self._normalize_color(item["color"])
            border_color = self._normalize_color(item["border_color"])

            # Draw on an alpha-enabled temp surface so RGBA works reliably.
            rect_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            local_rect = rect_surface.get_rect()
            pygame.draw.rect(rect_surface, fill_color, local_rect, border_radius=item["border_radius"])

            if item["border_width"] > 0:
                pygame.draw.rect(
                    rect_surface,
                    border_color,
                    local_rect,
                    width=item["border_width"],
                    border_radius=item["border_radius"],
                )

            surface.blit(rect_surface, rect.topleft)

            text_color_norm = self._normalize_color(item["text_color"])
            label = item["font"].render(item["text"], True, text_color_norm[:3])
            angle = item.get("text_angle", 0)
            if angle:
                label = pygame.transform.rotate(label, angle)
            # Apply alpha channel of text_color via set_alpha
            text_alpha = text_color_norm[3]
            if text_alpha < 255:
                label.set_alpha(text_alpha)
            label_rect = label.get_rect(center=rect.center)
            surface.blit(label, label_rect)

        self._queue.clear()

    @staticmethod
    def _normalize_color(color):
        if len(color) == 3:
            return (int(color[0]), int(color[1]), int(color[2]), 255)

        if len(color) == 4:
            r, g, b, a = color
            if isinstance(a, float) and 0.0 <= a <= 1.0:
                a = int(a * 255)
            return (int(r), int(g), int(b), max(0, min(255, int(a))))

        return (255, 255, 255, 255)


_ui_manager = UIManager()


# Funzione globale richiamabile da ovunque per aggiungere elementi UI.
def add_graphic_element(
    *,
    rect,
    text,
    color,
    font,
    text_color=(25, 25, 25),
    border_radius=10,
    border_color=(40, 40, 40),
    border_width=2,
    text_angle=0,
):
    _ui_manager.add_rect_text(
        rect=rect,
        text=text,
        color=color,
        font=font,
        text_color=text_color,
        border_radius=border_radius,
        border_color=border_color,
        border_width=border_width,
        text_angle=text_angle,
    )


def draw_graphic_elements(surface):
    _ui_manager.draw(surface)
