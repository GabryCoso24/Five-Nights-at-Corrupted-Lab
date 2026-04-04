import os
import random
import re

import pygame

from modules.ui_manager import add_graphic_element


class VideoCamere:
    def __init__(self, width, height, label_font, title_font):
        self.width = width
        self.height = height
        self.label_font = label_font
        self.title_font = title_font
        self.trigger_visible = True
        self.trigger_interactable = True

        self.trigger_rect = pygame.Rect(24, self.height - 96, 220, 64)
        panel_w = min(1420, max(1080, int(self.width * 0.72)))
        panel_h = min(820, max(680, int(self.height * 0.78)))
        panel_x = max(0, self.width - panel_w)
        panel_y = max(36, (self.height - panel_h) // 2 - 8)
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        self.is_open = False
        self.is_trigger_hovered = False

        self._supported_ext = {".png", ".jpg", ".jpeg", ".webp", ".jfif"}
        self._cams_folder = os.path.join("assets", "images", "cams")
        self._cam_map_path = os.path.join(self._cams_folder, "cam_map.png")
        self._cam_map_vent_path = os.path.join(self._cams_folder, "cam_map_vent.png")
        self._feeds = []
        self._selected_feed_idx = 0
        self._cam_button_rects = []
        self._threat_cameras = set()
        self._threat_sprite = None
        self._cam_map_surface = None
        self._cam_map_vent_surface = None
        self._active_map = "main"
        self._last_selected_camera_by_map = {"main": None, "vents": None}
        self._threat_sprites_by_camera = {}
        self._map_toggle_rect = pygame.Rect(0, 0, 0, 0)
        self._cam_switch_sound = os.path.join("assets", "audio", "switch_cam_sound.wav")
        self._cam_switch_sound_obj = None
        self._camera_jam_until = {}

        self._load_map_surface()
        self._load_feeds()
        self._ensure_virtual_vent_feeds()

    def set_trigger_rect(self, x, y, w, h):
        self.trigger_rect = pygame.Rect(x, y, w, h)
        return self.trigger_rect

    def set_trigger_visible(self, visible):
        self.trigger_visible = bool(visible)
        if not self.trigger_visible:
            self.is_trigger_hovered = False
        return self.trigger_visible

    def set_trigger_interactable(self, interactable):
        self.trigger_interactable = bool(interactable)
        if not self.trigger_interactable:
            self.is_trigger_hovered = False
        return self.trigger_interactable

    def set_panel_rect(self, x, y, w, h):
        self.panel_rect = pygame.Rect(x, y, w, h)
        return self.panel_rect

    def update_hover(self, mouse_pos):
        self.is_trigger_hovered = (
            self.trigger_visible
            and self.trigger_interactable
            and self.trigger_rect.collidepoint(mouse_pos)
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB and self.is_open:
            self._remember_selected_for_active_map()
            self._active_map = "vents" if self._active_map == "main" else "main"
            if not self._restore_selected_for_active_map():
                self._ensure_selected_feed_visible()
            return True

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False

        if self.trigger_visible and self.trigger_interactable and self.trigger_rect.collidepoint(event.pos):
            self.is_open = not self.is_open
            return True

        if not self.is_open:
            return False

        if self._map_toggle_rect.collidepoint(event.pos):
            self._remember_selected_for_active_map()
            self._active_map = "vents" if self._active_map == "main" else "main"
            if not self._restore_selected_for_active_map():
                self._ensure_selected_feed_visible()
            return True

        for idx, button_rect in self._cam_button_rects:
            if button_rect.collidepoint(event.pos):
                if self._selected_feed_idx != idx:
                    self._selected_feed_idx = idx
                    self._play_switch_sound()
                self._remember_selected_for_active_map()
                return True

        if not self.panel_rect.collidepoint(event.pos):
            self.is_open = False
            return True

        return False

    def queue_trigger(self):
        if not self.trigger_visible:
            return

        if self.is_open:
            # Keep CAM visible but subtle while monitor is open.
            color = (64, 186, 227, 34)
            text_color = (115, 216, 250, 130)
        elif self.trigger_interactable:
            color = (64, 186, 227, 110) if self.is_trigger_hovered else (64, 186, 227, 74)
            text_color = (115, 216, 250, 235)
        else:
            return

        add_graphic_element(
            rect=self.trigger_rect,
            text="CAM",
            color=color,
            font=self.label_font,
            text_color=text_color,
            border_radius=12,
            border_color=(35, 35, 35, 255),
            border_width=2,
            text_angle=90
        )

    def get_selected_camera_id(self):
        if not self._feeds:
            return None
        return self._feeds[self._selected_feed_idx]["camera_id"]

    def _visible_camera_ids(self):
        if self._active_map == "main":
            return {f"cam{i}" for i in range(1, 11)}
        return {f"cam{i}" for i in range(11, 16)}

    def _ensure_selected_feed_visible(self):
        if not self._feeds:
            return

        visible = self._visible_camera_ids()
        current_id = self._feeds[self._selected_feed_idx]["camera_id"]
        if current_id in visible:
            return

        for idx, feed in enumerate(self._feeds):
            if feed["camera_id"] in visible:
                self._selected_feed_idx = idx
                return

    def _remember_selected_for_active_map(self):
        if not self._feeds:
            return
        current_id = self._feeds[self._selected_feed_idx]["camera_id"]
        self._last_selected_camera_by_map[self._active_map] = current_id

    def _restore_selected_for_active_map(self):
        target_camera_id = self._last_selected_camera_by_map.get(self._active_map)
        if not target_camera_id:
            return False

        for idx, feed in enumerate(self._feeds):
            if feed["camera_id"] == target_camera_id:
                self._selected_feed_idx = idx
                return True

        return False

    def close(self):
        self.is_open = False

    def set_threat_cameras(self, camera_ids):
        self._threat_cameras = set(camera_ids or [])

    def set_threat_sprite(self, sprite_surface):
        self._threat_sprite = sprite_surface

    def set_threats_by_camera(self, threats_dict):
        self._threat_sprites_by_camera = threats_dict or {}

    def register_movement(self, from_camera, to_camera, jam_duration_ms=1400):
        now_ms = pygame.time.get_ticks()
        until = now_ms + jam_duration_ms
        for camera_id in (from_camera, to_camera):
            if not camera_id:
                continue
            current_until = self._camera_jam_until.get(camera_id, 0)
            self._camera_jam_until[camera_id] = max(current_until, until)

    def _is_camera_jammed(self, camera_id, now_ms):
        return self._camera_jam_until.get(camera_id, 0) > now_ms

    def _extract_sort_key(self, filename):
        base_name = os.path.splitext(filename)[0]
        found = re.search(r"cam[\s_-]*(\d+)", base_name, flags=re.IGNORECASE)
        if found:
            return int(found.group(1)), base_name.lower()
        return 999, base_name.lower()

    def _camera_id_from_filename(self, filename):
        base_name = os.path.splitext(filename)[0].lower()

        # Vent files are named like cam_1_vent, cam_2_vent, ...
        vent_match = re.search(r"cam[\s_-]*(\d+).*vent", base_name, flags=re.IGNORECASE)
        if vent_match:
            vent_num = int(vent_match.group(1))
            # Map vent feed numbering to CAM 11.. (vent1->cam11, vent2->cam12, ...)
            return f"cam{10 + vent_num}"

        found = re.search(r"cam[\s_-]*(\d+)", base_name, flags=re.IGNORECASE)
        if found:
            return f"cam{found.group(1)}"

        return base_name.replace(" ", "_")

    def _load_feeds(self):
        self._feeds = []
        self._selected_feed_idx = 0

        if not os.path.isdir(self._cams_folder):
            return

        files = []
        for entry in os.listdir(self._cams_folder):
            if entry.lower() in ("cam_map.png", "cam_map_vent.png"):
                continue
            ext = os.path.splitext(entry)[1].lower()
            if ext in self._supported_ext:
                files.append(entry)

        files.sort(key=self._extract_sort_key)

        for filename in files:
            full_path = os.path.join(self._cams_folder, filename)
            try:
                image = pygame.image.load(full_path).convert()
            except Exception:
                continue

            camera_id = self._camera_id_from_filename(filename)
            label = f"CAM {camera_id.replace('cam', '')}" if camera_id.startswith("cam") else camera_id.upper()
            self._feeds.append(
                {
                    "surface": image,
                    "camera_id": camera_id,
                    "label": label,
                    "filename": filename,
                }
            )

    def _load_map_surface(self):
        self._cam_map_surface = None
        self._cam_map_vent_surface = None
        if not os.path.isfile(self._cam_map_path):
            self._cam_map_surface = None
        else:
            try:
                self._cam_map_surface = pygame.image.load(self._cam_map_path).convert_alpha()
            except Exception:
                try:
                    self._cam_map_surface = pygame.image.load(self._cam_map_path).convert()
                except Exception:
                    self._cam_map_surface = None

        if not os.path.isfile(self._cam_map_vent_path):
            self._cam_map_vent_surface = None
        else:
            try:
                self._cam_map_vent_surface = pygame.image.load(self._cam_map_vent_path).convert_alpha()
            except Exception:
                try:
                    self._cam_map_vent_surface = pygame.image.load(self._cam_map_vent_path).convert()
                except Exception:
                    self._cam_map_vent_surface = None

    def _build_vent_placeholder(self, label):
        base_w, base_h = 640, 360
        if self._feeds:
            base_w = self._feeds[0]["surface"].get_width()
            base_h = self._feeds[0]["surface"].get_height()

        surf = pygame.Surface((base_w, base_h), pygame.SRCALPHA)
        surf.fill((14, 20, 24))
        for _ in range(max(120, (base_w * base_h) // 6000)):
            x = random.randint(0, base_w - 2)
            y = random.randint(0, base_h - 2)
            a = random.randint(25, 90)
            g = random.randint(60, 150)
            pygame.draw.rect(surf, (g, g, g, a), (x, y, 2, 1))

        label_top = self.title_font.render(label, True, (205, 215, 220))
        label_sub = self.label_font.render("CONDOTTI", True, (145, 172, 180))
        surf.blit(label_top, label_top.get_rect(center=(base_w // 2, base_h // 2 - 20)))
        surf.blit(label_sub, label_sub.get_rect(center=(base_w // 2, base_h // 2 + 28)))
        return surf.convert()

    def _ensure_virtual_vent_feeds(self):
        existing_ids = {feed["camera_id"] for feed in self._feeds}
        for cam_n in (11, 12, 13, 14, 15):
            cam_id = f"cam{cam_n}"
            if cam_id in existing_ids:
                continue
            self._feeds.append(
                {
                    "surface": self._build_vent_placeholder(f"CAM {cam_n}"),
                    "camera_id": cam_id,
                    "label": f"CAM {cam_n}",
                    "filename": "virtual_vent",
                }
            )

    def _build_cam_button_rects(self, map_rect):
        self._cam_button_rects = []
        if not self._feeds:
            return

        anchors_main = {
            # Tuned to the provided cam_map style (0..1 in map space).
            "cam1": (0.08, 0.72),
            "cam2": (0.57, 0.69),
            "cam3": (0.89, 0.57),
            "cam4": (0.89, 0.40),
            "cam5": (0.43, 0.42),
            "cam6": (0.08, 0.47),
            "cam7": (0.08, 0.28),
            "cam8": (0.34, 0.20),
            "cam9": (0.54, 0.08),
            "cam10": (0.81, 0.16),
        }
        anchors_vents = {
            # Vent map based on provided reference image.
            "cam11": (0.10, 0.07),
            "cam12": (0.30, 0.34),
            "cam13": (0.50, 0.55),
            "cam14": (0.72, 0.33),
            "cam15": (0.86, 0.66),
        }

        anchors = anchors_main if self._active_map == "main" else anchors_vents
        visible_ids = set(anchors.keys())

        button_w = max(42, int(map_rect.width * 0.13))
        button_h = max(30, int(button_w * 0.62))
        pad = 4

        for idx, feed in enumerate(self._feeds):
            cam_id = feed["camera_id"]
            if cam_id not in visible_ids:
                continue

            anchor = anchors.get(cam_id)
            if anchor is None and self._active_map == "main":
                col = idx % 4
                row = idx // 4
                anchor = (0.16 + col * 0.2, 0.2 + row * 0.16)
            if anchor is None:
                continue

            x = map_rect.left + int(anchor[0] * map_rect.width) - button_w // 2
            y = map_rect.top + int(anchor[1] * map_rect.height) - button_h // 2
            x = max(map_rect.left + pad, min(x, map_rect.right - button_w - pad))
            y = max(map_rect.top + pad, min(y, map_rect.bottom - button_h - pad))
            self._cam_button_rects.append((idx, pygame.Rect(x, y, button_w, button_h)))

    def _draw_map_background(self, surface, map_rect):
        pygame.draw.rect(surface, (8, 10, 14), map_rect)
        if self._active_map == "main":
            if self._cam_map_surface is not None:
                scaled_map = pygame.transform.smoothscale(self._cam_map_surface, (map_rect.width, map_rect.height))
                surface.blit(scaled_map, map_rect)

            overlay = pygame.Surface((map_rect.width, map_rect.height), pygame.SRCALPHA)
            overlay.fill((8, 12, 16, 48))
            surface.blit(overlay, map_rect.topleft)
        else:
            if self._cam_map_vent_surface is not None:
                scaled_map = pygame.transform.smoothscale(self._cam_map_vent_surface, (map_rect.width, map_rect.height))
                surface.blit(scaled_map, map_rect)
            else:
                layer = pygame.Surface((map_rect.width, map_rect.height), pygame.SRCALPHA)
                layer.fill((16, 22, 26, 220))
                surface.blit(layer, map_rect.topleft)

            overlay = pygame.Surface((map_rect.width, map_rect.height), pygame.SRCALPHA)
            overlay.fill((8, 12, 16, 35))
            surface.blit(overlay, map_rect.topleft)

        pygame.draw.rect(surface, (122, 146, 162), map_rect, width=2)

    def _draw_monitor_button(self, surface, rect, text):
        pygame.draw.rect(surface, (42, 44, 50), rect)
        pygame.draw.rect(surface, (186, 190, 198), rect, width=2)

        # pygame.font.render does not support multiline strings directly.
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            lines = [text]

        rendered = [self.title_font.render(line, True, (218, 223, 230)) for line in lines]
        max_w = max(1, max(img.get_width() for img in rendered))
        total_h = max(1, sum(img.get_height() for img in rendered))

        text_surface = pygame.Surface((max_w, total_h), pygame.SRCALPHA)
        y = 0
        for img in rendered:
            x = (max_w - img.get_width()) // 2
            text_surface.blit(img, (x, y))
            y += img.get_height()

        text_img = pygame.transform.smoothscale(
            text_surface,
            (max(40, rect.width - 20), max(26, rect.height - 14)),
        )
        surface.blit(text_img, text_img.get_rect(center=rect.center))

    def _draw_feed_noise(self, surface, feed_area, intensity=1.0):
        noise = pygame.Surface((feed_area.width, feed_area.height), pygame.SRCALPHA)
        particles = int(max(340, feed_area.width) * max(0.7, intensity))
        for _ in range(particles):
            x = random.randint(0, max(0, feed_area.width - 2))
            y = random.randint(0, max(0, feed_area.height - 2))
            w = random.randint(1, 4)
            h = random.randint(1, 3)
            alpha = random.randint(18, int(58 * max(1.0, intensity)))
            gray = random.randint(130, 228)
            pygame.draw.rect(noise, (gray, gray, gray, alpha), (x, y, w, h))

        for y in range(0, feed_area.height, 2):
            base = 14 if intensity < 1.2 else 24
            a = base if random.random() > 0.85 else max(7, base - 6)
            pygame.draw.line(noise, (10, 10, 10, a), (0, y), (feed_area.width, y))

        surface.blit(noise, feed_area.topleft)

    def _draw_feed_glitch(self, surface, feed_area, intensity=1.0):
        # Horizontal tearing bands for CRT-like camera glitches.
        if random.random() > min(1.0, 0.55 * intensity):
            return

        snapshot = surface.subsurface(feed_area).copy()
        bands = random.randint(6, int(16 * max(1.0, intensity)))
        for _ in range(bands):
            y = random.randint(0, max(0, feed_area.height - 6))
            h = random.randint(2, 14)
            shift = random.randint(-28, 28)
            src = pygame.Rect(0, y, feed_area.width, h)
            surface.blit(snapshot, (feed_area.x + shift, feed_area.y + y), src)

    def _draw_total_jam(self, surface, feed_area):
        # Total signal loss: static storm + dark layer that fully hides feed details.
        self._draw_feed_noise(surface, feed_area, intensity=4.0)
        self._draw_feed_glitch(surface, feed_area, intensity=4.0)

        blackout = pygame.Surface((feed_area.width, feed_area.height), pygame.SRCALPHA)
        blackout.fill((5, 7, 9, 215))
        surface.blit(blackout, feed_area.topleft)

        burst = pygame.Surface((feed_area.width, feed_area.height), pygame.SRCALPHA)
        for _ in range(max(900, (feed_area.width * feed_area.height) // 130)):
            x = random.randint(0, max(0, feed_area.width - 1))
            y = random.randint(0, max(0, feed_area.height - 1))
            c = random.randint(120, 255)
            a = random.randint(70, 170)
            burst.set_at((x, y), (c, c, c, a))
        surface.blit(burst, feed_area.topleft)

        label = self.title_font.render("NO SIGNAL", True, (255, 130, 130))
        label = pygame.transform.smoothscale(
            label,
            (max(110, int(feed_area.width * 0.42)), max(24, int(feed_area.height * 0.10))),
        )
        surface.blit(label, label.get_rect(center=feed_area.center))

    def _play_switch_sound(self):
        if not os.path.isfile(self._cam_switch_sound):
            return
        try:
            if self._cam_switch_sound_obj is None:
                self._cam_switch_sound_obj = pygame.mixer.Sound(self._cam_switch_sound)
            self._cam_switch_sound_obj.set_volume(0.9)
            self._cam_switch_sound_obj.play()
        except pygame.error:
            return

    def draw_overlay(self, surface):
        if not self.is_open:
            return

        now_ms = pygame.time.get_ticks()

        # Do not dim the rest of the office while cameras are open.

        pygame.draw.rect(surface, (18, 20, 24), self.panel_rect)
        pygame.draw.rect(surface, (92, 98, 106), self.panel_rect, width=2)

        title = self.title_font.render("SISTEMA CAMERE", True, (235, 235, 235))
        surface.blit(title, title.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 40)))

        if not self._feeds:
            missing = self.label_font.render("Nessuna immagine camera trovata in assets/images/cams", True, (255, 110, 110))
            surface.blit(missing, missing.get_rect(center=self.panel_rect.center))
            return

        self._selected_feed_idx = max(0, min(self._selected_feed_idx, len(self._feeds) - 1))
        self._ensure_selected_feed_visible()
        active_feed = self._feeds[self._selected_feed_idx]

        feed_area_top = self.panel_rect.top + 100
        map_width = max(210, int(self.panel_rect.width * 0.34))
        map_height = map_width
        map_height = min(map_height, max(180, int(self.panel_rect.height * 0.58)))
        map_rect = pygame.Rect(
            self.panel_rect.right - map_width - 16,
            self.panel_rect.bottom - map_height - 16,
            map_width,
            map_height,
        )
        self._build_cam_button_rects(map_rect)

        feed_area_bottom = self.panel_rect.bottom - 18
        feed_area_right = map_rect.left - 12
        if feed_area_right <= self.panel_rect.left + 24:
            feed_area_right = self.panel_rect.right - 18

        feed_area = pygame.Rect(
            self.panel_rect.left + 18,
            feed_area_top,
            max(10, feed_area_right - (self.panel_rect.left + 18)),
            max(10, feed_area_bottom - feed_area_top),
        )

        img = pygame.transform.smoothscale(active_feed["surface"], (feed_area.width, feed_area.height))
        surface.blit(img, feed_area)
        active_jammed = self._is_camera_jammed(active_feed["camera_id"], now_ms)
        noise_intensity = 1.55 if not active_jammed else 3.8
        self._draw_feed_noise(surface, feed_area, intensity=noise_intensity)
        self._draw_feed_glitch(surface, feed_area, intensity=noise_intensity)

        if active_jammed:
            self._draw_total_jam(surface, feed_area)

        active_camera_id = active_feed["camera_id"]
        if (not active_jammed) and active_camera_id in self._threat_sprites_by_camera:
            sprite_list = self._threat_sprites_by_camera[active_camera_id]
            if sprite_list:
                count = len(sprite_list)
                usable_width = int(feed_area.width * 0.76)
                max_sprite_w = max(36, usable_width // max(1, count))
                base_sprite_h = int(feed_area.height * 0.62)
                base_y = feed_area.bottom - int(feed_area.height * 0.06)
                start_x = feed_area.centerx - (usable_width // 2)
                for idx, sprite_surface in enumerate(sprite_list):
                    target_h = max(36, base_sprite_h - (idx * 10))
                    scale = target_h / max(1, sprite_surface.get_height())
                    target_w = int(sprite_surface.get_width() * scale)
                    if target_w > max_sprite_w:
                        scale = max_sprite_w / max(1, sprite_surface.get_width())
                        target_w = max(36, int(sprite_surface.get_width() * scale))
                        target_h = max(36, int(sprite_surface.get_height() * scale))
                    sprite = pygame.transform.smoothscale(sprite_surface, (target_w, target_h)).convert_alpha()
                    sprite.set_alpha(220)

                    group_gap = max(8, int(feed_area.width * 0.02))
                    group_width = (target_w * count) + (group_gap * (count - 1))
                    group_x = start_x + (usable_width - group_width) // 2
                    x = group_x + idx * (target_w + group_gap)
                    y = base_y - target_h + random.randint(-6, 6)
                    surface.blit(sprite, (x, y))

                warning = self.label_font.render("MOVIMENTO RILEVATO", True, (255, 90, 90))
                surface.blit(warning, warning.get_rect(topright=(feed_area.right - 12, feed_area.top + 16)))
        elif (not active_jammed) and active_camera_id in self._threat_cameras and self._threat_sprite is not None:
            sprite_h = int(feed_area.height * 0.65)
            sprite_w = int(self._threat_sprite.get_width() * (sprite_h / max(1, self._threat_sprite.get_height())))
            sprite_w = max(48, min(sprite_w, int(feed_area.width * 0.56)))
            sprite_h = max(48, min(sprite_h, int(feed_area.height * 0.88)))

            sprite = pygame.transform.smoothscale(self._threat_sprite, (sprite_w, sprite_h)).convert_alpha()
            sprite.set_alpha(228)

            jitter_x = random.randint(-14, 14)
            jitter_y = random.randint(-7, 7)
            sprite_x = feed_area.centerx - (sprite_w // 2) + jitter_x
            sprite_y = feed_area.bottom - sprite_h + jitter_y
            surface.blit(sprite, (sprite_x, sprite_y))

            warning = self.label_font.render("MOVIMENTO RILEVATO", True, (255, 90, 90))
            surface.blit(warning, warning.get_rect(topright=(feed_area.right - 12, feed_area.top + 16)))

        pygame.draw.rect(surface, (168, 172, 178), feed_area, width=2)

        cam_text = self.title_font.render(active_feed["label"], True, (245, 245, 245))
        surface.blit(cam_text, cam_text.get_rect(midleft=(feed_area.left + 12, feed_area.top + 26)))

        button_w = max(108, int(map_rect.width * 0.44))
        button_h = max(40, int(map_rect.height * 0.15))
        button_x = map_rect.left + (map_rect.width - button_w) // 2
        button_y = max(self.panel_rect.top + 100, map_rect.top - button_h - 8)
        self._map_toggle_rect = pygame.Rect(button_x, button_y, button_w, button_h)
        toggle_text = "Map\nCondotti" if self._active_map == "main" else "Map\nPrincipale"
        self._draw_monitor_button(surface, self._map_toggle_rect, toggle_text)

        self._draw_map_background(surface, map_rect)

        for idx, cam_rect in self._cam_button_rects:
            feed = self._feeds[idx]
            is_selected = idx == self._selected_feed_idx

            if is_selected:
                fill = (112, 150, 20)
                border = (226, 255, 140)
            else:
                fill = (58, 62, 69)
                border = (188, 194, 203)

            pygame.draw.rect(surface, fill, cam_rect)
            pygame.draw.rect(surface, border, cam_rect, width=2)

            cam_number = feed["label"].replace("CAM ", "").strip()
            top = self.label_font.render("CAM", True, (238, 242, 248))
            bottom = self.label_font.render(cam_number, True, (238, 242, 248))
            top = pygame.transform.smoothscale(top, (max(20, cam_rect.width - 10), max(12, cam_rect.height // 2 - 2)))
            bottom = pygame.transform.smoothscale(bottom, (max(12, cam_rect.width - 16), max(10, cam_rect.height // 2 - 2)))
            surface.blit(top, top.get_rect(center=(cam_rect.centerx, cam_rect.top + cam_rect.height * 0.3)))
            surface.blit(bottom, bottom.get_rect(center=(cam_rect.centerx, cam_rect.top + cam_rect.height * 0.72)))
