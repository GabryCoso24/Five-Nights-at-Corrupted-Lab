import pygame

from modules.ui_manager import add_graphic_element


class SystemPanel:
    def __init__(self, width, height, label_font, title_font):
        self.width = width
        self.height = height
        self.label_font = label_font
        self.title_font = title_font
        # Use a compact terminal-like font inside this panel to avoid text overlaps.
        self.panel_font = pygame.font.SysFont("consolas", 34)
        self.panel_title_font = pygame.font.SysFont("consolas", 44, bold=True)

        self.trigger_visible = True
        self.trigger_interactable = True
        self.is_trigger_hovered = False
        self.is_open = False
        self._mouse_pos = (0, 0)

        self.trigger_rect = pygame.Rect(18, self.height - 94, 210, 82)
        panel_w = min(int(self.width * 0.86), 980)
        panel_h = min(int(self.height * 0.84), 780)
        panel_x = max(18, (self.width - panel_w) // 2)
        panel_y = max(16, (self.height - panel_h) // 2)
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        self._button_rects = {
            "reboot_camera": pygame.Rect(0, 0, 0, 0),
            "reboot_ventilation": pygame.Rect(0, 0, 0, 0),
            "reboot_flashlight": pygame.Rect(0, 0, 0, 0),
            "reboot_all": pygame.Rect(0, 0, 0, 0),
            "exit": pygame.Rect(0, 0, 0, 0),
        }

    def set_trigger_rect(self, x, y, w, h):
        self.trigger_rect = pygame.Rect(x, y, w, h)
        return self.trigger_rect

    def set_trigger_visible(self, visible):
        self.trigger_visible = bool(visible)
        if not self.trigger_visible:
            self.is_trigger_hovered = False
        return self.trigger_visible

    def set_trigger_interactable(self, interactable):
        self.trigger_interactable = bool(interactable)
        if not self.trigger_interactable:
            self.is_trigger_hovered = False
        return self.trigger_interactable

    def update_hover(self, mouse_pos):
        self._mouse_pos = mouse_pos
        self.is_trigger_hovered = (
            self.trigger_visible
            and self.trigger_interactable
            and self.trigger_rect.collidepoint(mouse_pos)
        )

    def queue_trigger(self):
        if not self.trigger_visible:
            return

        if self.is_open:
            fill = (255, 148, 46, 45)
            text_color = (255, 173, 94, 160)
        elif self.trigger_interactable:
            fill = (255, 142, 32, 140) if self.is_trigger_hovered else (255, 132, 16, 96)
            text_color = (255, 196, 120, 245)
        else:
            return

        add_graphic_element(
            rect=self.trigger_rect,
            text="SYSTEM",
            color=fill,
            font=self.label_font,
            text_color=text_color,
            border_radius=12,
            border_color=(40, 24, 12, 255),
            border_width=2,
            text_angle=0,
        )

    def handle_event(self, event, lock_open=False):
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False, None

        if self.trigger_visible and self.trigger_interactable and self.trigger_rect.collidepoint(event.pos):
            if lock_open and self.is_open:
                return True, "reboot_reset_close"
            self.is_open = not self.is_open
            return True, None

        if not self.is_open:
            return False, None

        for action, rect in self._button_rects.items():
            if rect.collidepoint(event.pos):
                if action == "exit" and lock_open:
                    return True, "reboot_reset_close"
                return True, action

        if not self.panel_rect.collidepoint(event.pos):
            if lock_open:
                return True, "reboot_reset_close"
            self.is_open = False
            return True, None

        return True, None

    def draw_overlay(self, surface, errors, reboots=None, now_ms=0):
        if not self.is_open:
            return

        reboots = reboots or {}

        pygame.draw.rect(surface, (12, 20, 12), self.panel_rect)
        pygame.draw.rect(surface, (36, 85, 36), self.panel_rect, width=2)

        x = self.panel_rect.left + 20
        y = self.panel_rect.top + 16

        self._draw_line(surface, "system restart", (124, 255, 124), x, y, title=True)
        y += 52
        self._draw_line(surface, "menu>>>", (124, 255, 124), x, y)
        y += 50

        self._draw_error_line(surface, "camera system", errors.get("camera", False), x, y, reboots.get("camera", 0), now_ms)
        y += 48
        self._draw_error_line(surface, "ventilation", errors.get("ventilation", False), x, y, reboots.get("ventilation", 0), now_ms)
        y += 48
        self._draw_error_line(surface, "flashlight", errors.get("flashlight", False), x, y, reboots.get("flashlight", 0), now_ms)
        y += 62

        self._button_rects["reboot_camera"] = self._draw_action(surface, "reboot camera", x, y)
        y += 44
        self._button_rects["reboot_ventilation"] = self._draw_action(surface, "reboot ventilation", x, y)
        y += 44
        self._button_rects["reboot_flashlight"] = self._draw_action(surface, "reboot flashlight", x, y)
        y += 46
        self._button_rects["reboot_all"] = self._draw_action(surface, "reboot all", x, y, important=True)
        y += 46
        self._button_rects["exit"] = self._draw_action(surface, "exit", x, y)

    def _draw_line(self, surface, text, color, x, y, title=False):
        font = self.panel_title_font if title else self.panel_font
        label = font.render(text, True, color)
        surface.blit(label, (x, y))

    def _draw_error_line(self, surface, name, active, x, y, reboot_until=0, now_ms=0):
        base = self.panel_font.render(f">>> {name}", True, (120, 250, 120))
        surface.blit(base, (x, y))

        if reboot_until and now_ms < reboot_until:
            remaining = (reboot_until - now_ms) / 1000.0
            state = f"reboot {remaining:0.1f}s"
            color = (255, 210, 120)
        else:
            state = "error" if active else "ok"
            color = (255, 95, 95) if active else (120, 250, 120)
        state_label = self.panel_font.render(state, True, color)
        state_x = self.panel_rect.right - state_label.get_width() - 28
        surface.blit(state_label, (state_x, y))

    def _draw_action(self, surface, text, x, y, important=False):
        hit_rect = pygame.Rect(x - 8, y - 6, 520, 46)
        if hit_rect.collidepoint(self._mouse_pos):
            hover_bg = pygame.Surface((hit_rect.width, hit_rect.height), pygame.SRCALPHA)
            hover_bg.fill((70, 120, 70, 90) if not important else (140, 95, 45, 95))
            surface.blit(hover_bg, hit_rect.topleft)
            pygame.draw.rect(surface, (126, 220, 126) if not important else (255, 192, 118), hit_rect, width=1)

        color = (136, 255, 136) if not important else (255, 180, 95)
        label = self.panel_font.render(text, True, color)
        rect = label.get_rect(topleft=(x, y))
        surface.blit(label, rect)
        return hit_rect
