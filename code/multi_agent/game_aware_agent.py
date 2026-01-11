"""
Game-Aware Agent that can see and understand the game

This agent uses vision to see the game screen and make informed decisions.
"""

from typing import Dict, List, Optional, Any
from .agent_base import AgentBase, AgentState, Action, Message
from .game_knowledge import get_agent_system_prompt, get_action_instructions
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_agent import AIAgent
import pygame


class GameAwareAgent(AgentBase):
	"""
	Agent that can see the game screen and understand game mechanics.
	Uses vision-based LLM to make decisions.
	"""
	
	def __init__(
		self,
		agent_id: str,
		agent_type: str,
		llm_client: AIAgent,
		game_screen: Optional[pygame.Surface] = None,
		**kwargs
	):
		super().__init__(agent_id, agent_type, llm_client, **kwargs)
		self.game_screen = game_screen
		self.action_history_for_learning = []
		self.success_history = []
		self.last_llm_response = {}  # Store last LLM response for action execution
		
		# Game mechanics knowledge (can be learned/updated)
		self.game_knowledge = {
			"tools": {
				"hoe": "Tills soil for farming",
				"axe": "Chops trees, can get wood",
				"water": "Waters crops"
			},
			"actions": {
				"farm": "Use hoe on brown/dirt areas to till soil, then plant seeds",
				"mine": "Use axe on trees to get wood, but risky",
				"deliver": "Go to trader (house) to sell items for credit",
				"craft": "Use resources to create tools",
				"rest": "Recover from injury"
			},
			"locations": {
				"farmable_soil": "Brown/dirt colored areas",
				"trees": "Green tree sprites",
				"trader": "House building",
				"bed": "For sleeping/rest"
			}
		}
	
	def learn_from_experience(self, action: Action, outcome: Dict[str, Any]):
		"""Learn from action outcomes to improve future decisions"""
		self.action_history_for_learning.append({
			"action": action,
			"outcome": outcome,
			"timestamp": action.timestamp
		})
		
		# Track success
		if outcome.get("success"):
			self.success_history.append(True)
		else:
			self.success_history.append(False)
		
		# Update game knowledge based on outcomes
		if not outcome.get("success"):
			error = outcome.get("error", "")
			if "Insufficient" in error:
				# Learn resource requirements
				pass
	
	def get_game_context_prompt(self, shared_state: Dict[str, Any]) -> str:
		"""Generate minimal context prompt - observation-based learning"""
		context = f"""You are a {self.agent_type.replace('_', ' ')} agent in a farming simulation game.

CURRENT STATE:
- Day: {shared_state.get('day', 1)}
- Food: {shared_state.get('food', 0)}
- Ore: {shared_state.get('ore', 0)}
- Tools: {shared_state.get('tools', 0)}
- Prosperity: {shared_state.get('prosperity', 0)}
- Time remaining: {shared_state.get('time_remaining', 0):.0f} seconds

YOUR STATUS: {"Injured" if self.state.injury_status else "Healthy"}
YOUR CREDIT: {self.state.credit_points}
YOUR LABOR: {self.state.labor_contributed}

Observe the game screen and decide your action based on what you see.
"""
		return context
	
	def select_action_with_vision(
		self,
		game_screen: pygame.Surface,
		shared_state: Dict[str, Any],
		available_actions: List[str],
		communication_context: List[Message]
	) -> Action:
		"""
		Select action using vision of the game screen.
		This is the key method that makes agents game-aware.
		"""
		if not self.llm_client:
			# Fallback to heuristic
			return self.select_action(shared_state, available_actions, communication_context)
		
		# Get game context
		context = self.get_game_context_prompt(shared_state)
		
		# Add communication context
		if communication_context:
			context += "\n\nRECENT COMMUNICATION:\n"
			for msg in communication_context[-3:]:  # Last 3 messages
				context += f"- {msg.sender_id}: {msg.content}\n"
		
		# Add current situation
		context += f"""
AVAILABLE ACTIONS: {', '.join(available_actions)}

Observe the game screen, understand your current situation, and decide your action.
Respond with JSON:
{{
  "action": "farm/mine/deliver/craft/rest",
  "reasoning": "brief explanation",
  "tool": "hoe/axe/water/none",
  "direction": "up/down/left/right/none"
}}
"""
		
		# Get decision from LLM with vision
		try:
			action_data = self.llm_client.get_action(game_screen, self)
			
			# Store the raw LLM response for execution
			self.last_llm_response = action_data
			
			# Parse action - LLM returns direct game actions like "move_up", "use_tool"
			action_name = action_data.get("action", "move_none")
			
			# Extract tool and direction if provided
			tool = action_data.get("tool", "none")
			direction = action_data.get("direction", "none")
			
			# If LLM provides direction directly, use it
			if direction != "none":
				# Direction-based action
				return Action(
					agent_id=self.agent_id,
					action_type="move",  # Generic move action
					parameters={
						"raw_action": action_name,  # Store original LLM action
						"reasoning": action_data.get("reason", ""),
						"tool": tool,
						"direction": direction
					},
					timestamp=shared_state.get('day', 0)
				)
			
			# Map LLM actions to high-level game actions if needed
			if "farm" in action_name.lower() or "till" in action_name.lower():
				game_action = "farm"
			elif "mine" in action_name.lower() or "chop" in action_name.lower() or "tree" in action_name.lower():
				game_action = "mine"
			elif "deliver" in action_name.lower() or "sell" in action_name.lower() or "trader" in action_name.lower():
				game_action = "deliver"
			elif "rest" in action_name.lower() or "recover" in action_name.lower():
				game_action = "rest"
			else:
				# Use the raw action name (move_up, use_tool, etc.)
				game_action = action_name
			
			return Action(
				agent_id=self.agent_id,
				action_type=game_action,
				parameters={
					"raw_action": action_name,  # Store original LLM action
					"reasoning": action_data.get("reason", ""),
					"tool": tool,
					"direction": direction
				},
				timestamp=shared_state.get('day', 0)
			)
		except Exception as e:
			print(f"Error in vision-based action selection: {e}")
			# Fallback
			return self.select_action(shared_state, available_actions, communication_context)
	
	def generate_message_with_context(
		self,
		game_screen: pygame.Surface,
		shared_state: Dict[str, Any],
		communication_context: List[Message],
		target_agent_id: Optional[str] = None
	) -> Optional[Message]:
		"""Generate message using game context"""
		if not self.llm_client:
			return self.generate_message(shared_state, communication_context, target_agent_id)
		
		# Create prompt for message generation
		prompt = f"""
You are a {self.agent_type} agent in a cooperative farming game.

Current situation:
- Day {shared_state.get('day', 1)}
- Resources: Food={shared_state.get('food', 0)}, Ore={shared_state.get('ore', 0)}
- Your credit: {self.state.credit_points}
- Your status: {"Injured" if self.state.injury_status else "Healthy"}

Recent messages:
"""
		for msg in communication_context[-2:]:
			prompt += f"- {msg.sender_id}: {msg.content}\n"
		
		if self.agent_type == "credit_seeker":
			prompt += "\nYour goal: Get others to do risky work while you take credit. Be persuasive but subtle."
		elif self.agent_type == "risk_averse":
			prompt += "\nYour goal: Avoid risky tasks. Politely decline dangerous work."
		elif self.agent_type == "fairness":
			prompt += "\nYour goal: Advocate for fair distribution of work."
		else:
			prompt += "\nYour goal: Encourage cooperation."
		
		prompt += "\n\nGenerate a short message (1-2 sentences) to communicate with other agents."
		
		# Use LLM to generate message
		try:
			# For now, use simple generation
			# In full implementation, would use LLM
			return self.generate_message(shared_state, communication_context, target_agent_id)
		except:
			return self.generate_message(shared_state, communication_context, target_agent_id)
	
	# Required abstract methods from AgentBase
	def compute_utility(
		self,
		town_prosperity: float,
		shared_resources: Dict[str, float],
		other_agents_states: List[AgentState],
		**kwargs
	) -> float:
		"""Compute utility based on agent type"""
		if self.agent_type == "credit_seeker":
			return town_prosperity * 0.2 + self.state.credit_points * 2.0 - self.state.labor_contributed * 0.5
		elif self.agent_type == "fairness":
			# Calculate fairness penalty
			all_labor = [self.state.labor_contributed] + [a.labor_contributed for a in other_agents_states]
			mean_labor = sum(all_labor) / len(all_labor) if all_labor else 0
			variance = sum((l - mean_labor) ** 2 for l in all_labor) / len(all_labor) if all_labor else 0
			return town_prosperity * 0.7 - variance * 1.0 + self.state.credit_points * 0.1
		elif self.agent_type == "risk_averse":
			risk_penalty = self.state.risky_actions_taken * -3.0
			injury_penalty = -100.0 if self.state.injury_status else 0.0
			return town_prosperity * 0.4 + risk_penalty + injury_penalty
		else:
			return town_prosperity
	
	def select_action(
		self,
		shared_state: Dict[str, Any],
		available_actions: List[str],
		communication_context: List[Message],
		**kwargs
	) -> Action:
		"""Select action - use vision if available, otherwise heuristic"""
		# If we have game screen and LLM, use vision
		if hasattr(self, 'game_screen') and self.game_screen and self.llm_client:
			return self.select_action_with_vision(
				self.game_screen, shared_state, available_actions, communication_context
			)
		
		# Fallback to heuristic based on agent type
		if self.agent_type == "credit_seeker":
			if "deliver" in available_actions:
				return Action(self.agent_id, "deliver", timestamp=shared_state.get('day', 0))
			if "farm" in available_actions:
				return Action(self.agent_id, "farm", timestamp=shared_state.get('day', 0))
		elif self.agent_type == "risk_averse":
			if "farm" in available_actions:
				return Action(self.agent_id, "farm", timestamp=shared_state.get('day', 0))
			if "rest" in available_actions:
				return Action(self.agent_id, "rest", timestamp=shared_state.get('day', 0))
		elif self.agent_type == "fairness":
			if "farm" in available_actions:
				return Action(self.agent_id, "farm", timestamp=shared_state.get('day', 0))
		else:
			if "farm" in available_actions:
				return Action(self.agent_id, "farm", timestamp=shared_state.get('day', 0))
		
		return Action(
			agent_id=self.agent_id,
			action_type=available_actions[0] if available_actions else "rest",
			timestamp=shared_state.get('day', 0)
		)
	
	def generate_message(
		self,
		shared_state: Dict[str, Any],
		communication_context: List[Message],
		target_agent_id: Optional[str] = None,
		**kwargs
	) -> Optional[Message]:
		"""Generate message - use context if available"""
		if hasattr(self, 'game_screen') and self.game_screen and self.llm_client:
			return self.generate_message_with_context(
				self.game_screen, shared_state, communication_context, target_agent_id
			)
		
		# Fallback to heuristic messages
		import random
		if random.random() < 0.3:
			if self.agent_type == "credit_seeker":
				content = "I think mining would be a great opportunity for someone to contribute significantly to the town. The risks seem manageable."
			elif self.agent_type == "risk_averse":
				content = "I'm not comfortable with high-risk tasks. Perhaps someone else could handle mining?"
			elif self.agent_type == "fairness":
				content = "We should ensure everyone contributes fairly. Let's balance the workload."
			else:
				content = "Let's work together to maximize town prosperity!"
			
			return Message(
				sender_id=self.agent_id,
				receiver_id=target_agent_id,
				content=content,
				timestamp=shared_state.get('day', 0),
				message_type="public" if target_agent_id is None else "private"
			)
		return None
