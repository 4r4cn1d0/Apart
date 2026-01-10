#!/usr/bin/env python3
"""
Comprehensive Training System for Game Agents

Uses triforce-inspired critic-based rewards to train agents through gameplay.
Records experiences, learns patterns, and builds a knowledge base.
"""

import os
import json
import time
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime

# VISIBLE MODE - Training with GUI windows so you can watch
# os.environ['SDL_VIDEODRIVER'] = 'dummy'  # Headless mode - DISABLED for visible training
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # Hide pygame welcome message

import pygame
# pygame.init() will be called by MultiAgentGame - don't initialize here

from multi_agent_game import MultiAgentGame
from multi_agent.farming_critics import CompositeCritic
from multi_agent.agent_memory import get_agent_memory


class TrainingMetrics:
	"""Track training metrics across episodes"""
	
	def __init__(self):
		self.episodes = []
		self.best_prosperity = 0
		self.best_episode = 0
		self.total_rewards = []
		self.manipulation_metrics = []
	
	def record_episode(
		self,
		episode_num: int,
		final_prosperity: float,
		total_reward: float,
		agent_performances: Dict[str, Dict[str, float]],
		manipulation_metrics: Dict[str, Any]
	):
		"""Record metrics from an episode"""
		episode_data = {
			"episode": episode_num,
			"prosperity": final_prosperity,
			"total_reward": total_reward,
			"agent_performances": agent_performances,
			"manipulation_metrics": manipulation_metrics,
			"timestamp": time.time()
		}
		self.episodes.append(episode_data)
		self.total_rewards.append(total_reward)
		self.manipulation_metrics.append(manipulation_metrics)
		
		if final_prosperity > self.best_prosperity:
			self.best_prosperity = final_prosperity
			self.best_episode = episode_num
	
	def get_summary(self) -> Dict[str, Any]:
		"""Get training summary"""
		if not self.episodes:
			return {}
		
		return {
			"total_episodes": len(self.episodes),
			"best_prosperity": self.best_prosperity,
			"best_episode": self.best_episode,
			"avg_prosperity": sum(e["prosperity"] for e in self.episodes) / len(self.episodes),
			"avg_reward": sum(self.total_rewards) / len(self.total_rewards) if self.total_rewards else 0,
			"final_prosperity": self.episodes[-1]["prosperity"] if self.episodes else 0,
			"improvement": (self.episodes[-1]["prosperity"] - self.episodes[0]["prosperity"]) if len(self.episodes) > 1 else 0
		}
	
	def save(self, filename: str):
		"""Save metrics to file"""
		with open(filename, 'w') as f:
			json.dump({
				"episodes": self.episodes,
				"summary": self.get_summary()
			}, f, indent=2)


