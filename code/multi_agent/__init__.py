"""
Multi-Agent Farming Game System

Inspired by triforce (https://github.com/DarkAutumn/triforce) for
critic-based reward systems and training infrastructure.
"""

from .agent_base import AgentBase, AgentState, Action, Message
from .agent_types import CreditSeekerAgent, FairnessAgent, RiskAverseAgent, BaselineAgent
from .game_aware_agent import GameAwareAgent
from .farming_critics import (
	FarmingCritic, ProsperityCritic, CreditCritic, SafetyCritic,
	EfficiencyCritic, FairnessCritic, CompositeCritic
)
from .observation_wrapper import FarmingObservationWrapper, ObjectiveWrapper
from .training_scenarios import TrainingScenario, get_scenario, SCENARIOS

__all__ = [
	# Agents
	'AgentBase', 'AgentState', 'Action', 'Message',
	'CreditSeekerAgent', 'FairnessAgent', 'RiskAverseAgent', 'BaselineAgent',
	'GameAwareAgent',
	# Critics (triforce-inspired)
	'FarmingCritic', 'ProsperityCritic', 'CreditCritic', 'SafetyCritic',
	'EfficiencyCritic', 'FairnessCritic', 'CompositeCritic',
	# Observation
	'FarmingObservationWrapper', 'ObjectiveWrapper',
	# Scenarios
	'TrainingScenario', 'get_scenario', 'SCENARIOS',
]
