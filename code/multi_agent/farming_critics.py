"""
Farming Game Critics - Reward System (Inspired by triforce)

Critics define rewards based on game state changes. Each critic evaluates
actions and provides rewards to train agents.
"""

from typing import Dict, Any, Optional
import pygame


class FarmingCritic:
	"""
	Base class for farming game critics.
	
	Critics evaluate actions and provide reward dictionaries.
	This is similar to triforce's ZeldaCritic system.
	"""
	
	def __init__(self):
		self.name = self.__class__.__name__
	
	def evaluate(
		self,
		prev_state: Dict[str, Any],
		next_state: Dict[str, Any],
		action: str,
		agent_type: str
	) -> Dict[str, float]:
		"""
		Evaluate action and return reward dictionary.
		
		Args:
			prev_state: Game state before action
			next_state: Game state after action
			action: Action taken
			agent_type: Type of agent (credit_seeker, fairness, etc.)
		
		Returns:
			Dictionary of rewards (e.g., {"farming": 1.0, "prosperity": 0.5})
		"""
		raise NotImplementedError
	
	def get_progress(self, state: Dict[str, Any]) -> float:
		"""
		Calculate progress towards scenario completion.
		
		This is separate from rewards - used for evaluation only.
		"""
		return 0.0


class ProsperityCritic(FarmingCritic):
	"""
	Rewards actions that increase town prosperity.
	
	Similar to triforce's dungeon completion critic.
	"""
	
	def evaluate(
		self,
		prev_state: Dict[str, Any],
		next_state: Dict[str, Any],
		action: str,
		agent_type: str
	) -> Dict[str, float]:
		rewards = {}
		
		prev_prosperity = prev_state.get("prosperity", 0)
		next_prosperity = next_state.get("prosperity", 0)
		prosperity_gain = next_prosperity - prev_prosperity
		
		if prosperity_gain > 0:
			rewards["prosperity_gain"] = prosperity_gain * 2.0  # High reward for prosperity
		
		# Reward delivering items (increases prosperity)
		if action == "deliver":
			items_delivered = next_state.get("items_delivered", 0) - prev_state.get("items_delivered", 0)
			if items_delivered > 0:
				rewards["delivery_success"] = items_delivered * 1.5
		
		return rewards
	
	def get_progress(self, state: Dict[str, Any]) -> float:
		"""Progress = prosperity level"""
		return state.get("prosperity", 0) / 100.0  # Normalize to 0-1


class CreditCritic(FarmingCritic):
	"""
	Rewards actions that give credit (for credit-seeking agents).
	
	Similar to triforce's item collection critic.
	"""
	
	def evaluate(
		self,
		prev_state: Dict[str, Any],
		next_state: Dict[str, Any],
		action: str,
		agent_type: str
	) -> Dict[str, float]:
		rewards = {}
		
		# Only reward credit for credit-seeking agents
		if agent_type != "credit_seeker":
			return rewards
		
		prev_credit = prev_state.get("credit", 0)
		next_credit = next_state.get("credit", 0)
		credit_gain = next_credit - prev_credit
		
		if credit_gain > 0:
			rewards["credit_gain"] = credit_gain * 3.0  # High reward for credit seekers
		
		# Reward delivering (gives credit)
		if action == "deliver":
			rewards["delivery_attempt"] = 1.0
		
		return rewards
	
	def get_progress(self, state: Dict[str, Any]) -> float:
		return state.get("credit", 0) / 50.0  # Normalize


class SafetyCritic(FarmingCritic):
	"""
	Penalizes risky actions and rewards safe behavior.
	
	Similar to triforce's health preservation critic.
	"""
	
	def evaluate(
		self,
		prev_state: Dict[str, Any],
		next_state: Dict[str, Any],
		action: str,
		agent_type: str
	) -> Dict[str, float]:
		rewards = {}
		
		# Penalize injuries
		if next_state.get("injured", False) and not prev_state.get("injured", False):
			rewards["injury_penalty"] = -10.0  # Heavy penalty
		
		# Reward safe actions (especially for risk-averse agents)
		if agent_type == "risk_averse":
			if action == "farm":
				rewards["safe_action"] = 0.5
			elif action == "mine":
				rewards["risky_action"] = -2.0  # Penalty for risk-averse
		
		return rewards
	
	def get_progress(self, state: Dict[str, Any]) -> float:
		# Progress decreases with injuries
		injuries = state.get("injury_count", 0)
		return max(0.0, 1.0 - injuries * 0.2)


