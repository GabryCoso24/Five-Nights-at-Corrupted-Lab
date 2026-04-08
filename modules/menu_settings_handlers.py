"""Gestione dell'input per menu e schermata impostazioni."""

import pygame


def handle_menu_events(game, event):
    """Gestisce tastiera e mouse nel menu principale, aprendo la partita o le altre schermate."""
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RETURN:
            if game.can_continue:
                game.continue_game()
            else:
                game.start_new_game()
        elif event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if game.new_game_button.collidepoint(event.pos):
            game.start_new_game()
        elif game.can_continue and game.continue_button.collidepoint(event.pos):
            game.continue_game()
        elif game.credits_button.collidepoint(event.pos):
            game.audio.play_sound(game.button_sound, volume=0.8)
            game._start_credits_video()
        elif game.settings_button.collidepoint(event.pos):
            game.audio.play_sound(game.button_sound, volume=0.8)
            game.state = "settings"
        elif game.exit_button.collidepoint(event.pos):
            game.audio.play_sound(game.button_sound, volume=0.8)
            pygame.event.post(pygame.event.Event(pygame.QUIT))


def handle_settings_events(game, event):
    """Gestisce i click e gli shortcut della schermata impostazioni, applicando subito le scelte."""
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            game.audio.play_sound(game.button_sound, volume=0.8)
            game.state = "menu"
            return

    if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
        return

    if game.settings_back_button.collidepoint(event.pos):
        game.audio.play_sound(game.button_sound, volume=0.8)
        game.state = "menu"
        return

    for mode, rect in game.settings_display_mode_buttons.items():
        if rect.collidepoint(event.pos):
            if game.set_display_mode(mode):
                game.audio.play_sound(game.button_sound, volume=0.8)
            return

    for size, rect in game.settings_window_size_buttons.items():
        if rect.collidepoint(event.pos):
            if game.set_window_size(size):
                game.audio.play_sound(game.button_sound, volume=0.8)
            return

    for size, rect in game.settings_cursor_size_buttons.items():
        if rect.collidepoint(event.pos):
            if game.set_cursor_size(size):
                game.audio.play_sound(game.button_sound, volume=0.8)
            return

    for language, rect in game.settings_language_buttons.items():
        if rect.collidepoint(event.pos):
            if game.set_language(language):
                game.audio.play_sound(game.button_sound, volume=0.8)
            return

