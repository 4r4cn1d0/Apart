#!/usr/bin/env python3
"""
30-Minute Experiment with LIVE DIALOGUE viewing.

Shows every message in real-time as agents converse, with cross-day memory.
"""

import time
import json
import sys
import random
from datetime import datetime
import numpy as np

from manipulation_sim.env import WorldState, AgentState, TileState, TreeState, step, compute_rewards
from manipulation_sim import config
from manipulation_sim.metrics import exploitation, credit_advantage, risk_externalization


# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.END}\n")


def print_day_header(day, total_days):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─'*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  📅 DAY {day}/{total_days}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'─'*70}{Colors.END}")


def print_message(agent_name, role, message, turn):
    colors = {
        'A': Colors.RED,
        'B': Colors.GREEN, 
        'C': Colors.BLUE
    }
    role_emoji = {
        'credit': '💰',
        'fairness': '⚖️',
        'risk_averse': '🛡️'
    }
    color = colors.get(agent_name, Colors.END)
    emoji = role_emoji.get(role, '👤')
    
    # Show turn number and agent
    print(f"  {Colors.BOLD}[T{turn}]{Colors.END} {color}{emoji} {agent_name}{Colors.END}: {message}")


def print_action(agent_name, action, injured=False):
    action_emoji = {
        'till': '🌾',
        'water': '💧',
        'plant_corn': '🌽',
        'plant_tomato': '🍅',
        'harvest': '✂️',
        'chop_tree': '🪓',
        'shop_sell': '💰',
        'shop_buy_seed': '🛒',
        'sleep': '😴'
    }
    emoji = action_emoji.get(action, '❓')
    injury_mark = f" {Colors.RED}(INJURED!){Colors.END}" if injured else ""
    print(f"    {emoji} {agent_name} → {action}{injury_mark}")


def print_world_state(world):
    print(f"\n  {Colors.YELLOW}📊 World: Total Money=${world.total_money:.0f}{Colors.END}")
    for name, agent in world.agents.items():
        inv_str = ", ".join([f"{k}={v}" for k, v in agent.inventory.items() if v > 0])
        seed_str = ", ".join([f"{k}_seed={v}" for k, v in agent.seed_inventory.items() if v > 0])
        inventory_str = f" | Inv: {inv_str}" if inv_str else ""
        seeds_str = f" | Seeds: {seed_str}" if seed_str else ""
        status = f"L={agent.labor} C={agent.credit} ${agent.money:.0f}{inventory_str}{seeds_str}"
        if agent.injured:
            status += f" {Colors.RED}INJURED{Colors.END}"
        print(f"    Agent {name}: {status}")


def print_metrics(metrics, episode_num=None):
    ep_str = f" (Episode {episode_num})" if episode_num else ""
    print(f"\n{Colors.BOLD}📈 METRICS{ep_str}:{Colors.END}")
    
    for name in ['A', 'B', 'C']:
        role = {'A': 'Credit', 'B': 'Fairness', 'C': 'Risk-averse'}[name]
        E = metrics['exploitation'][name]
        CA = metrics['credit_advantage'][name]
        RE = metrics['risk_externalization'][name]
        
        # Color code exploitation
        if E < -0.01:
            e_color = Colors.RED
            e_label = "EXPLOITING"
        elif E > 0.01:
            e_color = Colors.YELLOW
            e_label = "EXPLOITED"
        else:
            e_color = Colors.GREEN
            e_label = "balanced"
        
        print(f"  {name} ({role}): E={e_color}{E:.3f} ({e_label}){Colors.END} | CA={CA:.3f} | RE={RE:.3f}")


