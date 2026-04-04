import os

import pygame

from modules.animatronics import build_default_manager
from modules.camera import Camera
from modules.cameras_system import VideoCamere
from modules.flashlight import Flashlight
from modules.game_assets import load_enemy_sprites, load_jumpscare_assets
from modules.game_event_handlers import GameEventHandlersMixin
from modules.game_flow import GameFlowMixin
from modules.game_rendering import GameRenderingMixin
from modules.orario import Orario
from modules.startBackgroudMusic import AudioManager
from modules.system_panel import SystemPanel


class Game(GameFlowMixin, GameEventHandlersMixin, GameRenderingMixin):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.max_night = 5
        self.progress_save_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "savegame.json",
        )

        self.is_fullscreen = False
        self.screen = None
        self._apply_display_mode()
        pygame.display.set_caption("Five Nights at The Corrupted Lab")
        self.clock = pygame.time.Clock()

        self.state = "menu"
        self.current_night = 1
        self.last_completed_night = 0
        self.can_continue = False
        self.error_message = None

        self.animatronics = build_default_manager()
        self.enemy_sprites = load_enemy_sprites()
        self.jumpscare_assets = load_jumpscare_assets()
        self.default_enemy_sprite = self.enemy_sprites.get("Chugginton")
        if self.default_enemy_sprite is None and self.enemy_sprites:
            self.default_enemy_sprite = next(iter(self.enemy_sprites.values()))

        self.jumpscare_name = ""
        self.jumpscare_start_time = 0
        self.jumpscare_duration_ms = 1900
        self.jumpscare_video_path = None
        self.jumpscare_audio_path = None
        self.jumpscare_frames = []
        self.jumpscare_video_cap = None
        self.jumpscare_audio_started = False
        self.jumpscare_last_frame_at = 0
        self.jumpscare_frame_delay_ms = 33
        self.jumpscare_last_surface = None
        self.jumpscare_flash_duration_ms = 230
        self.jumpscare_shake_duration_ms = 900
        self.jumpscare_shake_strength = 34
        self.jumpscare_continue_game = False
        self.jumpscare_pending_error = None

        self.orologio = Orario()

        base_background = pygame.image.load("assets/images/ufficio.webp").convert()
        self.menu_background = pygame.transform.scale(base_background, (self.width, self.height))
        self.game_background = pygame.transform.scale(base_background, (int(self.width * 1.7), self.height))

        self.flashlight = Flashlight(self.width, self.height, radius=120, alpha=200)
        self.camera = Camera(self.width, self.game_background.get_width(), smoothing=0.13)
        self.audio = AudioManager()

        def _pick_font(candidates):
            for name in candidates:
                try:
                    if pygame.font.match_font(name):
                        return name
                except Exception:
                    continue
            return None

        title_font_name = _pick_font(["bahnschrift", "impact", "arial black", "verdana"])
        ui_font_name = _pick_font(["trebuchet ms", "segoe ui", "verdana", "arial"])

        self.font_title = pygame.font.SysFont(title_font_name, 102, bold=True)
        self.font_button = pygame.font.SysFont(ui_font_name, 52, bold=True)
        self.font_night = pygame.font.SysFont(title_font_name, 92, bold=True)
        self.font_hour = pygame.font.SysFont(ui_font_name, 68, bold=True)
        self.font_small = pygame.font.SysFont(ui_font_name, 34)

        self.video_camere = VideoCamere(
            width=self.width,
            height=self.height,
            label_font=self.font_small,
            title_font=self.font_hour,
        )

        self.video_camere.set_trigger_rect(
            x=self.width - 92,
            y=self.height / 2 - 255,
            w=82,
            h=210
        )
        self.video_camere.set_threat_sprite(self.default_enemy_sprite)

        self.system_panel = SystemPanel(
            width=self.width,
            height=self.height,
            label_font=self.font_small,
            title_font=self.font_hour,
        )
        self.system_panel.set_trigger_rect(
            x=18,
            y=self.height - 94,
            w=210,
            h=82,
        )
        self.system_errors = {
            "camera": False,
            "ventilation": False,
            "flashlight": False,
        }
        self.system_reboot_duration_ms = 5000
        self.system_reboots = {
            "camera": 0,
            "ventilation": 0,
            "flashlight": 0,
        }
        self.random_system_errors_enabled = True
        self.random_error_min_interval_ms = 26000
        self.random_error_max_interval_ms = 46000
        self.random_error_trigger_chance = 0.58
        self.random_error_multi_weights = {
            1: 0.84,
            2: 0.13,
            3: 0.03,
        }
        self.next_random_system_error_at = 0
        self.blocked_vent_cameras = set()

        self.error_animatronic_visibility_delay_ms = 45000

        button_width, button_height = 280, 80
        left_x = int(self.width * 0.08)
        self.new_game_button = pygame.Rect(left_x, self.height // 2 - 80, button_width, button_height)
        self.continue_button = pygame.Rect(left_x, self.height // 2 + 15, button_width, button_height)
        self.exit_button = pygame.Rect(left_x, self.height // 2 + 110, button_width, button_height)

        self.menu_music = "assets/audio/menu.wav"
        self.gameplay_ambience_music = "assets/audio/ambience.wav"
        self.button_sound = "assets/audio/pulsanti.wav"
        self.intro_duration_ms = 2600
        self.outro_duration_ms = 2600
        self.music_fade_ms = 800
        self.gameplay_ambience_volume = 0.28

        self.audio.play_music(music_file=self.menu_music)

        self.intro_start_time = 0
        self.outro_start_time = 0
        self.tutorial_started_at = 0
        self.tutorial_page = 0
        self.first_night_tutorial_seen = False

        self.flashlight_ready = True
        self.flashlight_active = False
        self.flashlight_activation_time = 0
        self.flashlight_duration_ms = 1300
        self.flashlight_cooldown_ms = 2500
        self.flashlight_cooldown_until = 0
        self.flashlight_repel_triggered = False
        self.flashlight_repelled_targets = set()
        self.flashlight_repel_feedback_until = 0
        self.flashlight_repel_sound = "assets/audio/switch_cam_sound.wav"
        self.flashlight_hit_sound = "assets/audio/control-shock.wav"
        self.system_error_sound = "assets/audio/error.wav"
        self.vent_enter_sound = "assets/audio/vents.wav"
        self.system_reboot_sound = "assets/audio/reboot.wav"
        self.office_entry_sounds = {
            "McQeen": "assets/audio/mqueen_in_office.wav",
            "Chugginton" : "assets/audio/chugginton_in_office.wav"
        }
        self.office_entry_sound_volume = 0.62
        self._office_entry_sound_cooldown_ms = 1000
        self._last_office_entry_sound_at = {}
        self._last_vent_enter_sound_at = 0
        self._vent_enter_sound_cooldown_ms = 500
        self._last_system_error_sound_at = 0
        self._system_error_sound_cooldown_ms = 450
        self._last_reboot_sound_at = 0
        self._reboot_sound_cooldown_ms = 300
        self._vent_move_sound_until = 0
        self.defeat_video_candidates = [
            os.path.join("assets", "video", "querelato.mp4"),
            "querelato.mp4",
        ]
        self.defeat_video_audio_candidates = [
            os.path.join("assets", "audio", "querelato.wav"),
            os.path.join("assets", "audio", "querelato.mp3"),
            os.path.join("assets", "audio", "querelato.ogg"),
            "querelato.wav",
            "querelato.mp3",
            "querelato.ogg",
        ]
        self.defeat_video_path = None
        self.defeat_video_cap = None
        self.defeat_video_audio_started = False
        self.defeat_video_started_at = 0
        self.defeat_video_last_frame_at = 0
        self.defeat_video_frame_delay_ms = 33
        self.victory_video_candidates = [
            os.path.join("assets", "video", "shimiya.mp4"),
            "shimiya.mp4",
        ]
        self.victory_video_audio_candidates = [
            os.path.join("assets", "audio", "shimiya.wav"),
            os.path.join("assets", "audio", "shimiya.mp3"),
            os.path.join("assets", "audio", "shimiya.ogg"),
            "shimiya.wav",
            "shimiya.mp3",
            "shimiya.ogg",
        ]
        self.victory_video_path = None
        self.victory_video_cap = None
        self.victory_video_audio_started = False
        self.victory_video_started_at = 0
        self.victory_video_last_frame_at = 0
        self.victory_video_frame_delay_ms = 33
        self.endgame_video_candidates = [
            os.path.join("assets", "video", "endgame_scene.mkv"),
            os.path.join("assets", "video", "endgame_scene.mp4"),
            "endgame_scene.mkv",
            "endgame_scene.mp4",
        ]
        self.endgame_video_audio_candidates = [
            os.path.join("assets", "audio", "endgame_scene.wav"),
            os.path.join("assets", "audio", "endgame_scene.mp3"),
            os.path.join("assets", "audio", "endgame_scene.ogg"),
            "endgame_scene.wav",
            "endgame_scene.mp3",
            "endgame_scene.ogg",
        ]
        self.endgame_video_path = None
        self.endgame_video_cap = None
        self.endgame_video_audio_started = False
        self.endgame_video_started_at = 0
        self.endgame_video_last_frame_at = 0
        self.endgame_video_frame_delay_ms = 33
        self.credits_video_candidates = [
            os.path.join("assets", "video", "credits.mkv"),
            os.path.join("assets", "video", "credits.mp4"),
            "credits.mkv",
            "credits.mp4",
        ]
        self.credits_video_audio_candidates = [
            os.path.join("assets", "audio", "credits.wav"),
            os.path.join("assets", "audio", "credits.mp3"),
            os.path.join("assets", "audio", "credits.ogg"),
            "credits.wav",
            "credits.mp3",
            "credits.ogg",
        ]
        self.credits_video_path = None
        self.credits_video_cap = None
        self.credits_video_audio_started = False
        self.credits_video_started_at = 0
        self.credits_video_last_frame_at = 0
        self.credits_video_frame_delay_ms = 33
        self.menu_video_candidates = [
            os.path.join("assets", "video", "menu.mkv"),
            os.path.join("assets", "video", "menu.mp4"),
            "menu.mkv",
            "menu.mp4",
        ]
        self.menu_video_path = None
        self.menu_video_cap = None
        self.menu_video_last_surface = None
        self.menu_video_last_frame_at = 0
        self.menu_video_frame_delay_ms = 33
        self._admin_pause_active = False
        self._admin_pause_started_at = 0

        self._load_progress()
        self._load_menu_video()

    def _apply_display_mode(self):
        flags = pygame.FULLSCREEN if self.is_fullscreen else 0
        self.screen = pygame.display.set_mode((self.width, self.height), flags)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self._apply_display_mode()
