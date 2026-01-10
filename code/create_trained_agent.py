#!/usr/bin/env python3
"""
Create agents with pre-loaded game knowledge

This ensures agents "know" the game from the start, not learning from scratch.
"""

from multi_agent.game_knowledge import get_agent_system_prompt, GAME_MANUAL
from multi_agent.game_aware_agent import GameAwareAgent
from ai_agent import AIAgent
import os
import json


def create_trained_agent(agent_id: str, agent_type: str, llm_client=None):
	"""
	Create an agent that already knows how to play the game.
	
	The agent receives the full game manual as part of its system prompt,
	so it doesn't need to learn from scratch.
	"""
	if llm_client:
		agent = GameAwareAgent(
			agent_id=agent_id,
			agent_type=agent_type,
			llm_client=llm_client,
			game_screen=None
		)
	else:
		# For non-LLM agents, they still have the knowledge in their behavior
		from multi_agent.agent_types import (
			CreditSeekerAgent, FairnessAgent, 
			RiskAverseAgent, BaselineAgent
		)
		
		if agent_type == "credit_seeker":
			agent = CreditSeekerAgent(agent_id, llm_client=None)
		elif agent_type == "fairness":
			agent = FairnessAgent(agent_id, llm_client=None)
		elif agent_type == "risk_averse":
			agent = RiskAverseAgent(agent_id, llm_client=None)
		else:
			agent = BaselineAgent(agent_id, llm_client=None)
	
	# Store game knowledge with agent
	agent.game_manual = GAME_MANUAL
	agent.agent_strategy = get_agent_system_prompt(agent_type)
	
	print(f"Created {agent_type} agent with full game knowledge")
	return agent


def create_all_trained_agents(use_llm=False, api_provider="openai", api_key=None):
	"""Create all agents with pre-loaded game knowledge"""
	agent_types = ["credit_seeker", "fairness", "risk_averse", "baseline"]
	agents = []
	llm_clients = []
	
	if use_llm:
		api_key = api_key or os.getenv(f"{api_provider.upper()}_API_KEY")
		if api_key:
			for i in range(len(agent_types)):
				try:
					client = AIAgent(api_provider=api_provider, api_key=api_key)
					llm_clients.append(client)
				except:
					llm_clients.append(None)
		else:
			llm_clients = [None] * len(agent_types)
	else:
		llm_clients = [None] * len(agent_types)
	
	for i, agent_type in enumerate(agent_types):
		agent_id = f"agent_{i+1}"
		llm_client = llm_clients[i] if i < len(llm_clients) else None
		agent = create_trained_agent(agent_id, agent_type, llm_client)
		agents.append(agent)
	
	return agents


if __name__ == '__main__':
	# Test creating trained agents
	print("Creating agents with pre-loaded game knowledge...")
	agents = create_all_trained_agents(use_llm=False)
	print(f"\n✅ Created {len(agents)} agents")
	print("All agents know how to play the game from the start!")
	
	# Show knowledge
	print("\nSample knowledge (first 500 chars):")
	print(agents[0].game_manual[:500] + "...")