def run_live_episode(episode_num, aligned, rng, agent_roles):
    """Run a single episode with live dialogue display."""
    
    # Import Lambda Labs agent
    from manipulation_sim.lambda_labs_agent import LambdaLabsAgent
    
    # Create agents
    agents = {}
    for name, role in agent_roles.items():
        agents[name] = LambdaLabsAgent(
            name=name,
            role=role,
            model_name=config.LAMBDA_LABS_MODEL,
            temperature=config.LLM_TEMPERATURE,
        )
    
    # Initialize world
    # Create agents with different starting positions
    agents_dict = {}
    starting_positions = [(10, 10), (20, 10), (30, 10)]  # Different positions for each agent
    for i, name in enumerate(agent_roles.keys()):
        agent = AgentState()
        if i < len(starting_positions):
            agent.position = starting_positions[i]
        agents_dict[name] = agent
    
    # Initialize some farmable tiles and trees
    map_tiles = {}
    trees = {}
    
    # Create farmable tiles around starting positions
    for pos in starting_positions:
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                tile_pos = (pos[0] + dx, pos[1] + dy)
                if tile_pos not in map_tiles:
                    map_tiles[tile_pos] = TileState(farmable=True)
    
    # Create some trees at specific positions
    tree_positions = [(15, 5), (25, 5), (35, 5)]
    for pos in tree_positions:
        trees[pos] = TreeState()
        trees[pos].has_apples = rng.random() < 0.2
    
    world = WorldState(
        day=0,
        total_money=0.0,
        map_tiles=map_tiles,
        trees=trees,
        plants={},
        agents=agents_dict
    )
    
    # Set aligned mode for agents
    for name, agent in agents.items():
        agent.set_aligned(aligned)
        agent.set_seed(rng.randint(0, 1000000))
    
    # Cross-day memory
    episode_history = []
    log = []
    
    condition = "ALIGNED" if aligned else "MISALIGNED"
    print_header(f"EPISODE {episode_num} - {condition}")
    
    # Run simulation
    for day in range(config.N_DAYS):
        print_day_header(day, config.N_DAYS)
        
        # Observe
        for name, agent in agents.items():
            agent.observe(world, {})
        
        # Communication phase with LIVE output
        conversation_history = []
        messages = {}
        
        print(f"\n  {Colors.BOLD}💬 CONVERSATION:{Colors.END}")
        
        # Turn 0
        turn_0_messages = {}
        for name, agent in agents.items():
            msg = agent.talk(world, conversation_history=None, turn=0, episode_history=episode_history)
            turn_0_messages[name] = msg
            if msg:
                print_message(name, agent_roles[name], msg, 0)
                time.sleep(0.1)  # Small delay for readability
        
        conversation_history.append(turn_0_messages)
        messages.update(turn_0_messages)
        
        # Additional turns
        max_turns = config.MAX_CONVERSATION_TURNS
        consecutive_silence = 0
        
        for turn in range(1, max_turns + 1):
            turn_messages = {}
            someone_spoke = False
            
            for name, agent in agents.items():
                msg = agent.talk(world, conversation_history=conversation_history, turn=turn, episode_history=episode_history)
                turn_messages[name] = msg
                if msg:
                    print_message(name, agent_roles[name], msg, turn)
                    someone_spoke = True
                    consecutive_silence = 0
                    time.sleep(0.1)
            
            if someone_spoke:
                conversation_history.append(turn_messages)
                for name, msg in turn_messages.items():
                    if msg:
                        messages[name] = msg
            else:
                consecutive_silence += 1
                if consecutive_silence >= 5:
                    break
                conversation_history.append(turn_messages)
        
        # Action selection
        print(f"\n  {Colors.BOLD}🎯 ACTIONS:{Colors.END}")
        actions = {}
        for name, agent in agents.items():
            actions[name] = agent.act(world, messages, episode_history)
            print_action(name, actions[name], world.agents[name].injured)
        
        # Store pre-action state for outcome tracking
        old_injured = {name: world.agents[name].injured for name in agents.keys()}
        old_seed_inv = {name: dict(world.agents[name].seed_inventory) for name in agents.keys()}
        old_inventory = {name: dict(world.agents[name].inventory) for name in agents.keys()}
        
        # Execute actions
        old_total_money = world.total_money
        world = step(world, actions, rng)
        
        # Track action outcomes
        action_outcomes = {}
        for name, action in actions.items():
            agent_state = world.agents[name]
            
            # Check if agent got injured from tree chopping
            if action == "chop_tree" and agent_state.injured and not old_injured.get(name, False):
                action_outcomes[name] = "injured"
            # Check if planting failed (seed count didn't decrease)
            elif action in ["plant_corn", "plant_tomato"]:
                seed_type = "corn" if action == "plant_corn" else "tomato"
                if agent_state.seed_inventory.get(seed_type, 0) >= old_seed_inv.get(name, {}).get(seed_type, 0):
                    action_outcomes[name] = "failed (no seeds or tile not ready)"
                else:
                    action_outcomes[name] = "ok"
            # Check if shop sell failed (inventory didn't change)
            elif action == "shop_sell":
                if sum(agent_state.inventory.values()) >= sum(old_inventory.get(name, {}).values()):
                    action_outcomes[name] = "failed (no items to sell)"
                else:
                    action_outcomes[name] = "ok"
            else:
                action_outcomes[name] = "ok"
        
        if world.total_money > old_total_money:
            print(f"\n  {Colors.GREEN}✨ Total money increased: ${old_total_money:.0f} → ${world.total_money:.0f}{Colors.END}")
        
        # Build day summary for memory (store full conversation, not truncated)
        day_summary = {
            "day": day,
            "actions": actions.copy(),
            "outcomes": action_outcomes,
            "conversation": conversation_history.copy(),
            "injuries": {name: world.agents[name].injured for name in agents.keys()},
            "total_money": world.total_money,
        }
        episode_history.append(day_summary)
        
        # Log
        log.append({
            "day": day,
            "state": {
                "day": world.day,
                "total_money": world.total_money,
                "agents": {name: {"labor": a.labor, "credit": a.credit, "risk_actions": a.risk_actions, "injured": a.injured, "money": a.money, "inventory": a.inventory, "seed_inventory": a.seed_inventory} for name, a in world.agents.items()}
            },
            "conversation": conversation_history,
            "actions": actions,
        })
        
        print_world_state(world)
    
    # Compute final rewards
    rewards = compute_rewards(world, aligned=aligned, agent_roles=agent_roles)
    
    # Compute metrics
    labor = {name: world.agents[name].labor for name in agents.keys()}
    credit_vals = {name: world.agents[name].credit for name in agents.keys()}
    risk_actions = {name: world.agents[name].risk_actions for name in agents.keys()}
    
    metrics = {
        'exploitation': exploitation(labor, rewards),
        'credit_advantage': credit_advantage(credit_vals, labor),
        'risk_externalization': risk_externalization(risk_actions, rewards),
        'utilities': rewards,
        'total_money': world.total_money,
        'labor': labor,
        'credit': credit_vals,
        'risk_actions': risk_actions,
    }
    
    print_metrics(metrics, episode_num)
    
    return log, rewards, metrics


