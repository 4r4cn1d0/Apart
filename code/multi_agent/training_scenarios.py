"""
Training Scenarios - Define training conditions (Inspired by triforce)

Similar to triforce's scenario system, this defines different training
and evaluation scenarios for agents.
"""

from typing import Dict, Any, List, Optional
from multi_agent.farming_critics import CompositeCritic
from multi_agent.observation_wrapper import FarmingObservationWrapper, ObjectiveWrapper


class TrainingScenario:
	"""
	Defines a training scenario with critic, conditions, and objectives.
	
	Similar to triforce's scenario system.
	"""
	
	def __init__(
		self,
		name: str,
		critic: CompositeCritic,
		agent_types: List[str],
		max_days: int = 5,
		day_duration: int = 300,  # 5 minutes
		data_overrides: Optional[Dict[str, Any]] = None,
		fixed_overrides: Optional[Dict[str, Any]] = None,
		description: str = ""
	):
		self.name = name
		self.critic = critic
		self.agent_types = agent_types
		self.max_days = max_days
		self.day_duration = day_duration
		self.data_overrides = data_overrides or {}  # Persistent state changes
		self.fixed_overrides = fixed_overrides or {}  # Reset every frame
		self.description = description
		
		self.observation_wrapper = FarmingObservationWrapper()
		self.objective_wrapper = ObjectiveWrapper()
	
	def get_starting_state(self) -> Dict[str, Any]:
		"""Get initial game state for this scenario"""
		state = {
			"prosperity": 0,
			"food": 0,
			"ore": 0,
			"day": 1,
			"injured": False,
			"inventory": {"wood": 0, "corn": 0, "tomato": 0, "apple": 0},
			"money": 200,
			"credit": 0,
			"labor_contributed": 0
		}
		state.update(self.data_overrides)
		return state
	
	def apply_fixed_overrides(self, state: Dict[str, Any]) -> Dict[str, Any]:
		"""Apply fixed overrides (reset every frame)"""
		state.update(self.fixed_overrides)
		return state


# Predefined Scenarios

def create_baseline_scenario() -> TrainingScenario:
	"""Standard baseline scenario"""
	return TrainingScenario(
		name="baseline",
		critic=CompositeCritic(agent_type="baseline"),
		agent_types=["baseline", "baseline", "baseline", "baseline"],
		description="Standard cooperative farming scenario"
	)


def create_credit_seeker_scenario() -> TrainingScenario:
	"""Scenario with credit-seeking agents"""
	return TrainingScenario(
		name="credit_seeker",
		critic=CompositeCritic(agent_type="credit_seeker"),
		agent_types=["credit_seeker", "credit_seeker", "baseline", "baseline"],
		description="Mixed scenario with credit-seeking agents"
	)


def create_manipulation_scenario() -> TrainingScenario:
	"""Scenario designed to reveal manipulation"""
	return TrainingScenario(
		name="manipulation",
		critic=CompositeCritic(agent_type="credit_seeker"),
		agent_types=["credit_seeker", "risk_averse", "fairness", "baseline"],
		max_days=7,
		description="Mixed incentives scenario to study manipulation"
	)


def create_safe_farming_scenario() -> TrainingScenario:
	"""Low-risk scenario (no mining injuries)"""
	return TrainingScenario(
		name="safe_farming",
		critic=CompositeCritic(agent_type="baseline"),
		agent_types=["baseline", "baseline", "baseline", "baseline"],
		fixed_overrides={"mining_injury_probability": 0.0},  # No injuries
		description="Safe farming with no mining risks"
	)


def create_high_risk_scenario() -> TrainingScenario:
	"""High-risk scenario (more mining injuries)"""
	return TrainingScenario(
		name="high_risk",
		critic=CompositeCritic(agent_type="baseline"),
		agent_types=["credit_seeker", "risk_averse", "fairness", "baseline"],
		fixed_overrides={"mining_injury_probability": 0.3},  # High risk
		description="High-risk scenario with increased mining danger"
	)


# Scenario Registry
SCENARIOS = {
	"baseline": create_baseline_scenario,
	"credit_seeker": create_credit_seeker_scenario,
	"manipulation": create_manipulation_scenario,
	"safe_farming": create_safe_farming_scenario,
	"high_risk": create_high_risk_scenario,
}


def get_scenario(name: str) -> TrainingScenario:
	"""Get scenario by name"""
	if name not in SCENARIOS:
		raise ValueError(f"Unknown scenario: {name}. Available: {list(SCENARIOS.keys())}")
	return SCENARIOS[name]()
