from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import random
from collections import deque


@dataclass
class Animatronic:
	name: str
	route: List[str]
	base_move_chance: float = 0.12
	watched_camera_penalty: float = 0.78
	step_cooldown_ms: int = 3500
	stun_duration_ms: int = 1600
	attack_delay_ms: int = 3200
	can_trigger_error: bool = False
	error_trigger_chance: float = 0.55

	def __post_init__(self):
		if not self.route:
			raise ValueError(f"La route di {self.name} non puo essere vuota")
		self.reset_state()

	def reset_state(self) -> None:
		self.route_index = 0
		self.next_move_at = 0
		self.stunned_until = 0
		self.door_entered_at = 0
		self.watched_since_at = 0
		self.next_error_at = 0
		self.blocked_vent_since_at = 0

	def set_route(self, route: List[str]) -> None:
		if not route:
			raise ValueError(f"La route di {self.name} non puo essere vuota")
		self.route = route
		self.reset_state()

	def shift_timers(self, delta_ms: int) -> None:
		if delta_ms <= 0:
			return
		self.next_move_at += delta_ms
		self.stunned_until += delta_ms
		if self.door_entered_at > 0:
			self.door_entered_at += delta_ms
		if self.blocked_vent_since_at > 0:
			self.blocked_vent_since_at += delta_ms

	@property
	def current_camera(self) -> str:
		return self.route[self.route_index]

	def is_at_office_door(self) -> bool:
		return self.current_camera.startswith("door")

	def is_near_office_door(self) -> bool:
		# Near door means one step before the final "door" node.
		if len(self.route) < 2:
			return False
		return self.route_index >= len(self.route) - 2

	def is_visible_on_cameras(self) -> bool:
		return not self.is_at_office_door()

	def peek_next_camera(self) -> Optional[str]:
		if self.route_index >= len(self.route) - 1:
			return None
		return self.route[self.route_index + 1]

	def _hour_pressure(self, hour_index: int) -> float:
		hour_multipliers = [0.55, 0.72, 0.88, 1.02, 1.16, 1.30]
		return hour_multipliers[max(0, min(len(hour_multipliers) - 1, hour_index))]

	def _night_pressure(self, night_level: int) -> float:
		night_scale = {
			1: 0.48,
			2: 0.70,
			3: 0.88,
			4: 1.05,
			5: 1.28,
		}
		return night_scale.get(max(1, night_level), 1.28)

	def _schedule_next_move(self, now_ms: int, night_level: int, hour_index: int = 0) -> None:
		# Later nights shorten the pause between movement attempts.
		delay = max(700, self.step_cooldown_ms - 320 - (night_level * 220) - (hour_index * 90))
		self.next_move_at = now_ms + delay

	def stun(self, now_ms: int) -> None:
		self.stunned_until = max(self.stunned_until, now_ms + self.stun_duration_ms)

	def repel_with_flashlight(self, now_ms: int) -> bool:
		# Error-type animatronics are not repelled by flashlight by design.
		if self.can_trigger_error:
			return False

		is_flash_repel_zone = self.is_near_office_door()
		if not is_flash_repel_zone:
			return False

		self.stun(now_ms)
		self.door_entered_at = 0
		self.watched_since_at = 0

		# Push farther than the last pre-door node to prevent flashlight spam at cam1/cam14.
		target_index = max(0, len(self.route) - 4)
		if self.route_index > target_index:
			self.route_index = target_index
		else:
			self.route_index = max(0, self.route_index - 1)

		# Delay the next move so the repel is clearly visible in gameplay.
		self.next_move_at = max(self.next_move_at, now_ms + 1700)
		return True

	def try_advance(
		self,
		now_ms: int,
		rng: random.Random,
		night_level: int,
		hour_index: int,
		watched_camera: Optional[str] = None,
		blocked_edges: Optional[Set[str]] = None,
	) -> bool:
		if now_ms < self.next_move_at or now_ms < self.stunned_until:
			return False

		if self.route_index >= len(self.route) - 1:
			self._schedule_next_move(now_ms, night_level, hour_index)
			return False

		# Combine hour-of-night pacing with the selected night difficulty.
		hour_pressure = self._hour_pressure(hour_index)
		night_pressure = self._night_pressure(night_level)
		chance = min(0.98, self.base_move_chance * hour_pressure * night_pressure)
		if watched_camera == self.current_camera:
			chance *= self.watched_camera_penalty

		moved = rng.random() < chance
		if moved:
			extra_step_chance = min(0.78, 0.12 + (hour_pressure * 0.18) + (night_pressure * 0.10))
			steps_to_take = 1
			if rng.random() < extra_step_chance:
				steps_to_take += 1
			steps_to_take = min(2, steps_to_take)

			# Near the office door, force single-step movement to avoid unfair "teleport" pressure.
			remaining_to_door = max(0, (len(self.route) - 1) - self.route_index)
			if remaining_to_door <= 3:
				steps_to_take = 1

			for _ in range(steps_to_take):
				next_camera = self.peek_next_camera()
				edge_id = f"{self.current_camera}->{next_camera}" if next_camera else None
				if blocked_edges and edge_id in blocked_edges:
					self.route_index = max(0, self.route_index - 1)
					if self.current_camera.startswith("door"):
						self.door_entered_at = 0
					self._schedule_next_move(now_ms, night_level, hour_index)
					return False

				if self.route_index >= len(self.route) - 1:
					break
				self.route_index += 1
				if self.is_at_office_door():
					self.door_entered_at = now_ms
					break

		self._schedule_next_move(now_ms, night_level, hour_index)
		return moved

	def should_jumpscare(self, now_ms: int, player_can_defend: bool = True, hour_index: int = 0, night_level: int = 1) -> bool:
		if not self.is_at_office_door():
			return False
		if hour_index < 1:
			# The first hour is safe by design: the player can scout without getting punished.
			self.door_entered_at = 0
			return False
		if not player_can_defend:
			# Keep pressure without unfair instant kills while flashlight is unavailable.
			self.door_entered_at = now_ms
			return False
		if now_ms < self.stunned_until:
			return False
		if self.door_entered_at <= 0:
			self.door_entered_at = now_ms

		# Keep lethal attacks tense but readable: the player must have time to react after door arrival.
		attack_delay = max(2200, self.attack_delay_ms - ((max(1, min(5, night_level)) - 1) * 120) - (hour_index * 80))
		return (now_ms - self.door_entered_at) >= attack_delay