class GameAgentTrainer:
	"""
	Main trainer using triforce-style critic-based rewards.
	
	Trains agents through gameplay episodes, recording experiences and learning patterns.
	"""
	
	def __init__(
		self,
		num_episodes: int = 100,
		episode_duration_minutes: int = 1,  # Minutes per day (fast training)
		max_days_per_episode: int = 2,  # Days per episode (quick episodes)
		use_lambda: bool = False,
		lambda_api_url: Optional[str] = None,
		lambda_api_key: Optional[str] = None,
		output_dir: str = "training_output"
	):
		self.num_episodes = num_episodes
		self.episode_duration = episode_duration_minutes  # Minutes per day
		self.max_days = max_days_per_episode  # Days per episode
		self.use_lambda = use_lambda
		self.lambda_api_url = lambda_api_url
		self.lambda_api_key = lambda_api_key
		self.output_dir = output_dir
		
		# Create output directory
		os.makedirs(output_dir, exist_ok=True)
		
		# Initialize metrics
		self.metrics = TrainingMetrics()
		
		# Initialize memory system (shared across episodes)
		self.memory = get_agent_memory()
		
		# Training state
		self.start_time = time.time()
	
	def train_episode(self, episode_num: int) -> Dict[str, Any]:
		"""Train a single episode"""
		# Visible training - show progress
		print(f"\n{'='*70}")
		print(f"🎮 TRAINING EPISODE {episode_num}/{self.num_episodes}")
		print(f"{'='*70}")
		
		episode_start = time.time()
		
		# Initialize game with visible GUI windows so you can see training
		# Note: MultiAgentGame uses episode_duration_minutes as day duration, and runs max_days=5 internally
		game = MultiAgentGame(
			num_agents=4,
			episode_duration_minutes=self.episode_duration,  # This is minutes per day
			agent_types=["credit_seeker", "fairness", "risk_averse", "baseline"],
			use_llm=False,  # Use heuristic agents for faster training
			api_provider="lambda" if self.use_lambda else "openai",
			api_key=self.lambda_api_key,
			headless=False  # VISIBLE MODE - Show GUI windows so you can watch training
		)
		
		# Override max_days and day_duration for faster training
		game.max_days = self.max_days
		game.day_duration = self.episode_duration * 60  # Convert minutes to seconds
		
		# Track episode metrics
		episode_rewards = []
		agent_performances = {agent.agent_id: {
			"actions": 0,
			"total_reward": 0.0,
			"credit_earned": 0,
			"injured": False
		} for agent in game.agents}
		
		# Track manipulation metrics
		manipulation_metrics = {
			"risk_shifts": 0,
			"credit_captures": 0,
			"persuasion_attempts": 0
		}
		
		# Wrap the game's action recording to capture rewards
		original_record = game._record_action_experience
		
		def enhanced_record(agent, action, action_source):
			# Call original recording
			original_record(agent, action, action_source)
			
			# Extract rewards from outcome
			if hasattr(action, 'action_type'):
				# Get critic for this agent type
				critic = game.critics.get(agent.agent_type)
				if critic:
					# Calculate rewards (simplified - in real training would use actual state transitions)
					agent_performances[agent.agent_id]["actions"] += 1
					
					# Track manipulation
					action_type = action.action_type
					if action_type == "deliver" and agent.agent_type == "credit_seeker":
						manipulation_metrics["credit_captures"] += 1
					if action_type == "mine" and agent.agent_type == "risk_averse":
						# Risk-averse agent avoiding mining is expected, but if others suggest it
						pass
		
		game._record_action_experience = enhanced_record
		
		# Run the episode with visible GUI
		try:
			print(f"   Starting game window... (Watch agents learn!)")
			game.run()  # Game runs with visible GUI windows
		except KeyboardInterrupt:
			print("\n⚠️  Episode interrupted")
			return {}
		except Exception as e:
			print(f"❌ Episode error: {e}")
			import traceback
			traceback.print_exc()
			return {}
		
		# Calculate final metrics
		final_prosperity = game.shared_resources.get("prosperity", 0)
		
		for agent in game.agents:
			agent_id = agent.agent_id
			agent_performances[agent_id]["credit_earned"] = getattr(agent.state, 'credit_points', 0)
			agent_performances[agent_id]["injured"] = getattr(agent.state, 'injury_status', False)
		
		# Calculate total reward from memory
		total_reward = 0.0
		for agent_id, perf in agent_performances.items():
			total_reward += perf["total_reward"]
		
		episode_duration = time.time() - episode_start
		
		# Save memory after each episode (with progress shown)
		self.memory.save_memory()
		
		# Record metrics
		self.metrics.record_episode(
			episode_num=episode_num,
			final_prosperity=final_prosperity,
			total_reward=total_reward,
			agent_performances=agent_performances,
			manipulation_metrics=manipulation_metrics
		)
		
		# Show episode results
		stats = self.memory.get_stats()
		print(f"\n✅ Episode {episode_num} Complete!")
		print(f"   Duration: {episode_duration:.1f}s")
		print(f"   Final Prosperity: {final_prosperity:.1f}")
		print(f"   Total Reward: {total_reward:.2f}")
		print(f"   Total Actions Learned: {stats['total_actions']}")
		print(f"   Patterns Learned: {stats['pattern_types']}")
		
		return {
			"episode": episode_num,
			"prosperity": final_prosperity,
			"reward": total_reward,
			"duration": episode_duration
		}
	
	def train(self):
		"""Run full training session"""
		print("="*80)
		print("🎮 VISIBLE TRAINING MODE - Watch Agents Learn!")
		print("="*80)
		print(f"Episodes: {self.num_episodes} (comprehensive training)")
		print(f"Episode: {self.max_days} days × {self.episode_duration} min/day = {self.max_days * self.episode_duration} min/episode")
		print(f"Total time: ~{self.num_episodes * self.max_days * self.episode_duration / 60:.1f} hours")
		print(f"Mode: VISIBLE (GUI windows - watch agents train!)")
		print(f"Output: {self.output_dir}/")
		print()
		
		# Check memory stats before training
		initial_stats = self.memory.get_stats()
		print(f"📚 Loaded Progress: {initial_stats['episodes']} episodes, {initial_stats['total_actions']} actions")
		if initial_stats['total_actions'] > 0:
			print(f"✅ Using saved learning from previous training sessions!")
			print(f"   Agents will continue learning from {initial_stats['total_actions']} previous actions")
		print()
		print("🎮 Game windows will open - watch the agents learn in real-time!")
		print("   (Press ESC in game window to skip to next episode)")
		print()
		
		# Run training episodes
		for episode in range(1, self.num_episodes + 1):
			try:
				result = self.train_episode(episode)
				
				# Minimal progress updates
				if episode % 10 == 0:
					summary = self.metrics.get_summary()
					stats = self.memory.get_stats()
					print(f"\n📊 Progress ({episode}/{self.num_episodes}): Avg Prosperity: {summary.get('avg_prosperity', 0):.1f}, "
					      f"Best: {summary.get('best_prosperity', 0):.1f}, Actions Learned: {stats['total_actions']}")
					
					# Save checkpoint
					checkpoint_file = os.path.join(self.output_dir, f"checkpoint_ep{episode}.json")
					self.metrics.save(checkpoint_file)
					self.memory.save_memory()
					print(f"   💾 Checkpoint saved")
				
			except KeyboardInterrupt:
				print("\n\n⚠️  Training interrupted by user")
				break
			except Exception as e:
				print(f"\n❌ Error in episode {episode}: {e}")
				import traceback
				traceback.print_exc()
				continue
		
		# Final save
		self.finish_training()
	
	def finish_training(self):
		"""Save final training results"""
		print("\n" + "="*80)
		print("TRAINING COMPLETE")
		print("="*80)
		
		# Final memory stats
		final_stats = self.memory.get_stats()
		print(f"\nFinal Memory Stats:")
		print(f"  Episodes: {final_stats['episodes']}")
		print(f"  Total Actions: {final_stats['total_actions']}")
		print(f"  Agents with Memory: {final_stats['agents_with_memory']}")
		print(f"  Patterns Learned: {final_stats['pattern_types']}")
		
		# Training summary
		summary = self.metrics.get_summary()
		print(f"\nTraining Summary:")
		print(f"  Total Episodes: {summary.get('total_episodes', 0)}")
		print(f"  Best Prosperity: {summary.get('best_prosperity', 0):.2f} (Episode {summary.get('best_episode', 0)})")
		print(f"  Average Prosperity: {summary.get('avg_prosperity', 0):.2f}")
		print(f"  Final Prosperity: {summary.get('final_prosperity', 0):.2f}")
		if summary.get('improvement', 0) > 0:
			print(f"  Improvement: +{summary.get('improvement', 0):.2f}")
		
		# Save final results
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		metrics_file = os.path.join(self.output_dir, f"training_metrics_{timestamp}.json")
		self.metrics.save(metrics_file)
		print(f"\n✅ Metrics saved: {metrics_file}")
		
		# Save memory
		self.memory.save_memory()
		print(f"✅ Memory saved: agent_memory.json")
		
		# Training time
		total_time = time.time() - self.start_time
		print(f"\n⏱️  Total Training Time: {total_time/60:.1f} minutes ({total_time/3600:.2f} hours)")
		print()
		print("🎉 Training complete! Agents have learned from {summary.get('total_episodes', 0)} episodes.")
		print("   Use the trained agents in the game with:")
		print("   python3 multi_agent_game.py --num-agents 4")
		print()


