import pygame


class GameEventHandlersMixin:
    def handle_event(self, event):
        if self.state == "menu":
            self.handle_menu_events(event)
        elif self.state == "night_intro":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_gameplay()
        elif self.state == "night_outro":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.enter_menu(play_click=True)
        elif self.state == "jumpscare":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.enter_menu(play_click=False)
        elif self.state == "game":
            self.handle_game_events(event)

    def handle_menu_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.can_continue:
                    self.continue_game()
                else:
                    self.start_new_game()
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.new_game_button.collidepoint(event.pos):
                self.start_new_game()
            elif self.can_continue and self.continue_button.collidepoint(event.pos):
                self.continue_game()
            elif self.exit_button.collidepoint(event.pos):
                self.audio.play_sound(self.button_sound, volume=0.8)
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_game_events(self, event):
        if self.video_camere.handle_event(event):
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_SPACE and self.flashlight_ready:
            self.flashlight_active = True
            self.flashlight_activation_time = pygame.time.get_ticks()
            self.flashlight_ready = False
            self.flashlight_cooldown_until = self.flashlight_activation_time + self.flashlight_cooldown_ms
            self.flashlight_repel_triggered = False
            self.flashlight_repelled_targets.clear()
        elif event.key == pygame.K_m:
            self.enter_menu(play_click=True)
        elif event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
