import os
import random
import re
import json
from collections import deque

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
        self._blocked_vent_cameras = set()
        self._vent_blocking_enabled = True
        self._camera_error_active = False
        self._vent_block_rects = {}
        self._vent_block_size_by_edge = {}
        self._vent_block_anchor_by_edge = {}
        self._vent_closure_links_by_camera = {}
        self._vent_closure_links_by_edge = {}
        self._admin_selected_vent_edge = None
        self._admin_drag_vent_edge = None
        self._main_edge_control_points = {}
        self._vent_edge_control_points = {}
        self._line_waypoints_main = {}
        self._line_waypoints_vents = {}
        self._admin_drag_line_waypoint = None
        self._last_line_click = {"key": None, "time": 0}
        self._last_waypoint_click = {"key": None, "time": 0}
        self._external_node_rects = {}
        self._cam_button_rect_by_id = {}
        self._current_map_rect = pygame.Rect(0, 0, 0, 0)

        self._layout_config_path = os.path.join("assets", "camera_layout.json")
        self._anchors_main = {
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
        self._anchors_vents = {
            "cam11": (0.10, 0.07),
            "cam12": (0.30, 0.34),
            "cam13": (0.50, 0.55),
            "cam14": (0.72, 0.33),
            "cam15": (0.86, 0.66),
        }
        self._button_scale_by_map = {"main": 1.0, "vents": 1.0}
        self._button_scale_by_camera = {}
        self._camera_triangle_by_id = {}
        self._vent_block_anchor_by_camera = {
            "cam11": (0.14, 0.15),
            "cam12": (0.34, 0.42),
            "cam13": (0.53, 0.62),
            "cam14": (0.75, 0.40),
            "cam15": (0.88, 0.72),
        }
        self._camera_connections = {
            "cam10": ["cam9", "cam8"],
            "cam9": ["cam7"],
            "cam7": ["cam6"],
            "cam6": ["cam1"],
            "cam8": ["cam12"],
            "cam12": ["cam14"],
            "cam14": [],
            "cam1": [],
        }
        self._vent_connections = {
            "cam11": ["cam12"],
            "cam12": ["cam13"],
            "cam13": ["cam14"],
            "cam14": ["cam15"],
        }
        self._external_nodes_main = {
            "office_left": (0.08, 0.90),
            "office_right": (0.92, 0.90),
        }
        for cam_idx in range(11, 16):
            self._external_nodes_main[f"cam{cam_idx}"] = (0.16 + ((cam_idx - 11) * 0.16), 0.95)
        self._external_nodes_vents = {
            "office_left": (0.74, 0.90),
            "office_right": (0.90, 0.90),
        }
        for cam_idx in range(1, 11):
            col = (cam_idx - 1) % 5
            row = (cam_idx - 1) // 5
            self._external_nodes_vents[f"cam{cam_idx}"] = (0.08 + (col * 0.18), 0.92 + (row * 0.06))
        self._vent_closure_edge_ids = {
            f"{src}->{dst}"
            for src, targets in self._vent_connections.items()
            for dst in targets
        }
        self._vent_closure_edge_ids.add("cam15->office_right")
        self._office_targets = {"left": "cam1", "right": "cam14"}
        self._admin_mode = False
        self._admin_drag_camera_id = None
        self._admin_selected_camera_id = None
        self._admin_connection_from = None
        self._last_vent_click = {"edge": None, "time": 0}
        self._last_vent_cam_click = {"cam": None, "time": 0}
        self._vent_block_transition = {"edge": None, "target_closed": False, "until": 0}
        self._vent_block_transition_delay_ms = 650

        self._load_map_surface()
        self._load_feeds()
        self._ensure_virtual_vent_feeds()
        self._load_layout_config()

    def set_trigger_rect(self, x, y, w, h):
        self.trigger_rect = pygame.Rect(x, y, w, h)
        return self.trigger_rect

    def _toggle_single_blocked_edge(self, edge_id, now_ms=None):
        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        currently_closed = edge_id in self._blocked_vent_cameras
        self._vent_block_transition = {
            "edge": edge_id,
            "target_closed": not currently_closed,
            "until": now_ms + self._vent_block_transition_delay_ms,
        }

    def _update_vent_block_transition(self, now_ms=None):
        now_ms = pygame.time.get_ticks() if now_ms is None else now_ms
        edge_id = self._vent_block_transition.get("edge")
        until = int(self._vent_block_transition.get("until", 0) or 0)
        if not edge_id or now_ms < until:
            return

        if self._vent_block_transition.get("target_closed", False):
            self._blocked_vent_cameras = {edge_id}
        else:
            self._blocked_vent_cameras.clear()

        self._vent_block_transition = {"edge": None, "target_closed": False, "until": 0}

    def _edge_for_vent_camera(self, cam_id):
        # Prefer outgoing vent route from selected vent camera.
        targets = self._vent_connections.get(cam_id, [])
        if targets:
            return f"{cam_id}->{targets[0]}"

        # Fallback to any known closure edge involving this camera.
        prefix = f"{cam_id}->"
        for edge_id in sorted(self._vent_closure_edge_ids):
            if edge_id.startswith(prefix):
                return edge_id

        suffix = f"->{cam_id}"
        for edge_id in sorted(self._vent_closure_edge_ids):
            if edge_id.endswith(suffix):
                return edge_id

        return None

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

    def is_admin_mode(self):
        return self._admin_mode

    def set_admin_mode(self, enabled):
        self._admin_mode = bool(enabled)
        self._admin_drag_camera_id = None
        self._admin_drag_vent_edge = None
        self._admin_drag_line_waypoint = None
        self._admin_connection_from = None
        self._admin_selected_vent_edge = None
        return self._admin_mode

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
        self._update_vent_block_transition()

        if event.type == pygame.KEYDOWN and event.key == pygame.K_F9 and self.is_open:
            self.set_admin_mode(not self._admin_mode)
            return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_s and self._admin_mode and self.is_open:
            self.save_layout_config()
            return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB and self.is_open:
            self._remember_selected_for_active_map()
            self._active_map = "vents" if self._active_map == "main" else "main"
            if not self._restore_selected_for_active_map():
                self._ensure_selected_feed_visible()
            return True

        if event.type == pygame.MOUSEMOTION and self._admin_mode and self.is_open and self._admin_drag_camera_id:
            self._set_anchor_from_mouse(self._admin_drag_camera_id, event.pos)
            return True

        if event.type == pygame.MOUSEMOTION and self._admin_mode and self.is_open and self._admin_drag_vent_edge:
            self._set_vent_block_anchor_from_mouse(self._admin_drag_vent_edge, event.pos)
            return True

        if event.type == pygame.MOUSEMOTION and self._admin_mode and self.is_open and self._admin_drag_line_waypoint:
            map_kind, edge_id, waypoint_idx = self._admin_drag_line_waypoint
            self._set_line_waypoint_from_mouse(map_kind, edge_id, waypoint_idx, event.pos)
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._admin_drag_camera_id = None
            self._admin_drag_vent_edge = None
            self._admin_drag_line_waypoint = None

        if event.type != pygame.MOUSEBUTTONDOWN:
            return False

        if event.button == 1 and self.trigger_visible and self.trigger_interactable and self.trigger_rect.collidepoint(event.pos):
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

        if self._active_map == "vents":
            for edge_id, rect in self._vent_block_rects.items():
                if rect.collidepoint(event.pos):
                    if self._admin_mode and event.button in (4, 5):
                        self._admin_selected_vent_edge = edge_id
                        size = self._vent_block_size_by_edge.get(edge_id, [34, 18])
                        width = int(size[0])
                        height = int(size[1])
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_SHIFT:
                            delta_h = 2 if event.button == 4 else -2
                            height = max(8, min(120, height + delta_h))
                        else:
                            delta_w = 4 if event.button == 4 else -4
                            width = max(12, min(220, width + delta_w))
                        self._vent_block_size_by_edge[edge_id] = [width, height]
                        return True

                    if self._admin_mode and event.button == 3:
                        if self._admin_connection_from is None:
                            self._admin_connection_from = ("edge", edge_id)
                            return True
                        if self._toggle_admin_link(("edge", edge_id)):
                            return True

                    if self._admin_mode and event.button == 1:
                        self._admin_selected_vent_edge = edge_id
                        self._admin_drag_vent_edge = edge_id
                    if event.button == 1 and self._vent_blocking_enabled:
                        now_ms = pygame.time.get_ticks()
                        last_edge = self._last_vent_click["edge"]
                        last_time = self._last_vent_click["time"]
                        if last_edge == edge_id and (now_ms - last_time) <= 520:
                            self._toggle_single_blocked_edge(edge_id, now_ms=now_ms)
                            self._last_vent_click = {"edge": None, "time": 0}
                        else:
                            self._last_vent_click = {"edge": edge_id, "time": now_ms}
                    return True

            if self._admin_mode and self._admin_selected_vent_edge and event.button in (4, 5):
                size = self._vent_block_size_by_edge.get(self._admin_selected_vent_edge, [34, 18])
                width = int(size[0])
                height = int(size[1])
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    delta_h = 2 if event.button == 4 else -2
                    height = max(8, min(120, height + delta_h))
                else:
                    delta_w = 4 if event.button == 4 else -4
                    width = max(12, min(220, width + delta_w))

                self._vent_block_size_by_edge[self._admin_selected_vent_edge] = [width, height]
                return True

        if self._admin_mode and event.button == 3:
            for node_id, node_rect in self._external_node_rects.items():
                if node_rect.collidepoint(event.pos):
                    if self._admin_connection_from is None:
                        self._admin_connection_from = ("node", node_id)
                        return True
                    if self._toggle_admin_link(("node", node_id)):
                        return True

        if self._admin_mode and event.button == 1:
            for node_rect in self._external_node_rects.values():
                if node_rect.collidepoint(event.pos):
                    # Prevent accidental camera drag when clicking external connector nodes.
                    return True

        if self._admin_mode and event.button == 1:
            waypoint_hit = self._hit_test_line_waypoint(event.pos)
            if waypoint_hit is not None:
                map_kind, edge_id, waypoint_idx = waypoint_hit
                now_ms = pygame.time.get_ticks()
                click_key = f"{map_kind}:{edge_id}:{waypoint_idx}"
                if self._last_waypoint_click["key"] == click_key and (now_ms - self._last_waypoint_click["time"]) <= 320:
                    self._remove_line_waypoint(map_kind, edge_id, waypoint_idx)
                    self._admin_drag_line_waypoint = None
                    self._last_waypoint_click = {"key": None, "time": 0}
                else:
                    self._admin_drag_line_waypoint = waypoint_hit
                    self._last_waypoint_click = {"key": click_key, "time": now_ms}
                return True

            line_hit = self._hit_test_connection_line(event.pos)
            if line_hit is not None:
                map_kind, edge_id, segment_idx = line_hit
                now_ms = pygame.time.get_ticks()
                click_key = f"{map_kind}:{edge_id}"
                if self._last_line_click["key"] == click_key and (now_ms - self._last_line_click["time"]) <= 320:
                    waypoint_idx = self._insert_line_waypoint_from_mouse(map_kind, edge_id, segment_idx, event.pos)
                    self._admin_drag_line_waypoint = (map_kind, edge_id, waypoint_idx)
                    self._last_line_click = {"key": None, "time": 0}
                else:
                    self._last_line_click = {"key": click_key, "time": now_ms}
                return True

        for idx, button_rect in self._cam_button_rects:
            if button_rect.collidepoint(event.pos):
                feed = self._feeds[idx]
                cam_id = feed["camera_id"]

                if self._admin_mode and event.button == 3:
                    if self._admin_connection_from is None:
                        self._admin_connection_from = ("cam", cam_id)
                    else:
                        if self._toggle_admin_link(("cam", cam_id)):
                            self._admin_selected_camera_id = cam_id
                            return True
                    self._admin_selected_camera_id = cam_id
                    return True

                if self._admin_mode and event.button == 1:
                    self._admin_selected_camera_id = cam_id
                    self._admin_drag_camera_id = cam_id

                if (not self._admin_mode) and self._active_map == "vents" and event.button == 1 and self._vent_blocking_enabled:
                    now_ms = pygame.time.get_ticks()
                    last_cam = self._last_vent_cam_click["cam"]
                    last_time = self._last_vent_cam_click["time"]
                    if last_cam == cam_id and (now_ms - last_time) <= 520:
                        target_edge = self._edge_for_vent_camera(cam_id)
                        if target_edge:
                            self._toggle_single_blocked_edge(target_edge, now_ms=now_ms)
                        self._last_vent_cam_click = {"cam": None, "time": 0}
                    else:
                        self._last_vent_cam_click = {"cam": cam_id, "time": now_ms}

                if self._admin_mode and event.button == 2:
                    self._camera_triangle_by_id[cam_id] = not bool(self._camera_triangle_by_id.get(cam_id, False))
                    self._admin_selected_camera_id = cam_id
                    return True

                if self._admin_mode and event.button == 4 and self._admin_selected_camera_id == cam_id:
                    self._button_scale_by_camera[cam_id] = min(1.9, float(self._button_scale_by_camera.get(cam_id, 1.0)) + 0.08)
                    return True

                if self._admin_mode and event.button == 5 and self._admin_selected_camera_id == cam_id:
                    self._button_scale_by_camera[cam_id] = max(0.6, float(self._button_scale_by_camera.get(cam_id, 1.0)) - 0.08)
                    return True

                if self._selected_feed_idx != idx:
                    self._selected_feed_idx = idx
                    self._play_switch_sound()
                self._remember_selected_for_active_map()
                return True

        if self._admin_mode and event.button == 3:
            if self._remove_link_at_pos(event.pos):
                self._admin_connection_from = None
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

    def _set_anchor_from_mouse(self, camera_id, mouse_pos):
        if self._current_map_rect.width <= 0 or self._current_map_rect.height <= 0:
            return

        rel_x = (mouse_pos[0] - self._current_map_rect.left) / max(1, self._current_map_rect.width)
        rel_y = (mouse_pos[1] - self._current_map_rect.top) / max(1, self._current_map_rect.height)
        rel_x = max(0.02, min(0.98, rel_x))
        rel_y = max(0.02, min(0.98, rel_y))

        if self._active_map == "main":
            self._anchors_main[camera_id] = (rel_x, rel_y)
        else:
            self._anchors_vents[camera_id] = (rel_x, rel_y)

    def _set_vent_block_anchor_from_mouse(self, edge_id, mouse_pos):
        if self._current_map_rect.width <= 0 or self._current_map_rect.height <= 0:
            return

        rel_x = (mouse_pos[0] - self._current_map_rect.left) / max(1, self._current_map_rect.width)
        rel_y = (mouse_pos[1] - self._current_map_rect.top) / max(1, self._current_map_rect.height)
        rel_x = max(0.02, min(0.98, rel_x))
        rel_y = max(0.02, min(0.98, rel_y))
        self._vent_block_anchor_by_edge[edge_id] = (rel_x, rel_y)

    def _external_nodes_for_active_map(self):
        return self._external_nodes_main if self._active_map == "main" else self._external_nodes_vents

    def _toggle_admin_link(self, target):
        if self._admin_connection_from is None:
            return False

        src_kind, src_id = self._admin_connection_from
        dst_kind, dst_id = target

        if src_kind == dst_kind and src_id == dst_id:
            self._admin_connection_from = None
            return True

        if src_kind in ("cam", "node") and dst_kind in ("cam", "node"):
            graph = self._camera_connections if self._active_map == "main" else self._vent_connections
            linked = graph.setdefault(src_id, [])
            if dst_id in linked:
                linked.remove(dst_id)
            else:
                linked.append(dst_id)
                if self._active_map == "vents":
                    self._vent_closure_edge_ids.add(f"{src_id}->{dst_id}")
            self._admin_connection_from = None
            return True

        if self._active_map == "vents" and src_kind == "cam" and dst_kind == "edge":
            linked_edges = self._vent_closure_links_by_camera.setdefault(src_id, [])
            if dst_id in linked_edges:
                linked_edges.remove(dst_id)
            else:
                linked_edges.append(dst_id)
            self._admin_connection_from = None
            return True

        if self._active_map == "vents" and src_kind == "edge" and dst_kind in ("cam", "node"):
            linked_targets = self._vent_closure_links_by_edge.setdefault(src_id, [])
            if dst_id in linked_targets:
                linked_targets.remove(dst_id)
            else:
                linked_targets.append(dst_id)
            self._admin_connection_from = None
            return True

        return False

    def _node_point(self, map_kind, node_id, map_rect):
        if map_kind == "main":
            anchor = self._anchors_main.get(node_id)
            if anchor is None:
                anchor = self._external_nodes_main.get(node_id)
        else:
            anchor = self._anchors_vents.get(node_id)
            if anchor is None:
                anchor = self._external_nodes_vents.get(node_id)

        if anchor is None:
            return None

        return (
            map_rect.left + int(anchor[0] * map_rect.width),
            map_rect.top + int(anchor[1] * map_rect.height),
        )

    def _build_external_node_rects(self, map_rect):
        self._external_node_rects = {}
        nodes = self._external_nodes_for_active_map()
        for node_id, anchor in nodes.items():
            center = (
                map_rect.left + int(anchor[0] * map_rect.width),
                map_rect.top + int(anchor[1] * map_rect.height),
            )
            rect = pygame.Rect(0, 0, 86, 24)
            rect.center = center
            self._external_node_rects[node_id] = rect

    def _draw_external_nodes(self, surface):
        if not self._external_node_rects:
            return
        for node_id, rect in self._external_node_rects.items():
            pygame.draw.rect(surface, (0, 0, 0, 0), rect)
            pygame.draw.rect(surface, (235, 235, 235), rect, width=2)
            label = node_id.replace("office_", "OFFICE ").replace("cam", "CAM ").upper()
            txt = self.label_font.render(label, True, (235, 235, 235))
            surface.blit(txt, txt.get_rect(center=rect.center))

    def _set_line_control_point_from_mouse(self, map_kind, edge_id, mouse_pos):
        if self._current_map_rect.width <= 0 or self._current_map_rect.height <= 0:
            return

        rel_x = (mouse_pos[0] - self._current_map_rect.left) / max(1, self._current_map_rect.width)
        rel_y = (mouse_pos[1] - self._current_map_rect.top) / max(1, self._current_map_rect.height)
        rel_x = max(0.02, min(0.98, rel_x))
        rel_y = max(0.02, min(0.98, rel_y))

        if map_kind == "main":
            self._main_edge_control_points[edge_id] = (rel_x, rel_y)
        else:
            self._vent_edge_control_points[edge_id] = (rel_x, rel_y)

    def _waypoint_dict(self, map_kind):
        return self._line_waypoints_main if map_kind == "main" else self._line_waypoints_vents

    def _get_line_waypoints(self, map_kind, edge_id):
        waypoints = self._waypoint_dict(map_kind).get(edge_id, [])
        if waypoints:
            return list(waypoints)

        # Backward compatibility: migrate single control point into waypoint list lazily.
        legacy = self._main_edge_control_points.get(edge_id) if map_kind == "main" else self._vent_edge_control_points.get(edge_id)
        if legacy is not None:
            self._waypoint_dict(map_kind)[edge_id] = [legacy]
            return [legacy]

        return []

    def _set_line_waypoint_from_mouse(self, map_kind, edge_id, waypoint_idx, mouse_pos):
        if self._current_map_rect.width <= 0 or self._current_map_rect.height <= 0:
            return

        rel_x = (mouse_pos[0] - self._current_map_rect.left) / max(1, self._current_map_rect.width)
        rel_y = (mouse_pos[1] - self._current_map_rect.top) / max(1, self._current_map_rect.height)
        rel_x = max(0.02, min(0.98, rel_x))
        rel_y = max(0.02, min(0.98, rel_y))

        wps = self._get_line_waypoints(map_kind, edge_id)
        if waypoint_idx < 0 or waypoint_idx >= len(wps):
            return
        wps[waypoint_idx] = (rel_x, rel_y)
        self._waypoint_dict(map_kind)[edge_id] = wps

    def _insert_line_waypoint_from_mouse(self, map_kind, edge_id, segment_idx, mouse_pos):
        if self._current_map_rect.width <= 0 or self._current_map_rect.height <= 0:
            return 0

        rel_x = (mouse_pos[0] - self._current_map_rect.left) / max(1, self._current_map_rect.width)
        rel_y = (mouse_pos[1] - self._current_map_rect.top) / max(1, self._current_map_rect.height)
        rel_x = max(0.02, min(0.98, rel_x))
        rel_y = max(0.02, min(0.98, rel_y))

        wps = self._get_line_waypoints(map_kind, edge_id)
        insert_idx = max(0, min(len(wps), segment_idx))
        wps.insert(insert_idx, (rel_x, rel_y))
        self._waypoint_dict(map_kind)[edge_id] = wps
        return insert_idx

    def _remove_line_waypoint(self, map_kind, edge_id, waypoint_idx):
        wps = self._get_line_waypoints(map_kind, edge_id)
        if waypoint_idx < 0 or waypoint_idx >= len(wps):
            return
        del wps[waypoint_idx]
        if wps:
            self._waypoint_dict(map_kind)[edge_id] = wps
        else:
            self._waypoint_dict(map_kind).pop(edge_id, None)

    def _edge_polyline_points(self, map_kind, edge_id, p1, p2, map_rect):
        points = [p1]
        for rel_x, rel_y in self._get_line_waypoints(map_kind, edge_id):
            points.append((map_rect.left + int(rel_x * map_rect.width), map_rect.top + int(rel_y * map_rect.height)))
        points.append(p2)
        return points

    def _hit_test_line_waypoint(self, point):
        if self._current_map_rect.width <= 0 or self._current_map_rect.height <= 0:
            return None

        map_kind = self._active_map
        graph = self._camera_connections if map_kind == "main" else self._vent_connections

        best = None
        best_dist = 9999.0
        tolerance = 12.0

        for src, targets in graph.items():
            p1 = self._node_point(map_kind, src, self._current_map_rect)
            if p1 is None:
                continue
            for dst in targets:
                p2 = self._node_point(map_kind, dst, self._current_map_rect)
                if p2 is None:
                    continue
                edge_id = f"{src}->{dst}"
                poly = self._edge_polyline_points(map_kind, edge_id, p1, p2, self._current_map_rect)
                for wp_idx in range(1, len(poly) - 1):
                    wp = poly[wp_idx]
                    dist = ((point[0] - wp[0]) ** 2 + (point[1] - wp[1]) ** 2) ** 0.5
                    if dist <= tolerance and dist < best_dist:
                        best_dist = dist
                        best = (map_kind, edge_id, wp_idx - 1)

        return best

    def _get_line_control_point(self, map_kind, edge_id, p1, p2, map_rect):
        if map_kind == "main":
            rel = self._main_edge_control_points.get(edge_id)
        else:
            rel = self._vent_edge_control_points.get(edge_id)

        if rel is None:
            return ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)

        return (
            map_rect.left + int(rel[0] * map_rect.width),
            map_rect.top + int(rel[1] * map_rect.height),
        )

    def _distance_point_to_segment(self, point, a, b):
        px, py = point
        ax, ay = a
        bx, by = b
        abx = bx - ax
        aby = by - ay
        apx = px - ax
        apy = py - ay
        ab_len_sq = (abx * abx) + (aby * aby)
        if ab_len_sq <= 0:
            dx = px - ax
            dy = py - ay
            return (dx * dx + dy * dy) ** 0.5

        t = (apx * abx + apy * aby) / ab_len_sq
        t = max(0.0, min(1.0, t))
        cx = ax + (abx * t)
        cy = ay + (aby * t)
        dx = px - cx
        dy = py - cy
        return (dx * dx + dy * dy) ** 0.5

    def _hit_test_vent_closure_link(self, point):
        if self._current_map_rect.width <= 0 or self._current_map_rect.height <= 0:
            return None
        if self._active_map != "vents":
            return None

        best = None
        best_dist = 9999.0
        tolerance = 14.0

        for cam_id, edge_list in self._vent_closure_links_by_camera.items():
            p1 = self._node_point("vents", cam_id, self._current_map_rect)
            if p1 is None:
                continue
            for edge_id in edge_list:
                rect = self._vent_block_rects.get(edge_id)
                if rect is None:
                    continue
                p2 = rect.center
                dist = self._distance_point_to_segment(point, p1, p2)
                if dist <= tolerance and dist < best_dist:
                    best_dist = dist
                    best = ("cam", cam_id, edge_id)

        for edge_id, targets in self._vent_closure_links_by_edge.items():
            src_rect = self._vent_block_rects.get(edge_id)
            if src_rect is None:
                continue
            p1 = src_rect.center
            for target_id in targets:
                p2 = self._node_point("vents", target_id, self._current_map_rect)
                if p2 is None:
                    continue
                dist = self._distance_point_to_segment(point, p1, p2)
                if dist <= tolerance and dist < best_dist:
                    best_dist = dist
                    best = ("edge", edge_id, target_id)

        return best

    def _remove_link_at_pos(self, point):
        # Priority: remove direct graph edges first, then optional camera->closure links.
        line_hit = self._hit_test_connection_line(point)
        if line_hit is not None:
            map_kind, edge_id = line_hit
            src, dst = edge_id.split("->", 1)
            graph = self._camera_connections if map_kind == "main" else self._vent_connections
            linked = graph.get(src, [])
            if dst in linked:
                linked.remove(dst)
                if map_kind == "main":
                    self._main_edge_control_points.pop(edge_id, None)
                    self._line_waypoints_main.pop(edge_id, None)
                else:
                    self._vent_edge_control_points.pop(edge_id, None)
                    self._line_waypoints_vents.pop(edge_id, None)
                return True

        closure_hit = self._hit_test_vent_closure_link(point)
        if closure_hit is not None:
            link_type, src_id, dst_id = closure_hit
            if link_type == "cam":
                edge_list = self._vent_closure_links_by_camera.get(src_id, [])
                if dst_id in edge_list:
                    edge_list.remove(dst_id)
                    if not edge_list:
                        self._vent_closure_links_by_camera.pop(src_id, None)
                    return True
            elif link_type == "edge":
                target_list = self._vent_closure_links_by_edge.get(src_id, [])
                if dst_id in target_list:
                    target_list.remove(dst_id)
                    if not target_list:
                        self._vent_closure_links_by_edge.pop(src_id, None)
                    return True

        return False

    def _hit_test_connection_line(self, point):
        if self._current_map_rect.width <= 0 or self._current_map_rect.height <= 0:
            return None

        map_kind = self._active_map
        if map_kind == "main":
            graph = self._camera_connections
            anchors = self._anchors_main
        else:
            graph = self._vent_connections
            anchors = self._anchors_vents

        best = None
        best_dist = 9999.0
        tolerance = 14.0

        for src, targets in graph.items():
            p1 = self._node_point(map_kind, src, self._current_map_rect)
            if p1 is None:
                continue
            for dst in targets:
                p2 = self._node_point(map_kind, dst, self._current_map_rect)
                if p2 is None:
                    continue
                edge_id = f"{src}->{dst}"
                poly = self._edge_polyline_points(map_kind, edge_id, p1, p2, self._current_map_rect)
                for seg_idx in range(len(poly) - 1):
                    dist = self._distance_point_to_segment(point, poly[seg_idx], poly[seg_idx + 1])
                    if dist <= tolerance and dist < best_dist:
                        best_dist = dist
                        best = (map_kind, edge_id, seg_idx)

        return best

    def close(self):
        self.is_open = False

    def set_threat_cameras(self, camera_ids):
        self._threat_cameras = set(camera_ids or [])

    def set_threat_sprite(self, sprite_surface):
        self._threat_sprite = sprite_surface

    def set_threats_by_camera(self, threats_dict):
        self._threat_sprites_by_camera = threats_dict or {}

    def set_camera_error(self, active):
        self._camera_error_active = bool(active)

    def set_vent_blocking_enabled(self, enabled):
        self._vent_blocking_enabled = bool(enabled)

    def set_blocked_vents(self, blocked_camera_ids):
        self._blocked_vent_cameras = set(blocked_camera_ids or [])

    def get_blocked_vents(self):
        return self.get_blocked_vent_edges()

    def set_blocked_vent_edges(self, blocked_edges):
        self._blocked_vent_cameras = set(blocked_edges or [])

    def get_blocked_vent_edges(self):
        blocked = set(self._blocked_vent_cameras)
        pending_edge = self._vent_block_transition.get("edge")
        if pending_edge and self._vent_block_transition.get("target_closed", False):
            blocked.add(pending_edge)
        return blocked

    def build_routes_by_side(self):
        left_target = self._office_targets.get("left", "cam1")
        right_target = self._office_targets.get("right", "cam14")
        left_path = self._find_path("cam10", left_target, self._combined_graph())
        right_path = self._find_path("cam10", right_target, self._combined_graph())

        fallback_left = ["cam10", "cam9", "cam7", "cam6", "cam1"]
        fallback_right = ["cam10", "cam8", "cam12", "cam14"]

        left_route = (left_path if left_path else fallback_left) + ["door_left"]
        right_route = (right_path if right_path else fallback_right) + ["door_right"]
        return {"left": left_route, "right": right_route}

    def build_navigation_graph(self):
        return self._combined_graph()

    def _combined_graph(self):
        graph = {key: list(values) for key, values in self._camera_connections.items()}
        for key, values in self._vent_connections.items():
            graph.setdefault(key, [])
            for value in values:
                if value not in graph[key]:
                    graph[key].append(value)
        return graph

    def _find_path(self, start_id, target_id, graph):
        if start_id == target_id:
            return [start_id]

        queue = deque([[start_id]])
        visited = {start_id}
        while queue:
            path = queue.popleft()
            node = path[-1]
            for nxt in graph.get(node, []):
                if nxt in visited:
                    continue
                new_path = path + [nxt]
                if nxt == target_id:
                    return new_path
                visited.add(nxt)
                queue.append(new_path)
        return []

    def _load_layout_config(self):
        if not os.path.isfile(self._layout_config_path):
            return
        try:
            with open(self._layout_config_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError, json.JSONDecodeError):
            return

        if not isinstance(payload, dict):
            return

        self._anchors_main.update(payload.get("anchors_main", {}))
        self._anchors_vents.update(payload.get("anchors_vents", {}))
        self._button_scale_by_map.update(payload.get("button_scale_by_map", {}))
        self._button_scale_by_camera.update(payload.get("button_scale_by_camera", {}))
        triangles = payload.get("camera_triangle_by_id", {})
        if isinstance(triangles, dict):
            self._camera_triangle_by_id = {str(cam_id): bool(enabled) for cam_id, enabled in triangles.items()}
        vent_sizes = payload.get("vent_block_size_by_edge", {})
        if isinstance(vent_sizes, dict):
            normalized = {}
            for edge_id, size in vent_sizes.items():
                if isinstance(size, (list, tuple)) and len(size) >= 2:
                    normalized[str(edge_id)] = [
                        max(12, int(size[0])),
                        max(8, int(size[1])),
                    ]
            self._vent_block_size_by_edge = normalized
        vent_closure_links = payload.get("vent_closure_links_by_camera", {})
        if isinstance(vent_closure_links, dict):
            normalized = {}
            for cam_id, edge_list in vent_closure_links.items():
                if isinstance(edge_list, list):
                    normalized[str(cam_id)] = [str(edge_id) for edge_id in edge_list]
            self._vent_closure_links_by_camera = normalized
        vent_closure_links_by_edge = payload.get("vent_closure_links_by_edge", {})
        if isinstance(vent_closure_links_by_edge, dict):
            normalized = {}
            for edge_id, target_list in vent_closure_links_by_edge.items():
                if isinstance(target_list, list):
                    normalized[str(edge_id)] = [str(target_id) for target_id in target_list]
            self._vent_closure_links_by_edge = normalized
        main_line_points = payload.get("main_edge_control_points", {})
        if isinstance(main_line_points, dict):
            normalized = {}
            for edge_id, anchor in main_line_points.items():
                if isinstance(anchor, (list, tuple)) and len(anchor) >= 2:
                    normalized[str(edge_id)] = (
                        max(0.02, min(0.98, float(anchor[0]))),
                        max(0.02, min(0.98, float(anchor[1]))),
                    )
            self._main_edge_control_points = normalized
        main_waypoints = payload.get("line_waypoints_main", {})
        if isinstance(main_waypoints, dict):
            normalized = {}
            for edge_id, points in main_waypoints.items():
                if not isinstance(points, list):
                    continue
                vals = []
                for pt in points:
                    if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                        vals.append((max(0.02, min(0.98, float(pt[0]))), max(0.02, min(0.98, float(pt[1])))))
                normalized[str(edge_id)] = vals
            self._line_waypoints_main = normalized
        vent_line_points = payload.get("vent_edge_control_points", {})
        if isinstance(vent_line_points, dict):
            normalized = {}
            for edge_id, anchor in vent_line_points.items():
                if isinstance(anchor, (list, tuple)) and len(anchor) >= 2:
                    normalized[str(edge_id)] = (
                        max(0.02, min(0.98, float(anchor[0]))),
                        max(0.02, min(0.98, float(anchor[1]))),
                    )
            self._vent_edge_control_points = normalized
        vent_waypoints = payload.get("line_waypoints_vents", {})
        if isinstance(vent_waypoints, dict):
            normalized = {}
            for edge_id, points in vent_waypoints.items():
                if not isinstance(points, list):
                    continue
                vals = []
                for pt in points:
                    if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                        vals.append((max(0.02, min(0.98, float(pt[0]))), max(0.02, min(0.98, float(pt[1])))))
                normalized[str(edge_id)] = vals
            self._line_waypoints_vents = normalized
        vent_anchors = payload.get("vent_block_anchor_by_edge", {})
        if isinstance(vent_anchors, dict):
            normalized = {}
            for edge_id, anchor in vent_anchors.items():
                if isinstance(anchor, (list, tuple)) and len(anchor) >= 2:
                    rel_x = max(0.02, min(0.98, float(anchor[0])))
                    rel_y = max(0.02, min(0.98, float(anchor[1])))
                    normalized[str(edge_id)] = (rel_x, rel_y)
            self._vent_block_anchor_by_edge = normalized
        self._vent_block_anchor_by_camera.update(payload.get("vent_block_anchor_by_camera", {}))
        self._camera_connections = payload.get("camera_connections", self._camera_connections)
        self._vent_connections = payload.get("vent_connections", self._vent_connections)
        closure_edges = payload.get("vent_closure_edge_ids", None)
        if isinstance(closure_edges, list):
            self._vent_closure_edge_ids = {str(edge_id) for edge_id in closure_edges if isinstance(edge_id, str)}
        else:
            self._vent_closure_edge_ids = {
                f"{src}->{dst}"
                for src, targets in self._vent_connections.items()
                for dst in targets
            }
        self._vent_closure_edge_ids.update(
            {
                f"{src}->{dst}"
                for src, targets in self._vent_connections.items()
                for dst in targets
            }
        )
        self._vent_closure_edge_ids.add("cam15->office_right")
        self._office_targets.update(payload.get("office_targets", {}))

    def save_layout_config(self):
        payload = {
            "anchors_main": self._anchors_main,
            "anchors_vents": self._anchors_vents,
            "button_scale_by_map": self._button_scale_by_map,
            "button_scale_by_camera": self._button_scale_by_camera,
            "camera_triangle_by_id": self._camera_triangle_by_id,
            "vent_block_size_by_edge": self._vent_block_size_by_edge,
            "vent_closure_links_by_camera": self._vent_closure_links_by_camera,
            "vent_closure_links_by_edge": self._vent_closure_links_by_edge,
            "main_edge_control_points": self._main_edge_control_points,
            "vent_edge_control_points": self._vent_edge_control_points,
            "line_waypoints_main": self._line_waypoints_main,
            "line_waypoints_vents": self._line_waypoints_vents,
            "vent_block_anchor_by_edge": self._vent_block_anchor_by_edge,
            "vent_block_anchor_by_camera": self._vent_block_anchor_by_camera,
            "camera_connections": self._camera_connections,
            "vent_connections": self._vent_connections,
            "vent_closure_edge_ids": sorted(self._vent_closure_edge_ids),
            "office_targets": self._office_targets,
        }
        os.makedirs(os.path.dirname(self._layout_config_path), exist_ok=True)
        try:
            with open(self._layout_config_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=True, indent=2)
        except OSError:
            return False
        return True

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
        self._cam_button_rect_by_id = {}
        if not self._feeds:
            return

        anchors = self._anchors_main if self._active_map == "main" else self._anchors_vents
        visible_ids = set(anchors.keys())

        map_scale = float(self._button_scale_by_map.get(self._active_map, 1.0))
        button_w = max(42, int(map_rect.width * 0.13 * map_scale))
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

            cam_scale = float(self._button_scale_by_camera.get(cam_id, 1.0))
            cam_w = max(32, int(button_w * cam_scale))
            cam_h = max(22, int(button_h * cam_scale))

            x = map_rect.left + int(anchor[0] * map_rect.width) - cam_w // 2
            y = map_rect.top + int(anchor[1] * map_rect.height) - cam_h // 2
            x = max(map_rect.left + pad, min(x, map_rect.right - cam_w - pad))
            y = max(map_rect.top + pad, min(y, map_rect.bottom - cam_h - pad))
            rect = pygame.Rect(x, y, cam_w, cam_h)
            self._cam_button_rects.append((idx, rect))
            self._cam_button_rect_by_id[cam_id] = rect

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

    def _draw_connection_lines(self, surface, map_rect):
        if self._active_map == "main":
            for src, targets in self._camera_connections.items():
                p1 = self._node_point("main", src, map_rect)
                if p1 is None:
                    continue
                for dst in targets:
                    p2 = self._node_point("main", dst, map_rect)
                    if p2 is None:
                        continue
                    edge_id = f"{src}->{dst}"
                    poly = self._edge_polyline_points("main", edge_id, p1, p2, map_rect)
                    pygame.draw.lines(surface, (80, 116, 134), False, poly, 2)
                    if self._admin_mode:
                        for wp in poly[1:-1]:
                            pygame.draw.circle(surface, (172, 210, 226), wp, 5)
        else:
            for src, targets in self._vent_connections.items():
                p1 = self._node_point("vents", src, map_rect)
                if p1 is None:
                    continue
                for dst in targets:
                    p2 = self._node_point("vents", dst, map_rect)
                    if p2 is None:
                        continue
                    edge_id = f"{src}->{dst}"
                    poly = self._edge_polyline_points("vents", edge_id, p1, p2, map_rect)
                    pygame.draw.lines(surface, (96, 96, 118), False, poly, 2)
                    if self._admin_mode:
                        for wp in poly[1:-1]:
                            pygame.draw.circle(surface, (192, 192, 216), wp, 5)

    def _draw_vent_block_rects(self, surface, map_rect):
        self._vent_block_rects = {}
        if self._active_map != "vents":
            return

        now_ms = pygame.time.get_ticks()

        edge_ids = set()
        for src, targets in self._vent_connections.items():
            for dst in targets:
                edge_ids.add(f"{src}->{dst}")
        edge_ids.update(self._vent_closure_edge_ids)
        edge_ids.update(self._vent_block_size_by_edge.keys())
        edge_ids.update(self._vent_block_anchor_by_edge.keys())
        edge_ids.update(self._blocked_vent_cameras)
        edge_ids.update(self._vent_closure_links_by_edge.keys())
        for edge_list in self._vent_closure_links_by_camera.values():
            for edge_id in edge_list:
                edge_ids.add(edge_id)

        for edge_id in edge_ids:
            if "->" not in edge_id:
                continue
            src, dst = edge_id.split("->", 1)
            p1 = self._node_point("vents", src, map_rect)
            p2 = self._node_point("vents", dst, map_rect)
            if p1 is None or p2 is None:
                continue

            block_size = self._vent_block_size_by_edge.get(edge_id, [34, 18])
            rect = pygame.Rect(0, 0, int(block_size[0]), int(block_size[1]))
            anchor = self._vent_block_anchor_by_edge.get(edge_id)
            if anchor is None:
                center = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
            else:
                center = (
                    map_rect.left + int(anchor[0] * map_rect.width),
                    map_rect.top + int(anchor[1] * map_rect.height),
                )
            rect.center = center
            self._vent_block_rects[edge_id] = rect

            blocked = edge_id in self._blocked_vent_cameras
            is_pending = self._vent_block_transition.get("edge") == edge_id and now_ms < int(self._vent_block_transition.get("until", 0) or 0)
            if not self._vent_blocking_enabled:
                fill = (88, 88, 88)
                border = (160, 160, 160)
            elif is_pending:
                blink_phase = ((now_ms // 120) % 2) == 0
                fill = (226, 138, 56) if blink_phase else (250, 190, 92)
                border = (255, 235, 160)
            elif blocked:
                fill = (210, 80, 48)
                border = (255, 190, 130)
            else:
                fill = (70, 190, 88)
                border = (178, 255, 196)

            pygame.draw.rect(surface, fill, rect)
            pygame.draw.rect(surface, border, rect, width=2)

            if self._admin_mode and self._admin_selected_vent_edge == edge_id:
                pygame.draw.rect(surface, (255, 222, 132), rect.inflate(6, 6), width=2)

        if self._admin_mode:
            # Optional links from vent cameras/blocks to closure rectangles are admin-only traces.
            for cam_id, edge_list in self._vent_closure_links_by_camera.items():
                p1 = self._node_point("vents", cam_id, map_rect)
                if p1 is None:
                    continue
                for edge_id in edge_list:
                    rect = self._vent_block_rects.get(edge_id)
                    if rect is None:
                        continue
                    p2 = rect.center
                    pygame.draw.line(surface, (222, 178, 92), p1, p2, 2)

            for edge_id, targets in self._vent_closure_links_by_edge.items():
                src_rect = self._vent_block_rects.get(edge_id)
                if src_rect is None:
                    continue
                p1 = src_rect.center
                for target_id in targets:
                    p2 = self._node_point("vents", target_id, map_rect)
                    if p2 is None:
                        continue
                    pygame.draw.line(surface, (248, 206, 116), p1, p2, 2)

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

    def _draw_cam_triangle(self, surface, cam_rect, enabled, is_selected):
        if not enabled:
            return

        tri_w = max(8, int(cam_rect.width * 0.24))
        tri_h = max(8, int(cam_rect.height * 0.56))
        center_y = cam_rect.centery
        base_x = cam_rect.right - 1
        points = [
            (base_x, center_y - tri_h // 2),
            (base_x, center_y + tri_h // 2),
            (base_x + tri_w, center_y),
        ]

        fill = (238, 242, 248) if is_selected else (210, 216, 226)
        border = (28, 32, 36)
        pygame.draw.polygon(surface, fill, points)
        pygame.draw.polygon(surface, border, points, width=2)

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
            self._cam_switch_sound_obj.set_volume(0.45)
            self._cam_switch_sound_obj.play()
        except pygame.error:
            return

    def draw_overlay(self, surface):
        if not self.is_open:
            return

        now_ms = pygame.time.get_ticks()
        self._update_vent_block_transition(now_ms)

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
        self._current_map_rect = map_rect.copy()
        self._build_cam_button_rects(map_rect)
        self._build_external_node_rects(map_rect)

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
        if self._camera_error_active:
            blackout = pygame.Surface((feed_area.width, feed_area.height), pygame.SRCALPHA)
            blackout.fill((0, 0, 0, 245))
            surface.blit(blackout, feed_area.topleft)
            label = self.title_font.render("CAM ERROR", True, (255, 80, 80))
            surface.blit(label, label.get_rect(center=feed_area.center))
        else:
            noise_intensity = 1.55 if not active_jammed else 3.8
            self._draw_feed_noise(surface, feed_area, intensity=noise_intensity)
            self._draw_feed_glitch(surface, feed_area, intensity=noise_intensity)

            if active_jammed:
                self._draw_total_jam(surface, feed_area)

        active_camera_id = active_feed["camera_id"]
        if (not self._camera_error_active) and (not active_jammed) and active_camera_id in self._threat_sprites_by_camera:
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
        elif (not self._camera_error_active) and (not active_jammed) and active_camera_id in self._threat_cameras and self._threat_sprite is not None:
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
        if self._admin_mode:
            self._draw_connection_lines(surface, map_rect)
        if self._active_map == "vents":
            self._draw_vent_block_rects(surface, map_rect)
        if self._admin_mode:
            self._draw_external_nodes(surface)

        for idx, cam_rect in self._cam_button_rects:
            feed = self._feeds[idx]
            is_selected = idx == self._selected_feed_idx
            is_blocked_vent = self._active_map == "vents" and feed["camera_id"] in self._blocked_vent_cameras

            if is_selected:
                fill = (112, 150, 20)
                border = (226, 255, 140)
            elif is_blocked_vent:
                fill = (186, 92, 26)
                border = (255, 182, 118)
            else:
                fill = (58, 62, 69)
                border = (188, 194, 203)

            pygame.draw.rect(surface, fill, cam_rect)
            pygame.draw.rect(surface, border, cam_rect, width=2)

            triangle_enabled = bool(self._camera_triangle_by_id.get(feed["camera_id"], False))
            self._draw_cam_triangle(surface, cam_rect, triangle_enabled, is_selected)

            cam_number = feed["label"].replace("CAM ", "").strip()
            top = self.label_font.render("CAM", True, (238, 242, 248))
            bottom = self.label_font.render(cam_number, True, (238, 242, 248))
            top = pygame.transform.smoothscale(top, (max(20, cam_rect.width - 10), max(12, cam_rect.height // 2 - 2)))
            bottom = pygame.transform.smoothscale(bottom, (max(12, cam_rect.width - 16), max(10, cam_rect.height // 2 - 2)))
            surface.blit(top, top.get_rect(center=(cam_rect.centerx, cam_rect.top + cam_rect.height * 0.3)))
            surface.blit(bottom, bottom.get_rect(center=(cam_rect.centerx, cam_rect.top + cam_rect.height * 0.72)))

        if self._admin_mode:
            hint = self.label_font.render("ADMIN: drag=move | double-click line=add node | drag node=shape path | vent: double-click close/open (1 only) | drag+wheel, shift+wheel=H | right-click line=remove | right-click cam/node/vent-rect=toggle link | middle=triangle | S=save", True, (255, 192, 96))
            surface.blit(hint, hint.get_rect(bottomleft=(self.panel_rect.left + 16, self.panel_rect.bottom - 12)))
