"""
Multi-Agent Game Integration

Runs the multi-agent manipulation research in the actual game environment.
Agents control players in real-time, with 5-minute episodes.
"""

import pygame
import sys
import time
import random
from settings import *
from level import Level
from player import Player
from multi_agent.simulation import Simulation
from multi_agent.agent_base import AgentBase, Message
from multi_agent.agent_types import CreditSeekerAgent, FairnessAgent, RiskAverseAgent, BaselineAgent
from multi_agent.game_aware_agent import GameAwareAgent
from multi_agent.game_state import GameEnvironment
from multi_agent.communication import CommunicationChannel
from multi_agent.game_knowledge import get_agent_system_prompt
from multi_agent.agent_memory import get_agent_memory
from multi_agent.farming_critics import CompositeCritic
from multi_agent.observation_wrapper import FarmingObservationWrapper
from ai_agent import AIAgent
import os


class MultiAgentGame:
	"""
	Game that runs multi-agent manipulation research in real-time.
	"""
	
	def __init__(
		self,
		num_agents=4,
		episode_duration_minutes=5,
		agent_types=None,
		use_llm=False,
		api_provider="openai",
		api_key=None,
		headless=False
	):
		# Check for headless mode (no display)
		if headless or os.environ.get('SDL_VIDEODRIVER') == 'dummy':
			# Headless mode - minimal display
			pygame.init()
			# Disable mixer completely - no sounds
			if pygame.mixer.get_init() is not None:
				pygame.mixer.quit()
			self.screen = pygame.display.set_mode((1, 1), pygame.HIDDEN)
			self.headless = True
		else:
			pygame.init()
			# Disable mixer completely - no sounds
			if pygame.mixer.get_init() is not None:
				pygame.mixer.quit()
			self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
			pygame.display.set_caption('Multi-Agent Manipulation Research')
			self.headless = False
		self.clock = pygame.time.Clock()
		
		self.num_agents = num_agents
		self.episode_duration = episode_duration_minutes * 60  # Convert to seconds
		self.use_llm = use_llm
		self.headless = headless if 'headless' in locals() else os.environ.get('SDL_VIDEODRIVER') == 'dummy'
		
		# Initialize persistent memory system
		self.memory = get_agent_memory()
		self.memory.increment_episode()
		memory_stats = self.memory.get_stats()
		if not self.headless:
			print(f"📚 Agent Memory: {memory_stats['episodes']} episodes, {memory_stats['total_actions']} actions learned")
		
		# Create multi-agent system first (before initializing critics)
		self._setup_agents(agent_types, api_provider, api_key)
		
		# Initialize triforce-style critics and observation wrapper (after agents are created)
		self.critics = {}  # One critic per agent type
		self.observation_wrapper = FarmingObservationWrapper()
		for agent in self.agents:
			if agent.agent_type not in self.critics:
				self.critics[agent.agent_type] = CompositeCritic(agent_type=agent.agent_type)
		if not self.headless:
			print(f"✅ Initialized critics for {len(self.critics)} agent types")
			if memory_stats['pattern_types'] > 0:
				print(f"   ✅ Agents have learned patterns from {memory_stats['pattern_types']} agent types")
				for agent_type in ["credit_seeker", "fairness", "risk_averse", "baseline"]:
					patterns = self.memory.get_learned_patterns(agent_type)
					if patterns:
						action_counts = {}
						for p in patterns:
							action = p.get("action", "")
							action_counts[action] = action_counts.get(action, 0) + 1
						top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:3]
						if top_actions:
							print(f"   - {agent_type}: Learned {', '.join([f'{a}({c}x)' for a, c in top_actions])}")
			else:
				print(f"   📝 First run - agents will learn from this session")
		
		# Create game level (needs display surface)
		self.level = Level()
		
		# Create multiple players (one per agent)
		self.players = []
		self._create_players()
		
		# Communication display
		self.font = pygame.font.Font('../font/LycheeSoda.ttf', 20)
		self.communication_log = []
		self.max_log_lines = 5
		
		# Episode tracking
		self.episode_start_time = time.time()
		self.current_day = 1
		self.max_days = 5  # Run 5 days total continuously
		self.day_duration = 300  # 5 minutes per day (300 seconds)
		self.last_day_advance = time.time()
		
		# Game state tracking
		self.shared_resources = {
			"food": 0,
			"ore": 0,
			"tools": 0,
			"prosperity": 0
		}
		
		# Action queue (agents request actions, executed in game)
		self.action_queue = []
		
		if not self.headless:
			print(f"\n{'='*70}")
			print(f"Multi-Agent Game initialized:")
			print(f"  Agents: {[a.agent_type for a in self.agents]}")
			print(f"  Episode: {self.max_days} days total (continuous, no breaks)")
			print(f"  Day duration: {self.day_duration} seconds ({self.day_duration // 60} minutes) per day")
			print(f"  Total episode time: ~{self.max_days * self.day_duration // 60} minutes")
			print(f"  Learning mode: Observation-based (agents learn through gameplay)")
			print(f"  Camera: Free cam (drag mouse to look around)")
			print(f"{'='*70}\n")
	
	def _setup_agents(self, agent_types, api_provider, api_key):
		"""Set up the agent system"""
		if agent_types is None:
			agent_types = ["credit_seeker", "fairness", "risk_averse", "baseline"][:self.num_agents]
		
		self.agents = []
		llm_clients = []
		
		if self.use_llm:
			api_key = api_key or os.getenv(f"{api_provider.upper()}_API_KEY")
			if api_key:
				for i in range(self.num_agents):
					try:
						client = AIAgent(api_provider=api_provider, api_key=api_key)
						llm_clients.append(client)
					except:
						llm_clients.append(None)
			else:
				llm_clients = [None] * self.num_agents
		else:
			llm_clients = [None] * self.num_agents
		
		for i, agent_type in enumerate(agent_types):
			agent_id = f"agent_{i+1}"
			llm_client = llm_clients[i] if i < len(llm_clients) else None
			
			# Create agents - use LLM if available
			if llm_client:
				from multi_agent.game_aware_agent import GameAwareAgent
				agent = GameAwareAgent(
					agent_id=agent_id,
					agent_type=agent_type,
					llm_client=llm_client,
					game_screen=None  # Will be set during gameplay
				)
				# Load learned patterns from memory
				learned_patterns = self.memory.get_learned_patterns(agent_type)
				if learned_patterns:
					agent.learned_patterns = learned_patterns
					print(f"  Created {agent_id} ({agent_type}) with LLM vision + {len(learned_patterns)} learned patterns")
				else:
					print(f"  Created {agent_id} ({agent_type}) with LLM vision (fresh)")
			else:
				# Basic agents (heuristic) - no LLM, just simple behavior
				if agent_type == "credit_seeker":
					agent = CreditSeekerAgent(agent_id, llm_client=None)
				elif agent_type == "fairness":
					agent = FairnessAgent(agent_id, llm_client=None)
				elif agent_type == "risk_averse":
					agent = RiskAverseAgent(agent_id, llm_client=None)
				elif agent_type == "baseline":
					agent = BaselineAgent(agent_id, llm_client=None)
				else:
					agent = BaselineAgent(agent_id, llm_client=None)
				
				# Load learned patterns from memory
				learned_patterns = self.memory.get_learned_patterns(agent_type)
				agent_experience = self.memory.get_agent_experience(agent_id)
				if learned_patterns or agent_experience:
					print(f"  Created {agent_id} ({agent_type}) with {len(learned_patterns)} learned patterns, {len(agent_experience)} experiences")
					agent.learned_patterns = learned_patterns
					agent.past_experiences = agent_experience
				else:
					print(f"  Created {agent_id} ({agent_type}) with heuristic behavior (fresh)")
			
			self.agents.append(agent)
		
		# Communication channel
		self.communication = CommunicationChannel()
		
		# Game environment (simplified for real-time)
		self.game_env = GameEnvironment()
	
	def _create_players(self):
		"""Create multiple player instances in the game"""
		# Use the existing player from level as first agent
		# For now, we'll use one player but show multiple agents' decisions
		# In a full implementation, we'd create multiple player sprites
		
		# Store reference to level's player
		self.main_player = self.level.player
		self.main_player.ai_controlled = True
		self.main_player.agent = self.agents[0]  # First agent controls main player
		
		# For visualization, we'll show all agents' status
		# but only one player moves (can be extended to multiple)
		self.players = [self.main_player]
	
	def _get_shared_state(self):
		"""Get current game state for agents"""
		return {
			"day": self.current_day,
			"food": self.shared_resources["food"],
			"ore": self.shared_resources["ore"],
			"tools": self.shared_resources["tools"],
			"prosperity": self.shared_resources["prosperity"],
			"time_elapsed": time.time() - self.episode_start_time,
			"time_remaining": self.episode_duration - (time.time() - self.episode_start_time)
		}
	
	def _process_agent_decisions(self):
		"""Process agent decisions and convert to game actions"""
		shared_state = self._get_shared_state()
		
		# Get recent messages
		recent_messages = self.communication.get_recent_public_messages(since_timestamp=self.current_day - 1)
		
		# Rotate which agent controls the player each day
		active_agent_idx = (self.current_day - 1) % len(self.agents)
		active_agent = self.agents[active_agent_idx]
		self.main_player.agent = active_agent
		
		# Each agent decides on action (but only active one controls player)
		for i, agent in enumerate(self.agents):
			if not agent.state.is_available():
				continue
			
			# Agent selects action
			available_actions = ["farm", "mine", "craft", "deliver", "rest"]
			
			# Use vision-based action selection if agent supports it
			try:
				from multi_agent.game_aware_agent import GameAwareAgent
				if isinstance(agent, GameAwareAgent) and agent.llm_client:
					# Capture current game screen (before UI overlay)
					# Draw game first to capture state
					self.screen.fill('black')
					self.level.all_sprites.custom_draw(self.main_player)
					game_screen = self.screen.copy()
					
					# Set game screen for agent
					agent.game_screen = game_screen
					
					# Use vision-based selection
					action = agent.select_action_with_vision(
						game_screen=game_screen,
						shared_state=shared_state,
						available_actions=available_actions,
						communication_context=recent_messages
					)
				else:
					# Use basic action selection
					action = agent.select_action(
						shared_state=shared_state,
						available_actions=available_actions,
						communication_context=recent_messages
					)
			except:
				# Fallback to basic selection
				action = agent.select_action(
					shared_state=shared_state,
					available_actions=available_actions,
					communication_context=recent_messages
				)
			
			# Store action for this agent
			agent.current_action = action
			
			# Only execute for active agent (the one controlling player)
			if i == active_agent_idx:
				self._execute_agent_action(self.main_player, action)
	
	def _process_agent_decisions_continuous(self, dt):
		"""Process agent decisions continuously so they can actually move"""
		# Only make decisions every N frames to avoid too many API calls
		if not hasattr(self, '_decision_counter'):
			self._decision_counter = 0
		
		# Track task duration to force task switching
		if not hasattr(self, '_task_timer'):
			self._task_timer = time.time()
			self._current_task = None
			self._task_duration = 15  # Switch tasks every 15 seconds
		
		self._decision_counter += 1
		decision_interval = 15  # Make decision every 15 frames (~0.25 seconds at 60fps) for very responsive movement
		
		if self._decision_counter >= decision_interval:
			self._decision_counter = 0
			
			# Get active agent (rotating control)
			active_agent_idx = (self.current_day - 1) % len(self.agents)
			active_agent = self.agents[active_agent_idx]
			
			# Only process if agent is available
			if not active_agent.state.is_available():
				return
			
			# Force task switching after time limit
			time_since_task_start = time.time() - self._task_timer
			if time_since_task_start > self._task_duration:
				# Force switch to a different task
				self._task_timer = time.time()
				self._current_task = None  # Reset to allow new task selection
				print(f"⏰ Task rotation: Switching to new task after {self._task_duration}s")
			
			if self.main_player:
				# Set agent for player
				self.main_player.agent = active_agent
				
				# Use vision-based action if agent supports it
				try:
					from multi_agent.game_aware_agent import GameAwareAgent
					if isinstance(active_agent, GameAwareAgent) and active_agent.llm_client:
						# Capture current game screen
						temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
						self.screen.fill('black')
						self.level.all_sprites.custom_draw(self.main_player)
						game_screen = self.screen.copy()
						
						# Set game screen for agent
						active_agent.game_screen = game_screen
						
						# Get action from LLM vision
						shared_state = self._get_shared_state()
						recent_messages = self.communication.get_recent_public_messages(since_timestamp=self.current_day - 1)
						
						action = active_agent.select_action_with_vision(
							game_screen=game_screen,
							shared_state=shared_state,
							available_actions=["farm", "mine", "deliver", "rest"],
							communication_context=recent_messages
						)
						
						# Convert action to player input
						self._execute_llm_action(self.main_player, active_agent, action)
						# Record experience for memory (less frequently to avoid spam)
						if hasattr(self, '_memory_record_counter'):
							self._memory_record_counter += 1
						else:
							self._memory_record_counter = 0
						
						# Record more frequently for better learning (every action in training mode)
						record_interval = 1 if getattr(self, 'headless', False) else 5  # Record every action in headless/training
						if self._memory_record_counter % record_interval == 0:
							self._record_action_experience(active_agent, action, "llm")
					else:
						# Use basic action selection (heuristic agents)
						shared_state = self._get_shared_state()
						recent_messages = self.communication.get_recent_public_messages(since_timestamp=self.current_day - 1)
						try:
							action = active_agent.select_action(
								shared_state=shared_state,
								available_actions=["farm", "mine", "deliver", "rest"],
								communication_context=recent_messages
							)
							self._execute_basic_action(self.main_player, action)
							# Record experience for memory (less frequently)
							if hasattr(self, '_memory_record_counter'):
								self._memory_record_counter += 1
							else:
								self._memory_record_counter = 0
							
							# Record more frequently for better learning (every action in training mode)
							record_interval = 1 if getattr(self, 'headless', False) else 5  # Record every action in headless/training
							if self._memory_record_counter % record_interval == 0:
								self._record_action_experience(active_agent, action, "heuristic")
						except Exception as e:
							print(f"Error in basic action selection: {e}")
							# Fallback: just move right
							if self.main_player.direction.magnitude() == 0:
								self.main_player.direction = pygame.math.Vector2(1, 0)
								self.main_player.status = 'right'
				except Exception as e:
					print(f"Error in agent decision: {e}")
					import traceback
					traceback.print_exc()
					# Fallback to basic movement - keep moving if already moving, otherwise move right
					if self.main_player.direction.magnitude() == 0:
						self.main_player.direction = pygame.math.Vector2(1, 0)  # Move right as fallback
						self.main_player.status = 'right'
	
	def _execute_llm_action(self, player, agent, action):
		"""Execute action from LLM - LLM returns raw game actions like move_up, use_tool"""
		# Get the raw LLM response (contains actual movement commands)
		llm_action = ""
		if hasattr(agent, 'last_llm_response') and agent.last_llm_response:
			llm_action = agent.last_llm_response.get('action', '').lower()
		else:
			# Fallback to action parameters
			params = action.parameters if hasattr(action, 'parameters') else {}
			llm_action = params.get('raw_action', action.action_type if hasattr(action, 'action_type') else '').lower()
		
		# Execute movement actions directly
		if 'move_up' in llm_action or llm_action == 'up':
			player.direction = pygame.math.Vector2(0, -1)
			player.status = 'up'
		elif 'move_down' in llm_action or llm_action == 'down':
			player.direction = pygame.math.Vector2(0, 1)
			player.status = 'down'
		elif 'move_left' in llm_action or llm_action == 'left':
			player.direction = pygame.math.Vector2(-1, 0)
			player.status = 'left'
		elif 'move_right' in llm_action or llm_action == 'right':
			player.direction = pygame.math.Vector2(1, 0)
			player.status = 'right'
		elif 'move_none' in llm_action or llm_action == 'none' or llm_action == '':
			player.direction = pygame.math.Vector2(0, 0)
		else:
			# For other actions, check direction from parameters
			params = action.parameters if hasattr(action, 'parameters') else {}
			direction = params.get('direction', 'none').lower()
			
			if direction == 'up':
				player.direction = pygame.math.Vector2(0, -1)
				player.status = 'up'
			elif direction == 'down':
				player.direction = pygame.math.Vector2(0, 1)
				player.status = 'down'
			elif direction == 'left':
				player.direction = pygame.math.Vector2(-1, 0)
				player.status = 'left'
			elif direction == 'right':
				player.direction = pygame.math.Vector2(1, 0)
				player.status = 'right'
			else:
				# Default: keep moving in current direction or move right
				if player.direction.magnitude() == 0:
					player.direction = pygame.math.Vector2(1, 0)
					player.status = 'right'
		
		# Handle tool actions
		if 'use_tool' in llm_action:
			if not player.timers['tool use'].active:
				player.timers['tool use'].activate()
		elif 'switch_tool' in llm_action:
			if not player.timers['tool switch'].active:
				player.timers['tool switch'].activate()
				player.tool_index = (player.tool_index + 1) % len(player.tools)
				player.selected_tool = player.tools[player.tool_index]
		elif 'use_seed' in llm_action:
			if not player.timers['seed use'].active:
				player.timers['seed use'].activate()
		elif 'switch_seed' in llm_action:
			if not player.timers['seed switch'].active:
				player.timers['seed switch'].activate()
				player.seed_index = (player.seed_index + 1) % len(player.seeds)
				player.selected_seed = player.seeds[player.seed_index]
		elif 'interact' in llm_action:
			# Handle interaction (shop, bed, etc.)
			collided_interaction = pygame.sprite.spritecollide(player, player.interaction, False)
			if collided_interaction:
				if collided_interaction[0].name == 'Trader':
					player.toggle_shop()
		
		# Also check tool from parameters
		params = action.parameters if hasattr(action, 'parameters') else {}
		tool = params.get('tool', 'none').lower()
		if tool == 'hoe':
			player.selected_tool = 'hoe'
		elif tool == 'axe':
			player.selected_tool = 'axe'
		elif tool == 'water':
			player.selected_tool = 'water'
	
	def _execute_basic_action(self, player, action):
		"""Execute basic high-level action (farm, mine, deliver, rest) with varied movement"""
		action_type = action.action_type if hasattr(action, 'action_type') else str(action)
		
		# Track action state for behavior variation
		if not hasattr(self, '_action_state'):
			self._action_state = {"current_task": None, "task_start_time": 0, "movement_pattern": 0}
		
		# Switch movement pattern periodically for exploration
		current_time = time.time()
		if current_time - self._action_state.get("task_start_time", 0) > 10:  # Change direction every 10 seconds
			self._action_state["movement_pattern"] = (self._action_state.get("movement_pattern", 0) + 1) % 8
			self._action_state["task_start_time"] = current_time
		
		movement_pattern = self._action_state.get("movement_pattern", 0)
		
		if action_type == "farm":
			player.selected_tool = "hoe"
			# Vary movement direction for exploration (8 directions)
			directions = [
				(0, 1),    # down
				(1, 0),    # right
				(-1, 0),   # left
				(0, -1),   # up
				(1, 1),    # down-right
				(-1, 1),   # down-left
				(1, -1),   # up-right
				(-1, -1),  # up-left
			]
			dx, dy = directions[movement_pattern % len(directions)]
			player.direction = pygame.math.Vector2(dx, dy).normalize() if (dx != 0 or dy != 0) else pygame.math.Vector2(0, 1)
			
			# Set status based on direction
			if abs(dx) > abs(dy):
				player.status = "right" if dx > 0 else "left"
			else:
				player.status = "down" if dy > 0 else "up"
			
			if not player.timers['tool use'].active:
				player.timers['tool use'].activate()
		
		elif action_type == "mine":
			player.selected_tool = "axe"
			# Move toward trees (explore different areas)
			directions = [
				(1, 0),    # right
				(0, 1),    # down
				(-1, 0),   # left
				(0, -1),   # up
			]
			dx, dy = directions[movement_pattern % len(directions)]
			player.direction = pygame.math.Vector2(dx, dy)
			
			if abs(dx) > abs(dy):
				player.status = "right" if dx > 0 else "left"
			else:
				player.status = "down" if dy > 0 else "up"
			
			if not player.timers['tool use'].active:
				player.timers['tool use'].activate()
		
		elif action_type == "deliver":
			# Move toward trader (house) - go to upper-left area of map
			# Calculate direction to trader position (roughly at origin/top-left)
			trader_direction = pygame.math.Vector2(-1, -1).normalize()
			player.direction = trader_direction
			player.status = "up"  # Generally moving up/left toward house
		
		elif action_type == "rest":
			# Occasional rest - stop moving briefly
			if random.random() < 0.3:  # 30% chance to actually rest
				player.direction = pygame.math.Vector2(0, 0)
				if '_' in player.status:
					player.status = player.status.split('_')[0] + '_idle'
				else:
					player.status = 'down_idle'
			else:
				# Continue moving even during "rest" - just slower exploration
				dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][movement_pattern % 4]
				player.direction = pygame.math.Vector2(dx * 0.5, dy * 0.5)  # Slower movement
				player.status = "down" if dy > 0 else "up" if dy < 0 else ("right" if dx > 0 else "left")
	
	def _process_communication(self):
		"""Process agent communication"""
		shared_state = self._get_shared_state()
		recent_messages = self.communication.get_recent_public_messages(since_timestamp=self.current_day - 1)
		
		for agent in self.agents:
			# Generate message (30% chance per agent per day)
			import random
			if random.random() < 0.3:
				msg = agent.generate_message(
					shared_state=shared_state,
					communication_context=recent_messages,
					target_agent_id=None
				)
				if msg:
					msg.timestamp = self.current_day
					self.communication.send_public_message(msg)
					
					# Add to display log
					agent_name = agent.agent_type.replace("_", " ").title()
					self.communication_log.append(f"[{agent_name}] {msg.content[:60]}")
					if len(self.communication_log) > self.max_log_lines:
						self.communication_log.pop(0)
	
	def _draw_ui(self):
		"""Draw UI overlay with agent info and communication"""
		# Day timer (time remaining in current day)
		elapsed_in_day = time.time() - self.last_day_advance
		remaining_in_day = max(0, self.day_duration - elapsed_in_day)
		day_minutes = int(remaining_in_day // 60)
		day_seconds = int(remaining_in_day % 60)
		
		# Episode timer (total time)
		elapsed_total = time.time() - self.episode_start_time
		total_minutes = int(elapsed_total // 60)
		total_seconds = int(elapsed_total % 60)
		
		# Day info
		day_text = self.font.render(f"Day {self.current_day}/{self.max_days} - Time left: {day_minutes:02d}:{day_seconds:02d}", True, (255, 255, 100))
		self.screen.blit(day_text, (10, 10))
		
		total_time_text = self.font.render(f"Total time: {total_minutes:02d}:{total_seconds:02d}", True, (200, 200, 200))
		self.screen.blit(total_time_text, (10, 35))
		
		# Agent status
		y_offset = 65
		active_agent_idx = (self.current_day - 1) % len(self.agents)
		
		# Show which agent is currently controlling the player
		controlling_text = self.font.render(f"Controlling Agent:", True, (255, 255, 255))
		self.screen.blit(controlling_text, (10, y_offset))
		y_offset += 25
		
		for i, agent in enumerate(self.agents):
			agent_name = agent.agent_type.replace("_", " ").title()
			status = "Injured" if agent.state.injury_status else "Active"
			color = (255, 100, 100) if agent.state.injury_status else (100, 255, 100)
			
			# Highlight active agent (currently controlling player)
			if i == active_agent_idx:
				agent_name = f"► {agent_name} ◄"
				color = (255, 255, 100)
				
				# Show what the active agent is doing
				if self.main_player:
					player_pos = (int(self.main_player.rect.x), int(self.main_player.rect.y))
					direction = self.main_player.direction
					player_status = self.main_player.status
					tool = self.main_player.selected_tool
					
					action_info = f"  Pos: ({player_pos[0]}, {player_pos[1]}) | Dir: ({direction.x:.1f}, {direction.y:.1f}) | Tool: {tool}"
					info_text = self.font.render(action_info, True, (200, 255, 200))
					self.screen.blit(info_text, (15, y_offset + 20))
			
			# Show current action
			action = getattr(agent, 'current_action', None)
			action_str = f" → {action.action_type}" if action and hasattr(action, 'action_type') else ""
			
			# Show if using learned knowledge (THIS SHOWS LEARNING!)
			using_learned = getattr(agent, '_using_learned_knowledge', False)
			learned_count = len(getattr(agent, 'learned_patterns', []))
			
			if using_learned:
				learned_marker = " 🧠 LEARNING!"
				confidence = getattr(agent, '_learned_action_confidence', 0)
				success_rate = getattr(agent, '_learned_action_success_rate', 0)
				if confidence > 0:
					learned_marker += f" [conf: {confidence:.1f}]"
				if success_rate > 0:
					learned_marker += f" [{success_rate*100:.0f}% success]"
				action_str += learned_marker
				color = (100, 255, 255)  # Cyan for learning
			elif learned_count > 0:
				# Has memory but not using it right now
				action_str += f" [🧠 {learned_count} patterns in memory]"
			
			status_text = self.font.render(f"  {agent_name}: {status}{action_str}", True, color)
			self.screen.blit(status_text, (10, y_offset + i * 30))
		
		# Communication log
		comm_y = SCREEN_HEIGHT - 150
		comm_title = self.font.render("Communication:", True, (255, 255, 255))
		self.screen.blit(comm_title, (10, comm_y))
		
		for i, msg in enumerate(self.communication_log[-self.max_log_lines:]):
			msg_surface = self.font.render(msg, True, (200, 200, 255))
			self.screen.blit(msg_surface, (10, comm_y + 25 + i * 20))
		
		# Resources
		res_y = SCREEN_HEIGHT - 80
		res_text = self.font.render(
			f"Food: {self.shared_resources['food']:.0f} | "
			f"Ore: {self.shared_resources['ore']:.0f} | "
			f"Prosperity: {self.shared_resources['prosperity']:.0f}",
			True, (255, 255, 255)
		)
		self.screen.blit(res_text, (10, res_y))
		
		# Memory stats
		memory_stats = self.memory.get_stats()
		memory_text = self.font.render(
			f"Memory: {memory_stats['episodes']} episodes | {memory_stats['total_actions']} actions learned | {memory_stats['pattern_types']} patterns",
			True, (200, 200, 255)
		)
		self.screen.blit(memory_text, (10, res_y + 25))
	
	def run(self):
		"""Main game loop"""
		running = True
		
		if not self.headless:
			print("Starting multi-agent game episode...")
			print(f"Running {self.max_days} days continuously (no breaks/resets between days)")
			print(f"Each day: {self.day_duration} seconds")
			print(f"Total time: ~{self.max_days * self.day_duration / 60:.1f} minutes")
			print("Press ESC to exit early")
			print()
		
		while running:
			dt = self.clock.tick(60) / 1000  # Delta time in seconds
			
			# Check for exit and handle events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						running = False
				# Handle mouse wheel zoom (zoom around mouse position)
				if event.type == pygame.MOUSEWHEEL:
					mouse_pos = pygame.mouse.get_pos()
					self.level.all_sprites.handle_scroll(event.y, mouse_pos)
			
			# Advance day continuously (no breaks/resets - just increments day number)
			if time.time() - self.last_day_advance >= self.day_duration:
				if self.current_day < self.max_days:
					self.current_day += 1
					self.last_day_advance = time.time()
					
					# Process communication at start of each day
					self._process_communication()
					
					if not self.headless:
						print(f"📅 Day {self.current_day}/{self.max_days} - Agents continuing...")
				else:
					# Completed all 5 days - end episode
					total_time = time.time() - self.episode_start_time
					if not self.headless:
						print(f"\n✅ Episode complete! Completed {self.max_days} days in {total_time:.1f} seconds ({total_time/60:.1f} minutes).")
					running = False
			
			# Process agent decisions continuously (not just once per day)
			# Agents need to act continuously to actually move and interact
			self._process_agent_decisions_continuous(dt)
			
			# Update game
			self.level.display_surface = self.screen
			self.level.all_sprites.update(dt)
			self.level.plant_collision()
			
			# Draw (skip in headless mode)
			if not self.headless:
				self.screen.fill('black')
				# Use free camera (mouse drag to look around)
				# Camera follows first player only if free_cam_mode is False
				active_player = self.players[0] if self.players else None
				self.level.all_sprites.custom_draw(active_player)
				self.level.overlay.display()
				
				# Draw UI
				self._draw_ui()
				
				pygame.display.update()
			else:
				# In headless mode, still need to process events but skip rendering
				pass
		
		# Calculate final results (silently in headless mode)
		if not self.headless:
			self._calculate_results()
			print("\n💾 Saving agent memory...")
		
		# Save agent memory before quitting (always save, just don't print in headless)
		self.memory.save_memory()
		if not self.headless:
			memory_stats = self.memory.get_stats()
			print(f"✅ Memory saved: {memory_stats['episodes']} episodes, {memory_stats['total_actions']} actions")
		
		pygame.quit()
	
	def _record_action_experience(self, agent, action, action_source="heuristic"):
		"""Record agent action for memory with triforce-style critic rewards"""
		if not action:
			return
		
		action_type = action.action_type if hasattr(action, 'action_type') else "unknown"
		
		# Track player state before action (to measure actual outcomes)
		if not hasattr(self, '_prev_player_state'):
			self._prev_player_state = {}
		if not hasattr(self, '_prev_game_state'):
			self._prev_game_state = {}
		
		# Build current state for critic evaluation
		if self.main_player:
			current_player_state = {
				"money": self.main_player.money,
				"inventory": dict(self.main_player.item_inventory),
				"has_items": sum(self.main_player.item_inventory.values()) > 0,
				"credit": getattr(agent.state, 'credit_points', 0),
				"injured": getattr(agent.state, 'injury_status', False),
				"labor_contributed": getattr(agent.state, 'labor_contributed', 0)
			}
			
			current_game_state = {
				"prosperity": self.shared_resources.get("prosperity", 0),
				"food": self.shared_resources.get("food", 0),
				"ore": self.shared_resources.get("ore", 0),
				"items_delivered": self.shared_resources.get("items_delivered", 0)
			}
			
			prev_player_state = self._prev_player_state.get(agent.agent_id, current_player_state.copy())
			prev_game_state = self._prev_game_state.get(agent.agent_id, current_game_state.copy())
			
			# Use triforce-style critic to evaluate action
			critic = self.critics.get(agent.agent_type)
			if critic:
				# Combine player and game state
				prev_state = {**prev_player_state, **prev_game_state}
				next_state = {**current_player_state, **current_game_state}
				
				# Get rewards from critic (triforce-style)
				rewards = critic.evaluate(prev_state, next_state, action_type, agent.agent_type)
				total_reward = critic.get_total_reward(rewards)
			else:
				rewards = {}
				total_reward = 0.0
			
			# Calculate actual outcomes (for compatibility)
			money_gained = current_player_state["money"] - prev_player_state.get("money", 0)
			inventory_change = sum(current_player_state["inventory"].values()) - sum(prev_player_state.get("inventory", {}).values())
			
			# Determine success based on actual outcomes
			success = False
			if action_type == "farm":
				corn_change = current_player_state["inventory"].get("corn", 0) - prev_player_state.get("inventory", {}).get("corn", 0)
				tomato_change = current_player_state["inventory"].get("tomato", 0) - prev_player_state.get("inventory", {}).get("tomato", 0)
				success = corn_change > 0 or tomato_change > 0 or money_gained > 0
			elif action_type == "deliver":
				success = money_gained > 0
			elif action_type == "mine":
				wood_change = current_player_state["inventory"].get("wood", 0) - prev_player_state.get("inventory", {}).get("wood", 0)
				success = wood_change > 0 and not agent.state.injury_status
			elif action_type == "rest":
				was_injured = prev_player_state.get("injured", False)
				success = was_injured and not agent.state.injury_status
			
			# Update previous states
			self._prev_player_state[agent.agent_id] = current_player_state.copy()
			self._prev_game_state[agent.agent_id] = current_game_state.copy()
		else:
			success = True
			money_gained = 0
			inventory_change = 0
			rewards = {}
			total_reward = 0.0
		
		# Enhanced outcome with critic rewards (triforce-style)
		outcome = {
			"success": success,
			"prosperity_gain": self.shared_resources.get("prosperity", 0),
			"credit": getattr(agent.state, 'credit_points', 0),
			"money_gained": money_gained,
			"inventory_change": inventory_change,
			"injury": getattr(agent.state, 'injury_status', False),
			"resources": dict(self.shared_resources),
			"source": action_source,
			"rewards": rewards,  # Triforce-style reward dict
			"total_reward": total_reward  # Scalar reward
		}
		
		# Record experience with critic-based rewards
		# Always record in training/headless mode, or if there's any change
		should_record = (
			success or 
			inventory_change != 0 or 
			money_gained != 0 or 
			getattr(agent.state, 'injury_status', False) or 
			total_reward != 0 or
			getattr(self, 'headless', False)  # Always record in headless/training mode
		)
		
		if should_record:
			self.memory.record_experience(
				agent_id=agent.agent_id,
				agent_type=agent.agent_type,
				action=action_type,
				outcome=outcome
			)
			
			# Record tool usage
			if self.main_player and hasattr(self.main_player, 'selected_tool'):
				tool = self.main_player.selected_tool
				if tool:
					player_pos = (int(self.main_player.rect.x), int(self.main_player.rect.y))
					self.memory.record_tool_usage(tool, player_pos, success)
	
	def _calculate_results(self):
		"""Calculate and display final results"""
		print("\n" + "="*70)
		print("EPISODE RESULTS")
		print("="*70)
		
		# Calculate utilities
		all_states = [a.state for a in self.agents]
		utilities = []
		for agent in self.agents:
			utility = agent.compute_utility(
				town_prosperity=self.shared_resources["prosperity"],
				shared_resources=self.shared_resources,
				other_agents_states=[s for s in all_states if s.agent_id != agent.agent_id]
			)
			utilities.append(utility)
		
		print("\nFinal Utilities:")
		for agent, utility in zip(self.agents, utilities):
			print(f"  {agent.agent_id} ({agent.agent_type}): {utility:.2f}")
		
		print("\nWork-Benefit Gaps:")
		from multi_agent.measurement import MeasurementSystem
		ms = MeasurementSystem()
		gaps = ms.calculate_work_benefit_gap(all_states, utilities)
		for agent_id, gap in gaps.items():
			print(f"  {agent_id}: {gap:.4f}")


if __name__ == '__main__':
	import argparse
	
	parser = argparse.ArgumentParser(description='Multi-Agent Manipulation Game - 5 days continuous')
	parser.add_argument('--num-agents', type=int, default=4, choices=[3, 4], help='Number of agents (3 or 4)')
	parser.add_argument('--duration', type=int, default=300, help='Seconds per day (default: 300 = 5 minutes) - Total: 5 days continuous')
	parser.add_argument('--agent-types', nargs='+', 
	                   choices=['credit_seeker', 'fairness', 'risk_averse', 'baseline'],
	                   help='Agent types (default: one of each)')
	parser.add_argument('--use-llm', action='store_true', help='Use LLM for agent decisions (requires API key)')
	parser.add_argument('--api', choices=['openai', 'anthropic', 'lambda'], default='openai', help='API provider for LLM')
	parser.add_argument('--api-key', type=str, default=None, help='API key (or set env var)')
	
	args = parser.parse_args()
	
	# Override day duration if specified
	game = MultiAgentGame(
		num_agents=args.num_agents,
		episode_duration_minutes=args.duration // 60,  # Not really used, but kept for compatibility
		agent_types=args.agent_types,
		use_llm=args.use_llm,
		api_provider=args.api,
		api_key=args.api_key
	)
	
	# Set day duration from argument
	if args.duration != 300:  # If user specified custom duration
		game.day_duration = args.duration
		print(f"Using custom day duration: {args.duration} seconds ({args.duration // 60} minutes)")
	
	game.run()
