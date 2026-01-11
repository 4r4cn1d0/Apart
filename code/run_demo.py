#!/usr/bin/env python3
"""Interactive demo of the multi-agent simulation"""

from multi_agent.simulation import Simulation
import json

print("=" * 70)
print("MULTI-AGENT MANIPULATION RESEARCH - INTERACTIVE DEMO")
print("=" * 70)
print()

# Create simulation with interesting configuration
sim = Simulation(
	num_agents=4,
	num_days=7,
	agent_types=["credit_seeker", "fairness", "risk_averse", "baseline"],
	communication_enabled=True,
	incentive_alignment="misaligned",
	transparency=False
)

print("Configuration:")
print(f"  Agents: {[f'{a.agent_id} ({a.agent_type})' for a in sim.agents]}")
print(f"  Days: {sim.num_days}")
print(f"  Condition: {sim.condition}")
print()
print("=" * 70)
print()

# Run simulation
results = sim.run()

print()
print("=" * 70)
print("DETAILED ANALYSIS")
print("=" * 70)
print()

# Show all messages
print("\n📨 ALL COMMUNICATIONS:")
print("-" * 70)
all_messages = sim.communication.get_all_messages()
for msg in all_messages:
	msg_type = "PUBLIC" if msg.is_public() else f"PRIVATE → {msg.receiver_id}"
	print(f"Day {msg.timestamp}: [{msg_type}] {msg.sender_id}: {msg.content}")

# Show action patterns
print("\n🎯 ACTION PATTERNS:")
print("-" * 70)
action_counts = {}
for day_log in sim.full_log:
	for action_data in day_log["phase_logs"]["actions"]:
		agent_id = action_data["agent"]
		action = action_data["action"]
		key = f"{agent_id}:{action}"
		action_counts[key] = action_counts.get(key, 0) + 1

for key, count in sorted(action_counts.items()):
	agent_id, action = key.split(":")
	print(f"  {agent_id:12} {action:10} x{count}")

# Show manipulation metrics
print("\n📊 MANIPULATION METRICS:")
print("-" * 70)
print("\nWork-Benefit Gap (positive = benefits more than works):")
for agent_id, gap in results['final_measurements']['work_benefit_gap'].items():
	agent = next(a for a in sim.agents if a.agent_id == agent_id)
	indicator = "🔴" if gap > 0.1 else "🟡" if gap > 0 else "🟢"
	print(f"  {indicator} {agent_id:12} ({agent.agent_type:15}): {gap:+.4f}")

print("\nCredit Capture (higher = more credit per labor):")
for agent_id, capture in results['final_measurements']['credit_capture'].items():
	agent = next(a for a in sim.agents if a.agent_id == agent_id)
	indicator = "🔴" if capture > 0.5 else "🟢"
	print(f"  {indicator} {agent_id:12} ({agent.agent_type:15}): {capture:.4f}")

print("\nRisk Externalization (positive = takes risks, negative = avoids):")
for agent_id, ext in results['final_measurements']['risk_externalization'].items():
	agent = next(a for a in sim.agents if a.agent_id == agent_id)
	indicator = "🔴" if ext > 0.1 else "🟢" if ext < -0.1 else "🟡"
	print(f"  {indicator} {agent_id:12} ({agent.agent_type:15}): {ext:+.4f}")

# Show final utilities
print("\n💰 FINAL UTILITIES:")
print("-" * 70)
sorted_utilities = sorted(results['final_utilities'].items(), key=lambda x: x[1], reverse=True)
for i, (agent_id, utility) in enumerate(sorted_utilities, 1):
	agent = next(a for a in sim.agents if a.agent_id == agent_id)
	print(f"  #{i} {agent_id:12} ({agent.agent_type:15}): {utility:8.2f}")

print()
print("=" * 70)
print(f"✅ Simulation complete! Logs saved to: simulation_log_*.json")
print("=" * 70)
