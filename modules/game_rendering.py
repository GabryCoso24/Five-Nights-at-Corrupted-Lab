import random

import pygame

from modules.ui_manager import add_graphic_element, draw_graphic_elements


class GameRenderingMixin:
    def draw_menu(self):
        self.screen.blit(self.menu_background, (0, 0))

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        self.screen.blit(dim, (0, 0))

        title_jitter_x = random.randint(-2, 2)
        title_jitter_y = random.randint(-1, 1)
        title = self.font_title.render("Five Nights at The Corrupted Lab", True, (245, 245, 245))
        title_rect = title.get_rect(center=(self.width // 2 + title_jitter_x, self.height // 3 - 30 + title_jitter_y))
        self.screen.blit(title, title_rect)

        self.queue_button(self.new_game_button, "New Game")
        if self.can_continue:
            self.queue_button(self.continue_button, "Continua")
        self.queue_button(self.exit_button, "Exit")
        draw_graphic_elements(self.screen)

        self.draw_glitch_overlay(self.screen)

        if self.error_message:
            err_label = self.font_small.render(self.error_message, True, (255, 60, 60))
            err_rect = err_label.get_rect(center=(self.width // 2, self.height - 60))
            self.screen.blit(err_label, err_rect)

    def queue_button(self, rect, text):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = (210, 210, 210) if hovered else (170, 170, 170)
        add_graphic_element(
            rect=rect,
            text=text,
            color=color,
            font=self.font_button,
            text_color=(25, 25, 25),
            border_radius=14,
            border_color=(40, 40, 40),
            border_width=3,
        )

    def draw_glitch_overlay(self, surface):
        scanlines = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, 4):
            pygame.draw.line(scanlines, (0, 0, 0, 24), (0, y), (self.width, y))
        surface.blit(scanlines, (0, 0))

        if random.random() > 0.16:
            return

        snapshot = surface.copy()

        for _ in range(random.randint(6, 16)):
            y = random.randint(0, self.height - 6)
            h = random.randint(2, 10)
            shift = random.randint(-45, 45)
            src = pygame.Rect(0, y, self.width, h)
            surface.blit(snapshot, (shift, y), src)

        noise = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for _ in range(240):
            x = random.randint(0, self.width - 2)
            y = random.randint(0, self.height - 2)
            w = random.randint(1, 5)
            h = random.randint(1, 3)
            c = random.randint(120, 255)
            a = random.randint(40, 110)
            pygame.draw.rect(noise, (c, c, c, a), (x, y, w, h))
        surface.blit(noise, (0, 0))

        tint = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        tint.fill((30, 0, 0, random.randint(12, 38)))
        surface.blit(tint, (0, 0))

    def draw_night_intro(self):
        elapsed = pygame.time.get_ticks() - self.intro_start_time
        if elapsed >= self.intro_duration_ms:
            self.start_gameplay()

        self.screen.fill((0, 0, 0))
        title = self.font_night.render(f"Notte {self.current_night}", True, (235, 235, 235))
        hour = self.font_hour.render("Ore 12:00", True, (235, 235, 235))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 40)))
        self.screen.blit(hour, hour.get_rect(center=(self.width // 2, self.height // 2 + 38)))

    def draw_night_outro(self):
        elapsed = pygame.time.get_ticks() - self.outro_start_time
        if elapsed >= self.outro_duration_ms:
            self.enter_menu(play_click=True)

        self.screen.fill((0, 0, 0))
        title = self.font_night.render(f"Notte {self.current_night - 1}", True, (235, 235, 235))
        desc = self.font_night.render("SUPERATA!!", True, (235, 235, 235))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 40)))
        self.screen.blit(desc, desc.get_rect(center=(self.width // 2, self.height // 2 + 38)))

    def draw_game(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_x, _ = mouse_pos
        self.camera.update_from_cursor(mouse_x)
        cam_x = self.camera.get_offset_x()

        self.screen.blit(self.game_background, (-cam_x, 0))

        now_ms = pygame.time.get_ticks()
        if self.flashlight_active and now_ms - self.flashlight_activation_time >= self.flashlight_duration_ms:
            self.flashlight_active = False
            self.flashlight_repel_triggered = False
            self.flashlight_repelled_targets.clear()

        if self.flashlight_active:
            self.flashlight.draw(self.screen)
            # Repel any newly lit enemy while the beam stays active.
            lit_targets = self._get_flashlight_lit_targets(positions=self.animatronics.get_positions(), cam_x=cam_x)
            new_targets = [name for name in lit_targets if name not in self.flashlight_repelled_targets]
            repelled = self.animatronics.on_flashlight(now_ms, target_names=new_targets)
            if repelled:
                self.flashlight_repelled_targets.update(repelled)
                self.flashlight_repel_triggered = True
                self.flashlight_repel_feedback_until = now_ms + 360
                self.audio.play_sound(self.flashlight_repel_sound, volume=0.7)
                self.audio.play_sound(self.flashlight_hit_sound, volume=0.8)

        label = self.orologio.update(now_ms)

        watched_camera = self.video_camere.get_selected_camera_id() if self.video_camere.is_open else None
        player_can_defend = self.flashlight_ready or self.flashlight_active
        events = self.animatronics.update(
            now_ms=now_ms,
            night_level=self.current_night,
            watched_camera=watched_camera,
            player_can_defend=player_can_defend,
        )

        for event in events:
            if event.get("type") == "moved":
                self.video_camere.register_movement(
                    from_camera=event.get("from"),
                    to_camera=event.get("to"),
                    jam_duration_ms=2200,
                )
            if event.get("type") == "jumpscare":
                self.enter_jumpscare(event.get("name", "Sconosciuto"))
                return

        positions = self.animatronics.get_positions()
        threat_cameras = self.animatronics.get_cameras_with_presence()
        self.video_camere.set_threat_cameras(threat_cameras)

        # Mostra tutti i nemici presenti nella camera corrente con sprite distinti.
        threats_by_camera = {}
        for name, camera_id in positions.items():
            camera_slots = [camera_id]
            if camera_id == "door_left":
                camera_slots.append("cam1")
            elif camera_id == "door_right":
                camera_slots.append("cam14")

            sprite = self.enemy_sprites.get(name, self.default_enemy_sprite)
            if sprite is None:
                continue

            for slot in camera_slots:
                threats_by_camera.setdefault(slot, []).append(sprite)

        self.video_camere.set_threats_by_camera(threats_by_camera)

        if self.video_camere.is_open and watched_camera:
            first_sprite = threats_by_camera.get(watched_camera, [self.default_enemy_sprite])[0]
            self.video_camere.set_threat_sprite(first_sprite)
        else:
            self.video_camere.set_threat_sprite(self.default_enemy_sprite)

        if not self.flashlight_ready and now_ms >= self.flashlight_cooldown_until:
            self.flashlight_ready = True

        clock_text = self.font_hour.render(label, True, (235, 235, 235))
        self.screen.blit(clock_text, clock_text.get_rect(topright=(self.width - 30, 24)))

        if self.flashlight_active:
            indicator_text = "Flashlight: ATTIVA"
            indicator_color = (80, 255, 80)
        elif self.flashlight_ready:
            indicator_text = "Flashlight: PRONTA"
            indicator_color = (80, 80, 255)
        else:
            remaining_ms = max(0, self.flashlight_cooldown_until - now_ms)
            indicator_text = f"Flashlight: COOLDOWN {remaining_ms / 1000:.1f}s"
            indicator_color = (255, 80, 80)

        indicator_label = self.font_small.render(indicator_text, True, indicator_color)
        self.screen.blit(indicator_label, (24, 24))

        left_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_left"]
        right_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_right"]
        if left_door_threats:
            self._draw_door_threats(left_door_threats, cam_x, side="left")
        if right_door_threats:
            self._draw_door_threats(right_door_threats, cam_x, side="right")

        self.video_camere.update_hover(mouse_pos)
        self.video_camere.queue_trigger()
        draw_graphic_elements(self.screen)
        self.video_camere.draw_overlay(self.screen)

        if now_ms < self.flashlight_repel_feedback_until:
            self._draw_flashlight_repel_feedback(now_ms)

        if self.orologio.is_finished():
            self.current_night += 1
            self.can_continue = True
            self.exit_night()
            return

    def draw_jumpscare(self):
        now_ms = pygame.time.get_ticks()
        elapsed = now_ms - self.jumpscare_start_time
        if elapsed >= self.jumpscare_duration_ms:
            self._stop_jumpscare_media()
            self._start_defeat_video()
            return

        self.screen.fill((0, 0, 0))

        frame_surface = None

        if self.jumpscare_video_cap is not None:
            if now_ms - self.jumpscare_last_frame_at >= self.jumpscare_frame_delay_ms:
                ok, frame = self.jumpscare_video_cap.read()
                self.jumpscare_last_frame_at = now_ms
                if ok:
                    frame_rgb = frame[:, :, ::-1]
                    frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                    self.jumpscare_last_surface = frame_surface
                else:
                    try:
                        self.jumpscare_video_cap.release()
                    except Exception:
                        pass
                    self.jumpscare_video_cap = None

            if frame_surface is None:
                frame_surface = self.jumpscare_last_surface

        if frame_surface is None and self.jumpscare_frames:
            total_frames = len(self.jumpscare_frames)
            frame_index = min(total_frames - 1, int((elapsed / max(1, self.jumpscare_duration_ms)) * total_frames))
            frame_surface = self.jumpscare_frames[frame_index]

        if frame_surface is None:
            frame_surface = self.enemy_sprites.get(self.jumpscare_name, self.default_enemy_sprite)

        if frame_surface is not None:
            scaled = pygame.transform.smoothscale(frame_surface, (self.width, self.height))

            shake_x = 0
            shake_y = 0
            if elapsed < self.jumpscare_shake_duration_ms:
                progress = elapsed / max(1, self.jumpscare_shake_duration_ms)
                intensity = int(self.jumpscare_shake_strength * (1.0 - progress))
                if intensity > 0:
                    shake_x = random.randint(-intensity, intensity)
                    shake_y = random.randint(-intensity, intensity)

            self.screen.blit(scaled, (shake_x, shake_y))

            if elapsed < self.jumpscare_flash_duration_ms:
                flash_progress = elapsed / max(1, self.jumpscare_flash_duration_ms)
                alpha = int(255 * (1.0 - flash_progress))
                flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                flash.fill((255, 255, 255, max(0, min(255, alpha))))
                self.screen.blit(flash, (0, 0))

    def draw_defeat_video(self):
        now_ms = pygame.time.get_ticks()

        if self.defeat_video_cap is None:
            # Fallback: il file manca o OpenCV non e disponibile.
            self.screen.fill((0, 0, 0))
            info = self.font_small.render("Video non disponibile", True, (255, 120, 120))
            self.screen.blit(info, info.get_rect(center=(self.width // 2, self.height // 2)))
            if now_ms - self.defeat_video_started_at >= 1500:
                self.enter_menu(play_click=False)
            return

        if now_ms - self.defeat_video_last_frame_at < self.defeat_video_frame_delay_ms:
            return

        ok, frame = self.defeat_video_cap.read()
        self.defeat_video_last_frame_at = now_ms

        if not ok:
            self.enter_menu(play_click=False)
            return

        frame_rgb = frame[:, :, ::-1]
        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        frame_surface = pygame.transform.smoothscale(frame_surface, (self.width, self.height))
        self.screen.blit(frame_surface, (0, 0))

    def draw_victory_video(self):
        now_ms = pygame.time.get_ticks()

        if self.victory_video_cap is None:
            self.screen.fill((0, 0, 0))
            info = self.font_small.render("Video vittoria non disponibile", True, (120, 255, 120))
            self.screen.blit(info, info.get_rect(center=(self.width // 2, self.height // 2)))
            if now_ms - self.victory_video_started_at >= 1500:
                self.enter_menu(play_click=False)
            return

        if now_ms - self.victory_video_last_frame_at < self.victory_video_frame_delay_ms:
            return

        ok, frame = self.victory_video_cap.read()
        self.victory_video_last_frame_at = now_ms

        if not ok:
            self.enter_menu(play_click=False)
            return

        frame_rgb = frame[:, :, ::-1]
        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        frame_surface = pygame.transform.smoothscale(frame_surface, (self.width, self.height))
        self.screen.blit(frame_surface, (0, 0))

    def _draw_door_threats(self, door_threats, cam_x, side="right"):
        # Anchor near the office side door in world space, then convert to screen space.
        if side == "left":
            door_world_x = int(self.game_background.get_width() * 0.24)
        else:
            door_world_x = self.game_background.get_width() - 320
        base_screen_x = door_world_x - cam_x
        base_screen_y = int(self.height * 0.26)

        for idx, name in enumerate(door_threats):
            sprite = self.enemy_sprites.get(name, self.default_enemy_sprite)
            if sprite is None:
                continue

            target_h = int(self.height * 0.38)
            target_w = int(sprite.get_width() * (target_h / max(1, sprite.get_height())))
            target_w = min(target_w, int(self.width * 0.34))
            img = pygame.transform.smoothscale(sprite, (target_w, target_h)).convert_alpha()
            img.set_alpha(228)

            x = base_screen_x + (idx * 56) - (target_w // 2)
            y = base_screen_y + (idx * 12)
            self.screen.blit(img, (x, y))

    def _get_flashlight_lit_targets(self, positions, cam_x):
        mouse_pos = pygame.mouse.get_pos()
        lit_targets = []

        left_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_left"]
        right_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_right"]

        for side, threats in (("left", left_door_threats), ("right", right_door_threats)):
            if side == "left":
                door_world_x = int(self.game_background.get_width() * 0.24)
            else:
                door_world_x = self.game_background.get_width() - 320
            base_screen_x = door_world_x - cam_x
            base_screen_y = int(self.height * 0.26)

            for idx, name in enumerate(threats):
                sprite = self.enemy_sprites.get(name, self.default_enemy_sprite)
                if sprite is None:
                    continue

                target_h = int(self.height * 0.38)
                target_w = int(sprite.get_width() * (target_h / max(1, sprite.get_height())))
                target_w = min(target_w, int(self.width * 0.34))
                x = base_screen_x + (idx * 56) - (target_w // 2)
                y = base_screen_y + (idx * 12)
                rect = pygame.Rect(x, y, target_w, target_h)

                if self._is_rect_hit_by_flashlight(rect, mouse_pos):
                    lit_targets.append(name)

        return lit_targets

    def _is_rect_hit_by_flashlight(self, rect, light_center):
        light_x, light_y = light_center
        closest_x = max(rect.left, min(light_x, rect.right))
        closest_y = max(rect.top, min(light_y, rect.bottom))
        dx = light_x - closest_x
        dy = light_y - closest_y
        return (dx * dx + dy * dy) <= (self.flashlight.radius * self.flashlight.radius)

    def _draw_flashlight_repel_feedback(self, now_ms):
        remaining = max(0, self.flashlight_repel_feedback_until - now_ms)
        alpha = int(165 * (remaining / 360.0))
        pulse = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pulse.fill((210, 255, 235, max(0, min(180, alpha))))
        self.screen.blit(pulse, (0, 0))

        text = self.font_small.render("FLASH HIT", True, (230, 255, 240))
        text_shadow = self.font_small.render("FLASH HIT", True, (20, 30, 25))
        center = (self.width // 2, int(self.height * 0.18))
        self.screen.blit(text_shadow, text_shadow.get_rect(center=(center[0] + 2, center[1] + 2)))
        self.screen.blit(text, text.get_rect(center=center))
