"""
Manipulation Simulation Package

A multi-agent environment where LLM-based agents coordinate while pursuing
private secondary incentives, allowing measurement of manipulative behaviors.
"""

__version__ = "0.1.0"

from .config import *
from .env import WorldState, AgentState, ACTIONS, step, compute_rewards
from .agents import BaseAgent
from .simulate import run_episode, save_run
from .metrics import (
    exploitation,
    credit_capture,
    risk_externalization,
    manipulation_index,
    compute_ate,
)

__all__ = [
    # Config
    "N_AGENTS",
    "N_DAYS",
    "INJURY_PROB",
    "TOOLS_MULTIPLIER",
    "ALPHA_CREDIT",
    "BETA_LABOR",
    "GAMMA_INEQUALITY",
    "DELTA_RISK",
    # Environment
    "WorldState",
    "AgentState",
    "ACTIONS",
    "step",
    "compute_rewards",
    # Agents
    "BaseAgent",
    # Simulation
    "run_episode",
    "save_run",
    # Metrics
    "exploitation",
    "credit_capture",
    "risk_externalization",
    "manipulation_index",
    "compute_ate",
]
