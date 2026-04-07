import sys
import traceback
import json
import os
import random

import pygame

try:
    import cv2
except Exception:
    cv2 = None


class GameFlowMixin:
    def _stop_system_loop_sounds(self):
        self.audio.stop_loop_sound(getattr(self, "system_reboot_sound", "assets/audio/reboot.wav"))
        self.audio.stop_loop_sound(getattr(self, "system_error_sound", "assets/audio/error.wav"))

    def _update_error_loop_sound(self):
        sound_file = getattr(self, "system_error_sound", "assets/audio/error.wav")
        if any(bool(v) for v in self.system_errors.values()):
            self.audio.start_loop_sound(sound_file, volume=0.6)
        else:
            self.audio.stop_loop_sound(sound_file)

    def _start_gameplay_ambience(self):
        self.audio.play_music(
            music_file=getattr(self, "gameplay_ambience_music", "assets/audio/ambience.wav"),
            loop=True,
            volume=getattr(self, "gameplay_ambience_volume", 0.28),
            fade_ms=300,
        )

    def _stop_gameplay_ambience(self, fade_ms=None):
        self.audio.stop_music(fade_ms=getattr(self, "music_fade_ms", 800) if fade_ms is None else fade_ms)

    def _schedule_next_random_error(self, now_ms=None):
        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        min_ms = int(getattr(self, "random_error_min_interval_ms", 18000))
        max_ms = int(getattr(self, "random_error_max_interval_ms", 32000))
        if max_ms < min_ms:
            min_ms, max_ms = max_ms, min_ms
        self.next_random_system_error_at = now_ms + random.randint(max(1000, min_ms), max(1000, max_ms))

    def maybe_trigger_random_system_error(self, now_ms=None, allow_when_admin_paused=False):
        if not bool(getattr(self, "random_system_errors_enabled", True)):
            return False

        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        if not allow_when_admin_paused and bool(getattr(self, "_admin_pause_active", False)):
            return False

        next_at = int(getattr(self, "next_random_system_error_at", 0) or 0)
        if next_at <= 0:
            self._schedule_next_random_error(now_ms)
            return False
        if now_ms < next_at:
            return False

        if random.random() > float(getattr(self, "random_error_trigger_chance", 0.58)):
            self._schedule_next_random_error(now_ms)
            return False

        available_errors = [name for name, active in self.system_errors.items() if not active]
        if not available_errors:
            self._schedule_next_random_error(now_ms)
            return False

        weights_by_count = dict(getattr(self, "random_error_multi_weights", {1: 0.84, 2: 0.13, 3: 0.03}) or {})
        max_count = min(len(available_errors), 3)
        roll = random.random()
        acc = 0.0
        count = 1
        for candidate in range(1, max_count + 1):
            acc += float(weights_by_count.get(candidate, 0.0))
            if roll <= acc:
                count = candidate
                break

        picked_errors = random.sample(available_errors, k=count)
        for error_type in picked_errors:
            self.trigger_system_error(error_type)
        self._schedule_next_random_error(now_ms)
        return True

    def _is_rebooting(self, error_type, now_ms=None):
        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        return now_ms < int(self.system_reboots.get(error_type, 0) or 0)

    def _is_any_rebooting(self, now_ms=None):
        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        return any(now_ms < int(v or 0) for v in self.system_reboots.values())

    def _start_reboot(self, error_type, now_ms=None):
        if error_type not in self.system_errors:
            return
        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        self.system_reboots[error_type] = now_ms + int(getattr(self, "system_reboot_duration_ms", 5000))

    def _restart_active_reboots(self, now_ms=None):
        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        duration = int(getattr(self, "system_reboot_duration_ms", 5000))
        for error_type, until in list(self.system_reboots.items()):
            if now_ms < int(until or 0):
                self.system_reboots[error_type] = now_ms + duration

    def _cancel_active_reboots(self, now_ms=None):
        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        had_active = False
        for error_type, until in list(self.system_reboots.items()):
            if now_ms < int(until or 0):
                self.system_reboots[error_type] = 0
                # Keep the subsystem in error state: user must start reboot again from scratch.
                self.system_errors[error_type] = True
                had_active = True

        if had_active:
            self.audio.stop_loop_sound(getattr(self, "system_reboot_sound", "assets/audio/reboot.wav"))
            self._update_error_loop_sound()

    def _update_reboots(self, now_ms=None):
        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        for error_type, until in list(self.system_reboots.items()):
            until = int(until or 0)
            if until <= 0 or now_ms < until:
                continue
            self.system_reboots[error_type] = 0
            self.system_errors[error_type] = False
            if error_type == "camera":
                self.video_camere.set_camera_error(False)
            elif error_type == "ventilation":
                self.video_camere.set_vent_blocking_enabled(True)

        self._update_error_loop_sound()

        if self._is_any_rebooting(now_ms):
            self.audio.start_loop_sound(getattr(self, "system_reboot_sound", "assets/audio/reboot.wav"), volume=0.9)
        else:
            self.audio.stop_loop_sound(getattr(self, "system_reboot_sound", "assets/audio/reboot.wav"))

    def reset_system_errors(self):
        self.system_errors = {
            "camera": False,
            "ventilation": False,
            "flashlight": False,
        }
        self.system_reboots = {
            "camera": 0,
            "ventilation": 0,
            "flashlight": 0,
        }
        self.blocked_vent_cameras.clear()
        self.video_camere.set_camera_error(False)
        self.video_camere.set_vent_blocking_enabled(True)
        self.video_camere.set_blocked_vents(self.blocked_vent_cameras)
        self._stop_system_loop_sounds()
        self.audio.stop_loop_sound(getattr(self, "vent_enter_sound", "assets/audio/vents.wav"))
        self._schedule_next_random_error()

    def trigger_system_error(self, error_type):
        if error_type not in self.system_errors:
            return
        self.system_errors[error_type] = True
        self._update_error_loop_sound()
        if error_type == "camera":
            self.video_camere.set_camera_error(True)
        elif error_type == "ventilation":
            self.video_camere.set_vent_blocking_enabled(False)
            # Ventilation failure forces all vents open immediately.
            self.blocked_vent_cameras.clear()
            self.video_camere.set_blocked_vent_edges(set())
        elif error_type == "flashlight":
            self.flashlight_active = False

    def handle_system_panel_action(self, action):
        now_ms = pygame.time.get_ticks()
        self._update_reboots(now_ms)

        if action in ("reboot_camera", "reboot_ventilation", "reboot_flashlight", "reboot_all") and self._is_any_rebooting(now_ms):
            # A reboot is already running: ignore further reboot requests until completion.
            return

        if action in ("reboot_camera", "reboot_ventilation", "reboot_flashlight", "reboot_all"):
            if now_ms - getattr(self, "_last_reboot_sound_at", 0) >= getattr(self, "_reboot_sound_cooldown_ms", 300):
                self.audio.play_sound(getattr(self, "system_reboot_sound", "assets/audio/reboot.wav"), volume=0.9)
                self._last_reboot_sound_at = now_ms
            self.audio.start_loop_sound(getattr(self, "system_reboot_sound", "assets/audio/reboot.wav"), volume=0.9)

        if action == "reboot_camera":
            self._start_reboot("camera", now_ms)
        elif action == "reboot_ventilation":
            self._start_reboot("ventilation", now_ms)
        elif action == "reboot_flashlight":
            self._start_reboot("flashlight", now_ms)
        elif action == "reboot_all":
            self._start_reboot("camera", now_ms)
            self._start_reboot("ventilation", now_ms)
            self._start_reboot("flashlight", now_ms)
        elif action == "reboot_lock_close_attempt":
            self._restart_active_reboots(now_ms)
            self.system_panel.is_open = True
        elif action == "reboot_reset_close":
            self._cancel_active_reboots(now_ms)
            self.system_panel.is_open = False
        elif action == "exit":
            self.system_panel.is_open = False

    def _shift_gameplay_timers(self, delta_ms):
        if delta_ms <= 0:
            return
        self.flashlight_activation_time += delta_ms
        self.flashlight_cooldown_until += delta_ms
        self.flashlight_repel_feedback_until += delta_ms
        self._vent_move_sound_until += delta_ms
        self._last_vent_enter_sound_at += delta_ms
        self._last_system_error_sound_at += delta_ms
        self._last_reboot_sound_at += delta_ms
        self.animatronics.shift_timers(delta_ms)

    def _clamp_night(self, night_value):
        try:
            night_int = int(night_value)
        except (TypeError, ValueError):
            night_int = 1
        max_night = max(1, int(getattr(self, "max_night", 5)))
        return max(1, min(max_night, night_int))

    def _get_progress_save_path(self):
        return getattr(self, "progress_save_path", os.path.join(os.getcwd(), "savegame.json"))

    def _load_progress(self):
        data = self._read_progress_data()
        completed = bool(data.get("completed", False)) if data else False
        self.current_night = self._clamp_night(data.get("next_night", 1)) if not completed else 1
        self.can_continue = bool(data) and not completed
        return data

    def _read_progress_data(self):
        save_path = self._get_progress_save_path()
        if not os.path.isfile(save_path):
            return {}

        try:
            with open(save_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError, json.JSONDecodeError):
            return {}

        if not isinstance(payload, dict):
            return {}

        return payload

    def save_progress(self, next_night=None, completed=False):
        save_path = self._get_progress_save_path()
        progress = {
            "schema_version": 1,
            "next_night": self._clamp_night(next_night if next_night is not None else getattr(self, "current_night", 1)),
            "completed": bool(completed),
            "updated_at_ms": pygame.time.get_ticks(),
        }

        try:
            with open(save_path, "w", encoding="utf-8") as handle:
                json.dump(progress, handle, ensure_ascii=True, indent=2)
        except OSError:
            return False

        self.can_continue = True
        return True

    def _resolve_jumpscare_data(self, name):
        if not getattr(self, "jumpscare_assets", None):
            return None

        if name in self.jumpscare_assets:
            return self.jumpscare_assets[name]

        lowered_name = (name or "").lower().replace(" ", "")
        for key, data in self.jumpscare_assets.items():
            key_norm = key.lower().replace(" ", "")
            if key_norm == lowered_name or lowered_name in key_norm or key_norm in lowered_name:
                return data
        return None

    def _stop_jumpscare_media(self):
        if getattr(self, "jumpscare_video_cap", None) is not None:
            try:
                self.jumpscare_video_cap.release()
            except Exception:
                pass

        if getattr(self, "jumpscare_audio_started", False):
            self.audio.stop_music()

        self.jumpscare_video_cap = None
        self.jumpscare_video_path = None
        self.jumpscare_audio_path = None
        self.jumpscare_frames = []
        self.jumpscare_audio_started = False
        self.jumpscare_last_frame_at = 0
        self.jumpscare_last_surface = None
        self.jumpscare_shake_strength = 0

    def run(self):
        running = True
        while running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        continue
                    self.handle_event(event)

                self.update_and_draw()
                self.draw_custom_cursor()
                pygame.display.flip()
                self.clock.tick(60)
                self.error_message = None
            except Exception as exc:
                self.error_message = f"Errore: {exc}"
                traceback.print_exc()

        pygame.quit()
        sys.exit()

    def update_and_draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "loading":
            self.draw_loading_screen()
        elif self.state == "night_intro":
            self.draw_night_intro()
        elif self.state == "night_tutorial":
            self.draw_night_tutorial()
        elif self.state == "night_outro":
            self.draw_night_outro()
        elif self.state == "jumpscare":
            self.draw_jumpscare()
        elif self.state == "defeat_video":
            self.draw_defeat_video()
        elif self.state == "victory_video":
            self.draw_victory_video()
        elif self.state == "endgame_video":
            self.draw_endgame_video()
        elif self.state == "credits_video":
            self.draw_credits_video()
        elif self.state == "game":
            self.draw_game()

    def _enter_night_intro(self):
        self.audio.play_sound(self.button_sound, volume=0.8)
        self.audio.stop_music(fade_ms=self.music_fade_ms)
        self.audio.play_sound(getattr(self, "night_start_sound", "assets/audio/night_start.wav"), volume=0.95)
        self.intro_start_time = pygame.time.get_ticks()
        self.state = "night_intro"

    def _start_loading_screen(self, next_action, message=None, duration_ms=1000):
        self.loading_message = str(message or self.tr("loading.default"))
        self.loading_started_at = pygame.time.get_ticks()
        self.loading_duration_ms = max(200, int(duration_ms))
        self.loading_next_action = next_action
        self.state = "loading"

    def start_new_game(self):
        self.current_night = 1
        self.last_completed_night = 0
        self.first_night_tutorial_seen = False
        self.save_progress(next_night=self.current_night)
        self._start_loading_screen(
            next_action=self._enter_night_intro,
            message=self.tr("loading.night", night=self.current_night),
            duration_ms=900,
        )

    def continue_game(self):
        self._load_progress()
        if not self.can_continue:
            return
        self._start_loading_screen(
            next_action=self._enter_night_intro,
            message=self.tr("loading.resume", night=self.current_night),
            duration_ms=900,
        )

    def enter_game(self):
        # Backward-compatible alias.
        self.start_new_game()

    def _enter_first_night_tutorial(self):
        self.first_night_tutorial_seen = True
        self.tutorial_started_at = pygame.time.get_ticks()
        self.tutorial_page = 0
        self.state = "night_tutorial"

    def start_gameplay(self):
        if self.current_night == 1 and not bool(getattr(self, "first_night_tutorial_seen", False)):
            self._enter_first_night_tutorial()
            return
        self._start_loading_screen(
            next_action=self._begin_gameplay_session,
            message=self.tr("loading.prepare"),
            duration_ms=850,
        )

    def _begin_gameplay_session(self):
        self._stop_jumpscare_media()
        self.state = "game"
        self.orologio.start(pygame.time.get_ticks())
        self.reset_system_errors()
        self.system_panel.is_open = False
        self.flashlight_ready = True
        self.flashlight_active = False
        self.flashlight_repel_triggered = False
        self.flashlight_repelled_targets.clear()
        self.flashlight_cooldown_until = 0
        self._vent_move_sound_until = 0
        self.audio.stop_loop_sound(getattr(self, "vent_enter_sound", "assets/audio/vents.wav"))
        self.jumpscare_continue_game = False
        self.jumpscare_pending_error = None
        self.animatronics.set_navigation_graph(self.video_camere.build_navigation_graph())
        self.animatronics.set_routes_by_side(self.video_camere.build_routes_by_side())
        self.animatronics.reset()
        
        now_ms = pygame.time.get_ticks()
        delay_ms = int(getattr(self, "error_animatronic_visibility_delay_ms", 45000))
        self.animatronics.set_error_animatronic_visibility_delay(now_ms, delay_ms, self.current_night)
        
        self.video_camere.set_threat_cameras([])
        self.jumpscare_name = ""
        self.save_progress(next_night=self.current_night)
        self._stop_defeat_video()
        self._stop_victory_video()
        self._start_gameplay_ambience()
        self.video_camere.close()

    def enter_jumpscare(self, name, continue_game=False, pending_error=None):
        self._stop_jumpscare_media()
        self._stop_system_loop_sounds()
        self.jumpscare_name = name
        self.jumpscare_start_time = pygame.time.get_ticks()
        self.jumpscare_continue_game = bool(continue_game)
        self.jumpscare_pending_error = pending_error
        self.jumpscare_duration_ms = 1900
        self.jumpscare_flash_duration_ms = 230
        self.jumpscare_shake_duration_ms = 900
        self.jumpscare_shake_strength = 34

        jumpscare_data = self._resolve_jumpscare_data(name)
        if jumpscare_data is not None:
            self.jumpscare_video_path = jumpscare_data.get("video")
            self.jumpscare_audio_path = jumpscare_data.get("audio")
            self.jumpscare_frames = list(jumpscare_data.get("frames", []))

        if self.jumpscare_video_path and cv2 is not None:
            try:
                self.jumpscare_video_cap = cv2.VideoCapture(self.jumpscare_video_path)
                if not self.jumpscare_video_cap.isOpened():
                    self.jumpscare_video_cap = None
                else:
                    frame_count = float(self.jumpscare_video_cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
                    if frame_count > 1.0:
                        fps = float(self.jumpscare_video_cap.get(cv2.CAP_PROP_FPS) or 0.0)
                        if not (20.0 <= fps <= 120.0):
                            fps = 30.0
                        est_ms = int((frame_count / fps) * 1000)
                        self.jumpscare_duration_ms = max(1000, min(8000, est_ms))
            except Exception:
                self.jumpscare_video_cap = None

        if self.jumpscare_video_cap is None and self.jumpscare_frames:
            est_ms = len(self.jumpscare_frames) * 80
            self.jumpscare_duration_ms = max(1000, min(5000, est_ms))

        audio_source = None
        if self.jumpscare_audio_path and os.path.isfile(self.jumpscare_audio_path):
            audio_source = self.jumpscare_audio_path
        elif self.jumpscare_video_path and os.path.isfile(self.jumpscare_video_path):
            audio_source = self.jumpscare_video_path

        if audio_source:
            self.jumpscare_audio_started = self.audio.play_music(
                music_file=audio_source,
                loop=False,
                volume=1.0,
            )

        self.state = "jumpscare"

    def enter_error_jumpscare(self, name, error_type):
        self.enter_jumpscare(name=name, continue_game=True, pending_error=error_type)

    def _start_defeat_video(self):
        self._stop_jumpscare_media()
        self._stop_system_loop_sounds()
        self._stop_defeat_video()
        self.defeat_video_started_at = pygame.time.get_ticks()
        self.defeat_video_last_frame_at = 0
        self.defeat_video_path = None
        self.defeat_video_audio_started = False

        for candidate in getattr(self, "defeat_video_candidates", []):
            if os.path.isfile(candidate):
                self.defeat_video_path = candidate
                break

        if self.defeat_video_path and cv2 is not None:
            try:
                self.defeat_video_cap = cv2.VideoCapture(self.defeat_video_path)
                if not self.defeat_video_cap.isOpened():
                    self.defeat_video_cap = None
                else:
                    # Calculate frame delay based on video FPS
                    fps = float(self.defeat_video_cap.get(cv2.CAP_PROP_FPS) or 0.0)
                    if fps > 0:
                        self.defeat_video_frame_delay_ms = int(1000.0 / fps)
                    else:
                        self.defeat_video_frame_delay_ms = 33
            except Exception:
                self.defeat_video_cap = None

        # Prova prima a usare direttamente il file video come sorgente audio.
        if self.defeat_video_path:
            self.defeat_video_audio_started = self.audio.play_music(
                music_file=self.defeat_video_path,
                loop=False,
                volume=1.0,
            )

        # Fallback: usa un file audio dedicato con stesso contenuto del video.
        if not self.defeat_video_audio_started:
            for candidate in getattr(self, "defeat_video_audio_candidates", []):
                if not os.path.isfile(candidate):
                    continue
                self.defeat_video_audio_started = self.audio.play_music(
                    music_file=candidate,
                    loop=False,
                    volume=1.0,
                )
                if self.defeat_video_audio_started:
                    break

        self.state = "defeat_video"

    def _stop_defeat_video(self):
        if self.defeat_video_cap is not None:
            try:
                self.defeat_video_cap.release()
            except Exception:
                pass
        if self.defeat_video_audio_started:
            self.audio.stop_music()
        self.defeat_video_cap = None
        self.defeat_video_path = None
        self.defeat_video_audio_started = False

    def _start_victory_video(self):
        self._stop_victory_video()
        self._stop_system_loop_sounds()
        self.victory_video_started_at = pygame.time.get_ticks()
        self.victory_video_last_frame_at = 0
        self.victory_video_path = None
        self.victory_video_audio_started = False

        for candidate in getattr(self, "victory_video_candidates", []):
            if os.path.isfile(candidate):
                self.victory_video_path = candidate
                break

        if self.victory_video_path and cv2 is not None:
            try:
                self.victory_video_cap = cv2.VideoCapture(self.victory_video_path)
                if not self.victory_video_cap.isOpened():
                    self.victory_video_cap = None
                else:
                    # Calculate frame delay based on video FPS
                    fps = float(self.victory_video_cap.get(cv2.CAP_PROP_FPS) or 0.0)
                    if fps > 0:
                        self.victory_video_frame_delay_ms = int(1000.0 / fps)
                    else:
                        self.victory_video_frame_delay_ms = 33
            except Exception:
                self.victory_video_cap = None

        if self.victory_video_path:
            self.victory_video_audio_started = self.audio.play_music(
                music_file=self.victory_video_path,
                loop=False,
                volume=1.0,
            )

        if not self.victory_video_audio_started:
            for candidate in getattr(self, "victory_video_audio_candidates", []):
                if not os.path.isfile(candidate):
                    continue
                self.victory_video_audio_started = self.audio.play_music(
                    music_file=candidate,
                    loop=False,
                    volume=1.0,
                )
                if self.victory_video_audio_started:
                    break

        self.state = "victory_video"

    def _stop_victory_video(self):
        if self.victory_video_cap is not None:
            try:
                self.victory_video_cap.release()
            except Exception:
                pass
        if self.victory_video_audio_started:
            self.audio.stop_music()
        self.victory_video_cap = None
        self.victory_video_path = None
        self.victory_video_audio_started = False

    def _start_endgame_video(self):
        self._stop_endgame_video()
        self._stop_system_loop_sounds()
        self.endgame_video_started_at = pygame.time.get_ticks()
        self.endgame_video_last_frame_at = 0
        self.endgame_video_path = None
        self.endgame_video_audio_started = False

        for candidate in getattr(self, "endgame_video_candidates", []):
            if os.path.isfile(candidate):
                self.endgame_video_path = candidate
                break

        if self.endgame_video_path and cv2 is not None:
            try:
                self.endgame_video_cap = cv2.VideoCapture(self.endgame_video_path)
                if not self.endgame_video_cap.isOpened():
                    self.endgame_video_cap = None
                else:
                    fps = float(self.endgame_video_cap.get(cv2.CAP_PROP_FPS) or 0.0)
                    if fps > 0:
                        self.endgame_video_frame_delay_ms = int(1000.0 / fps)
                    else:
                        self.endgame_video_frame_delay_ms = 33
            except Exception:
                self.endgame_video_cap = None

        if self.endgame_video_path:
            self.endgame_video_audio_started = self.audio.play_music(
                music_file=self.endgame_video_path,
                loop=False,
                volume=1.0,
            )

        if not self.endgame_video_audio_started:
            for candidate in getattr(self, "endgame_video_audio_candidates", []):
                if not os.path.isfile(candidate):
                    continue
                self.endgame_video_audio_started = self.audio.play_music(
                    music_file=candidate,
                    loop=False,
                    volume=1.0,
                )
                if self.endgame_video_audio_started:
                    break

        self.state = "endgame_video"

    def _stop_endgame_video(self):
        if self.endgame_video_cap is not None:
            try:
                self.endgame_video_cap.release()
            except Exception:
                pass
        if self.endgame_video_audio_started:
            self.audio.stop_music()
        self.endgame_video_cap = None
        self.endgame_video_path = None
        self.endgame_video_audio_started = False

    def _start_credits_video(self):
        self._stop_credits_video()
        self._stop_system_loop_sounds()
        self.credits_video_started_at = pygame.time.get_ticks()
        self.credits_video_last_frame_at = 0
        self.credits_video_path = None
        self.credits_video_audio_started = False

        for candidate in getattr(self, "credits_video_candidates", []):
            if os.path.isfile(candidate):
                self.credits_video_path = candidate
                break

        if self.credits_video_path and cv2 is not None:
            try:
                self.credits_video_cap = cv2.VideoCapture(self.credits_video_path)
                if not self.credits_video_cap.isOpened():
                    self.credits_video_cap = None
                else:
                    fps = float(self.credits_video_cap.get(cv2.CAP_PROP_FPS) or 0.0)
                    if fps > 0:
                        self.credits_video_frame_delay_ms = int(1000.0 / fps)
                    else:
                        self.credits_video_frame_delay_ms = 33
            except Exception:
                self.credits_video_cap = None

        if self.credits_video_path:
            self.credits_video_audio_started = self.audio.play_music(
                music_file=self.credits_video_path,
                loop=False,
                volume=1.0,
            )

        if not self.credits_video_audio_started:
            for candidate in getattr(self, "credits_video_audio_candidates", []):
                if not os.path.isfile(candidate):
                    continue
                self.credits_video_audio_started = self.audio.play_music(
                    music_file=candidate,
                    loop=False,
                    volume=1.0,
                )
                if self.credits_video_audio_started:
                    break

        self.state = "credits_video"

    def _stop_credits_video(self):
        if self.credits_video_cap is not None:
            try:
                self.credits_video_cap.release()
            except Exception:
                pass
        if self.credits_video_audio_started:
            self.audio.stop_music()
        self.credits_video_cap = None
        self.credits_video_path = None
        self.credits_video_audio_started = False

    def _load_menu_video(self):
        if self.menu_video_cap is not None:
            try:
                self.menu_video_cap.release()
            except Exception:
                pass
        self.menu_video_cap = None
        self.menu_video_path = None
        self.menu_video_last_surface = None
        self.menu_video_last_frame_at = 0

        for candidate in getattr(self, "menu_video_candidates", []):
            if not os.path.isfile(candidate):
                continue
            self.menu_video_path = candidate
            break

        if self.menu_video_path and cv2 is not None:
            try:
                self.menu_video_cap = cv2.VideoCapture(self.menu_video_path)
                if not self.menu_video_cap.isOpened():
                    self.menu_video_cap = None
                else:
                    # Calculate frame delay based on video FPS
                    fps = float(self.menu_video_cap.get(cv2.CAP_PROP_FPS) or 0.0)
                    if fps > 0:
                        self.menu_video_frame_delay_ms = int(1000.0 / fps)
                    else:
                        # Fallback: assume 30 FPS if FPS detection fails
                        self.menu_video_frame_delay_ms = 33
            except Exception:
                self.menu_video_cap = None

    def exit_night(self):
        self.audio.play_sound(self.button_sound, volume=0.8)
        self.audio.stop_music(fade_ms=self.music_fade_ms)
        self._stop_system_loop_sounds()
        if getattr(self, "last_completed_night", 0) >= getattr(self, "max_night", 5):
            self.save_progress(next_night=1, completed=True)
            self.can_continue = False
            self._start_endgame_video()
        else:
            self.save_progress(next_night=self.current_night, completed=False)
            self._start_victory_video()

    def enter_menu(self, play_click=False):
        if play_click:
            self.audio.play_sound(self.button_sound, volume=0.8)
        self._stop_gameplay_ambience(fade_ms=300)
        self.audio.stop_loop_sound(getattr(self, "system_reboot_sound", "assets/audio/reboot.wav"))
        self.audio.stop_loop_sound(getattr(self, "system_error_sound", "assets/audio/error.wav"))
        self.audio.stop_loop_sound(getattr(self, "vent_enter_sound", "assets/audio/vents.wav"))
        self._stop_jumpscare_media()
        self._stop_defeat_video()
        self._stop_victory_video()
        self._stop_endgame_video()
        self._stop_credits_video()
        self.audio.play_music(music_file=self.menu_music, fade_ms=self.music_fade_ms)
        self.video_camere.set_threat_cameras([])
        self.video_camere.close()
        self.system_panel.is_open = False
        self.state = "menu"
        self._load_menu_video()
