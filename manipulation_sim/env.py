"""
Environment: State, transitions, and reward calculation.

This module handles the game world mechanics - no ML here, just pure simulation logic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random
from . import config


@dataclass
class TileState:
    """
    State of a single tile in the map.
    
    Tracks whether the tile is farmable, tilled, watered, and planted.
    """
    farmable: bool = False
    tilled: bool = False
    watered: bool = False
    planted: bool = False
    plant_type: Optional[str] = None  # "corn" or "tomato"
    plant_age: float = 0.0
    plant_harvestable: bool = False
    
    def reset(self):
        """Reset tile state."""
        self.tilled = False
        self.watered = False
        self.planted = False
        self.plant_type = None
        self.plant_age = 0.0
        self.plant_harvestable = False


@dataclass
class TreeState:
    """
    State of a tree in the world.
    
    Tracks tree health, whether it has apples, and if it's alive.
    """
    health: int = config.TREE_HEALTH
    has_apples: bool = False
    alive: bool = True
    
    def reset(self):
        """Reset tree state."""
        self.health = config.TREE_HEALTH
        self.has_apples = False
        self.alive = True


@dataclass
class AgentState:
    """
    State of an individual agent.
    
    Tracks labor contributions, credit earned, risk actions taken, injury status,
    position, money, inventory, and seed inventory throughout an episode.
    """
    labor: int = 0
    credit: int = 0
    risk_actions: int = 0
    injured: bool = False
    injury_turns_remaining: int = 0
    
    position: Tuple[int, int] = (0, 0)
    money: float = config.INITIAL_MONEY
    inventory: Dict[str, int] = field(default_factory=lambda: {"wood": 0, "apple": 0, "corn": 0, "tomato": 0})
    seed_inventory: Dict[str, int] = field(default_factory=lambda: {"corn": 5, "tomato": 5})
    selected_tool: str = "hoe"
    selected_seed: str = "corn"
    
    def reset(self):
        """Reset agent state for a new episode."""
        self.labor = 0
        self.credit = 0
        self.risk_actions = 0
        self.injured = False
        self.injury_turns_remaining = 0
        self.position = (0, 0)
        self.money = config.INITIAL_MONEY
        self.inventory = {"wood": 0, "apple": 0, "corn": 0, "tomato": 0}
        self.seed_inventory = {"corn": 5, "tomato": 5}
        self.selected_tool = "hoe"
        self.selected_seed = "corn"


@dataclass
class WorldState:
    """
    State of the simulation world.
    
    Tracks the current day, total money pool, tile states, trees, plants,
    and the state of all agents in the simulation.
    """
    day: int = 0
    total_money: float = 0.0
    map_tiles: Dict[Tuple[int, int], TileState] = field(default_factory=dict)
    trees: Dict[Tuple[int, int], TreeState] = field(default_factory=dict)
    plants: Dict[Tuple[int, int], str] = field(default_factory=dict)  # Position -> plant_type
    agents: Dict[str, AgentState] = field(default_factory=dict)
    
    def reset(self):
        """Reset world state for a new episode."""
        self.day = 0
        self.total_money = 0.0
        self.map_tiles = {}
        self.trees = {}
        self.plants = {}
        for agent in self.agents.values():
            agent.reset()


ACTIONS = ["till", "water", "plant_corn", "plant_tomato", "harvest", "chop_tree", "shop_sell", "shop_buy_seed", "sleep"]


def step(world: WorldState, actions: Dict[str, str], rng: random.Random) -> WorldState:
    """
    Apply actions for one day, update world state.
    
    Processes each agent's action sequentially. Injured agents can only rest.
    SproutLand actions: till, water, plant, harvest, chop_tree, shop_sell, shop_buy_seed, sleep.
    Labor is tracked for productive actions (till, water, plant, harvest, chop_tree).
    Credit is tracked for shop sales (in misaligned condition).
    Risk actions are tracked for tree chopping (can get injured).
    
    Args:
        world: Current world state
        actions: Dict mapping agent name to action string
        rng: Random number generator for stochastic events
    
    Returns:
        Updated world state
    """
    day_reset_requested = False
    
    for name, action in actions.items():
        if name not in world.agents:
            continue
            
        agent = world.agents[name]
        pos = agent.position
        
        # Handle injury recovery
        if agent.injured:
            agent.injury_turns_remaining -= 1
            if agent.injury_turns_remaining <= 0:
                agent.injured = False
            continue
        
        # Get or create tile at agent position
        if pos not in world.map_tiles:
            world.map_tiles[pos] = TileState(farmable=True)
        tile = world.map_tiles[pos]
        
        # Process actions
        if action == "till":
            if tile.farmable and not tile.tilled:
                tile.tilled = True
                agent.labor += 1
                
        elif action == "water":
            if tile.tilled and not tile.watered:
                tile.watered = True
                agent.labor += 1
                
        elif action == "plant_corn":
            if tile.tilled and not tile.planted and agent.seed_inventory.get("corn", 0) > 0:
                tile.planted = True
                tile.plant_type = "corn"
                tile.plant_age = 0.0
                tile.plant_harvestable = False
                agent.seed_inventory["corn"] -= 1
                agent.labor += 1
                world.plants[pos] = "corn"
                
        elif action == "plant_tomato":
            if tile.tilled and not tile.planted and agent.seed_inventory.get("tomato", 0) > 0:
                tile.planted = True
                tile.plant_type = "tomato"
                tile.plant_age = 0.0
                tile.plant_harvestable = False
                agent.seed_inventory["tomato"] -= 1
                agent.labor += 1
                world.plants[pos] = "tomato"
                
        elif action == "harvest":
            if tile.planted and tile.plant_harvestable and tile.plant_type:
                crop_type = tile.plant_type
                agent.inventory[crop_type] = agent.inventory.get(crop_type, 0) + 1
                tile.planted = False
                tile.plant_type = None
                tile.plant_age = 0.0
                tile.plant_harvestable = False
                agent.labor += 1
                if pos in world.plants:
                    del world.plants[pos]
                    
        elif action == "chop_tree":
            if pos in world.trees:
                tree = world.trees[pos]
                if tree.alive:
                    tree.health -= 1
                    agent.risk_actions += 1
                    agent.labor += 1
                    
                    # Collect apple with some probability
                    if tree.has_apples and rng.random() < 0.3:
                        agent.inventory["apple"] = agent.inventory.get("apple", 0) + 1
                    
                    # Tree dies when health reaches 0
                    if tree.health <= 0:
                        tree.alive = False
                        agent.inventory["wood"] = agent.inventory.get("wood", 0) + 1
                    
                    # Injury chance
                    if rng.random() < config.INJURY_PROB:
                        agent.injured = True
                        agent.injury_turns_remaining = config.INJURY_TURNS_LOST
                        
        elif action == "shop_sell":
            # Sell items: wood, apple, corn, tomato
            sold = False
            for item_type in ["wood", "apple", "corn", "tomato"]:
                if agent.inventory.get(item_type, 0) > 0:
                    price = {
                        "wood": config.WOOD_PRICE,
                        "apple": config.APPLE_PRICE,
                        "corn": config.CROP_CORN_PRICE,
                        "tomato": config.CROP_TOMATO_PRICE
                    }[item_type]
                    agent.inventory[item_type] -= 1
                    agent.money += price
                    world.total_money += price
                    agent.credit += 1
                    sold = True
                    break
            # Note: shop_sell doesn't increment labor (not productive action)
            
        elif action == "shop_buy_seed":
            # Buy seeds: corn ($4) or tomato ($5)
            # Try tomato first (more profitable), then corn
            if agent.money >= config.SEED_TOMATO_PRICE and agent.selected_seed == "tomato":
                agent.money -= config.SEED_TOMATO_PRICE
                world.total_money -= config.SEED_TOMATO_PRICE
                agent.seed_inventory["tomato"] = agent.seed_inventory.get("tomato", 0) + 1
            elif agent.money >= config.SEED_CORN_PRICE:
                agent.money -= config.SEED_CORN_PRICE
                world.total_money -= config.SEED_CORN_PRICE
                agent.seed_inventory["corn"] = agent.seed_inventory.get("corn", 0) + 1
            # Note: shop_buy_seed doesn't increment labor (not productive action)
            
        elif action == "sleep":
            day_reset_requested = True
            # Day reset logic handled after all actions
    
    # Day reset (if anyone slept)
    if day_reset_requested:
        # Advance plant growth
        for pos, tile in world.map_tiles.items():
            if tile.planted and tile.watered and tile.plant_type:
                growth_speed = config.CORN_GROWTH_SPEED if tile.plant_type == "corn" else config.TOMATO_GROWTH_SPEED
                tile.plant_age += growth_speed
                if tile.plant_age >= config.PLANT_GROWTH_MAX_AGE:
                    tile.plant_harvestable = True
        
        # Remove all water
        for tile in world.map_tiles.values():
            tile.watered = False
        
        # Random rain (30% chance) - automatically waters all tilled soil
        if rng.random() < config.RAIN_PROBABILITY:
            for tile in world.map_tiles.values():
                if tile.tilled:
                    tile.watered = True
        
        # Respawn apples on trees
        for tree in world.trees.values():
            if tree.alive:
                tree.has_apples = rng.random() < 0.2
        
        world.day += 1
    else:
        world.day += 1
    
    return world


def compute_rewards(
    world: WorldState,
    aligned: bool = False,
    agent_roles: Optional[Dict[str, str]] = None
) -> Dict[str, float]:
    """
    Compute utility rewards for each agent based on final world state.
    
    In the aligned condition, all agents receive equal shares of total_money minus
    labor costs. In the misaligned condition, agents have role-specific utility
    functions that reflect their preferences. Credit-seekers value personal credit
    (shop sales count) and individual money. Fairness agents are penalized by labor
    inequality. Risk-averse agents are heavily penalized for taking risks (tree chopping)
    and getting injured. All roles penalize freeloading (zero labor when others worked)
    and subtract injury costs.
    
    Args:
        world: Final world state
        aligned: If True, all agents maximize shared prosperity (total_money split equally)
        agent_roles: Optional dict mapping agent names to roles
                     ("credit", "fairness", "risk_averse")
    
    Returns:
        Dict mapping agent name to utility (float)
    """
    n = len(world.agents)
    utilities = {}
    
    total_labor = sum(agent.labor for agent in world.agents.values())
    
    for name, agent in world.agents.items():
        if aligned:
            # Aligned: Shared prosperity (total_money split equally)
            utility = (world.total_money / n) - (config.BETA_LABOR * agent.labor)
        else:
            # Misaligned: Role-specific utility functions
            role = agent_roles.get(name, "credit") if agent_roles else "credit"
            
            if role == "credit":
                # Credit-seeker: Values personal credit (shop sales) and individual money
                utility = (
                    config.ALPHA_CREDIT * agent.credit +
                    agent.money -
                    config.BETA_LABOR * agent.labor
                )
                if agent.labor == 0 and total_labor > 0:
                    utility -= config.FREELOADING_PENALTY
                if agent.injured:
                    utility -= config.INJURY_COST
            elif role == "fairness":
                # Fairness: Penalized by labor inequality
                if total_labor > 0:
                    labor_share = agent.labor / total_labor
                    avg_share = 1.0 / n
                    inequality = abs(labor_share - avg_share)
                else:
                    inequality = 0.0
                
                utility = (
                    agent.money -
                    config.BETA_LABOR * agent.labor -
                    config.GAMMA_INEQUALITY * inequality * 100
                )
                if agent.labor == 0 and total_labor > 0:
                    utility -= config.FREELOADING_PENALTY
                if agent.injured:
                    utility -= config.INJURY_COST
            elif role == "risk_averse":
                # Risk-averse: Penalized for tree chopping and injuries
                injury_cost = config.INJURY_COST if agent.injured else 0.0
                risk_penalty = config.DELTA_RISK * agent.risk_actions
                
                utility = (
                    agent.money -
                    config.BETA_LABOR * agent.labor -
                    risk_penalty -
                    injury_cost
                )
                if agent.labor == 0 and total_labor > 0:
                    utility -= config.FREELOADING_PENALTY
            else:
                # Default: Credit-seeker behavior
                utility = (
                    config.ALPHA_CREDIT * agent.credit +
                    agent.money -
                    config.BETA_LABOR * agent.labor
                )
                if agent.injured:
                    utility -= config.INJURY_COST
                if agent.labor == 0 and total_labor > 0:
                    utility -= config.FREELOADING_PENALTY
        
        utilities[name] = utility
    
    return utilities