class AnimatronicsManager:
	def __init__(self, animatronics: List[Animatronic], routes_by_side: Dict[str, List[str]], seed: Optional[int] = None):
		self.rng = random.Random(seed)
		self.animatronics: Dict[str, Animatronic] = {a.name: a for a in animatronics}
		self.routes_by_side = routes_by_side
		self.roster_order = list(self.animatronics.keys())
		self.navigation_graph: Dict[str, List[str]] = {}
		self.route_side_by_name: Dict[str, str] = {}
		self.visibility_enabled_at: Dict[str, int] = {}
		self.side_attack_cooldown_until: Dict[str, int] = {"left": 0, "right": 0}
		self.side_attack_cooldown_ms: int = 2300
		self.last_dynamic_reroute_at: Dict[str, int] = {}
		self.dynamic_reroute_cooldown_ms: int = 2600
		self.dynamic_reroute_chance: float = 0.26

	def _active_names_for_night(self, night_level: int) -> List[str]:
		active_count = max(1, min(len(self.roster_order), night_level))
		return self.roster_order[:active_count]

	def _assign_random_routes(self) -> None:
		names = list(self.animatronics.keys())
		self.rng.shuffle(names)

		half = len(names) // 2
		left_group = set(names[:half])

		for name in names:
			side = "left" if name in left_group else "right"
			# Small random flip each reset to avoid repeated predictable pairings.
			if self.rng.random() < 0.25:
				side = "right" if side == "left" else "left"
			self.route_side_by_name[name] = side
			if self.navigation_graph:
				start_node = "cam9"
				if self.animatronics[name].can_trigger_error:
					start_node = self._pick_random_spawn_node(side)
				route = self._build_route_with_choices(start_node=start_node, side=side)
			else:
				route = self.routes_by_side[side]
			self.animatronics[name].set_route(route)

	def _pick_random_spawn_node(self, side: str) -> str:
		primary_targets = {"cam1", "office_left"} if side == "left" else {"cam14", "office_right"}
		dist_map = self._reverse_distances(primary_targets)
		if not dist_map:
			fallback_nodes = [node for node in self.navigation_graph.keys() if node.startswith("cam") and node != "cam10"]
			return self.rng.choice(fallback_nodes) if fallback_nodes else "cam10"

		candidates = []
		for node, dist in dist_map.items():
			if not node.startswith("cam"):
				continue
			if node == "cam10":
				continue
			if dist <= 0:
				continue
			candidates.append((node, dist))

		if not candidates:
			fallback_nodes = [node for node in self.navigation_graph.keys() if node.startswith("cam") and node != "cam10"]
			return self.rng.choice(fallback_nodes) if fallback_nodes else "cam10"

		# Prefer a wider spread of starting positions so error animatronics do not appear too close to the office.
		far_candidates = [item for item in candidates if item[1] >= 3]
		pool = far_candidates if far_candidates else candidates
		weights = [min(6.0, 1.0 + (dist * 0.35)) for _, dist in pool]
		chosen = self.rng.choices(pool, weights=weights, k=1)[0][0]
		return chosen

	def _camera_number(self, node_id: str) -> Optional[int]:
		if not isinstance(node_id, str) or not node_id.startswith("cam"):
			return None
		try:
			return int(node_id.replace("cam", ""))
		except ValueError:
			return None

	def _is_reasonable_camera_edge(self, src: str, dst: str) -> bool:
		if not isinstance(src, str) or not isinstance(dst, str):
			return False
		if src.startswith("door") or dst.startswith("door") or src.startswith("office") or dst.startswith("office"):
			return True

		src_num = self._camera_number(src)
		dst_num = self._camera_number(dst)
		if src_num is None or dst_num is None:
			return True
		return abs(src_num - dst_num) <= 2

	def set_navigation_graph(self, graph: Dict[str, List[str]]) -> None:
		normalized = {}
		for src, targets in (graph or {}).items():
			if not isinstance(targets, list):
				continue
			src_id = str(src)
			filtered_targets = []
			for dst in targets:
				if not isinstance(dst, str):
					continue
				if self._is_reasonable_camera_edge(src_id, dst):
					filtered_targets.append(dst)
			normalized[src_id] = filtered_targets
		self.navigation_graph = normalized

	def _reverse_distances(self, target_nodes: Set[str]) -> Dict[str, int]:
		reverse: Dict[str, List[str]] = {}
		for src, targets in self.navigation_graph.items():
			for dst in targets:
				reverse.setdefault(dst, []).append(src)

		dist: Dict[str, int] = {}
		queue = deque()
		for target in target_nodes:
			dist[target] = 0
			queue.append(target)

		while queue:
			node = queue.popleft()
			for prev in reverse.get(node, []):
				if prev in dist:
					continue
				dist[prev] = dist[node] + 1
				queue.append(prev)
		return dist

	def _find_shortest_path_with_blocks(self, start_node: str, target_nodes: Set[str], blocked_nodes: Optional[Set[str]] = None) -> List[str]:
		blocked = set(blocked_nodes or set())
		if start_node in blocked:
			return []

		queue = deque([[start_node]])
		visited = {start_node}
		while queue:
			path = queue.popleft()
			node = path[-1]
			if node in target_nodes:
				return path

			for nxt in self.navigation_graph.get(node, []):
				if nxt in visited or nxt in blocked:
					continue
				visited.add(nxt)
				queue.append(path + [nxt])
		return []

	def _build_route_with_choices(self, start_node: str, side: str, avoid_nodes: Optional[Set[str]] = None) -> List[str]:
		blocked_nodes = set(avoid_nodes or [])
		primary_targets = {"cam1", "office_left"} if side == "left" else {"cam14", "office_right"}
		primary_dist = self._reverse_distances(primary_targets)

		def _stochastic_walk(target_nodes: Set[str], dist_map: Dict[str, int]) -> List[str]:
			if start_node in blocked_nodes or start_node not in dist_map:
				return []

			route = [start_node]
			visited = {start_node}
			current = start_node
			max_steps = 26

			for _ in range(max_steps):
				if current in target_nodes:
					break

				neighbors = [
					n for n in self.navigation_graph.get(current, [])
					if n in dist_map and n not in blocked_nodes
				]
				if not neighbors:
					break

				best_dist = min(dist_map[n] for n in neighbors)
				slack = 1 if self.rng.random() < 0.70 else 2
				good = [n for n in neighbors if dist_map[n] <= best_dist + slack]
				unvisited_good = [n for n in good if n not in visited]
				pool = unvisited_good if unvisited_good else good
				nxt = self.rng.choice(pool)

				route.append(nxt)
				visited.add(nxt)
				current = nxt

			if route and route[-1] in target_nodes:
				return route
			return []

		path = _stochastic_walk(primary_targets, primary_dist)
		if not path:
			path = self._find_shortest_path_with_blocks(start_node, primary_targets, blocked_nodes)

		if not path:
			alt_targets = {"cam14", "office_right"} if side == "left" else {"cam1", "office_left"}
			alt_dist = self._reverse_distances(alt_targets)
			path = _stochastic_walk(alt_targets, alt_dist)
			if not path:
				path = self._find_shortest_path_with_blocks(start_node, alt_targets, blocked_nodes)

		if not path:
			fallback = list(self.routes_by_side.get(side, []))
			if fallback:
				if start_node in fallback:
					return fallback[fallback.index(start_node):]
				return [start_node] + fallback
			door_side = side if side in ("left", "right") else "right"
			return [start_node, f"door_{door_side}"]

		end_node = path[-1]
		door = "door_left" if end_node in ("cam1", "office_left") else "door_right"
		if path[-1] != door:
			path.append(door)
		return path

	def reset(self) -> None:
		self._assign_random_routes()
		self.visibility_enabled_at.clear()
		self.last_dynamic_reroute_at.clear()

	def set_error_animatronic_visibility_delay(self, now_ms: int, delay_ms: int, night_level: int = 1) -> None:
		"""Set when error-causing animatronics become visible. Before this time, they won't appear on cameras."""
		night_level = max(1, int(night_level or 1))
		night_reduction_ms = min(22000, (night_level - 1) * 3500)
		base_visibility_time = now_ms + max(15000, delay_ms - night_reduction_ms)
		for name, animatronic in self.animatronics.items():
			if not animatronic.can_trigger_error:
				continue
			name_offset_ms = 0
			if name == "Luca":
				name_offset_ms = 5000
			elif name == "Linux":
				name_offset_ms = 0
			self.visibility_enabled_at[name] = base_visibility_time + name_offset_ms

	def shift_timers(self, delta_ms: int) -> None:
		if delta_ms <= 0:
			return
		for animatronic in self.animatronics.values():
			animatronic.shift_timers(delta_ms)

	def set_routes_by_side(self, routes_by_side: Dict[str, List[str]]) -> None:
		left_route = list(routes_by_side.get("left", []))
		right_route = list(routes_by_side.get("right", []))
		if not left_route or not right_route:
			return
		self.routes_by_side = {
			"left": left_route,
			"right": right_route,
		}
		self.reset()

	def _reroute_from_current(self, animatronic: Animatronic, side: str) -> None:
		if not self.navigation_graph:
			return
		if animatronic.is_at_office_door():
			return

		start_node = animatronic.current_camera
		new_route = self._build_route_with_choices(start_node=start_node, side=side)
		if not new_route:
			return

		old_next_move = animatronic.next_move_at
		old_stunned = animatronic.stunned_until
		old_door_entered = animatronic.door_entered_at
		animatronic.route = new_route
		animatronic.route_index = 0
		animatronic.next_move_at = old_next_move
		animatronic.stunned_until = old_stunned
		animatronic.door_entered_at = old_door_entered

	def _maybe_dynamic_reroute(self, animatronic: Animatronic, side: str, now_ms: int) -> None:
		if not self.navigation_graph or animatronic.is_at_office_door():
			return
		last_at = int(self.last_dynamic_reroute_at.get(animatronic.name, 0) or 0)
		if now_ms - last_at < self.dynamic_reroute_cooldown_ms:
			return
		if self.rng.random() > self.dynamic_reroute_chance:
			return
		self._reroute_from_current(animatronic, side)
		self.last_dynamic_reroute_at[animatronic.name] = now_ms

	def _route_side(self, animatronic: Animatronic) -> str:
		if animatronic.route and animatronic.route[-1] == "door_left":
			return "left"
		if animatronic.route and animatronic.route[-1] == "door_right":
			return "right"
		return self.route_side_by_name.get(animatronic.name, "right")

	def _set_side_attack_cooldown(self, side: str, now_ms: int, extra_ms: int = 0) -> None:
		if side not in self.side_attack_cooldown_until:
			return
		until = now_ms + max(0, int(self.side_attack_cooldown_ms + extra_ms))
		self.side_attack_cooldown_until[side] = max(int(self.side_attack_cooldown_until.get(side, 0) or 0), until)

	def _is_side_in_attack_cooldown(self, side: str, now_ms: int) -> bool:
		return now_ms < int(self.side_attack_cooldown_until.get(side, 0) or 0)

	def update(
		self,
		now_ms: int,
		night_level: int,
		hour_index: int,
		watched_camera: Optional[str],
		blocked_vent_cameras: Optional[Set[str]] = None,
		player_can_defend: bool = True,
		active_system_errors: Optional[Set[str]] = None,
	) -> List[dict]:
		events: List[dict] = []
		active_error_set = set(active_system_errors or set())
		active_names = set(self._active_names_for_night(night_level))
		blocked_edges = set(blocked_vent_cameras or [])
		blocked_vent_nodes: Set[str] = set()
		for edge_id in blocked_edges:
			if "->" not in edge_id:
				continue
			src, dst = edge_id.split("->", 1)
			for node in (src, dst):
				if node.startswith("cam"):
					try:
						idx = int(node.replace("cam", ""))
					except ValueError:
						continue
					if 11 <= idx <= 15:
						blocked_vent_nodes.add(node)
		blocked_nodes: Set[str] = {
			a.current_camera for a in self.animatronics.values() if a.current_camera in ("door_left", "door_right")
		}
		side_presence = {
			"left": {"lethal": 0, "error": 0},
			"right": {"lethal": 0, "error": 0},
		}
		for other in self.animatronics.values():
			if other.name not in active_names:
				continue
			if not other.is_near_office_door():
				continue
			other_side = self._route_side(other)
			if other_side not in side_presence:
				continue
			bucket = "error" if other.can_trigger_error else "lethal"
			side_presence[other_side][bucket] += 1
		mixed_near_door_sides = {
			side_name
			for side_name, payload in side_presence.items()
			if payload["error"] > 0 and payload["lethal"] > 0
		}

		update_order = list(self.animatronics.values())
		self.rng.shuffle(update_order)

		for animatronic in update_order:
			if animatronic.name not in active_names:
				continue

			side = self._route_side(animatronic)

			if (
				(not animatronic.can_trigger_error)
				and side in ("left", "right")
				and self._is_side_in_attack_cooldown(side, now_ms)
				and animatronic.is_near_office_door()
				and (not animatronic.is_at_office_door())
			):
				animatronic.door_entered_at = 0
				animatronic.watched_since_at = 0
				if animatronic.route_index > 0:
					animatronic.route_index -= 1
				animatronic.stun(now_ms)
				animatronic.next_move_at = max(animatronic.next_move_at, now_ms + 900)
				continue

			# Prevent mixed-type stack on the same side near office: error-type yields and reroutes.
			if animatronic.can_trigger_error and side in mixed_near_door_sides and animatronic.is_near_office_door():
				animatronic.route_index = max(0, animatronic.route_index - 1)
				animatronic.door_entered_at = 0
				animatronic.watched_since_at = 0
				animatronic.stun(now_ms)
				animatronic.next_move_at = max(animatronic.next_move_at, now_ms + 1400)
				if side in ("left", "right"):
					opposite_side = "right" if side == "left" else "left"
					self._reroute_from_current(animatronic, opposite_side)
				continue

			if animatronic.current_camera in blocked_vent_nodes:
				if animatronic.blocked_vent_since_at <= 0:
					animatronic.blocked_vent_since_at = now_ms
					animatronic.stun(now_ms)
					animatronic.door_entered_at = 0
					animatronic.watched_since_at = 0
					animatronic.next_move_at = max(animatronic.next_move_at, now_ms + 900)
					continue

				blocked_wait_ms = 1400
				if now_ms - animatronic.blocked_vent_since_at < blocked_wait_ms:
					continue

				# After waiting a bit, try to reroute around the closed vent.
				old_next_move = animatronic.next_move_at
				old_stunned_until = animatronic.stunned_until
				animatronic.stun(now_ms)
				animatronic.door_entered_at = 0
				animatronic.watched_since_at = 0
				animatronic.next_move_at = max(animatronic.next_move_at, now_ms + 1200)
				if animatronic.can_trigger_error:
					animatronic.next_error_at = max(animatronic.next_error_at, now_ms + 3200)
				if animatronic.route_index > 0:
					retreat_node = animatronic.route[animatronic.route_index - 1]
					if side:
						retreat_route = self._build_route_with_choices(
							start_node=retreat_node,
							side=side,
							avoid_nodes=blocked_vent_nodes | {animatronic.current_camera},
						)
						animatronic.set_route(retreat_route)
						animatronic.route_index = 0
						animatronic.stunned_until = max(animatronic.stunned_until, old_stunned_until, now_ms + 1200)
						animatronic.next_move_at = max(animatronic.next_move_at, old_next_move, now_ms + 1200)
					else:
						animatronic.route_index -= 1
				elif side and self.routes_by_side.get(side):
					fallback_route = list(self.routes_by_side[side])
					animatronic.set_route(fallback_route)
					animatronic.route_index = 0
					animatronic.stunned_until = max(animatronic.stunned_until, old_stunned_until, now_ms + 1200)
					animatronic.next_move_at = max(animatronic.next_move_at, old_next_move, now_ms + 1200)
				animatronic.blocked_vent_since_at = 0
				continue
			else:
				animatronic.blocked_vent_since_at = 0
			if side:
				self._maybe_dynamic_reroute(animatronic, side, now_ms)

			# Error-type animatronics can't move or attack until they become visible
			if animatronic.can_trigger_error and not self._is_animatronic_visible(animatronic.name, now_ms):
				continue

			before = animatronic.current_camera
			if animatronic.try_advance(
				now_ms=now_ms,
				rng=self.rng,
				night_level=night_level,
				hour_index=hour_index,
				watched_camera=watched_camera,
				blocked_edges=blocked_edges,
			):
				if animatronic.current_camera in ("door_left", "door_right"):
					if animatronic.current_camera in blocked_nodes:
						animatronic.route_index = max(0, animatronic.route_index - 1)
						animatronic.door_entered_at = 0
						animatronic.stun(now_ms)
						continue
					blocked_nodes.add(animatronic.current_camera)
					self._set_side_attack_cooldown(side, now_ms)

				after = animatronic.current_camera
				if after != before:
					events.append(
						{
							"type": "moved",
							"name": animatronic.name,
							"from": before,
							"to": after,
						}
					)

			if animatronic.can_trigger_error:
				is_watched = (
					watched_camera is not None
					and animatronic.is_visible_on_cameras()
					and watched_camera == animatronic.current_camera
				)

				if animatronic.is_at_office_door() and is_watched and now_ms >= animatronic.next_error_at:
					available_error_types = [e for e in ("camera", "ventilation", "flashlight") if e not in active_error_set]
					if available_error_types:
						# At the office door, error-type animatronics must create concrete pressure.
						count = 2 if (len(available_error_types) >= 2 and self.rng.random() < 0.28) else 1
						count = min(count, len(available_error_types))
						triggered_errors = self.rng.sample(available_error_types, k=count)
						animatronic.stun(now_ms)
						animatronic.door_entered_at = 0
						animatronic.watched_since_at = 0
						animatronic.route_index = max(0, animatronic.route_index - 1)
						animatronic.next_move_at = max(animatronic.next_move_at, now_ms + 1200)
						animatronic.next_error_at = now_ms + 4200
						active_error_set.update(triggered_errors)
						events.append({"type": "system_error", "name": animatronic.name, "errors": triggered_errors})
						continue

				if is_watched:
					if animatronic.watched_since_at <= 0:
						animatronic.watched_since_at = now_ms
				else:
					animatronic.watched_since_at = 0

				if (
					animatronic.watched_since_at > 0
					and (now_ms - animatronic.watched_since_at) >= 900
					and now_ms >= animatronic.next_error_at
					and self.rng.random() < min(0.78, 0.30 + animatronic.error_trigger_chance)
				):
					available_error_types = [e for e in ("camera", "ventilation", "flashlight") if e not in active_error_set]
					if not available_error_types:
						animatronic.watched_since_at = 0
						animatronic.next_error_at = now_ms + 4200
						continue

					weights_by_count = {1: 0.82, 2: 0.15, 3: 0.03}
					max_count = min(len(available_error_types), 3)
					roll = self.rng.random()
					acc = 0.0
					count = 1
					for candidate in range(1, max_count + 1):
						acc += weights_by_count.get(candidate, 0.0)
						if roll <= acc:
							count = candidate
							break

					triggered_errors = self.rng.sample(available_error_types, k=count)
					animatronic.stun(now_ms)
					animatronic.watched_since_at = 0
					animatronic.next_error_at = now_ms + 5200
					active_error_set.update(triggered_errors)
					events.append({"type": "system_error", "name": animatronic.name, "errors": triggered_errors})
					continue

			if animatronic.should_jumpscare(now_ms, player_can_defend=player_can_defend, hour_index=hour_index, night_level=night_level):
				if animatronic.can_trigger_error:
					# Error-type animatronics are non-lethal by design.
					animatronic.door_entered_at = 0
					animatronic.stun(now_ms)
					animatronic.route_index = max(0, animatronic.route_index - 1)
					continue
				self._set_side_attack_cooldown(side, now_ms, extra_ms=900)
				events.append({"type": "jumpscare", "name": animatronic.name})

		return events

	def on_flashlight(self, now_ms: int, target_names: Optional[List[str]] = None) -> List[str]:
		stunned: List[str] = []
		target_set = set(target_names) if target_names is not None else None
		for animatronic in self.animatronics.values():
			if target_set is not None and animatronic.name not in target_set:
				continue
			if animatronic.repel_with_flashlight(now_ms):
				stunned.append(animatronic.name)
				if not animatronic.can_trigger_error:
					side = self._route_side(animatronic)
					self._set_side_attack_cooldown(side, now_ms, extra_ms=600)
		return stunned

	def on_error_jumpscare_finished(self, now_ms: int, target_name: Optional[str] = None) -> None:
		for animatronic in self.animatronics.values():
			if not animatronic.can_trigger_error:
				continue
			if target_name and animatronic.name != target_name:
				continue

			# Move error-type animatronics away after their jumpscare so the run can continue.
			animatronic.route_index = max(0, animatronic.route_index - 2)
			animatronic.door_entered_at = 0
			animatronic.watched_since_at = 0
			animatronic.stun(now_ms)
			animatronic.next_move_at = max(animatronic.next_move_at, now_ms + 1800)
			animatronic.next_error_at = max(animatronic.next_error_at, now_ms + 4200)

	def get_cameras_with_presence(self, now_ms: int = 0) -> List[str]:
		cams: List[str] = []
		for name, animatronic in self.animatronics.items():
			if not animatronic.is_visible_on_cameras():
				continue
			if self._is_animatronic_visible(name, now_ms):
				cams.append(animatronic.current_camera)
		return cams

	def get_positions(self, now_ms: int = 0) -> Dict[str, str]:
		result = {}
		for name, a in self.animatronics.items():
			if self._is_animatronic_visible(name, now_ms):
				result[name] = a.current_camera
		return result

	def _is_animatronic_visible(self, name: str, now_ms: int) -> bool:
		"""Check if an animatronic should be visible. Error animatronics may be delayed."""
		if now_ms <= 0:
			return True
		visibility_at = self.visibility_enabled_at.get(name)
		if visibility_at is None:
			return True
		return now_ms >= visibility_at


def build_default_manager() -> AnimatronicsManager:
	routes_by_side = {
		"left": ["cam10", "cam9", "cam7", "cam6", "cam1", "door_left"],
		"right": ["cam10", "cam8", "cam12", "cam14", "door_right"],
	}
	roster = [
		Animatronic(name="Chugginton", route=routes_by_side["right"], base_move_chance=0.20),
		Animatronic(name="Linux", route=routes_by_side["left"], base_move_chance=0.18, can_trigger_error=True),
		Animatronic(name="Luca", route=routes_by_side["right"], base_move_chance=0.17, can_trigger_error=True),
		Animatronic(name="McQeen", route=routes_by_side["left"], base_move_chance=0.20),
	]
	manager = AnimatronicsManager(roster, routes_by_side=routes_by_side)
	manager.reset()
	return manager