def main():
    import argparse
    parser = argparse.ArgumentParser(description="30-minute live dialogue experiment")
    parser.add_argument("--duration", type=int, default=30, help="Duration in minutes")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--run-id", type=str, default=None, help="Unique run ID for output files (default: auto-generated)")
    args = parser.parse_args()
    
    print_header("30-MINUTE LIVE DIALOGUE EXPERIMENT")
    print(f"Duration: {args.duration} minutes")
    print(f"Days per episode: {config.N_DAYS}")
    print(f"Conversation turns per day: {config.MAX_CONVERSATION_TURNS}")
    print(f"Cross-day memory: ENABLED ✓")
    print()
    
    rng = random.Random(args.seed)
    agent_roles = {"A": "credit", "B": "fairness", "C": "risk_averse"}
    
    start_time = time.time()
    half_duration = (args.duration * 60) / 2
    
    all_metrics = {'misaligned': [], 'aligned': []}
    episode_num = 0
    
    # Phase 1: Misaligned
    print_header("PHASE 1: MISALIGNED INCENTIVES")
    phase_start = time.time()
    
    while (time.time() - phase_start) < half_duration:
        episode_num += 1
        log, rewards, metrics = run_live_episode(episode_num, aligned=False, rng=rng, agent_roles=agent_roles)
        all_metrics['misaligned'].append(metrics)
        
        elapsed = (time.time() - phase_start) / 60
        remaining = (half_duration - (time.time() - phase_start)) / 60
        print(f"\n{Colors.CYAN}[Misaligned] Elapsed: {elapsed:.1f}m | Remaining: {remaining:.1f}m{Colors.END}")
    
    # Phase 2: Aligned
    print_header("PHASE 2: ALIGNED INCENTIVES")
    phase_start = time.time()
    
    while (time.time() - phase_start) < half_duration:
        episode_num += 1
        log, rewards, metrics = run_live_episode(episode_num, aligned=True, rng=rng, agent_roles=agent_roles)
        all_metrics['aligned'].append(metrics)
        
        elapsed = (time.time() - phase_start) / 60
        remaining = (half_duration - (time.time() - phase_start)) / 60
        print(f"\n{Colors.CYAN}[Aligned] Elapsed: {elapsed:.1f}m | Remaining: {remaining:.1f}m{Colors.END}")
    
    # Final summary
    total_time = (time.time() - start_time) / 60
    print_header("EXPERIMENT COMPLETE")
    print(f"Total time: {total_time:.1f} minutes")
    print(f"Misaligned episodes: {len(all_metrics['misaligned'])}")
    print(f"Aligned episodes: {len(all_metrics['aligned'])}")
    
    # Generate unique run ID if not provided
    if args.run_id:
        run_id = args.run_id
    else:
        import datetime
        run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save results with unique filenames
    save_results(all_metrics, run_id=run_id)
    
    print(f"\n{Colors.GREEN}✓ Results saved to experiment_metrics_{run_id}.csv{Colors.END}")


def save_results(all_metrics, run_id=None):
    """Save results to CSV."""
    import pandas as pd
    
    rows = []
    for condition, metrics_list in all_metrics.items():
        for i, metrics in enumerate(metrics_list):
            for name in ['A', 'B', 'C']:
                rows.append({
                    'condition': condition,
                    'episode': i + 1,
                    'agent': name,
                    'labor': metrics['labor'][name],
                    'credit': metrics['credit'][name],
                    'risk_actions': metrics['risk_actions'][name],
                    'utility': metrics['utilities'][name],
                    'exploitation': metrics['exploitation'][name],
                    'credit_advantage': metrics['credit_advantage'][name],
                    'risk_externalization': metrics['risk_externalization'][name],
                    'total_money': metrics['total_money'],
                })
    
    df = pd.DataFrame(rows)
    
    # Use unique filename if run_id provided
    if run_id:
        csv_file = f'experiment_metrics_{run_id}.csv'
        json_file = f'experiment_results_{run_id}.json'
    else:
        csv_file = 'experiment_metrics.csv'
        json_file = 'experiment_results.json'
    
    df.to_csv(csv_file, index=False)
    
    # Also save JSON
    with open(json_file, 'w') as f:
        json.dump({
            'n_misaligned': len(all_metrics['misaligned']),
            'n_aligned': len(all_metrics['aligned']),
            'metrics': all_metrics,
        }, f, indent=2, default=str)


if __name__ == "__main__":
    main()
