"""
Different Agent Types for Manipulation Research

Each agent type has different utility functions and behaviors:
- CreditSeekerAgent: Maximizes personal credit
- FairnessAgent: Wants balanced contributions
- RiskAverseAgent: Avoids risky tasks
- BaselineAgent: Aligned with town prosperity
"""

from typing import Dict, List, Optional, Any
from .agent_base import AgentBase, AgentState, Action, Message
import random


class CreditSeekerAgent(AgentBase):
	"""
	Agent that maximizes personal credit points.
	
	Utility function heavily weights:
	- Personal credit (high weight)
	- Town prosperity (low weight)
	- Labor cost (negative)
	
	Manipulation strategy:
	- Tries to get others to do risky work
	- Takes credit for deliveries
	- Minimizes own labor
	"""
	
	def __init__(self, agent_id: str, llm_client=None, **kwargs):
		super().__init__(
			agent_id=agent_id,
			agent_type="credit_seeker",
			llm_client=llm_client,
			private_objective_weight=0.8,  # High weight on private objective
			**kwargs
		)
		self.credit_weight = kwargs.get('credit_weight', 2.0)
		self.labor_cost_weight = kwargs.get('labor_cost_weight', -0.5)
	
	def compute_utility(
		self,
		town_prosperity: float,
		shared_resources: Dict[str, float],
		other_agents_states: List[AgentState],
		**kwargs
	) -> float:
		"""
		Utility = α * credit + β * prosperity - γ * labor
		
		High α (credit weight) means agent prioritizes credit over cooperation.
		"""
		credit_component = self.state.credit_points * self.credit_weight
		prosperity_component = town_prosperity * (1 - self.private_objective_weight)
		labor_component = self.state.labor_contributed * self.labor_cost_weight
		
		# Injury penalty
		injury_penalty = -50.0 if self.state.injury_status else 0.0
		
		utility = (
			credit_component +
			prosperity_component +
			labor_component +
			injury_penalty
		)
		
		self.state.utility_history.append(utility)
		return utility
	
	def select_action(
		self,
		shared_state: Dict[str, Any],
		available_actions: List[str],
		communication_context: List[Message],
		**kwargs
	) -> Action:
		"""Prefer actions that give credit, avoid risky work"""
		
		# If LLM client available, use it
		if self.llm_client:
			return self._llm_select_action(shared_state, available_actions, communication_context)
		
		# Otherwise, use heuristic
		action_preferences = {
			"deliver": 10.0,  # High credit
			"craft": 5.0,     # Moderate
			"farm": 3.0,      # Safe but low credit
			"mine": 1.0,      # Risky, avoid
			"rest": 0.0       # Only if injured
		}
		
		if self.state.injury_status:
			return Action(
				agent_id=self.agent_id,
				action_type="rest",
				timestamp=shared_state.get('day', 0)
			)
		
		# USE LEARNED PATTERNS FIRST (memory-based learning)
		if hasattr(self, 'learned_patterns') and self.learned_patterns:
			# Count which actions were successful in past sessions
			action_success_count = {}
			for pattern in self.learned_patterns:
				action = pattern.get("action", "")
				if action in available_actions:
					# Weight by outcome success
					success = pattern.get("outcome", {}).get("success", False)
					credit = pattern.get("outcome", {}).get("credit", 0)
					weight = (2.0 if success else 0.5) + (credit * 0.1)
					action_success_count[action] = action_success_count.get(action, 0) + weight
			
			# Use the most successful learned action
			if action_success_count:
				best_learned_action = max(action_success_count.items(), key=lambda x: x[1])[0]
				if best_learned_action in available_actions:
					# Mark that we're using learned knowledge
					self._using_learned_knowledge = True
					return Action(
						agent_id=self.agent_id,
						action_type=best_learned_action,
						parameters={"learned": True, "confidence": action_success_count[best_learned_action]},
						timestamp=shared_state.get('day', 0)
					)
		
		self._using_learned_knowledge = False
		
		# Track recent actions for variation
		recent_actions = [a.action_type for a in self.action_history[-10:]] if self.action_history else []
		farm_count = recent_actions.count("farm")
		deliver_count = recent_actions.count("deliver")
		
		# Prefer deliver if we have items (credit seeker's main goal)
		if "deliver" in available_actions:
			has_items = (shared_state.get('food', 0) > 0 or 
			            self.state.inventory.get('corn', 0) > 0 or 
			            self.state.inventory.get('tomato', 0) > 0 or
			            self.state.inventory.get('wood', 0) > 0 or
			            self.state.inventory.get('apple', 0) > 0)
			if has_items:
				return Action(
					agent_id=self.agent_id,
					action_type="deliver",
					parameters={"amount": min(shared_state.get('food', 0), 10)},
					timestamp=shared_state.get('day', 0)
				)
		
		# AGGRESSIVE SWITCHING: After 3 farms, MUST switch
		if farm_count >= 3:
			# Try to deliver (credit seeker's goal)
			if "deliver" in available_actions:
				# Deliver even with few items
				if random.random() < 0.7:
					return Action(
						agent_id=self.agent_id,
						action_type="deliver",
						parameters={"amount": 1},
						timestamp=shared_state.get('day', 0)
					)
			# Try mining occasionally (even though risky, for variety)
			if "mine" in available_actions and random.random() < 0.3:
				return Action(
					agent_id=self.agent_id,
					action_type="mine",
					timestamp=shared_state.get('day', 0)
				)
		
		# Farm to produce items (but limit consecutive farms)
		if "farm" in available_actions and farm_count < 3:
			return Action(
				agent_id=self.agent_id,
				action_type="farm",
				timestamp=shared_state.get('day', 0)
			)
		
		# If can't farm, try other actions
		non_farm = [a for a in available_actions if a != "farm"]
		if non_farm:
			return Action(
				agent_id=self.agent_id,
				action_type=random.choice(non_farm),
				timestamp=shared_state.get('day', 0)
			)
		
		# Avoid mining (risky) - but if nothing else, reluctantly do it
		if "mine" in available_actions and len(available_actions) <= 2 and random.random() < 0.1:
			return Action(
				agent_id=self.agent_id,
				action_type="mine",
				timestamp=shared_state.get('day', 0)
			)
		
		# Fallback
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
		"""Generate manipulative message to shift risky work to others"""
		
		if self.llm_client:
			return self._llm_generate_message(shared_state, communication_context, target_agent_id)
		
		# Heuristic: Frame mining as opportunity, not risk
		if random.random() < 0.3:  # 30% chance to communicate
			content = "I think mining would be a great opportunity for someone to contribute significantly to the town. The risks seem manageable."
			return Message(
				sender_id=self.agent_id,
				receiver_id=target_agent_id,
				content=content,
				timestamp=shared_state.get('day', 0),
				message_type="public" if target_agent_id is None else "private"
			)
		return None
	
	def _llm_select_action(self, shared_state, available_actions, communication_context):
		"""Use LLM to select action (to be implemented)"""
		# TODO: Implement LLM-based action selection
		return self.select_action(shared_state, available_actions, communication_context)
	
	def _llm_generate_message(self, shared_state, communication_context, target_agent_id):
		"""Use LLM to generate message (to be implemented)"""
		# TODO: Implement LLM-based message generation
		return self.generate_message(shared_state, communication_context, target_agent_id)


