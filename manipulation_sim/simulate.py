"""
Simulation runner: runs full episodes and writes logs in a game-agnostic format.

The game later just reads these JSONs and replays them visually.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .env import WorldState, AgentState, step, compute_rewards
from .agents import BaseAgent
from . import config


def run_episode(
    run_id: str,
    aligned: bool,
    n_days: int,
    n_agents: int = None,
    agent_roles: Optional[Dict[str, str]] = None,
    rng_seed: int = 0,
    allow_communication: bool = True,
) -> Tuple[List[Dict], Dict[str, float]]:
    """
    Run a single episode of the simulation.
    
    Args:
        run_id: Unique identifier for this run
        aligned: If True, all agents maximize shared prosperity
        n_days: Number of days to simulate
        n_agents: Number of agents (defaults to config.N_AGENTS)
        agent_roles: Optional dict mapping agent names to roles.
                     If None, uses default roles.
        rng_seed: Random seed for reproducibility
        allow_communication: If False, agents don't communicate
    
    Returns:
        Tuple of (log, final_rewards)
        - log: List of day-by-day state/action records
        - final_rewards: Dict mapping agent names to final utilities
    """
    rng = random.Random(rng_seed)
    
    # Initialize agents
    if n_agents is None:
        n_agents = config.N_AGENTS
    
    # Default roles if not provided
    if agent_roles is None:
        if n_agents == 3:
            agent_roles = {"A": "credit", "B": "fairness", "C": "risk_averse"}
        elif n_agents == 4:
            agent_roles = {"A": "credit", "B": "credit", "C": "fairness", "D": "risk_averse"}
        else:
            # Default: all credit-seekers
            agent_roles = {chr(65 + i): "credit" for i in range(n_agents)}
    
    # Create Lambda Labs API agents
    from .lambda_labs_agent import LambdaLabsAgent
    agents = {}
    condition_str = "ALIGNED" if aligned else "MISALIGNED"
    for name, role in agent_roles.items():
        try:
            agent = LambdaLabsAgent(
                name=name,
                role=role,
                model_name=config.LAMBDA_LABS_MODEL,
                temperature=config.LLM_TEMPERATURE,
            )
            agent.set_seed(rng_seed + hash(name) % 10000)  # Seed agent RNG for reproducibility
            agent.set_aligned(aligned)  # Set incentive alignment mode
            print(f"[Lambda Labs] Created {name} ({role}) agent [{condition_str}]")
            agents[name] = agent
        except (ImportError, ValueError, Exception) as e:
            print(f"[ERROR] Lambda Labs agent failed for {name}: {e}")
            raise RuntimeError(
                f"Failed to create Lambda Labs agent for {name}. "
                "Check your Lambda Labs API key and configuration."
            )
    
    # Initialize world state
    # Create agents with different starting positions
    agents_dict = {}
    starting_positions = [(10, 10), (20, 10), (30, 10)]  # Different positions for each agent
    for i, name in enumerate(agent_roles.keys()):
        agent = AgentState()
        if i < len(starting_positions):
            agent.position = starting_positions[i]
        agents_dict[name] = agent
    
    # Initialize some farmable tiles and trees
    from .env import TileState, TreeState
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
    
    # Episodes log
    log = []
    
    # Cross-day memory: track what happened each day for agent memory
    episode_history = []  # List of day summaries for agent prompts
    
    # Run simulation for n_days
    for t in range(n_days):
        # Phase 1: Observation
        # Agents observe current state (with optional private info)
        private_infos = {}
        # Example: private risk information (if we want to add this)
        for name in agents.keys():
            private_infos[name] = {
                "risk_probability": config.INJURY_PROB,
                # Could add more private information here
            }
        
        for name, agent in agents.items():
            agent.observe(world, private_infos.get(name, {}))
        
        # Phase 2: Communication (if enabled)
        # Multi-turn conversation: agents discuss, respond to each other
        conversation_history = []  # List of message exchanges per turn
        messages = {}
        
        if allow_communication:
            # Turn 0: Initial messages from all agents
            turn_0_messages = {}
            for name, agent in agents.items():
                msg = agent.talk(world, conversation_history=None, turn=0, episode_history=episode_history)
                turn_0_messages[name] = msg
            conversation_history.append(turn_0_messages)
            messages.update(turn_0_messages)
            
            # Additional conversation turns (up to 50 turns for continuous dialogue)
            max_turns = config.MAX_CONVERSATION_TURNS  # Configurable: 50 turns per day
            consecutive_silence = 0
            max_silence = 5  # Stop if no one speaks for 5 consecutive turns (LLMs might be more silent)
            
            for turn in range(1, max_turns + 1):
                turn_messages = {}
                someone_spoke = False
                
                for name, agent in agents.items():
                    # Each agent can respond to the conversation (LLM or scripted)
                    msg = agent.talk(world, conversation_history=conversation_history, turn=turn, episode_history=episode_history)
                    turn_messages[name] = msg
                    if msg:
                        someone_spoke = True
                        consecutive_silence = 0  # Reset silence counter
                
                if someone_spoke:
                    conversation_history.append(turn_messages)
                    # Update messages dict with latest
                    for name, msg in turn_messages.items():
                        if msg:  # Only update if agent actually spoke
                            messages[name] = msg
                else:
                    # No one spoke this turn
                    consecutive_silence += 1
                    if consecutive_silence >= max_silence:
                        # Stop if no one speaks for several turns
                        break
                    
                    # Still add empty turn to history (shows silence)
                    conversation_history.append(turn_messages)
        else:
            # No communication
            for name in agents.keys():
                messages[name] = ""
        
        # Phase 3: Decision / Action selection
        actions = {}
        for name, agent in agents.items():
            actions[name] = agent.act(world, messages if allow_communication else {}, episode_history)
        
        # Store pre-action state for outcome tracking
        old_injured = {name: world.agents[name].injured for name in agents.keys()}
        old_seed_inv = {name: dict(world.agents[name].seed_inventory) for name in agents.keys()}
        old_inventory = {name: dict(world.agents[name].inventory) for name in agents.keys()}
        
        # Phase 4: Action execution
        world = step(world, actions, rng)
        
        # Track action outcomes for memory
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
        
        # Phase 5: Logging
        # Serialize world state for logging
        day_log = {
            "day": t,
            "state": serialize_world_state(world),
            "conversation": conversation_history if allow_communication else [],
            "messages": messages,  # Final messages (for backward compatibility)
            "actions": actions,
        }
        log.append(day_log)
        
        # Build day summary for cross-day memory
        # Store all conversation history for this day (full dialogue, not truncated)
        day_summary = {
            "day": t,
            "actions": actions.copy(),
            "outcomes": action_outcomes,
            "conversation": conversation_history.copy() if allow_communication else [],
            "injuries": {name: world.agents[name].injured for name in agents.keys()},
            "total_money": world.total_money,
        }
        episode_history.append(day_summary)
    
    # Phase 6: Compute final rewards
    final_rewards = compute_rewards(world, aligned=aligned, agent_roles=agent_roles)
    
    # Collect fallback counts from all agents
    fallback_counts = {}
    for name, agent in agents.items():
        if hasattr(agent, 'get_fallback_count'):
            fallback_counts[name] = agent.get_fallback_count()
        else:
            fallback_counts[name] = 0
    
    # Log fallback summary if any occurred
    total_fallbacks = sum(fallback_counts.values())
    if total_fallbacks > 0:
        fallback_str = ", ".join([f"{name}={count}" for name, count in fallback_counts.items()])
        print(f"[EPISODE] LLM fallbacks: {fallback_str}")
    
    return log, final_rewards


def save_run(
    run_id: str,
    log: List[Dict],
    rewards: Dict[str, float],
    metadata: Optional[Dict] = None,
    path: str = "logs"
) -> Path:
    """
    Save a simulation run to JSON file.
    
    Args:
        run_id: Unique identifier for this run
        log: List of day-by-day logs
        rewards: Final reward dict
        metadata: Optional metadata dict (aligned, n_days, etc.)
        path: Directory to save logs (default: "logs")
    
    Returns:
        Path to saved file
    """
    log_dir = Path(path)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare output
    output = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {},
        "log": log,
        "final_rewards": rewards,
    }
    
    # Save to JSON
    fname = log_dir / f"{run_id}.json"
    with open(fname, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    return fname


def load_run(run_id: str, path: str = "logs") -> Dict:
    """
    Load a simulation run from JSON file.
    
    Args:
        run_id: Run identifier
        path: Directory containing logs (default: "logs")
    
    Returns:
        Loaded run dict
    """
    log_dir = Path(path)
    fname = log_dir / f"{run_id}.json"
    
    with open(fname, "r") as f:
        return json.load(f)


def serialize_world_state(world: WorldState) -> Dict:
    """
    Serialize world state to dict for JSON logging.
    
    Args:
        world: WorldState instance
    
    Returns:
        Serializable dict
    """
    return {
        "day": world.day,
        "total_money": world.total_money,
        "agents": {
            name: {
                "labor": agent.labor,
                "credit": agent.credit,
                "risk_actions": agent.risk_actions,
                "injured": agent.injured,
                "injury_turns_remaining": agent.injury_turns_remaining,
                "position": agent.position,
                "money": agent.money,
                "inventory": agent.inventory,
                "seed_inventory": agent.seed_inventory,
            }
            for name, agent in world.agents.items()
        }
    }
