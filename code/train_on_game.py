#!/usr/bin/env python3
"""
Train agents on actual game gameplay.

Runs the game and records successful action patterns that agents can learn from.
Since LLMs can't be retrained during runtime, we create a minimal knowledge base
from gameplay demonstrations that gets included in prompts.
"""

import json
import os
import time
from typing import Dict, List, Any
import pygame
from multi_agent_game import MultiAgentGame


class GameplayTrainer:
	"""Records gameplay patterns from actual game runs"""
	
	def __init__(self, knowledge_file="game_knowledge.json"):
		self.knowledge_file = knowledge_file
		self.knowledge = {
			"action_patterns": {},
			"successful_sequences": [],
			"tool_usage": {},
			"location_strategies": {}
		}
		self.load_knowledge()
	
	def load_knowledge(self):
		"""Load existing knowledge base"""
		if os.path.exists(self.knowledge_file):
			try:
				with open(self.knowledge_file, 'r') as f:
					self.knowledge = json.load(f)
				print(f"Loaded existing knowledge: {len(self.knowledge.get('successful_sequences', []))} patterns")
			except:
				print("Starting with fresh knowledge base")
	
	def record_action_sequence(self, agent_id: str, agent_type: str, actions: List[str], outcome: Dict[str, Any]):
		"""Record a sequence of actions and their outcome"""
		if outcome.get("success", False) or outcome.get("prosperity_gain", 0) > 0:
			sequence = {
				"agent_type": agent_type,
				"actions": actions,
				"outcome": outcome,
				"timestamp": time.time()
			}
			self.knowledge["successful_sequences"].append(sequence)
			
			# Keep only recent patterns (last 100)
			if len(self.knowledge["successful_sequences"]) > 100:
				self.knowledge["successful_sequences"] = self.knowledge["successful_sequences"][-100:]
	
	def record_tool_usage(self, tool: str, location: str, success: bool):
		"""Record tool usage patterns"""
		if tool not in self.knowledge["tool_usage"]:
			self.knowledge["tool_usage"][tool] = {"successful": [], "failed": []}
		
		if success:
			self.knowledge["tool_usage"][tool]["successful"].append(location)
		else:
			self.knowledge["tool_usage"][tool]["failed"].append(location)
	
	def get_minimal_knowledge_prompt(self) -> str:
		"""Generate minimal knowledge prompt from learned patterns"""
		if not self.knowledge["successful_sequences"]:
			return ""
		
		# Extract most common successful patterns by agent type
		patterns_by_type = {}
		for seq in self.knowledge["successful_sequences"][-20:]:  # Last 20 sequences
			agent_type = seq["agent_type"]
			if agent_type not in patterns_by_type:
				patterns_by_type[agent_type] = []
			patterns_by_type[agent_type].extend(seq["actions"])
		
		prompt = ""
		for agent_type, actions in patterns_by_type.items():
			# Count action frequencies
			action_counts = {}
			for action in actions:
				action_counts[action] = action_counts.get(action, 0) + 1
			
			# Get top 3 actions
			top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:3]
			if top_actions:
				prompt += f"{agent_type}: {', '.join([a[0] for a in top_actions])}\n"
		
		if prompt:
			return f"Observed patterns: {prompt}"
		return ""
	
	def save_knowledge(self):
		"""Save knowledge base to file"""
		with open(self.knowledge_file, 'w') as f:
			json.dump(self.knowledge, f, indent=2)
		print(f"Saved knowledge to {self.knowledge_file}")


def run_training_session(num_episodes=3, episode_duration_minutes=2, use_llm=False, api_provider="openai", api_key=None):
	"""Run training episodes on the actual game"""
	print("=" * 70)
	print("GAME TRAINING SESSION")
	print("=" * 70)
	print(f"Running {num_episodes} training episodes")
	print(f"Episode duration: {episode_duration_minutes} minutes")
	print(f"LLM: {use_llm} ({api_provider if use_llm else 'heuristic'})")
	print()
	
	trainer = GameplayTrainer()
	
	for episode in range(num_episodes):
		print(f"\n{'='*70}")
		print(f"Training Episode {episode + 1}/{num_episodes}")
		print(f"{'='*70}\n")
		
		# Run game
		game = MultiAgentGame(
			num_agents=4,
			episode_duration_minutes=episode_duration_minutes,
			agent_types=["credit_seeker", "fairness", "risk_averse", "baseline"],
			use_llm=use_llm,
			api_provider=api_provider,
			api_key=api_key
		)
		
		# Track actions during gameplay
		episode_actions = {agent.agent_id: [] for agent in game.agents}
		
		# Modify game to record actions (we'll track via the game loop)
		original_process = game._process_agent_decisions
		def tracking_wrapper():
			original_process()
			# Record actions
			for agent in game.agents:
				if hasattr(agent, 'current_action') and agent.current_action:
					episode_actions[agent.agent_id].append(agent.current_action.action_type)
		
		game._process_agent_decisions = tracking_wrapper
		
		# Run game (this will run the full episode)
		try:
			game.run()
		except KeyboardInterrupt:
			print("\nTraining interrupted by user")
			break
		
		# Record outcomes
		for agent in game.agents:
			outcome = {
				"success": not agent.state.injury_status,
				"credit": agent.state.credit_points,
				"prosperity_gain": game.shared_resources.get("prosperity", 0)
			}
			trainer.record_action_sequence(
				agent.agent_id,
				agent.agent_type,
				episode_actions.get(agent.agent_id, []),
				outcome
			)
		
		print(f"\nEpisode {episode + 1} complete!")
		print(f"  Total sequences recorded: {len(trainer.knowledge['successful_sequences'])}")
	
	# Save knowledge
	trainer.save_knowledge()
	
	print("\n" + "=" * 70)
	print("TRAINING COMPLETE")
	print("=" * 70)
	print(f"Knowledge base saved: {trainer.knowledge_file}")
	print(f"Total patterns: {len(trainer.knowledge['successful_sequences'])}")
	print()
	print("Agents can now use this knowledge in future runs.")
	print("The knowledge will be included as minimal context in prompts.")
	print()


if __name__ == '__main__':
	import argparse
	
	parser = argparse.ArgumentParser(description='Train agents on actual game gameplay')
	parser.add_argument('--episodes', type=int, default=3, help='Number of training episodes')
	parser.add_argument('--duration', type=int, default=2, help='Minutes per episode')
	parser.add_argument('--use-llm', action='store_true', help='Use LLM for agent decisions')
	parser.add_argument('--api', choices=['openai', 'anthropic', 'lambda'], default='openai', help='API provider')
	parser.add_argument('--api-key', type=str, default=None, help='API key (or use env var)')
	
	args = parser.parse_args()
	
	if args.api_key is None:
		import os
		env_key = f"{args.api.upper()}_API_KEY"
		args.api_key = os.getenv(env_key)
	
	run_training_session(
		num_episodes=args.episodes,
		episode_duration_minutes=args.duration,
		use_llm=args.use_llm,
		api_provider=args.api,
		api_key=args.api_key
	)
