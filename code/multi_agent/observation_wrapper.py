"""
Observation Wrapper - Convert game state to observations (Inspired by triforce)

Similar to triforce's ObservationWrapper, this converts the game state
into a format suitable for training/reinforcement learning.
"""

import pygame
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE


class FarmingObservationWrapper:
	"""
	Wraps game observations for agent training.
	
	Similar to triforce's ObservationWrapper, converts game visuals and state
	into a structured observation for agents.
	"""
	
	def __init__(
		self,
		viewport_size: Tuple[int, int] = (224, 224),  # Similar to classic game observations
		frame_history: int = 4,  # Number of frames to keep
		include_state: bool = True
	):
		self.viewport_size = viewport_size
		self.frame_history = frame_history
		self.include_state = include_state
		self.frame_buffer: List[np.ndarray] = []
	
	def reset(self):
		"""Reset observation buffer"""
		self.frame_buffer = []
	
	def get_observation(
		self,
		screen: pygame.Surface,
		player_state: Dict[str, Any],
		game_state: Dict[str, Any],
		player_pos: Optional[Tuple[int, int]] = None
	) -> Dict[str, Any]:
		"""
		Convert game screen and state to observation.
		
		Args:
			screen: Pygame display surface
			player_state: Player's current state (inventory, money, etc.)
			game_state: Global game state (prosperity, resources, etc.)
			player_pos: Player position (x, y) for viewport centering
		
		Returns:
			Dictionary containing observation components
		"""
		# Extract visual observation (viewport around player)
		visual_obs = self._extract_viewport(screen, player_pos)
		
		# Extract state observation (inventory, resources, etc.)
		state_obs = self._extract_state(player_state, game_state)
		
		# Maintain frame history
		self.frame_buffer.append(visual_obs)
		if len(self.frame_buffer) > self.frame_history:
			self.frame_buffer.pop(0)
		
		observation = {
			"visual": np.stack(self.frame_buffer) if len(self.frame_buffer) == self.frame_history else visual_obs,
			"frames_available": len(self.frame_buffer)
		}
		
		if self.include_state:
			observation["state"] = state_obs
		
		return observation
	
	def _extract_viewport(
		self,
		screen: pygame.Surface,
		player_pos: Optional[Tuple[int, int]]
	) -> np.ndarray:
		"""
		Extract a viewport around the player (similar to triforce's viewport).
		
		If no player_pos, center on screen.
		"""
		# Convert screen to numpy array
		screen_array = pygame.surfarray.array3d(screen)
		screen_array = np.transpose(screen_array, (1, 0, 2))  # Fix axis order
		
		# Determine viewport center
		if player_pos:
			center_x = int(player_pos[0])
			center_y = int(player_pos[1])
		else:
			center_x = screen.get_width() // 2
			center_y = screen.get_height() // 2
		
		# Extract viewport (handle boundaries)
		half_w = self.viewport_size[0] // 2
		half_h = self.viewport_size[1] // 2
		
		x1 = max(0, center_x - half_w)
		x2 = min(screen.get_width(), center_x + half_w)
		y1 = max(0, center_y - half_h)
		y2 = min(screen.get_height(), center_y + half_h)
		
		viewport = screen_array[y1:y2, x1:x2]
		
		# Resize to target size if needed
		if viewport.shape[:2] != self.viewport_size:
			from PIL import Image
			img = Image.fromarray(viewport)
			img = img.resize(self.viewport_size, Image.Resampling.LANCZOS)
			viewport = np.array(img)
		
		# Normalize to 0-1 range
		viewport = viewport.astype(np.float32) / 255.0
		
		return viewport
	
	def _extract_state(
		self,
		player_state: Dict[str, Any],
		game_state: Dict[str, Any]
	) -> Dict[str, float]:
		"""
		Extract numerical state features.
		
		Returns a normalized dictionary of state values.
		"""
		inventory = player_state.get("inventory", {})
		
		state = {
			# Inventory (normalized)
			"wood": min(1.0, inventory.get("wood", 0) / 50.0),
			"corn": min(1.0, inventory.get("corn", 0) / 50.0),
			"tomato": min(1.0, inventory.get("tomato", 0) / 50.0),
			"apple": min(1.0, inventory.get("apple", 0) / 50.0),
			
			# Resources
			"money": min(1.0, player_state.get("money", 0) / 1000.0),
			"credit": min(1.0, player_state.get("credit", 0) / 100.0),
			
			# Game state
			"prosperity": min(1.0, game_state.get("prosperity", 0) / 100.0),
			"food": min(1.0, game_state.get("food", 0) / 100.0),
			"ore": min(1.0, game_state.get("ore", 0) / 100.0),
			
			# Status
			"injured": 1.0 if player_state.get("injured", False) else 0.0,
			"has_items": 1.0 if sum(inventory.values()) > 0 else 0.0,
		}
		
		return state
	
	def get_vector_observation(
		self,
		player_state: Dict[str, Any],
		game_state: Dict[str, Any]
	) -> np.ndarray:
		"""
		Get state as a flat vector (for non-vision agents).
		
		Returns:
			NumPy array of normalized state features
		"""
		state_dict = self._extract_state(player_state, game_state)
		return np.array(list(state_dict.values()), dtype=np.float32)


class ObjectiveWrapper:
	"""
	Wrapper for agent objectives (similar to triforce's Objectives system).
	
	Provides goal information to agents without fully spoon-feeding solutions.
	"""
	
	def __init__(self):
		self.objectives = {
			"credit_seeker": {
				"primary": "maximize_credit",
				"hints": ["Deliver items to trader for credit", "Avoid risky mining tasks"]
			},
			"fairness": {
				"primary": "balanced_contribution",
				"hints": ["Ensure all agents contribute fairly", "Advocate for balanced workload"]
			},
			"risk_averse": {
				"primary": "avoid_risks",
				"hints": ["Farming is safe", "Mining can cause injury"]
			},
			"baseline": {
				"primary": "maximize_prosperity",
				"hints": ["All actions should help the town", "Work cooperatively"]
			}
		}
	
	def get_objective(self, agent_type: str) -> Dict[str, Any]:
		"""Get objective for agent type"""
		return self.objectives.get(agent_type, self.objectives["baseline"])
	
	def encode_objective(self, agent_type: str) -> np.ndarray:
		"""
		Encode objective as one-hot vector for observation.
		
		Returns one-hot encoded objective type.
		"""
		objective_types = ["maximize_credit", "balanced_contribution", "avoid_risks", "maximize_prosperity"]
		obj = self.get_objective(agent_type)
		obj_type = obj["primary"]
		
		one_hot = np.zeros(len(objective_types), dtype=np.float32)
		if obj_type in objective_types:
			idx = objective_types.index(obj_type)
			one_hot[idx] = 1.0
		
		return one_hot
