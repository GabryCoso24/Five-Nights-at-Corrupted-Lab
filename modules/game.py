import pygame

from modules.animatronics import build_default_manager
from modules.camera import Camera
from modules.cameras_system import VideoCamere
from modules.flashlight import Flashlight
from modules.game_assets import load_enemy_sprites
from modules.game_event_handlers import GameEventHandlersMixin
from modules.game_flow import GameFlowMixin
from modules.game_rendering import GameRenderingMixin
from modules.orario import Orario
from modules.startBackgroudMusic import AudioManager


class Game(GameFlowMixin, GameEventHandlersMixin, GameRenderingMixin):
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Five Nights at The Corrupted Lab")
        self.clock = pygame.time.Clock()

        self.state = "menu"
        self.current_night = 1
        self.can_continue = False
        self.error_message = None

        self.animatronics = build_default_manager()
        self.enemy_sprites = load_enemy_sprites()
        self.default_enemy_sprite = self.enemy_sprites.get("Chugginton")
        if self.default_enemy_sprite is None and self.enemy_sprites:
            self.default_enemy_sprite = next(iter(self.enemy_sprites.values()))

        self.jumpscare_name = ""
        self.jumpscare_start_time = 0
        self.jumpscare_duration_ms = 1900

        self.orologio = Orario()

        base_background = pygame.image.load("assets/images/ufficio.webp").convert()
        self.menu_background = pygame.transform.scale(base_background, (self.width, self.height))
        self.game_background = pygame.transform.scale(base_background, (int(self.width * 1.7), self.height))

        self.flashlight = Flashlight(self.width, self.height, radius=120, alpha=200)
        self.camera = Camera(self.width, self.game_background.get_width(), smoothing=0.13)
        self.audio = AudioManager()

        self.font_title = pygame.font.SysFont(None, 96)
        self.font_button = pygame.font.SysFont(None, 56)
        self.font_night = pygame.font.SysFont(None, 92)
        self.font_hour = pygame.font.SysFont(None, 68)
        self.font_small = pygame.font.SysFont(None, 36)

        self.video_camere = VideoCamere(
            width=self.width,
            height=self.height,
            label_font=self.font_small,
            title_font=self.font_hour,
        )

        self.video_camere.set_trigger_rect(
            x=self.width - 70,
            y=self.height/2 - 250,
            w=100,
            h=250
        )
        self.video_camere.set_threat_sprite(self.default_enemy_sprite)

        button_width, button_height = 280, 80
        center_x = (self.width - button_width) // 2
        self.new_game_button = pygame.Rect(center_x, self.height // 2 - 80, button_width, button_height)
        self.continue_button = pygame.Rect(center_x, self.height // 2 + 15, button_width, button_height)
        self.exit_button = pygame.Rect(center_x, self.height // 2 + 110, button_width, button_height)

        self.menu_music = "assets/audio/menu.wav"
        self.button_sound = "assets/audio/pulsanti.wav"
        self.intro_duration_ms = 2600
        self.outro_duration_ms = 2600
        self.music_fade_ms = 800

        self.audio.play_music(music_file=self.menu_music)

        self.intro_start_time = 0
        self.outro_start_time = 0

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
