"""Rendering del menu principale, con pulsanti, sfondo animato e feedback visivo."""

import random

import pygame

from modules.ui_manager import add_graphic_element, draw_graphic_elements


def _queue_button(game, rect, text):
    """Aggiunge un pulsante alla coda grafica, cambiando colore quando il mouse lo sta puntando."""
    hovered = rect.collidepoint(pygame.mouse.get_pos())
    base_fill = (92, 138, 46, 238)
    hover_fill = (122, 176, 66, 252)
    color = hover_fill if hovered else base_fill
    border_color = (204, 238, 138, 255) if hovered else (33, 62, 24, 255)
    text_color = (8, 20, 7) if hovered else (12, 26, 10)
    add_graphic_element(
        rect=rect,
        text=text,
        color=color,
        font=game.font_button,
        text_color=text_color,
        border_radius=16,
        border_color=border_color,
        border_width=3,
    )


def draw_menu(game):
    """Disegna il menu principale, aggiorna l'eventuale video di sfondo e sovrappone l'interfaccia."""
    now_ms = pygame.time.get_ticks()
    game.screen.blit(game.menu_background, (0, 0))

    # Draw menu video background if available, but always continue drawing menu UI.
    if game.menu_video_cap is not None and now_ms - game.menu_video_last_frame_at >= game.menu_video_frame_delay_ms:
        ok, frame = game.menu_video_cap.read()
        game.menu_video_last_frame_at = now_ms

        if not ok:
            # OpenCV property id 1 == CAP_PROP_POS_FRAMES
            game.menu_video_cap.set(1, 0)
            ok, frame = game.menu_video_cap.read()

        if ok and frame is not None:
            frame_rgb = frame[:, :, ::-1]
            frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            # Use fast scale instead of smoothscale to avoid performance issues
            game.menu_video_last_surface = pygame.transform.scale(frame_surface, (game.width, game.height))

    last_surface = getattr(game, "menu_video_last_surface", None)
    if last_surface is not None:
        game.screen.blit(last_surface, (0, 0))

    dim = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
    dim.fill((6, 11, 6, 122))
    game.screen.blit(dim, (0, 0))

    accent = pygame.Surface((6, int(game.height * 0.82)), pygame.SRCALPHA)
    accent.fill((110, 166, 52, 190))
    game.screen.blit(accent, (int(game.width * 0.066), int(game.height * 0.08)))

    title_jitter_x = random.randint(-2, 2)
    title_jitter_y = random.randint(-1, 1)
    title = game.font_title.render("Five Nights at The Corrupted Lab", True, (199, 231, 120))
    title_shadow = game.font_title.render("Five Nights at The Corrupted Lab", True, (7, 14, 7))
    title_left_x = int(game.width * 0.08) + title_jitter_x
    title_y = int(game.height * 0.09) + title_jitter_y
    title_rect = title.get_rect(topleft=(title_left_x, title_y))
    game.screen.blit(title_shadow, title_rect.move(4, 4))
    game.screen.blit(title, title_rect)

    _queue_button(game, game.new_game_button, game.tr("menu.new_game"))
    if game.can_continue:
        _queue_button(game, game.continue_button, game.tr("menu.continue"))
    _queue_button(game, game.credits_button, game.tr("menu.credits"))
    _queue_button(game, game.settings_button, game.tr("menu.settings"))
    _queue_button(game, game.exit_button, game.tr("menu.exit"))
    draw_graphic_elements(game.screen)

    game.draw_glitch_overlay(game.screen)

    if game.error_message:
        err_label = game.font_small.render(game.error_message, True, (255, 60, 60))
        err_rect = err_label.get_rect(center=(game.width // 2, game.height - 60))
        game.screen.blit(err_label, err_rect)


