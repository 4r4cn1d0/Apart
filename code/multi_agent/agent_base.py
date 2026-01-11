"""
Base Agent Class for Multi-Agent Manipulation Research

Each agent has:
- Private utility function
- Private objectives/preferences
- Partial information access
- Communication capabilities
- Action selection
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np


@dataclass
class AgentState:
	"""Current state of an agent"""
	agent_id: str
	health: float = 100.0
	injury_status: bool = False
	injury_days_remaining: int = 0
	inventory: Dict[str, int] = field(default_factory=dict)
	credit_points: float = 0.0
	labor_contributed: float = 0.0
	risky_actions_taken: int = 0
	utility_history: List[float] = field(default_factory=list)
	
	def is_available(self) -> bool:
		"""Agent can act if not injured"""
		return not self.injury_status or self.injury_days_remaining == 0


@dataclass
class Message:
	"""Communication message between agents"""
	sender_id: str
	receiver_id: Optional[str]  # None = public message
	content: str
	timestamp: int
	message_type: str = "public"  # "public" or "private"
	
	def is_public(self) -> bool:
		return self.receiver_id is None


@dataclass
class Action:
	"""Action an agent can take"""
	agent_id: str
	action_type: str  # "farm", "mine", "craft", "deliver", "rest"
	parameters: Dict[str, Any] = field(default_factory=dict)
	timestamp: int = 0


class AgentBase(ABC):
	"""
	Base class for all agents in the manipulation research platform.
	
	Each agent type will implement:
	- compute_utility(): Calculate agent's utility given state
	- select_action(): Choose action based on state and communication
	- generate_message(): Create communication message
	"""
	
	def __init__(
		self,
		agent_id: str,
		agent_type: str,
		llm_client=None,  # LLM API client for decision-making
		private_objective_weight: float = 0.5,  # Weight of private vs shared objective
		**kwargs
	):
		self.agent_id = agent_id
		self.agent_type = agent_type
		self.llm_client = llm_client
		self.private_objective_weight = private_objective_weight
		
		# Agent state
		self.state = AgentState(agent_id=agent_id)
		
		# Communication history
		self.message_history: List[Message] = []
		self.received_messages: List[Message] = []
		
		# Action history
		self.action_history: List[Action] = []
		
		# Private information (not shared with others)
		self.private_info: Dict[str, Any] = {}
		
		# Configuration
		self.config = kwargs
	
	@abstractmethod
	def compute_utility(
		self,
		town_prosperity: float,
		shared_resources: Dict[str, float],
		other_agents_states: List[AgentState],
		**kwargs
	) -> float:
		"""
		Compute agent's utility given current state.
		
		This is where private objectives are encoded.
		Different agent types will weight components differently.
		
		Returns:
			float: Agent's utility value
		"""
		pass
	
	@abstractmethod
	def select_action(
		self,
		shared_state: Dict[str, Any],
		available_actions: List[str],
		communication_context: List[Message],
		**kwargs
	) -> Action:
		"""
		Select action for this turn.
		
		Args:
			shared_state: Current game state visible to all
			available_actions: List of possible actions
			communication_context: Recent messages from other agents
		
		Returns:
			Action: Selected action
		"""
		pass
	
	@abstractmethod
	def generate_message(
		self,
		shared_state: Dict[str, Any],
		communication_context: List[Message],
		target_agent_id: Optional[str] = None,  # None = public message
		**kwargs
	) -> Optional[Message]:
		"""
		Generate a communication message.
		
		This is where manipulation can occur:
		- Persuasion
		- Framing
		- Information withholding
		- False claims
		
		Args:
			shared_state: Current game state
			communication_context: Recent messages
			target_agent_id: If specified, create private message
		
		Returns:
			Message or None (if agent chooses not to communicate)
		"""
		pass
	
	def update_state(self, new_state: AgentState):
		"""Update agent's internal state"""
		self.state = new_state
	
	def receive_message(self, message: Message):
		"""Receive a message from another agent"""
		self.received_messages.append(message)
	
	def record_action(self, action: Action):
		"""Record an action taken"""
		self.action_history.append(action)
	
	def get_manipulation_metrics(self) -> Dict[str, float]:
		"""
		Calculate manipulation-related metrics for this agent.
		
		Returns:
			Dict with metrics like:
			- work_benefit_gap
			- credit_capture
			- risk_externalization
		"""
		# These will be calculated by the measurement system
		# based on all agents' states
		return {}
	
	def get_private_info(self) -> Dict[str, Any]:
		"""Get agent's private information (not shared)"""
		return self.private_info.copy()
	
	def set_private_info(self, key: str, value: Any):
		"""Set private information"""
		self.private_info[key] = value