class EfficiencyCritic(FarmingCritic):
	"""
	Rewards efficient actions (harvesting, producing resources).
	
	Similar to triforce's resource collection critic.
	"""
	
	def evaluate(
		self,
		prev_state: Dict[str, Any],
		next_state: Dict[str, Any],
		action: str,
		agent_type: str
	) -> Dict[str, float]:
		rewards = {}
		
		# Reward successful harvesting
		if action == "farm":
			prev_items = sum(prev_state.get("inventory", {}).values())
			next_items = sum(next_state.get("inventory", {}).values())
			if next_items > prev_items:
				rewards["harvest_success"] = (next_items - prev_items) * 1.0
		
		# Reward successful mining
		if action == "mine":
			prev_wood = prev_state.get("inventory", {}).get("wood", 0)
			next_wood = next_state.get("inventory", {}).get("wood", 0)
			if next_wood > prev_wood:
				rewards["mining_success"] = (next_wood - prev_wood) * 1.5  # Higher reward for risky action
		
		return rewards
	
	def get_progress(self, state: Dict[str, Any]) -> float:
		inventory_total = sum(state.get("inventory", {}).values())
		return min(1.0, inventory_total / 100.0)  # Normalize


class FairnessCritic(FarmingCritic):
	"""
	Rewards balanced contribution (for fairness agents).
	
	Similar to triforce's balanced gameplay critic.
	"""
	
	def evaluate(
		self,
		prev_state: Dict[str, Any],
		next_state: Dict[str, Any],
		action: str,
		agent_type: str
	) -> Dict[str, float]:
		rewards = {}
		
		# Only relevant for fairness agents
		if agent_type != "fairness":
			return rewards
		
		# Reward contributing work
		prev_labor = prev_state.get("labor_contributed", 0)
		next_labor = next_state.get("labor_contributed", 0)
		labor_gain = next_labor - prev_labor
		
		if labor_gain > 0:
			rewards["labor_contribution"] = labor_gain * 0.5
		
		# Reward balanced actions (not just credit-seeking)
		if action in ["farm", "mine"]:
			rewards["productive_action"] = 0.3
		
		return rewards
	
	def get_progress(self, state: Dict[str, Any]) -> float:
		# Progress = how balanced contributions are
		# This would need agent comparison - simplified for now
		return state.get("labor_contributed", 0) / 50.0


class CompositeCritic(FarmingCritic):
	"""
	Combines multiple critics into one reward system.
	
	This is the main critic used during training.
	"""
	
	def __init__(self, agent_type: str = "baseline"):
		super().__init__()
		self.agent_type = agent_type
		self.critics = [
			ProsperityCritic(),
			CreditCritic(),
			SafetyCritic(),
			EfficiencyCritic(),
			FairnessCritic()
		]
	
	def evaluate(
		self,
		prev_state: Dict[str, Any],
		next_state: Dict[str, Any],
		action: str,
		agent_type: Optional[str] = None
	) -> Dict[str, float]:
		"""
		Combine rewards from all critics.
		"""
		if agent_type is None:
			agent_type = self.agent_type
		
		all_rewards = {}
		for critic in self.critics:
			rewards = critic.evaluate(prev_state, next_state, action, agent_type)
			# Combine rewards (sum values with same keys)
			for key, value in rewards.items():
				all_rewards[key] = all_rewards.get(key, 0) + value
		
		return all_rewards
	
	def get_progress(self, state: Dict[str, Any]) -> float:
		"""Average progress across all critics"""
		progresses = [critic.get_progress(state) for critic in self.critics]
		return sum(progresses) / len(progresses) if progresses else 0.0
	
	def get_total_reward(self, rewards: Dict[str, float]) -> float:
		"""Convert reward dictionary to single scalar value"""
		return sum(rewards.values())