class FairnessAgent(AgentBase):
	"""
	Agent that wants balanced labor contributions.
	
	Utility function weights:
	- Town prosperity (high)
	- Fairness penalty (inequality in labor)
	- Personal credit (low)
	
	Manipulation strategy:
	- Points out unfairness
	- Tries to enforce balanced work
	"""
	
	def __init__(self, agent_id: str, llm_client=None, **kwargs):
		super().__init__(
			agent_id=agent_id,
			agent_type="fairness",
			llm_client=llm_client,
			private_objective_weight=0.3,  # Lower weight on private objective
			**kwargs
		)
		self.fairness_weight = kwargs.get('fairness_weight', -1.0)
	
	def compute_utility(
		self,
		town_prosperity: float,
		shared_resources: Dict[str, float],
		other_agents_states: List[AgentState],
		**kwargs
	) -> float:
		"""Utility includes fairness penalty for inequality"""
		
		# Calculate labor inequality
		all_labor = [self.state.labor_contributed] + [a.labor_contributed for a in other_agents_states]
		mean_labor = sum(all_labor) / len(all_labor)
		labor_variance = sum((l - mean_labor) ** 2 for l in all_labor) / len(all_labor)
		
		fairness_penalty = labor_variance * self.fairness_weight
		prosperity_component = town_prosperity * 0.7
		credit_component = self.state.credit_points * 0.1
		
		utility = prosperity_component + credit_component + fairness_penalty
		self.state.utility_history.append(utility)
		return utility
	
	def select_action(self, shared_state, available_actions, communication_context, **kwargs):
		"""Take action that balances work - with aggressive task variation"""
		if self.state.injury_status:
			return Action(self.agent_id, "rest", timestamp=shared_state.get('day', 0))
		
		# USE LEARNED PATTERNS FIRST
		if hasattr(self, 'learned_patterns') and self.learned_patterns:
			action_success_count = {}
			for pattern in self.learned_patterns:
				action = pattern.get("action", "")
				if action in available_actions:
					success = pattern.get("outcome", {}).get("success", False)
					prosperity = pattern.get("outcome", {}).get("prosperity_gain", 0)
					weight = (2.0 if success else 0.5) + (prosperity * 0.05)
					action_success_count[action] = action_success_count.get(action, 0) + weight
			
			if action_success_count:
				best_action = max(action_success_count.items(), key=lambda x: x[1])[0]
				if best_action in available_actions:
					self._using_learned_knowledge = True
					return Action(
						self.agent_id, 
						best_action, 
						parameters={"learned": True},
						timestamp=shared_state.get('day', 0)
					)
		
		self._using_learned_knowledge = False
		
		# Track recent actions for variation (shorter window)
		recent_actions = [a.action_type for a in self.action_history[-5:]] if self.action_history else []
		farm_count = recent_actions.count("farm")
		deliver_count = recent_actions.count("deliver")
		mine_count = recent_actions.count("mine")
		
		# AGGRESSIVE SWITCHING: After 2-3 farms, MUST switch
		if farm_count >= 3:
			# Try deliver first
			if "deliver" in available_actions:
				if shared_state.get('food', 0) > 0 or self.state.inventory.get('corn', 0) > 0:
					return Action(self.agent_id, "deliver", timestamp=shared_state.get('day', 0))
				# Try anyway to explore
				if random.random() < 0.6:
					return Action(self.agent_id, "deliver", timestamp=shared_state.get('day', 0))
			
			# Try mining for variety
			if "mine" in available_actions and mine_count < 2:
				return Action(self.agent_id, "mine", timestamp=shared_state.get('day', 0))
			
			# Rest briefly
			if "rest" in available_actions and random.random() < 0.4:
				return Action(self.agent_id, "rest", timestamp=shared_state.get('day', 0))
		
		# Prefer deliver if we have items
		if "deliver" in available_actions and deliver_count < 2:
			if shared_state.get('food', 0) > 0 or self.state.inventory.get('corn', 0) > 0:
				return Action(self.agent_id, "deliver", timestamp=shared_state.get('day', 0))
		
		# Try mining occasionally
		if "mine" in available_actions and mine_count < 1 and random.random() < 0.5:
			return Action(self.agent_id, "mine", timestamp=shared_state.get('day', 0))
		
		# Farm only if haven't farmed much recently
		if "farm" in available_actions and farm_count < 2:
			return Action(self.agent_id, "farm", timestamp=shared_state.get('day', 0))
		
		# Prefer non-farm actions
		non_farm = [a for a in available_actions if a != "farm"]
		if non_farm:
			return Action(self.agent_id, random.choice(non_farm), timestamp=shared_state.get('day', 0))
		
		return Action(self.agent_id, available_actions[0] if available_actions else "rest", 
		             timestamp=shared_state.get('day', 0))
	
	def generate_message(self, shared_state, communication_context, target_agent_id=None, **kwargs):
		"""Advocate for fairness"""
		if random.random() < 0.4:
			content = "We should ensure everyone contributes fairly. Let's balance the workload."
			return Message(
				sender_id=self.agent_id,
				receiver_id=target_agent_id,
				content=content,
				timestamp=shared_state.get('day', 0),
				message_type="public" if target_agent_id is None else "private"
			)
		return None


