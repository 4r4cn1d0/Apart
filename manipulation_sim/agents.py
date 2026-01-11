"""
Agent policies: goal-driven agents that communicate naturally.

Agents have misaligned goals but try to achieve them through natural communication.
Manipulation emerges if beneficial, not hardcoded.
"""

import random
from typing import Dict, Optional, List
from .env import ACTIONS, WorldState
from . import config


class BaseAgent:
    """
    Base agent class - agents pursue their goals through natural communication.
    
    Goals are encoded via role preferences, but communication and influence
    attempts emerge naturally from goal pursuit, not from manipulation scripts.
    """
    
    def __init__(self, name: str, role: str = "credit"):
        """
        Initialize agent.
        
        Args:
            name: Agent identifier (e.g., "A", "B", "C")
            role: Agent role ("credit", "fairness", "risk_averse")
                 - This defines the agent's goal, not manipulation tactics
        """
        self.name = name
        self.role = role
        self.history: List[tuple] = []
        self.conversation_turn = 0
        self.rng = random.Random()
    
    def set_seed(self, seed: int):
        """Set random seed for deterministic behavior."""
        self.rng = random.Random(seed)
    
    def observe(self, world: WorldState, private_info: Optional[Dict] = None):
        """
        Observe current world state and private information.
        
        Args:
            world: Current world state
            private_info: Optional dict with private information
        """
        self.history.append((world, private_info or {}))
    
    def talk(self, world: WorldState, conversation_history: Optional[List[Dict[str, str]]] = None, turn: int = 0, episode_history: Optional[List[Dict]] = None) -> str:
        """
        Generate a natural language message based on goals and situation.
        
        This method must be implemented by subclasses (LLM agents).
        BaseAgent does not provide hardcoded responses - all agents must use LLMs.
        
        Args:
            world: Current world state
            conversation_history: List of previous message exchanges in this day
            turn: Conversation turn (0 = first message, 1+ = responses, up to 50)
            episode_history: List of past days' summaries for cross-day memory
            
        Returns:
            Message string, or "" if agent doesn't want to speak this turn
        """
        raise NotImplementedError(
            "BaseAgent.talk() is abstract. Use LambdaLabsAgent instead. "
            "Hardcoded responses have been removed - all agents must use Lambda Labs API."
        )
    
    def act(self, world: WorldState, messages: Dict[str, str] = None, episode_history: Optional[List[Dict]] = None) -> str:
        """
        Choose an action based on current state and messages.
        
        This method provides a RANDOM fallback for LLM agents if they fail to generate actions.
        We intentionally DON'T use role-based heuristics here - that would defeat the purpose
        of testing LLM agent behavior.
        
        Args:
            world: Current world state
            messages: Dict mapping agent names to their messages
            episode_history: Optional list of past day summaries (unused in base class)
            
        Returns:
            Action string (one of ACTIONS)
        """
        if messages is None:
            messages = {}
        
        if world.agents[self.name].injured:
            return "rest"
        
        return self.rng.choice(ACTIONS)
    
    def reset(self):
        """Reset agent state for a new episode."""
        self.history = []
        self.conversation_turn = 0
        self.rng = random.Random()