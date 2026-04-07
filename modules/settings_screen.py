import pygame


def _draw_section_title(game, panel, row_buttons, text, color):
    if not row_buttons:
        return
    row_top = min(rect.top for rect in row_buttons.values())
    label = game.font_small.render(text, True, color)
    game.screen.blit(label, (panel.left + 44, row_top - 56))


def _render_fitted_label(game, text, max_width, selected):
    base_color = (18, 32, 14) if selected else (218, 232, 212)
    label = game.font_small.render(text, True, base_color)
    if label.get_width() <= max_width:
        return label

    fitted_font = pygame.font.SysFont("segoe ui", 28, bold=True)
    label = fitted_font.render(text, True, base_color)
    if label.get_width() <= max_width:
        return label

    scale = max(0.55, max_width / float(max(1, label.get_width())))
    new_size = (max(1, int(label.get_width() * scale)), max(1, int(label.get_height() * scale)))
    return pygame.transform.smoothscale(label, new_size)


def draw_settings(game):
    game.screen.blit(game.menu_background, (0, 0))

    overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
    overlay.fill((6, 12, 10, 190))
    game.screen.blit(overlay, (0, 0))

    panel = getattr(game, "settings_panel_rect", pygame.Rect(120, 80, game.width - 240, game.height - 160))
    pygame.draw.rect(game.screen, (16, 28, 18), panel, border_radius=14)
    pygame.draw.rect(game.screen, (140, 196, 102), panel, width=3, border_radius=14)

    title = game.font_hour.render(game.tr("settings.title"), True, (208, 236, 173))
    game.screen.blit(title, title.get_rect(midtop=(panel.centerx, panel.top + 20)))

    text_color = (220, 232, 218)
    mouse_pos = pygame.mouse.get_pos()

    current_mode = str(getattr(game, "display_mode", "windowed")).lower()
    current_size = tuple(getattr(game, "window_size", (game.width, game.height)))
    current_cursor_size = int(getattr(game, "selected_cursor_size", 48) or 48)
    current_language = str(getattr(game, "language", "en") or "en").lower()

    _draw_section_title(game, panel, getattr(game, "settings_display_mode_buttons", {}), game.tr("settings.display_mode"), text_color)

    for mode, rect in getattr(game, "settings_display_mode_buttons", {}).items():
        is_selected = mode == current_mode
        hovered = rect.collidepoint(mouse_pos)
        fill = (138, 186, 94) if is_selected else ((84, 122, 64) if hovered else (58, 86, 45))
        border = (220, 246, 186) if is_selected else (122, 164, 101)
        pygame.draw.rect(game.screen, fill, rect, border_radius=10)
        pygame.draw.rect(game.screen, border, rect, width=2, border_radius=10)
        mode_label = game.tr(f"settings.mode.{mode}")
        label = _render_fitted_label(game, mode_label, rect.width - 18, is_selected)
        game.screen.blit(label, label.get_rect(center=rect.center))

    _draw_section_title(game, panel, getattr(game, "settings_window_size_buttons", {}), game.tr("settings.window_size"), text_color)

    for size, rect in getattr(game, "settings_window_size_buttons", {}).items():
        is_selected = size == current_size
        hovered = rect.collidepoint(mouse_pos)
        fill = (138, 186, 94) if is_selected else ((84, 122, 64) if hovered else (58, 86, 45))
        border = (220, 246, 186) if is_selected else (122, 164, 101)
        pygame.draw.rect(game.screen, fill, rect, border_radius=10)
        pygame.draw.rect(game.screen, border, rect, width=2, border_radius=10)
        label_text = f"{size[0]} x {size[1]}"
        label = _render_fitted_label(game, label_text, rect.width - 18, is_selected)
        game.screen.blit(label, label.get_rect(center=rect.center))

    _draw_section_title(game, panel, getattr(game, "settings_cursor_size_buttons", {}), game.tr("settings.cursor_size"), text_color)

    for size, rect in getattr(game, "settings_cursor_size_buttons", {}).items():
        is_selected = int(size) == current_cursor_size
        hovered = rect.collidepoint(mouse_pos)
        fill = (138, 186, 94) if is_selected else ((84, 122, 64) if hovered else (58, 86, 45))
        border = (220, 246, 186) if is_selected else (122, 164, 101)
        pygame.draw.rect(game.screen, fill, rect, border_radius=10)
        pygame.draw.rect(game.screen, border, rect, width=2, border_radius=10)
        label = _render_fitted_label(game, str(int(size)), rect.width - 18, is_selected)
        game.screen.blit(label, label.get_rect(center=rect.center))

    _draw_section_title(game, panel, getattr(game, "settings_language_buttons", {}), game.tr("settings.language"), text_color)

    for language, rect in getattr(game, "settings_language_buttons", {}).items():
        is_selected = language == current_language
        hovered = rect.collidepoint(mouse_pos)
        fill = (138, 186, 94) if is_selected else ((84, 122, 64) if hovered else (58, 86, 45))
        border = (220, 246, 186) if is_selected else (122, 164, 101)
        pygame.draw.rect(game.screen, fill, rect, border_radius=10)
        pygame.draw.rect(game.screen, border, rect, width=2, border_radius=10)
        label = _render_fitted_label(game, game.tr(f"settings.language.{language}"), rect.width - 18, is_selected)
        game.screen.blit(label, label.get_rect(center=rect.center))

    back = game.settings_back_button
    hovered = back.collidepoint(mouse_pos)
    pygame.draw.rect(game.screen, (120, 170, 86) if hovered else (78, 118, 58), back, border_radius=10)
    pygame.draw.rect(game.screen, (222, 246, 190), back, width=2, border_radius=10)
    back_label = game.font_small.render(game.tr("settings.back"), True, (16, 30, 12))
    game.screen.blit(back_label, back_label.get_rect(center=back.center))
