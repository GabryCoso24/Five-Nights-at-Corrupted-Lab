"""Schermata di caricamento con barra di avanzamento e callback finale."""

import pygame


def draw_loading_screen(game):
    """Disegna il messaggio di caricamento, aggiorna la barra e avvia l'azione successiva a fine attesa."""
    now_ms = pygame.time.get_ticks()
    started_at = int(getattr(game, "loading_started_at", now_ms) or now_ms)
    duration_ms = max(200, int(getattr(game, "loading_duration_ms", 1000) or 1000))
    progress = min(1.0, max(0.0, (now_ms - started_at) / float(duration_ms)))

    game.screen.fill((0, 0, 0))

    message = str(getattr(game, "loading_message", game.tr("loading.default")) or game.tr("loading.default"))
    dots = "." * ((now_ms // 280) % 4)

    title = game.font_hour.render(f"{message}{dots}", True, (218, 230, 214))
    game.screen.blit(title, title.get_rect(center=(game.width // 2, game.height // 2 - 26)))

    bar_w = int(game.width * 0.42)
    bar_h = 24
    bar_x = (game.width - bar_w) // 2
    bar_y = game.height // 2 + 30

    pygame.draw.rect(game.screen, (38, 58, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
    fill_w = int((bar_w - 4) * progress)
    if fill_w > 0:
        pygame.draw.rect(game.screen, (132, 188, 108), (bar_x + 2, bar_y + 2, fill_w, bar_h - 4), border_radius=6)
    pygame.draw.rect(game.screen, (174, 214, 156), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=8)

    if progress >= 1.0:
        next_action = getattr(game, "loading_next_action", None)
        game.loading_next_action = None
        if callable(next_action):
            next_action()

