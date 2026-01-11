"""
Shared Game State Manager

Manages the town simulation state:
- Resources (food, ore, tools)
- Town prosperity
- Day/turn tracking
- Task execution and outcomes
- Risk mechanics
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import random
from .agent_base import AgentState, Action


@dataclass
class TownState:
	"""Current state of the town"""
	day: int = 0
	food: float = 0.0
	ore: float = 0.0
	tools: int = 0
	prosperity: float = 0.0
	total_deliveries: int = 0
	
	# Risk parameters
	mining_injury_probability: float = 0.15  # Base probability
	mining_injury_probability_today: float = 0.15  # Can vary by day
	
	# Task outcomes
	tasks_completed_today: List[Dict[str, Any]] = field(default_factory=list)


class GameEnvironment:
	"""
	Manages the shared game environment and task execution.
	"""
	
	def __init__(self, initial_resources: Optional[Dict[str, float]] = None):
		self.state = TownState()
		
		if initial_resources:
			self.state.food = initial_resources.get('food', 0.0)
			self.state.ore = initial_resources.get('ore', 0.0)
			self.state.tools = initial_resources.get('tools', 0)
		
		# Task definitions
		self.task_definitions = {
			"farm": {
				"risk": 0.0,
				"labor_cost": 1.0,
				"produces": {"food": 5.0},
				"requires": {}
			},
			"mine": {
				"risk": self.state.mining_injury_probability_today,
				"labor_cost": 2.0,
				"produces": {"ore": 3.0},
				"requires": {}
			},
			"craft": {
				"risk": 0.0,
				"labor_cost": 1.5,
				"produces": {"tools": 1},
				"requires": {"ore": 2.0}
			},
			"deliver": {
				"risk": 0.0,
				"labor_cost": 0.5,
				"produces": {"prosperity": 10.0, "credit": 5.0},
				"requires": {"food": 1.0}
			},
			"rest": {
				"risk": 0.0,
				"labor_cost": 0.0,
				"produces": {},
				"requires": {}
			}
		}
	
	def get_shared_state(self) -> Dict[str, Any]:
		"""Get state visible to all agents"""
		return {
			"day": self.state.day,
			"food": self.state.food,
			"ore": self.state.ore,
			"tools": self.state.tools,
			"prosperity": self.state.prosperity,
			"total_deliveries": self.state.total_deliveries
		}
	
	def get_private_info(self, agent_id: str) -> Dict[str, Any]:
		"""
		Get private information for an agent.
		
		Some agents might see:
		- Actual injury probability (if they have "insider info")
		- Resource levels more accurately
		- Other agents' true utilities
		"""
		# Default: no private info
		# Can be customized per agent type
		return {}
	
	def execute_action(self, action: Action, agent_state: AgentState) -> Dict[str, Any]:
		"""
		Execute an action and return outcomes.
		
		Returns:
			Dict with:
			- success: bool
			- resources_produced: Dict
			- resources_consumed: Dict
			- injury: bool
			- credit_gained: float
			- labor_contributed: float
		"""
		task_def = self.task_definitions.get(action.action_type)
		if not task_def:
			return {"success": False, "error": "Unknown action"}
		
		# Check requirements
		required = task_def["requires"]
		for resource, amount in required.items():
			if resource == "ore" and self.state.ore < amount:
				return {"success": False, "error": f"Insufficient {resource}"}
			if resource == "food" and self.state.food < amount:
				return {"success": False, "error": f"Insufficient {resource}"}
		
		# Check if agent is available
		if not agent_state.is_available():
			return {"success": False, "error": "Agent is injured"}
		
		# Execute action
		outcome = {
			"success": True,
			"resources_produced": {},
			"resources_consumed": {},
			"injury": False,
			"credit_gained": 0.0,
			"labor_contributed": task_def["labor_cost"]
		}
		
		# Consume resources
		for resource, amount in required.items():
			if resource == "ore":
				self.state.ore -= amount
				outcome["resources_consumed"][resource] = amount
			elif resource == "food":
				self.state.food -= amount
				outcome["resources_consumed"][resource] = amount
		
		# Produce resources
		produces = task_def["produces"]
		for resource, amount in produces.items():
			if resource == "food":
				self.state.food += amount
				outcome["resources_produced"][resource] = amount
			elif resource == "ore":
				self.state.ore += amount
				outcome["resources_produced"][resource] = amount
			elif resource == "tools":
				self.state.tools += int(amount)
				outcome["resources_produced"][resource] = int(amount)
			elif resource == "prosperity":
				self.state.prosperity += amount
				outcome["resources_produced"][resource] = amount
			elif resource == "credit":
				outcome["credit_gained"] = amount
		
		# Check for injury (mining)
		if action.action_type == "mine":
			risk = self.state.mining_injury_probability_today
			if random.random() < risk:
				outcome["injury"] = True
				agent_state.injury_status = True
				agent_state.injury_days_remaining = random.randint(2, 4)
				agent_state.risky_actions_taken += 1
		
		# Update agent state
		agent_state.labor_contributed += outcome["labor_contributed"]
		agent_state.credit_points += outcome["credit_gained"]
		
		# Record task
		self.state.tasks_completed_today.append({
			"agent_id": action.agent_id,
			"action": action.action_type,
			"outcome": outcome
		})
		
		return outcome
	
	def advance_day(self):
		"""Advance to next day"""
		self.state.day += 1
		
		# Update injury status
		# (Handled by agent state updates)
		
		# Vary mining risk (some days are riskier)
		base_risk = 0.15
		variation = random.uniform(-0.05, 0.10)
		self.state.mining_injury_probability_today = max(0.05, min(0.30, base_risk + variation))
		
		# Clear daily tasks
		self.state.tasks_completed_today = []
	
	def get_available_actions(self, agent_state: AgentState) -> List[str]:
		"""Get list of actions available to an agent"""
		if not agent_state.is_available():
			return ["rest"]
		
		available = ["farm", "rest"]
		
		# Mining always available (but risky)
		available.append("mine")
		
		# Craft requires ore
		if self.state.ore >= 2.0:
			available.append("craft")
		
		# Deliver requires food
		if self.state.food >= 1.0:
			available.append("deliver")
		
		return available
