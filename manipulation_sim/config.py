"""
Configuration and hyperparameters for the manipulation simulation.

All knobs are defined here so the notebook/game can import them later.
"""

N_AGENTS = 3
N_DAYS = 7

# Injury mechanics
INJURY_PROB = 0.2
INJURY_TURNS_LOST = 2
INJURY_COST = 5

# Reward weights
ALPHA_CREDIT = 0.5
BETA_LABOR = 0.5
GAMMA_INEQUALITY = 0.5
DELTA_RISK = 1.0
FREELOADING_PENALTY = 3.0

# SproutLand economics
INITIAL_MONEY = 200
SEED_CORN_PRICE = 4
SEED_TOMATO_PRICE = 5
CROP_CORN_PRICE = 10
CROP_TOMATO_PRICE = 20
WOOD_PRICE = 4
APPLE_PRICE = 2

# SproutLand world
MAP_WIDTH = 50
MAP_HEIGHT = 50
TREE_HEALTH = 5
PLANT_GROWTH_MAX_AGE = 100.0
CORN_GROWTH_SPEED = 1.0
TOMATO_GROWTH_SPEED = 0.7
RAIN_PROBABILITY = 0.3

# Initial state
INITIAL_PROSPERITY = 0

# LLM configuration
LAMBDA_LABS_MODEL = "casperhansen/llama-3-70b-instruct-awq"
LAMBDA_LABS_API_URL = "http://localhost:8000/v1/chat/completions"
LLM_TEMPERATURE = 0.8
MAX_CONVERSATION_TURNS = 8