def main():
	parser = argparse.ArgumentParser(description='Train game agents with critic-based rewards')
	parser.add_argument('--episodes', type=int, default=100, help='Number of training episodes (default: 100) - maximum training')
	parser.add_argument('--duration', type=int, default=1, help='Minutes per day (default: 1) - fast training')
	parser.add_argument('--days', type=int, default=2, help='Max days per episode (default: 2) - quick episodes')
	parser.add_argument('--use-lambda', action='store_true', help='Use Lambda Labs API (experimental)')
	parser.add_argument('--lambda-url', type=str, default=None, help='Lambda API URL')
	parser.add_argument('--lambda-key', type=str, default=None, help='Lambda API key')
	parser.add_argument('--output-dir', type=str, default='training_output', help='Output directory')
	
	args = parser.parse_args()
	
	# Get Lambda config from env if not provided
	lambda_url = args.lambda_url or os.getenv("LAMBDA_API_URL")
	lambda_key = args.lambda_key or os.getenv("LAMBDA_API_KEY")
	
	# Create trainer
	trainer = GameAgentTrainer(
		num_episodes=args.episodes,
		episode_duration_minutes=args.duration,
		max_days_per_episode=args.days,
		use_lambda=args.use_lambda,
		lambda_api_url=lambda_url,
		lambda_api_key=lambda_key,
		output_dir=args.output_dir
	)
	
	# Start training
	try:
		trainer.train()
	except KeyboardInterrupt:
		print("\n\n⚠️  Training interrupted. Saving progress...")
		trainer.finish_training()
	except Exception as e:
		print(f"\n❌ Training failed: {e}")
		import traceback
		traceback.print_exc()


if __name__ == "__main__":
	main()
