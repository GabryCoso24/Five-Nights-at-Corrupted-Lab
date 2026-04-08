import os
import random

import pygame

from modules.credits_screen import draw_credits_video as draw_credits_video_screen
from modules.loading_screen import draw_loading_screen as draw_loading_screen_module
from modules.menu_screen import draw_menu as draw_menu_screen
from modules.settings_screen import draw_settings as draw_settings_screen
from modules.ui_manager import add_graphic_element, draw_graphic_elements


class GameRenderingMixin:
    def _load_custom_cursor(self, cursor_path=None, hotspot=None):
        path = cursor_path if cursor_path is not None else getattr(self, "custom_cursor_path", None)
        self.custom_cursor_surface = None
        self.custom_cursor_hotspot = tuple(hotspot or getattr(self, "custom_cursor_hotspot", (0, 0)))

        if not path or not os.path.isfile(path):
            self._sync_custom_cursor_visibility()
            return False

        try:
            self.custom_cursor_surface = pygame.image.load(path).convert_alpha()
        except Exception:
            self.custom_cursor_surface = None
            self._sync_custom_cursor_visibility()
            return False

        self._sync_custom_cursor_visibility()
        return True

    def _sync_custom_cursor_visibility(self):
        try:
            pygame.mouse.set_visible(getattr(self, "custom_cursor_surface", None) is None)
        except Exception:
            pass

    def draw_custom_cursor(self):
        cursor = getattr(self, "custom_cursor_surface", None)
        if cursor is None:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        hotspot_x, hotspot_y = getattr(self, "custom_cursor_hotspot", (0, 0))
        self.screen.blit(cursor, (mouse_x - int(hotspot_x), mouse_y - int(hotspot_y)))

    @staticmethod
    def _get_video_fps(capture, default_fps=30.0):
        if capture is None:
            return float(default_fps)
        fps = float(capture.get(5) or 0.0)  # OpenCV property id 5 == CAP_PROP_FPS
        # Keep only plausible values; bad metadata can report 0 or absurd rates.
        if 20.0 <= fps <= 120.0:
            return fps
        return float(default_fps)

    def _read_synced_video_frame(self, capture, started_at_ms, now_ms):
        if capture is None:
            return None

        # Keep A/V sync from elapsed time, but avoid expensive seek-on-every-frame stutter.
        elapsed_ms = max(0, int(now_ms - started_at_ms))
        fps = self._get_video_fps(capture, default_fps=30.0)
        target_frame = max(0, int((elapsed_ms / 1000.0) * fps))

        if not hasattr(self, "_video_sync_cache"):
            self._video_sync_cache = {}

        # Include the playback start timestamp in the cache key to avoid
        # stale frame reuse if Python recycles the same object id.
        cache_key = (id(capture), int(started_at_ms))
        state = self._video_sync_cache.get(cache_key)
        if state is None:
            state = {
                "last_frame": -1,
                "last_surface": None,
            }
            self._video_sync_cache[cache_key] = state

        last_frame = int(state.get("last_frame", -1))
        last_surface = state.get("last_surface")

        # If we are still in the same frame time slot, reuse the last decoded frame.
        if target_frame <= last_frame:
            return last_surface

        frames_to_advance = target_frame - last_frame
        frame = None

        if frames_to_advance > 8:
            # Large drift: one seek is cheaper than decoding many frames.
            capture.set(1, target_frame)
            ok, frame = capture.read()
            if not ok or frame is None:
                return None
            last_frame = target_frame
        else:
            # Small drift: decode sequentially for smoother playback cadence.
            reads = max(1, frames_to_advance)
            for _ in range(reads):
                ok, frame = capture.read()
                if not ok or frame is None:
                    return None
                last_frame += 1

        frame_rgb = frame[:, :, ::-1]
        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        scaled_surface = pygame.transform.scale(frame_surface, (self.width, self.height))

        state["last_frame"] = last_frame
        state["last_surface"] = scaled_surface
        return scaled_surface

    def _draw_end_video_label(self, text, color):
        panel_h = 94
        panel = pygame.Surface((self.width, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))
        self.screen.blit(panel, (0, 0))

        label_shadow = self.font_night.render(text, True, (10, 10, 10))
        label = self.font_night.render(text, True, color)
        center = (self.width // 2, 46)
        self.screen.blit(label_shadow, label_shadow.get_rect(center=(center[0] + 2, center[1] + 2)))
        self.screen.blit(label, label.get_rect(center=center))

    def _draw_error_alert_overlay(self, now_ms):
        active_errors = [name for name, is_active in self.system_errors.items() if is_active]
        if not active_errors:
            return

        error_count = len(active_errors)
        pulse = 0.5 + (0.5 * abs(((now_ms // 90) % 10) - 5) / 5.0)
        alpha = int(min(115, 14 + (error_count * 14) + (pulse * 38)))

        red_flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        red_flash.fill((220, 24, 24, max(0, min(255, alpha))))
        self.screen.blit(red_flash, (0, 0))

    def draw_menu(self):
        draw_menu_screen(self)

    def draw_settings(self):
        draw_settings_screen(self)

    def draw_loading_screen(self):
        draw_loading_screen_module(self)

    def queue_button(self, rect, text):
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
            font=self.font_button,
            text_color=text_color,
            border_radius=16,
            border_color=border_color,
            border_width=3,
        )

    def _draw_mute_call_button(self, anchor_rect):
        if not getattr(self, "current_night_call_path", None):
            self.call_mute_button_rect = pygame.Rect(0, 0, 0, 0)
            return None

        button_text = self.tr("ui.mute_call")
        text_color = (232, 245, 226)
        text_surface = self.font_small.render(button_text, True, text_color)

        padding_x = 22
        padding_y = 11
        button_width = max(160, text_surface.get_width() + (padding_x * 2))
        button_height = max(40, text_surface.get_height() + (padding_y * 2))
        button_left = anchor_rect.right + 18
        button_top = anchor_rect.top - 4
        button_rect = pygame.Rect(button_left, button_top, button_width, button_height)

        if button_rect.right > self.width - 20:
            button_rect.right = self.width - 20

        hovered = button_rect.collidepoint(pygame.mouse.get_pos())
        muted = bool(getattr(self, "current_night_call_muted", False))

        fill_color = (42, 128, 56, 176 if hovered else 142)
        if muted:
            fill_color = (38, 102, 46, 118 if hovered else 96)
        border_color = (168, 232, 145, 220 if hovered else 165)
        if muted:
            border_color = (126, 186, 114, 160 if hovered else 132)

        button_surface = pygame.Surface((button_rect.width, button_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(button_surface, fill_color, button_surface.get_rect(), border_radius=14)
        pygame.draw.rect(button_surface, border_color, button_surface.get_rect(), width=2, border_radius=14)
        self.screen.blit(button_surface, button_rect.topleft)

        text_rect = text_surface.get_rect(center=button_rect.center)
        self.screen.blit(text_surface, text_rect)
        self.call_mute_button_rect = button_rect
        return button_rect

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
        title = self.font_night.render(self.tr("ui.night", night=self.current_night), True, (235, 235, 235))
        hour = self.font_hour.render(self.tr("ui.hour_start"), True, (235, 235, 235))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 40)))
        self.screen.blit(hour, hour.get_rect(center=(self.width // 2, self.height // 2 + 38)))

    def draw_night_tutorial(self):
        self.screen.fill((0, 0, 0))
        current_page = int(getattr(self, "tutorial_page", 0) or 0)

        panel_w = min(1280, int(self.width * 0.84))
        panel_h = min(760, int(self.height * 0.78))
        panel = pygame.Rect(
            (self.width - panel_w) // 2,
            (self.height - panel_h) // 2,
            panel_w,
            panel_h,
        )

        pygame.draw.rect(self.screen, (12, 20, 12), panel, border_radius=14)
        pygame.draw.rect(self.screen, (137, 198, 84), panel, width=3, border_radius=14)

        title = self.font_night.render(f"Tutorial - {self.tr('ui.night', night=1)} ({current_page + 1}/2)", True, (216, 241, 174))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.top + 62)))

        if current_page == 0:
            if self.language == "it":
                lines = [
                    "Obiettivo: sopravvivi fino alle 6 AM.",
                    "CAM: usa il trigger a destra per aprire il sistema telecamere.",
                    "Condotti: nelle CAM vent, doppio click su una tratta per chiuderla.",
                    "Torcia: premi SPACE quando sei in ufficio (non nelle CAM/pannello).",
                    "Errori di sistema: apri il pannello a sinistra e riavvia i moduli.",
                    "Se un nemico arriva alla porta, reagisci subito o perderai.",
                ]
                footer_text = "Premi INVIO o SPAZIO per continuare"
            else:
                lines = [
                    "Goal: survive until 6 AM.",
                    "CAM: use the trigger on the right to open the camera system.",
                    "Vents: in vent CAM map, double click a section to close it.",
                    "Flashlight: press SPACE in the office (not in CAM/panel).",
                    "System errors: open the left panel and reboot modules.",
                    "If an enemy reaches the door, react quickly or you lose.",
                ]
                footer_text = "Press ENTER or SPACE to continue"
        else:
            if self.language == "it":
                lines = [
                    "Esistono animatronics letali e animatronics che causano errori.",
                    "Letali: se arrivano alla porta e non li gestisci in tempo, perdi.",
                    "Contromossa: osserva le CAM spesso e usa la torcia al momento giusto.",
                    "Tipo errore: aumentano la pressione attivando malfunzionamenti.",
                    "Contromossa: apri subito il pannello e riavvia i moduli in errore.",
                    "Regola d'oro: alterna controllo CAM e pannello, senza tunnel vision.",
                ]
                footer_text = "Premi INVIO o SPAZIO per iniziare"
            else:
                lines = [
                    "There are lethal animatronics and error-causing animatronics.",
                    "Lethal: if they reach the door and you fail to react, you lose.",
                    "Counter: check CAM often and use the flashlight at the right time.",
                    "Error type: they increase pressure by triggering malfunctions.",
                    "Counter: open the panel quickly and reboot broken modules.",
                    "Golden rule: alternate CAM checks and panel checks, no tunnel vision.",
                ]
                footer_text = "Press ENTER or SPACE to start"

        y = panel.top + 140
        for text in lines:
            label = self.font_small.render(text, True, (230, 236, 224))
            self.screen.blit(label, (panel.left + 44, y))
            y += 58

        footer = self.font_hour.render(footer_text, True, (173, 227, 113))
        self.screen.blit(footer, footer.get_rect(center=(panel.centerx, panel.bottom - 66)))
        skip_tutorial = self.font_small.render(self.tr("tutorial.skip"), True, (182, 220, 138))
        skip_tutorial = pygame.transform.smoothscale(
            skip_tutorial,
            (max(1, int(skip_tutorial.get_width() * 0.82)), max(1, int(skip_tutorial.get_height() * 0.82))),
        )
        self.screen.blit(skip_tutorial, skip_tutorial.get_rect(center=(panel.centerx, panel.bottom - 14)))

    def draw_night_outro(self):
        elapsed = pygame.time.get_ticks() - self.outro_start_time
        if elapsed >= self.outro_duration_ms:
            self.enter_menu(play_click=True)

        self.screen.fill((0, 0, 0))
        completed_night = getattr(self, "last_completed_night", max(1, self.current_night - 1))
        title = self.font_night.render(self.tr("ui.night", night=completed_night), True, (235, 235, 235))
        desc = self.font_night.render(self.tr("ui.night_cleared"), True, (235, 235, 235))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 40)))
        self.screen.blit(desc, desc.get_rect(center=(self.width // 2, self.height // 2 + 38)))

    def draw_game(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_x, _ = mouse_pos
        admin_mode = self.video_camere.is_admin_mode()
        now_ms = pygame.time.get_ticks()
        self._sync_current_night_call()
        self._update_reboots(now_ms)
        self.maybe_trigger_random_system_error(now_ms=now_ms, allow_when_admin_paused=False)

        if now_ms >= getattr(self, "_vent_move_sound_until", 0):
            self.audio.stop_loop_sound(getattr(self, "vent_enter_sound", "assets/audio/vents.wav"))

        if admin_mode and not self._admin_pause_active:
            self.orologio.pause(now_ms)
            self._admin_pause_started_at = now_ms
            self._admin_pause_active = True
        elif not admin_mode and self._admin_pause_active:
            delta_ms = max(0, now_ms - getattr(self, "_admin_pause_started_at", now_ms))
            self._shift_gameplay_timers(delta_ms)
            self.orologio.resume(now_ms)
            self._admin_pause_active = False

        if not self.video_camere.is_open and not self.system_panel.is_open and not admin_mode:
            self.camera.update_from_cursor(mouse_x)
        cam_x = self.camera.get_offset_x()
        is_right_full = cam_x >= int(self.camera.max_offset * 0.9)
        is_left_full = cam_x <= int(self.camera.max_offset * 0.1)
        self.video_camere.set_trigger_visible(self.video_camere.is_open or is_right_full)
        self.video_camere.set_trigger_interactable(self.video_camere.is_open or is_right_full)
        self.system_panel.set_trigger_visible(self.system_panel.is_open or is_left_full)
        self.system_panel.set_trigger_interactable(self.system_panel.is_open or is_left_full)

        self.screen.blit(self.game_background, (-cam_x, 0))

        self._draw_error_alert_overlay(now_ms)

        self.video_camere.set_camera_error(self.system_errors.get("camera", False))
        self.video_camere.set_vent_blocking_enabled(not self.system_errors.get("ventilation", False))
        # Keep VideoCamere as the source of truth for live vent toggle interactions.
        self.blocked_vent_cameras = self.video_camere.get_blocked_vent_edges()

        now_ms = pygame.time.get_ticks()
        if self.system_errors.get("flashlight", False):
            self.flashlight_active = False
        if self.system_panel.is_open and self.flashlight_active:
            self.flashlight_active = False
            self.flashlight_repel_triggered = False
            self.flashlight_repelled_targets.clear()

        if not admin_mode:
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
                    self.audio.play_sound(self.flashlight_repel_sound, volume=0.45)
                    self.audio.play_sound(self.flashlight_hit_sound, volume=0.55)

        label = self.orologio.get_label() if admin_mode else self.orologio.update(now_ms)
        hour_index = getattr(self.orologio, "hour_index", 0)

        watched_camera = self.video_camere.get_selected_camera_id() if self.video_camere.is_open else None
        viewed_office_side = None
        if (not admin_mode) and (not self.video_camere.is_open) and (not self.system_panel.is_open):
            # Error-type at the office door should react only if the player is looking at that side.
            left_threshold = int(self.camera.max_offset * 0.35)
            right_threshold = int(self.camera.max_offset * 0.65)
            if cam_x <= left_threshold:
                viewed_office_side = "left"
            elif cam_x >= right_threshold:
                viewed_office_side = "right"

        player_can_defend = self.flashlight_ready or self.flashlight_active
        if not admin_mode:
            events = self.animatronics.update(
                now_ms=now_ms,
                night_level=self.current_night,
                hour_index=hour_index,
                watched_camera=watched_camera,
                viewed_office_side=viewed_office_side,
                blocked_vent_cameras=self.blocked_vent_cameras,
                player_can_defend=player_can_defend,
                active_system_errors={name for name, active in self.system_errors.items() if active},
            )

            for event in events:
                if event.get("type") == "moved":
                    mover_name = str(event.get("name", ""))
                    self.video_camere.register_movement(
                        from_camera=event.get("from"),
                        to_camera=event.get("to"),
                        jam_duration_ms=2200,
                    )
                    to_camera = str(event.get("to", ""))
                    if to_camera in ("door_left", "door_right"):
                        anim_data = self.animatronics.animatronics.get(mover_name)
                        if anim_data is not None and not anim_data.can_trigger_error:
                            sound_path = getattr(self, "office_entry_sounds", {}).get(mover_name)
                            if sound_path:
                                last_by_name = getattr(self, "_last_office_entry_sound_at", {})
                                last_at = int(last_by_name.get(mover_name, 0) or 0)
                                if now_ms - last_at >= getattr(self, "_office_entry_sound_cooldown_ms", 1000):
                                    self.audio.play_sound(
                                        sound_path,
                                        volume=getattr(self, "office_entry_sound_volume", 0.62),
                                    )
                                    last_by_name[mover_name] = now_ms
                                    self._last_office_entry_sound_at = last_by_name
                    if to_camera.startswith("cam"):
                        try:
                            to_idx = int(to_camera.replace("cam", ""))
                        except ValueError:
                            to_idx = -1
                        if 11 <= to_idx <= 15:
                            if now_ms - getattr(self, "_last_vent_enter_sound_at", 0) >= getattr(self, "_vent_enter_sound_cooldown_ms", 500):
                                self.audio.start_loop_sound(getattr(self, "vent_enter_sound", "assets/audio/vents.wav"), volume=0.8)
                                self._vent_move_sound_until = now_ms + 550
                                self._last_vent_enter_sound_at = now_ms
                if event.get("type") == "jumpscare":
                    self.enter_jumpscare(event.get("name", "Sconosciuto"))
                    return
                if event.get("type") == "system_error":
                    errors = event.get("errors")
                    if not isinstance(errors, list) or not errors:
                        one_error = event.get("error", "camera")
                        errors = [one_error]
                    self.enter_error_jumpscare(
                        event.get("name", "Sconosciuto"),
                        errors,
                    )
                    return

        positions = self.animatronics.get_positions(now_ms=now_ms)
        threat_cameras = self.animatronics.get_cameras_with_presence(now_ms=now_ms)
        self.video_camere.set_threat_cameras(threat_cameras)

        # Mostra tutti i nemici presenti nella camera corrente con sprite distinti.
        threats_by_camera = {}
        for name, camera_id in positions.items():
            if camera_id in ("door_left", "door_right"):
                continue
            camera_slots = [camera_id]

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

        if (not admin_mode) and (not self.flashlight_ready) and now_ms >= self.flashlight_cooldown_until:
            self.flashlight_ready = True

        clock_text = self.font_hour.render(label, True, (235, 235, 235))
        self.screen.blit(clock_text, clock_text.get_rect(topright=(self.width - 30, 24)))
        night_text = self.font_small.render(self.tr("ui.night", night=self.current_night), True, (235, 235, 235))
        self.screen.blit(night_text, night_text.get_rect(topright=(self.width - 34, 94)))

        if self.system_errors.get("flashlight", False):
            indicator_text = self.tr("ui.flashlight_error")
            indicator_color = (255, 80, 80)
        elif self.flashlight_active:
            indicator_text = self.tr("ui.flashlight_active")
            indicator_color = (80, 255, 80)
        elif self.flashlight_ready:
            indicator_text = self.tr("ui.flashlight_ready")
            indicator_color = (80, 80, 255)
        else:
            remaining_ms = max(0, self.flashlight_cooldown_until - now_ms)
            indicator_text = self.tr("ui.flashlight_cooldown", seconds=(remaining_ms / 1000.0))
            indicator_color = (255, 80, 80)

        indicator_label = self.font_small.render(indicator_text, True, indicator_color)
        indicator_rect = indicator_label.get_rect(topleft=(24, 24))
        self.screen.blit(indicator_label, indicator_rect)
        if getattr(self, "current_night_call_path", None):
            self._draw_mute_call_button(indicator_rect)
        else:
            self.call_mute_button_rect = pygame.Rect(0, 0, 0, 0)

        left_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_left"]
        right_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_right"]
        if left_door_threats:
            self._draw_door_threats(left_door_threats, cam_x, side="left")
        if right_door_threats:
            self._draw_door_threats(right_door_threats, cam_x, side="right")

        self.video_camere.update_hover(mouse_pos)
        self.system_panel.update_hover(mouse_pos)
        self.video_camere.draw_overlay(self.screen, self)
        self.system_panel.draw_overlay(self.screen, self.system_errors, self.system_reboots, now_ms, self)
        self.system_panel.queue_trigger(self)
        self.video_camere.queue_trigger(self)
        draw_graphic_elements(self.screen)

        if (not admin_mode) and now_ms < self.flashlight_repel_feedback_until:
            self._draw_flashlight_repel_feedback(now_ms)

        if (not admin_mode) and self.orologio.is_finished():
            self.last_completed_night = self.current_night
            if self.current_night < getattr(self, "max_night", 5):
                self.current_night += 1
            else:
                self.current_night = getattr(self, "max_night", 5)
            self.can_continue = True
            self.exit_night()
            return

    def draw_jumpscare(self):
        now_ms = pygame.time.get_ticks()
        elapsed = now_ms - self.jumpscare_start_time
        if elapsed >= self.jumpscare_duration_ms:
            self._stop_jumpscare_media()
            if getattr(self, "jumpscare_continue_game", False):
                self._shift_gameplay_timers(max(0, now_ms - self.jumpscare_start_time))
                pending_error = getattr(self, "jumpscare_pending_error", None)
                if pending_error:
                    self.animatronics.on_error_jumpscare_finished(now_ms, getattr(self, "jumpscare_name", None))
                    if isinstance(pending_error, (list, tuple, set)):
                        for err_name in pending_error:
                            self.trigger_system_error(str(err_name))
                    else:
                        self.trigger_system_error(str(pending_error))
                self._start_gameplay_ambience()
                self.jumpscare_continue_game = False
                self.jumpscare_pending_error = None
                self.state = "game"
                return
            self._start_defeat_video()
            return

        self.screen.fill((0, 0, 0))

        frame_surface = None

        if self.jumpscare_video_cap is not None:
            frame_surface = self._read_synced_video_frame(
                self.jumpscare_video_cap,
                self.jumpscare_start_time,
                now_ms,
            )
            self.jumpscare_last_frame_at = now_ms
            if frame_surface is not None:
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
            scaled = pygame.transform.scale(frame_surface, (self.width, self.height))

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
            self._draw_end_video_label("GAME OVER", (255, 90, 90))
            info = self.font_small.render(self.tr("ui.video_unavailable"), True, (255, 120, 120))
            self.screen.blit(info, info.get_rect(center=(self.width // 2, self.height // 2)))
            if now_ms - self.defeat_video_started_at >= 1500:
                self.enter_menu(play_click=False)
            return

        frame_surface = self._read_synced_video_frame(
            self.defeat_video_cap,
            self.defeat_video_started_at,
            now_ms,
        )
        self.defeat_video_last_frame_at = now_ms

        if frame_surface is None:
            # Allow a brief startup grace period for decoder warm-up.
            if now_ms - self.defeat_video_started_at < 550:
                self.screen.fill((0, 0, 0))
                self._draw_end_video_label("GAME OVER", (255, 90, 90))
                return
            self.enter_menu(play_click=False)
            return

        self.screen.blit(frame_surface, (0, 0))
        self._draw_end_video_label("GAME OVER", (255, 90, 90))

    def draw_victory_video(self):
        now_ms = pygame.time.get_ticks()

        if self.victory_video_cap is None:
            self.screen.fill((0, 0, 0))
            self._draw_end_video_label(self.tr("ui.victory"), (120, 255, 150))
            info = self.font_small.render(self.tr("ui.victory_video_unavailable"), True, (120, 255, 120))
            self.screen.blit(info, info.get_rect(center=(self.width // 2, self.height // 2)))
            if now_ms - self.victory_video_started_at >= 1500:
                self.enter_menu(play_click=False)
            return

        frame_surface = self._read_synced_video_frame(
            self.victory_video_cap,
            self.victory_video_started_at,
            now_ms,
        )
        self.victory_video_last_frame_at = now_ms

        if frame_surface is None:
            # Allow a brief startup grace period for decoder warm-up.
            if now_ms - self.victory_video_started_at < 550:
                self.screen.fill((0, 0, 0))
                self._draw_end_video_label(self.tr("ui.victory"), (120, 255, 150))
                return
            self.enter_menu(play_click=False)
            return

        self.screen.blit(frame_surface, (0, 0))
        self._draw_end_video_label(self.tr("ui.victory"), (120, 255, 150))

    def draw_endgame_video(self):
        now_ms = pygame.time.get_ticks()

        if self.endgame_video_cap is None:
            self.screen.fill((0, 0, 0))
            self._draw_end_video_label("ENDGAME", (255, 220, 120))
            info = self.font_small.render(self.tr("ui.endgame_video_unavailable"), True, (255, 220, 120))
            self.screen.blit(info, info.get_rect(center=(self.width // 2, self.height // 2)))
            skip_hint = self.font_small.render(self.tr("ui.press_e_skip"), True, (245, 220, 170))
            self.screen.blit(skip_hint, skip_hint.get_rect(bottomright=(self.width - 26, self.height - 24)))
            if now_ms - self.endgame_video_started_at >= 1500:
                self._start_credits_video()
            return

        frame_surface = self._read_synced_video_frame(
            self.endgame_video_cap,
            self.endgame_video_started_at,
            now_ms,
        )
        self.endgame_video_last_frame_at = now_ms

        if frame_surface is None:
            if now_ms - self.endgame_video_started_at < 550:
                self.screen.fill((0, 0, 0))
                self._draw_end_video_label("ENDGAME", (255, 220, 120))
                return
            self._start_credits_video()
            return

        self.screen.blit(frame_surface, (0, 0))
        self._draw_end_video_label("ENDGAME", (255, 220, 120))
        skip_hint = self.font_small.render(self.tr("ui.press_e_skip"), True, (245, 220, 170))
        self.screen.blit(skip_hint, skip_hint.get_rect(bottomright=(self.width - 26, self.height - 24)))

    def draw_credits_video(self):
        draw_credits_video_screen(self)

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
