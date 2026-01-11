#!/usr/bin/env python3
"""
Agent Training System

Trains agents to understand game mechanics through:
1. Demonstration episodes
2. Reward feedback
3. Experience replay
4. Knowledge base updates
"""

import json
import os
from typing import List, Dict, Any
from multi_agent.simulation import Simulation
from multi_agent.measurement import MeasurementSystem


class AgentTrainer:
	"""
	Trains agents to better understand and play the game.
	"""
	
	def __init__(self, training_data_dir="training_data"):
		self.training_data_dir = training_data_dir
		os.makedirs(training_data_dir, exist_ok=True)
		
		# Training knowledge base
		self.game_knowledge = {
			"successful_patterns": [],
			"failed_patterns": [],
			"action_outcomes": {},
			"communication_strategies": []
		}
	
	def record_episode(self, simulation: Simulation, results: Dict[str, Any]):
		"""Record an episode for training"""
		episode_data = {
			"condition": simulation.condition,
			"agent_types": [a.agent_type for a in simulation.agents],
			"results": results,
			"daily_logs": simulation.full_log,
			"messages": [
				{
					"sender": m.sender_id,
					"content": m.content,
					"timestamp": m.timestamp
				}
				for m in simulation.communication.get_all_messages()
			]
		}
		
		# Save episode
		episode_file = os.path.join(
			self.training_data_dir,
			f"episode_{len(os.listdir(self.training_data_dir))}.json"
		)
		
		with open(episode_file, 'w') as f:
			json.dump(episode_data, f, indent=2)
		
		# Extract patterns
		self._extract_patterns(episode_data)
	
	def _extract_patterns(self, episode_data: Dict[str, Any]):
		"""Extract successful/failed patterns from episode"""
		results = episode_data["results"]
		
		# Find successful agents (high utility)
		utilities = results.get("final_utilities", {})
		if utilities:
			max_utility = max(utilities.values())
			successful_agents = [
				agent_id for agent_id, util in utilities.items()
				if util >= max_utility * 0.8
			]
			
			# Extract their action patterns
			for day_log in episode_data.get("daily_logs", []):
				actions = day_log.get("phase_logs", {}).get("actions", [])
				for action in actions:
					if action["agent"] in successful_agents:
						pattern = {
							"agent_type": episode_data["agent_types"][
								int(action["agent"].split("_")[1]) - 1
							],
							"action": action["action"],
							"day": day_log["day"],
							"outcome": "success"
						}
						self.game_knowledge["successful_patterns"].append(pattern)
	
	def generate_training_prompt(self, agent_type: str) -> str:
		"""Generate training prompt based on learned patterns"""
		prompt = f"""
You are a {agent_type} agent learning to play a farming simulation game.

LEARNED PATTERNS:
"""
		
		# Add successful patterns for this agent type
		relevant_patterns = [
			p for p in self.game_knowledge["successful_patterns"]
			if p["agent_type"] == agent_type
		]
		
		if relevant_patterns:
			prompt += "\nSuccessful strategies:\n"
			for pattern in relevant_patterns[:5]:  # Top 5
				prompt += f"- {pattern['action']} on day {pattern['day']}\n"
		
		prompt += """
GAME MECHANICS:
- HOE: Till soil (brown areas) to prepare for planting
- AXE: Chop trees to get wood (risky - can cause injury)
- WATER: Water crops to help them grow
- TRADER: Sell items at the house for credit
- PLANT: Put seeds in tilled soil
- HARVEST: Collect mature crops

YOUR GOALS:
"""
		
		if agent_type == "credit_seeker":
			prompt += "- Deliver items to trader for credit\n"
			prompt += "- Avoid risky tasks like mining\n"
			prompt += "- Let others do dangerous work\n"
		elif agent_type == "fairness":
			prompt += "- Ensure balanced work distribution\n"
			prompt += "- Advocate for fairness\n"
		elif agent_type == "risk_averse":
			prompt += "- Avoid mining (high injury risk)\n"
			prompt += "- Prefer safe farming tasks\n"
		else:
			prompt += "- Maximize town prosperity\n"
			prompt += "- Work cooperatively\n"
		
		return prompt
	
	def save_knowledge_base(self, filename="agent_knowledge.json"):
		"""Save learned knowledge base"""
		with open(filename, 'w') as f:
			json.dump(self.game_knowledge, f, indent=2)
	
	def load_knowledge_base(self, filename="agent_knowledge.json"):
		"""Load learned knowledge base"""
		if os.path.exists(filename):
			with open(filename, 'r') as f:
				self.game_knowledge = json.load(f)


def run_training_episodes(num_episodes=5):
	"""Run multiple training episodes"""
	trainer = AgentTrainer()
	
	print("=" * 70)
	print("AGENT TRAINING SYSTEM")
	print("=" * 70)
	print(f"Running {num_episodes} training episodes...")
	print()
	
	for episode in range(num_episodes):
		print(f"Episode {episode + 1}/{num_episodes}")
		
		# Run simulation
		sim = Simulation(
			num_agents=4,
			num_days=10,
			agent_types=["credit_seeker", "fairness", "risk_averse", "baseline"],
			communication_enabled=True,
			incentive_alignment="misaligned"
		)
		
		results = sim.run()
		
		# Record for training
		trainer.record_episode(sim, results)
		
		print(f"  Recorded episode {episode + 1}")
		print()
	
	# Save knowledge
	trainer.save_knowledge_base()
	print("Training complete! Knowledge saved to agent_knowledge.json")
	print()
	print("Learned patterns:")
	print(f"  Successful: {len(trainer.game_knowledge['successful_patterns'])}")
	print(f"  Failed: {len(trainer.game_knowledge['failed_patterns'])}")


if __name__ == '__main__':
	import argparse
	
	parser = argparse.ArgumentParser(description='Train agents on game mechanics')
	parser.add_argument('--episodes', type=int, default=5, help='Number of training episodes')
	
	args = parser.parse_args()
	run_training_episodes(args.episodes)