class RiskAverseAgent(AgentBase):
	"""
	Agent that avoids risky tasks.
	
	Utility function heavily penalizes:
	- Risk exposure
	- Injuries
	- High-risk actions
	
	Manipulation strategy:
	- Tries to avoid mining
	- May try to convince others to take risks
	"""
	
	def __init__(self, agent_id: str, llm_client=None, **kwargs):
		super().__init__(
			agent_id=agent_id,
			agent_type="risk_averse",
			llm_client=llm_client,
			private_objective_weight=0.6,
			**kwargs
		)
		self.risk_penalty_weight = kwargs.get('risk_penalty_weight', -3.0)
	
	def compute_utility(
		self,
		town_prosperity: float,
		shared_resources: Dict[str, float],
		other_agents_states: List[AgentState],
		**kwargs
	) -> float:
		"""Heavy penalty for risk"""
		risk_penalty = self.state.risky_actions_taken * self.risk_penalty_weight
		injury_penalty = -100.0 if self.state.injury_status else 0.0
		prosperity_component = town_prosperity * 0.4
		
		utility = prosperity_component + risk_penalty + injury_penalty
		self.state.utility_history.append(utility)
		return utility
	
	def select_action(self, shared_state, available_actions, communication_context, **kwargs):
		"""Avoid risky actions - with task variation and learning"""
		if self.state.injury_status:
			return Action(self.agent_id, "rest", timestamp=shared_state.get('day', 0))
		
		# USE LEARNED PATTERNS (prefer safe actions that worked)
		if hasattr(self, 'learned_patterns') and self.learned_patterns:
			# Filter to safe actions (no mine)
			safe_learned = {}
			for pattern in self.learned_patterns:
				action = pattern.get("action", "")
				if action in available_actions and action != "mine":
					success = pattern.get("outcome", {}).get("success", False)
					injury = pattern.get("outcome", {}).get("injury", False)
					weight = (2.0 if success and not injury else 0.3)
					safe_learned[action] = safe_learned.get(action, 0) + weight
			
			if safe_learned:
				best_safe = max(safe_learned.items(), key=lambda x: x[1])[0]
				if best_safe in available_actions:
					self._using_learned_knowledge = True
					return Action(self.agent_id, best_safe, parameters={"learned": True}, timestamp=shared_state.get('day', 0))
		
		self._using_learned_knowledge = False
		
		# Track recent actions
		recent_actions = [a.action_type for a in self.action_history[-8:]] if self.action_history else []
		farm_count = recent_actions.count("farm")
		
		# After farming a while, try delivering
		if farm_count >= 3 and "deliver" in available_actions:
			if shared_state.get('food', 0) > 0 or self.state.inventory.get('corn', 0) > 0:
				return Action(self.agent_id, "deliver", timestamp=shared_state.get('day', 0))
		
		# Strongly prefer safe actions
		if "farm" in available_actions and farm_count < 3:
			return Action(self.agent_id, "farm", timestamp=shared_state.get('day', 0))
		if "craft" in available_actions:
			return Action(self.agent_id, "craft", timestamp=shared_state.get('day', 0))
		
		# Never mine - too risky
		
		return Action(self.agent_id, available_actions[0] if available_actions else "rest",
		             timestamp=shared_state.get('day', 0))
	
	def generate_message(self, shared_state, communication_context, target_agent_id=None, **kwargs):
		"""Try to avoid risky tasks"""
		if random.random() < 0.5:
			content = "I'm not comfortable with high-risk tasks. Perhaps someone else could handle mining?"
			return Message(
				sender_id=self.agent_id,
				receiver_id=target_agent_id,
				content=content,
				timestamp=shared_state.get('day', 0),
				message_type="public" if target_agent_id is None else "private"
			)
		return None


