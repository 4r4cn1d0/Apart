"""
Agent Memory System - Persistent Memory Between Game Sessions

Saves and loads agent experiences so they remember what they learned.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class AgentMemory:
	"""Manages persistent memory for agents across game sessions"""
	
	def __init__(self, memory_file="agent_memory.json"):
		self.memory_file = memory_file
		self.memory = {
			"agent_experiences": {},  # agent_id -> list of experiences
			"successful_patterns": {},  # agent_type -> patterns
			"tool_strategies": {},  # tool -> successful usage patterns
			"location_knowledge": {},  # locations -> what works there
			"episode_count": 0,
			"total_actions": 0,
			"last_updated": None
		}
		self.load_memory()
	
	def load_memory(self):
		"""Load existing memory from file"""
		if os.path.exists(self.memory_file):
			try:
				with open(self.memory_file, 'r') as f:
					self.memory = json.load(f)
				print(f"✅ Loaded agent memory: {self.memory.get('episode_count', 0)} episodes, {self.memory.get('total_actions', 0)} actions")
			except Exception as e:
				print(f"⚠️  Could not load memory file: {e}")
				print("Starting with fresh memory")
		else:
			print("📝 Starting with fresh agent memory")
	
	def save_memory(self):
		"""Save memory to file"""
		self.memory["last_updated"] = datetime.now().isoformat()
		try:
			with open(self.memory_file, 'w') as f:
				json.dump(self.memory, f, indent=2)
			print(f"💾 Saved agent memory to {self.memory_file}")
		except Exception as e:
			print(f"❌ Error saving memory: {e}")
	
	def record_experience(self, agent_id: str, agent_type: str, action: str, outcome: Dict[str, Any]):
		"""Record an agent's experience"""
		if agent_id not in self.memory["agent_experiences"]:
			self.memory["agent_experiences"][agent_id] = []
		
		experience = {
			"agent_type": agent_type,
			"action": action,
			"outcome": outcome,
			"timestamp": datetime.now().isoformat()
		}
		
		self.memory["agent_experiences"][agent_id].append(experience)
		self.memory["total_actions"] += 1
		
		# Keep only last 100 experiences per agent
		if len(self.memory["agent_experiences"][agent_id]) > 100:
			self.memory["agent_experiences"][agent_id] = self.memory["agent_experiences"][agent_id][-100:]
		
		# Update successful patterns
		if outcome.get("success", False) or outcome.get("prosperity_gain", 0) > 0:
			if agent_type not in self.memory["successful_patterns"]:
				self.memory["successful_patterns"][agent_type] = []
			
			pattern = {
				"action": action,
				"outcome": outcome,
				"timestamp": experience["timestamp"]
			}
			self.memory["successful_patterns"][agent_type].append(pattern)
			
			# Keep only last 50 patterns per type
			if len(self.memory["successful_patterns"][agent_type]) > 50:
				self.memory["successful_patterns"][agent_type] = self.memory["successful_patterns"][agent_type][-50:]
	
	def record_tool_usage(self, tool: str, location: tuple, success: bool):
		"""Record tool usage patterns"""
		if tool not in self.memory["tool_strategies"]:
			self.memory["tool_strategies"][tool] = {"successful": [], "failed": []}
		
		loc_str = f"{location[0]},{location[1]}"
		if success:
			if loc_str not in self.memory["tool_strategies"][tool]["successful"]:
				self.memory["tool_strategies"][tool]["successful"].append(loc_str)
		else:
			if loc_str not in self.memory["tool_strategies"][tool]["failed"]:
				self.memory["tool_strategies"][tool]["failed"].append(loc_str)
	
	def get_learned_patterns(self, agent_type: str) -> List[Dict[str, Any]]:
		"""Get learned successful patterns for an agent type"""
		return self.memory["successful_patterns"].get(agent_type, [])
	
	def get_agent_experience(self, agent_id: str) -> List[Dict[str, Any]]:
		"""Get all experiences for a specific agent"""
		return self.memory["agent_experiences"].get(agent_id, [])
	
	def get_knowledge_summary(self, agent_type: str) -> str:
		"""Get a summary of learned knowledge for prompts"""
		patterns = self.get_learned_patterns(agent_type)
		if not patterns:
			return ""
		
		# Count action frequencies
		action_counts = {}
		for pattern in patterns[-20:]:  # Last 20 patterns
			action = pattern.get("action", "")
			action_counts[action] = action_counts.get(action, 0) + 1
		
		if not action_counts:
			return ""
		
		# Get top 5 actions
		top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5]
		
		summary = f"From previous sessions, this {agent_type} agent learned that these actions work well:\n"
		for action, count in top_actions:
			summary += f"- {action} (successful {count} times)\n"
		
		return summary
	
	def increment_episode(self):
		"""Increment episode counter"""
		self.memory["episode_count"] = self.memory.get("episode_count", 0) + 1
	
	def get_stats(self) -> Dict[str, Any]:
		"""Get memory statistics"""
		return {
			"episodes": self.memory.get("episode_count", 0),
			"total_actions": self.memory.get("total_actions", 0),
			"agents_with_memory": len(self.memory.get("agent_experiences", {})),
			"pattern_types": len(self.memory.get("successful_patterns", {})),
			"last_updated": self.memory.get("last_updated", "Never")
		}


# Global memory instance
_global_memory: Optional[AgentMemory] = None

def get_agent_memory(memory_file="agent_memory.json") -> AgentMemory:
	"""Get or create global agent memory instance"""
	global _global_memory
	if _global_memory is None:
		_global_memory = AgentMemory(memory_file)
	return _global_memory
