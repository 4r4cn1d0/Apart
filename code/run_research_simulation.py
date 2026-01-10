#!/usr/bin/env python3
"""
Run Multi-Agent Manipulation Research Simulation

This is the main entry point for running experiments.
"""

import argparse
import os
from multi_agent.simulation import Simulation
from ai_agent import AIAgent  # Reuse existing AI agent for LLM integration


def main():
	parser = argparse.ArgumentParser(description='Multi-Agent Manipulation Research Platform')
	
	# Simulation parameters
	parser.add_argument('--num-agents', type=int, default=4, choices=[3, 4],
	                   help='Number of agents (default: 4)')
	parser.add_argument('--num-days', type=int, default=10,
	                   help='Number of days to simulate (default: 10)')
	parser.add_argument('--agent-types', nargs='+',
	                   choices=['credit_seeker', 'fairness', 'risk_averse', 'baseline'],
	                   help='Agent types (default: mix)')
	
	# Experimental conditions
	parser.add_argument('--incentive-alignment', choices=['aligned', 'misaligned'],
	                   default='misaligned', help='Incentive alignment condition')
	parser.add_argument('--communication', action='store_true', default=True,
	                   help='Enable communication (default: True)')
	parser.add_argument('--no-communication', dest='communication', action='store_false',
	                   help='Disable communication')
	parser.add_argument('--transparency', action='store_true',
	                   help='Enable full transparency/auditing')
	
	# LLM configuration
	parser.add_argument('--use-llm', action='store_true',
	                   help='Use LLM for agent decision-making')
	parser.add_argument('--api', choices=['openai', 'anthropic', 'lambda'],
	                   default='openai', help='LLM API provider')
	parser.add_argument('--api-key', type=str, default=None,
	                   help='API key (or use environment variable)')
	
	# Output
	parser.add_argument('--output', type=str, default=None,
	                   help='Output file for logs (default: auto-generated)')
	parser.add_argument('--export', action='store_true', default=True,
	                   help='Export logs to file')
	
	args = parser.parse_args()
	
	# Setup LLM clients if requested
	llm_clients = None
	if args.use_llm:
		print("Initializing LLM clients...")
		api_key = args.api_key or os.getenv(f"{args.api.upper()}_API_KEY")
		if not api_key:
			print(f"Warning: No API key found. Agents will use heuristic behavior.")
			llm_clients = None
		else:
			# Create LLM client for each agent
			llm_clients = []
			for i in range(args.num_agents):
				try:
					client = AIAgent(api_provider=args.api, api_key=api_key)
					llm_clients.append(client)
				except Exception as e:
					print(f"Warning: Failed to create LLM client {i}: {e}")
					llm_clients.append(None)
	
	# Create simulation
	sim = Simulation(
		num_agents=args.num_agents,
		num_days=args.num_days,
		agent_types=args.agent_types,
		communication_enabled=args.communication,
		incentive_alignment=args.incentive_alignment,
		transparency=args.transparency,
		llm_clients=llm_clients
	)
	
	# Run simulation
	results = sim.run()
	
	# Export logs
	if args.export:
		filename = sim.export_logs(args.output)
		print(f"\nResults exported to: {filename}")
	
	# Print summary
	print("\n=== Final Results ===")
	print(f"Condition: {results['condition']}")
	print(f"Final Prosperity: {results['final_prosperity']:.2f}")
	print("\nFinal Utilities:")
	for agent_id, utility in results['final_utilities'].items():
		print(f"  {agent_id}: {utility:.2f}")
	
	print("\nWork-Benefit Gaps:")
	for agent_id, gap in results['final_measurements']['work_benefit_gap'].items():
		print(f"  {agent_id}: {gap:.4f}")
	
	print("\nCredit Capture:")
	for agent_id, capture in results['final_measurements']['credit_capture'].items():
		print(f"  {agent_id}: {capture:.4f}")
	
	print("\nRisk Externalization:")
	for agent_id, externalization in results['final_measurements']['risk_externalization'].items():
		print(f"  {agent_id}: {externalization:.4f}")


if __name__ == '__main__':
	main()
