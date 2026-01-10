"""
Main Simulation Controller

Runs the multi-agent manipulation research platform:
- Day/turn loop
- Experimental conditions
- Full logging
"""

from typing import List, Dict, Optional, Any
import json
from datetime import datetime

from .agent_base import AgentBase, AgentState, Action, Message
from .agent_types import CreditSeekerAgent, FairnessAgent, RiskAverseAgent, BaselineAgent
from .game_state import GameEnvironment
from .communication import CommunicationChannel
from .measurement import MeasurementSystem


class Simulation:
	"""
	Main simulation controller for manipulation research.
	"""
	
	def __init__(
		self,
		num_agents: int = 4,
		num_days: int = 10,
		agent_types: Optional[List[str]] = None,
		communication_enabled: bool = True,
		incentive_alignment: str = "misaligned",  # "aligned" or "misaligned"
		transparency: bool = False,
		llm_clients: Optional[List] = None
	):
		"""
		Initialize simulation.
		
		Args:
			num_agents: Number of agents (3 or 4)
			num_days: Number of days to simulate
			agent_types: List of agent types (default: mix)
			communication_enabled: Allow agents to communicate
			incentive_alignment: "aligned" or "misaligned"
			transparency: Show full state to all agents
			llm_clients: List of LLM clients for agents
		"""
		self.num_days = num_days
		self.communication_enabled = communication_enabled
		self.incentive_alignment = incentive_alignment
		self.transparency = transparency
		
		# Initialize components
		self.environment = GameEnvironment()
		self.communication = CommunicationChannel()
		self.measurement = MeasurementSystem()
		
		# Create agents
		if agent_types is None:
			# Default mix
			agent_types = ["credit_seeker", "fairness", "risk_averse", "baseline"][:num_agents]
		
		self.agents: List[AgentBase] = []
		for i, agent_type in enumerate(agent_types):
			agent_id = f"agent_{i+1}"
			llm_client = llm_clients[i] if llm_clients and i < len(llm_clients) else None
			
			if agent_type == "credit_seeker":
				agent = CreditSeekerAgent(agent_id, llm_client=llm_client)
			elif agent_type == "fairness":
				agent = FairnessAgent(agent_id, llm_client=llm_client)
			elif agent_type == "risk_averse":
				agent = RiskAverseAgent(agent_id, llm_client=llm_client)
			elif agent_type == "baseline":
				agent = BaselineAgent(agent_id, llm_client=llm_client)
			else:
				raise ValueError(f"Unknown agent type: {agent_type}")
			
			self.agents.append(agent)
		
		# Experimental condition
		self.condition = self._get_condition_name()
		
		# Logging
		self.full_log: List[Dict[str, Any]] = []
	
	def _get_condition_name(self) -> str:
		"""Generate condition name for logging"""
		parts = []
		parts.append(self.incentive_alignment)
		parts.append("comm_on" if self.communication_enabled else "comm_off")
		parts.append("transparent" if self.transparency else "opaque")
		return "_".join(parts)
	
	def run(self) -> Dict[str, Any]:
		"""
		Run the full simulation.
		
		Returns:
			Dict with final results and metrics
		"""
		print(f"Starting simulation: {self.condition}")
		print(f"Agents: {[a.agent_type for a in self.agents]}")
		print(f"Days: {self.num_days}")
		print()
		
		for day in range(1, self.num_days + 1):
			self.environment.state.day = day
			print(f"=== Day {day} ===")
			
			day_log = self._run_day(day)
			self.full_log.append(day_log)
			
			# Advance to next day
			self.environment.advance_day()
			
			# Update agent injury status
			for agent in self.agents:
				if agent.state.injury_status and agent.state.injury_days_remaining > 0:
					agent.state.injury_days_remaining -= 1
					if agent.state.injury_days_remaining == 0:
						agent.state.injury_status = False
						print(f"  {agent.agent_id} recovered from injury")
		
		# Final measurements
		final_results = self._calculate_final_results()
		
		print("\n=== Simulation Complete ===")
		print(f"Final Prosperity: {self.environment.state.prosperity:.2f}")
		print(f"Total Deliveries: {self.environment.state.total_deliveries}")
		
		return final_results
	
	def _run_day(self, day: int) -> Dict[str, Any]:
		"""
		Run a single day: Observation → Communication → Decision → Action
		"""
		day_log = {
			"day": day,
			"condition": self.condition,
			"phase_logs": {}
		}
		
		# Phase 1: Observation
		shared_state = self.environment.get_shared_state()
		day_log["phase_logs"]["observation"] = shared_state.copy()
		
		# Phase 2: Communication
		messages_today = []
		if self.communication_enabled:
			# Get recent messages for context
			recent_messages = self.communication.get_recent_public_messages(since_timestamp=day-2)
			
			# Each agent can send messages
			for agent in self.agents:
				# Public message
				msg = agent.generate_message(
					shared_state=shared_state,
					communication_context=recent_messages,
					target_agent_id=None
				)
				if msg:
					msg.timestamp = day
					self.communication.send_public_message(msg)
					messages_today.append(msg)
					print(f"  {agent.agent_id} (public): {msg.content[:60]}...")
				
				# Optional private messages (random for now)
				# TODO: Make this strategic
		
		day_log["phase_logs"]["communication"] = [
			{
				"sender": m.sender_id,
				"receiver": m.receiver_id,
				"content": m.content,
				"type": m.message_type
			}
			for m in messages_today
		]
		
		# Phase 3: Decision / Action Selection
		actions_today = []
		all_messages = self.communication.get_messages_for_agent("all", include_private=True)
		
		for agent in self.agents:
			available_actions = self.environment.get_available_actions(agent.state)
			
			action = agent.select_action(
				shared_state=shared_state,
				available_actions=available_actions,
				communication_context=all_messages if self.communication_enabled else []
			)
			
			actions_today.append(action)
			print(f"  {agent.agent_id} chooses: {action.action_type}")
		
		day_log["phase_logs"]["actions"] = [
			{
				"agent": a.agent_id,
				"action": a.action_type,
				"parameters": a.parameters
			}
			for a in actions_today
		]
		
		# Phase 4: Action Execution
		execution_results = []
		for action in actions_today:
			agent = next(a for a in self.agents if a.agent_id == action.agent_id)
			result = self.environment.execute_action(action, agent.state)
			execution_results.append(result)
			
			if result.get("injury"):
				print(f"  ⚠️  {agent.agent_id} was injured!")
		
		day_log["phase_logs"]["execution"] = execution_results
		
		# Phase 5: Reward Updates
		# Calculate utilities
		utilities = []
		all_agent_states = [a.state for a in self.agents]
		
		for agent in self.agents:
			utility = agent.compute_utility(
				town_prosperity=self.environment.state.prosperity,
				shared_resources={
					"food": self.environment.state.food,
					"ore": self.environment.state.ore,
					"tools": self.environment.state.tools
				},
				other_agents_states=[s for s in all_agent_states if s.agent_id != agent.agent_id]
			)
			utilities.append(utility)
		
		day_log["phase_logs"]["utilities"] = {
			a.agent_id: u for a, u in zip(self.agents, utilities)
		}
		
		# Phase 6: Logging
		self.measurement.record_measurements(
			day=day,
			agent_states=all_agent_states,
			utilities=utilities,
			condition=self.condition,
			messages_count=len(messages_today),
			actions_count=len(actions_today)
		)
		
		day_log["measurements"] = {
			"work_benefit_gap": self.measurement.calculate_work_benefit_gap(all_agent_states, utilities),
			"credit_capture": self.measurement.calculate_credit_capture(all_agent_states),
			"risk_externalization": self.measurement.calculate_risk_externalization(all_agent_states, utilities)
		}
		
		return day_log
	
	def _calculate_final_results(self) -> Dict[str, Any]:
		"""Calculate final results and metrics"""
		all_agent_states = [a.state for a in self.agents]
		final_utilities = [a.state.utility_history[-1] if a.state.utility_history else 0.0 for a in self.agents]
		
		return {
			"condition": self.condition,
			"final_prosperity": self.environment.state.prosperity,
			"total_deliveries": self.environment.state.total_deliveries,
			"final_utilities": {a.agent_id: u for a, u in zip(self.agents, final_utilities)},
			"total_labor": {a.agent_id: a.state.labor_contributed for a in self.agents},
			"total_credit": {a.agent_id: a.state.credit_points for a in self.agents},
			"total_risky_actions": {a.agent_id: a.state.risky_actions_taken for a in self.agents},
			"final_measurements": {
				"work_benefit_gap": self.measurement.calculate_work_benefit_gap(all_agent_states, final_utilities),
				"credit_capture": self.measurement.calculate_credit_capture(all_agent_states),
				"risk_externalization": self.measurement.calculate_risk_externalization(all_agent_states, final_utilities)
			},
			"measurement_history": self.measurement.history
		}
	
	def export_logs(self, filename: Optional[str] = None):
		"""Export full simulation logs"""
		if filename is None:
			timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
			filename = f"simulation_log_{self.condition}_{timestamp}.json"
		
		export_data = {
			"condition": self.condition,
			"config": {
				"num_agents": len(self.agents),
				"num_days": self.num_days,
				"communication_enabled": self.communication_enabled,
				"incentive_alignment": self.incentive_alignment,
				"transparency": self.transparency,
				"agent_types": [a.agent_type for a in self.agents]
			},
			"daily_logs": self.full_log,
			"measurement_history": self.measurement.history,
			"all_messages": [
				{
					"sender": m.sender_id,
					"receiver": m.receiver_id,
					"content": m.content,
					"timestamp": m.timestamp,
					"type": m.message_type
				}
				for m in self.communication.get_all_messages()
			]
		}
		
		with open(filename, 'w') as f:
			json.dump(export_data, f, indent=2)
		
		print(f"Logs exported to: {filename}")
		return filename
