#!/usr/bin/env python3
"""Quick test of the simulation system"""

from multi_agent.simulation import Simulation

print("Testing Multi-Agent Simulation System...")
print()

# Run a quick 3-day test
sim = Simulation(
	num_agents=4,
	num_days=3,
	agent_types=["credit_seeker", "fairness", "risk_averse", "baseline"],
	communication_enabled=True,
	incentive_alignment="misaligned"
)

print("Running test simulation...")
print()

results = sim.run()

print("\n=== Test Results ===")
print(f"Final Prosperity: {results['final_prosperity']:.2f}")
print(f"Total Deliveries: {results['total_deliveries']}")

print("\nWork-Benefit Gaps:")
for agent_id, gap in results['final_measurements']['work_benefit_gap'].items():
	print(f"  {agent_id}: {gap:.4f}")

print("\n✅ Simulation test complete!")
