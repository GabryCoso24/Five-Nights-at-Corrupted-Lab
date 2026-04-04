from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import random


@dataclass
class Animatronic:
	name: str
	route: List[str]
	base_move_chance: float = 0.12
	watched_camera_penalty: float = 0.78
	step_cooldown_ms: int = 3500
	stun_duration_ms: int = 1600
	attack_delay_ms: int = 3200

	def __post_init__(self):
		if not self.route:
			raise ValueError(f"La route di {self.name} non puo essere vuota")
		self.reset_state()

	def reset_state(self) -> None:
		self.route_index = 0
		self.next_move_at = 0
		self.stunned_until = 0
		self.door_entered_at = 0

	def set_route(self, route: List[str]) -> None:
		if not route:
			raise ValueError(f"La route di {self.name} non puo essere vuota")
		self.route = route
		self.reset_state()

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
		if not self.is_near_office_door():
			return False

		self.stun(now_ms)
		self.door_entered_at = 0

		# Strong pushback from door/near-door to give the player fair reaction window.
		if self.is_at_office_door():
			self.route_index = max(0, self.route_index - 1)
		else:
			self.route_index = max(0, self.route_index)

		# Delay the next move so the repel is clearly visible in gameplay.
		self.next_move_at = max(self.next_move_at, now_ms + 900)
		return True

	def try_advance(
		self,
		now_ms: int,
		rng: random.Random,
		night_level: int,
		hour_index: int,
		watched_camera: Optional[str] = None,
		blocked_doors: Optional[Set[str]] = None,
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
			next_camera = self.peek_next_camera()
			if blocked_doors and next_camera in blocked_doors:
				self._schedule_next_move(now_ms, night_level, hour_index)
				return False
			self.route_index += 1
			if self.is_at_office_door():
				self.door_entered_at = now_ms

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

		attack_delay = max(950, self.attack_delay_ms - ((max(1, min(5, night_level)) - 1) * 220) - (hour_index * 170))
		return (now_ms - self.door_entered_at) >= attack_delay


class AnimatronicsManager:
	def __init__(self, animatronics: List[Animatronic], routes_by_side: Dict[str, List[str]], seed: Optional[int] = None):
		self.rng = random.Random(seed)
		self.animatronics: Dict[str, Animatronic] = {a.name: a for a in animatronics}
		self.routes_by_side = routes_by_side
		self.roster_order = list(self.animatronics.keys())

	def _active_names_for_night(self, night_level: int) -> List[str]:
		active_count = max(1, min(len(self.roster_order), night_level))
		return self.roster_order[:active_count]

	def _assign_random_routes(self) -> None:
		sides = ["left", "right"]
		names = list(self.animatronics.keys())
		self.rng.shuffle(names)

		for idx, name in enumerate(names):
			side = sides[(idx + self.rng.randint(0, 1)) % 2]
			self.animatronics[name].set_route(self.routes_by_side[side])

	def reset(self) -> None:
		self._assign_random_routes()

	def update(
		self,
		now_ms: int,
		night_level: int,
		hour_index: int,
		watched_camera: Optional[str],
		player_can_defend: bool = True,
	) -> List[dict]:
		events: List[dict] = []
		active_names = set(self._active_names_for_night(night_level))
		occupied_doors: Set[str] = {
			a.current_camera for a in self.animatronics.values() if a.current_camera in ("door_left", "door_right")
		}

		update_order = list(self.animatronics.values())
		self.rng.shuffle(update_order)

		for animatronic in update_order:
			if animatronic.name not in active_names:
				continue

			before = animatronic.current_camera
			if animatronic.try_advance(
				now_ms=now_ms,
				rng=self.rng,
				night_level=night_level,
				hour_index=hour_index,
				watched_camera=watched_camera,
				blocked_doors=occupied_doors,
			):
				events.append(
					{
						"type": "moved",
						"name": animatronic.name,
						"from": before,
						"to": animatronic.current_camera,
					}
				)
				if animatronic.current_camera in ("door_left", "door_right"):
					occupied_doors.add(animatronic.current_camera)

			if animatronic.should_jumpscare(now_ms, player_can_defend=player_can_defend, hour_index=hour_index, night_level=night_level):
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
		return stunned

	def get_cameras_with_presence(self) -> List[str]:
		cams: List[str] = []
		for animatronic in self.animatronics.values():
			if animatronic.is_visible_on_cameras():
				cams.append(animatronic.current_camera)
			elif animatronic.current_camera == "door_left":
				# Keep presence visible on the left-side camera when at left door.
				cams.append("cam1")
			elif animatronic.current_camera == "door_right":
				# Keep presence visible on the right-side camera when at right door.
				cams.append("cam14")
		return cams

	def get_positions(self) -> Dict[str, str]:
		return {name: a.current_camera for name, a in self.animatronics.items()}


def build_default_manager() -> AnimatronicsManager:
	routes_by_side = {
		"left": ["cam10", "cam9", "cam7", "cam6", "cam1", "door_left"],
		"right": ["cam10", "cam8", "cam12", "cam14", "door_right"],
	}
	roster = [
		Animatronic(name="Chugginton", route=routes_by_side["right"], base_move_chance=0.20),
		Animatronic(name="Linux", route=routes_by_side["left"], base_move_chance=0.18),
		Animatronic(name="Luca", route=routes_by_side["right"], base_move_chance=0.17),
		Animatronic(name="McQeen", route=routes_by_side["left"], base_move_chance=0.20),
	]
	manager = AnimatronicsManager(roster, routes_by_side=routes_by_side)
	manager.reset()
	return manager