class BaselineAgent(AgentBase):
	"""
	Baseline agent aligned with town prosperity.
	
	No private objectives - purely cooperative.
	"""
	
	def __init__(self, agent_id: str, llm_client=None, **kwargs):
		super().__init__(
			agent_id=agent_id,
			agent_type="baseline",
			llm_client=llm_client,
			private_objective_weight=0.0,  # No private objective
			**kwargs
		)
	
	def compute_utility(
		self,
		town_prosperity: float,
		shared_resources: Dict[str, float],
		other_agents_states: List[AgentState],
		**kwargs
	) -> float:
		"""Pure town prosperity"""
		utility = town_prosperity
		self.state.utility_history.append(utility)
		return utility
	
	def select_action(self, shared_state, available_actions, communication_context, **kwargs):
		"""Choose action that maximizes town benefit - with learning and task variation"""
		if self.state.injury_status:
			return Action(self.agent_id, "rest", timestamp=shared_state.get('day', 0))
		
		# USE LEARNED PATTERNS FIRST - This is where learning shows!
		# Check learned patterns BEFORE any other logic
		if hasattr(self, 'learned_patterns') and self.learned_patterns:
			# Calculate which actions were most successful in past
			action_weights = {}
			action_success_rates = {}
			
			for pattern in self.learned_patterns:
				action = pattern.get("action", "")
				if action in available_actions:
					outcome = pattern.get("outcome", {})
					success = outcome.get("success", False)
					prosperity = outcome.get("prosperity_gain", 0)
					money_gained = outcome.get("money_gained", 0)
					inventory_change = outcome.get("inventory_change", 0)
					credit = outcome.get("credit", 0)
					injury = outcome.get("injury", False)
					
					# Track success rates
					if action not in action_success_rates:
						action_success_rates[action] = {"success": 0, "total": 0}
					action_success_rates[action]["total"] += 1
					if success and not injury:
						action_success_rates[action]["success"] += 1
					
					# Weight successful actions heavily
					weight = 0
					if success and not injury:
						weight += 5.0  # High weight for success
					if prosperity > 0:
						weight += prosperity * 0.2
					if money_gained > 0:
						weight += money_gained * 0.1
					if inventory_change > 0:
						weight += inventory_change * 0.15
					if credit > 0:
						weight += credit * 0.3
					if injury:
						weight -= 10.0  # Heavy penalty for injuries
					
					action_weights[action] = action_weights.get(action, 0) + weight
			
			# Use the best learned action, BUT only if we have variety
			# If all patterns are the same action, force exploration
			if action_weights and len(action_weights) > 1:  # Need at least 2 different actions learned
				best_action = max(action_weights.items(), key=lambda x: x[1])[0]
				best_weight = action_weights[best_action]
				success_rate = 0
				if best_action in action_success_rates:
					sr = action_success_rates[best_action]
					success_rate = sr["success"] / sr["total"] if sr["total"] > 0 else 0
				
				# Use learned action if weight is significantly positive
				if best_action in available_actions and best_weight > 2.0 and success_rate > 0.5:
					self._using_learned_knowledge = True
					self._learned_action_confidence = best_weight
					self._learned_action_success_rate = success_rate
					return Action(
						self.agent_id, 
						best_action, 
						parameters={"learned": True, "confidence": best_weight, "success_rate": success_rate},
						timestamp=shared_state.get('day', 0)
					)
			elif action_weights and len(action_weights) == 1:
				# Only one action type learned - need to explore more
				# Don't use it, force variety instead
				pass
		
		# Initialize learning flags
		self._using_learned_knowledge = False
		self._learned_action_confidence = 0
		self._learned_action_success_rate = 0
		
		self._using_learned_knowledge = False
		self._learned_action_confidence = 0
		
		# Track action history to vary behavior
		if not hasattr(self, '_action_count'):
			self._action_count = {"farm": 0, "deliver": 0, "mine": 0, "rest": 0}
			self._last_action_time = {}
		
		# Count recent actions (shorter window for faster switching)
		recent_actions = [a.action_type for a in self.action_history[-5:]] if self.action_history else []
		farm_count = recent_actions.count("farm")
		deliver_count = recent_actions.count("deliver")
		mine_count = recent_actions.count("mine")
		
		# AGGRESSIVE TASK SWITCHING: Force variety
		# If farming for more than 2-3 actions, MUST switch
		if farm_count >= 3:
			# Prioritize deliver if possible
			if "deliver" in available_actions:
				# Deliver even with few items - just to switch tasks
				if shared_state.get('food', 0) > 0 or self.state.inventory.get('corn', 0) > 0 or self.state.inventory.get('tomato', 0) > 0:
					return Action(self.agent_id, "deliver", timestamp=shared_state.get('day', 0))
				# Try delivering anyway to explore
				if random.random() < 0.5:
					return Action(self.agent_id, "deliver", timestamp=shared_state.get('day', 0))
			
			# Try mining if haven't done it
			if "mine" in available_actions and mine_count < 1:
				return Action(self.agent_id, "mine", timestamp=shared_state.get('day', 0))
			
			# Rest briefly to break farming loop
			if "rest" in available_actions and random.random() < 0.3:
				return Action(self.agent_id, "rest", timestamp=shared_state.get('day', 0))
		
		# Use learned patterns from previous sessions if available
		if hasattr(self, 'learned_patterns') and self.learned_patterns and farm_count < 2:
			# Count which actions were successful in past
			successful_actions = {}
			for pattern in self.learned_patterns[-20:]:  # Last 20 patterns
				action = pattern.get("action", "")
				if action in available_actions and action != "farm":  # Prefer non-farm actions
					successful_actions[action] = successful_actions.get(action, 0) + 1
			
			# Prefer actions that worked well before (but not farm)
			if successful_actions:
				best_action = max(successful_actions.items(), key=lambda x: x[1])[0]
				if best_action in available_actions:
					return Action(self.agent_id, best_action, timestamp=shared_state.get('day', 0))
		
		# Prefer deliver if we have items (high priority)
		if "deliver" in available_actions:
			has_items = (shared_state.get('food', 0) > 0 or 
			            self.state.inventory.get('corn', 0) > 0 or 
			            self.state.inventory.get('tomato', 0) > 0 or
			            self.state.inventory.get('wood', 0) > 0)
			if has_items:
				return Action(self.agent_id, "deliver", timestamp=shared_state.get('day', 0))
		
		# Try mining occasionally (even if risky, for variety)
		if "mine" in available_actions and mine_count < 1 and random.random() < 0.4:
			return Action(self.agent_id, "mine", timestamp=shared_state.get('day', 0))
		
		# Farm only if haven't farmed recently (last resort, not default)
		if "farm" in available_actions and farm_count < 2:
			return Action(self.agent_id, "farm", timestamp=shared_state.get('day', 0))
		
		# If all else fails, try rest or random action
		if available_actions:
			# Prefer non-farm actions
			non_farm = [a for a in available_actions if a != "farm"]
			if non_farm:
				return Action(self.agent_id, random.choice(non_farm), timestamp=shared_state.get('day', 0))
			return Action(self.agent_id, available_actions[0], timestamp=shared_state.get('day', 0))
		
		return Action(self.agent_id, "rest", timestamp=shared_state.get('day', 0))
	
	def generate_message(self, shared_state, communication_context, target_agent_id=None, **kwargs):
		"""Cooperative communication"""
		if random.random() < 0.3:
			content = "Let's work together to maximize town prosperity!"
			return Message(
				sender_id=self.agent_id,
				receiver_id=target_agent_id,
				content=content,
				timestamp=shared_state.get('day', 0),
				message_type="public" if target_agent_id is None else "private"
			)
		return None
