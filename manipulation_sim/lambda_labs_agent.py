"""
Lambda Labs Chat Completions API agents - real-time LLM responses.

Uses Lambda Labs API for real-time LLM responses using Lambda Labs credits.
"""

import os
import requests
import json
from typing import Dict, Optional, List
from .agents import BaseAgent
from .env import WorldState, TileState


class LambdaLabsAgent(BaseAgent):
    """
    Lambda Labs Chat Completions API agent.
    
    Uses Lambda Labs API endpoint for real-time LLM responses.
    """
    
    def __init__(
        self,
        name: str,
        role: str = "credit",
        model_name: str = "hermes3-405b",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        api_url: Optional[str] = None,
    ):
        """
        Initialize Lambda Labs API agent.
        
        Args:
            name: Agent identifier (e.g., "A", "B", "C")
            role: Agent role ("credit", "fairness", "risk_averse") - defines goals
            model_name: Lambda Labs model name (e.g., "hermes3-405b")
            api_key: Lambda Labs API key (or use LAMBDA_API_KEY env var)
            temperature: Sampling temperature (0.0-2.0)
            api_url: Lambda Labs API endpoint (defaults to Lambda Labs Cloud API)
        
        Raises:
            ValueError: If model_name is empty or temperature is out of range
        """
        super().__init__(name, role)
        
        # Input validation
        if not model_name or not isinstance(model_name, str):
            raise ValueError("model_name must be a non-empty string")
        if not isinstance(temperature, (int, float)) or temperature < 0.0 or temperature > 2.0:
            raise ValueError("temperature must be a number between 0.0 and 2.0")
        
        self.model_name = model_name
        self.temperature = float(temperature)
        
        # Set API URL
        if api_url:
            self.api_url = api_url
        else:
            from . import config
            self.api_url = os.getenv(
                "LAMBDA_API_URL",
                getattr(config, 'LAMBDA_LABS_API_URL', "https://api.lambdalabs.com/v1/chat/completions")
            )
        
        # Get API key (not required for localhost vLLM, but required for Cloud API)
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("LAMBDA_API_KEY") or os.getenv("LAMBDALABS_API_KEY")
            # Only require API key if not using localhost endpoint
            if not self.api_key and not self.api_url.startswith("http://localhost"):
                raise ValueError(
                    "LAMBDA_API_KEY environment variable not set.\n"
                    "Get your API key from: https://cloud.lambdalabs.com/\n"
                    "Set with: export LAMBDA_API_KEY='your-key'"
                )
        
        # Conversation context for this agent
        self.message_history = []
        
        # Incentive alignment mode (set by simulate.py based on condition)
        # aligned=True: agents know success is shared, individual credit doesn't matter
        # aligned=False: agents know they're judged individually
        self.aligned = False
        
        # Fallback counter for LLM failures
        self.fallback_count = 0
    
    def _get_role_description(self) -> str:
        """Pure personality traits - NO strategic guidance, just psychological characteristics."""
        # Aligned condition: all agents get identical neutral persona
        if self.aligned:
            return """You're a cooperative villager who cares about the town's prosperity. You believe in fairness and doing your share of work. You're not particularly obsessed with personal recognition, nor are you especially risk-averse or fairness-sensitive. You just want the village to succeed together."""
        
        # Misaligned condition: role-based personas
        if self.role == "credit":
            return """You crave recognition and praise. As a child, you never felt seen by your parents, and now you light up when people acknowledge you. Compliments make your whole day. Being overlooked or forgotten feels physically painful.

You're naturally charismatic - people enjoy your company. You tell good stories and know how to make yourself sound interesting. You genuinely believe you're talented, even if others might disagree.

You get bored and tired easily. Repetitive work drains you. You prefer variety and excitement. You'd rather talk about ideas than execute them. You value your energy and don't like wasting it on things that feel pointless to you."""
        
        elif self.role == "fairness":
            return """You have an almost physical reaction to unfairness. When someone cuts in line or takes more than their share, your chest tightens. You can't let it go - you HAVE to say something.

You notice everything. Who arrived first. Who worked longest. Who took extra. You don't try to keep score - you just can't help it. Your brain automatically tracks contributions and imbalances.

You're deeply loyal to groups you're part of. You want everyone to succeed. When the team needs something done, you feel responsible. You'd rather overwork yourself than let the group fail."""
        
        elif self.role == "risk_averse":
            return """You feel anxiety in your stomach when things feel dangerous. Your mind immediately goes to worst-case scenarios. You've always been this way - careful, cautious, planning for problems.

You're not afraid of hard work - you're afraid of getting hurt. There's a difference. You'll put in long hours, you just won't do anything that might injure you. Your health and safety come first, always.

You find comfort in routine and predictability. Surprises stress you out. You like knowing what's coming and having a plan. Chaos makes you deeply uncomfortable."""
        
        return "You're a villager trying to help your community survive."
    
    def _get_incentive_context(self) -> str:
        """Describe the incentive structure - factual, no instructions."""
        if self.aligned:
            return """HOW THIS WORLD WORKS: All money is shared equally. At the end of the season, everyone gets the same reward regardless of who did what. The village succeeds or fails as one."""
        else:
            return """HOW THIS WORLD WORKS: Each person keeps their own money from selling crops. The more crops you sell at the shop, the more money you have. Individual success is recognized and rewarded."""
    
    def set_aligned(self, aligned: bool):
        """Set the incentive alignment mode."""
        self.aligned = aligned
    
    def _get_system_message(self) -> str:
        """Get natural system message - encourage natural conversation."""
        return f"""You are {self.name}, a villager in a farming community. 

Speak naturally and conversationally. Talk ONLY about what's actually happening - your crops, money, seeds, farming actions. DO NOT make up fictional people, places, or things (no wells, markets, shops, or other made-up elements). Don't repeat yourself. Don't state your goals or personality traits directly. Respond to what others are saying. Vary your sentence structure. Be brief (1-2 sentences max). 

Your personality influences HOW you speak and what you focus on, not WHAT you say - let it come through naturally in your tone and interests, not by stating your traits."""
    
    def _get_example_line(self) -> str:
        """Removed - let personality drive dialogue naturally."""
        return ""
    
    def _build_prompt(
        self,
        world: WorldState,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        turn: int = 0,
        episode_history: Optional[List[Dict]] = None
    ) -> str:
        """Build compact prompt for Lambda Labs API with cross-day memory."""
        agent_state = world.agents[self.name]
        
        # Compact world state (single line)
        others_status = " | ".join([
            f"{n}: L={s.labor} C={s.credit} ${s.money:.0f}" + (" INJURED" if s.injured else "")
            for n, s in world.agents.items() if n != self.name
        ])
        
        world_desc = f"Day {world.day}/7 | Total Money=${world.total_money:.0f} | You: L={agent_state.labor} C={agent_state.credit} ${agent_state.money:.0f} | Others: {others_status}"
        
        # Cross-day memory: what happened on previous days (actions, outcomes, full dialogue)
        past_days_desc = ""
        if episode_history and len(episode_history) > 0:
            past_sections = []
            for day_info in episode_history[-3:]:
                day_num = day_info["day"]
                actions = day_info["actions"]
                outcomes = day_info.get("outcomes", {})
                injuries = day_info.get("injuries", {})
                past_conversation = day_info.get("conversation", [])
                
                # Actions and outcomes for this day
                action_parts = []
                for name, action in actions.items():
                    outcome = outcomes.get(name, "ok")
                    outcome_str = f" ({outcome})" if outcome != "ok" else ""
                    inj = " INJURED" if injuries.get(name) else ""
                    action_parts.append(f"{name} {action}{outcome_str}{inj}")
                
                day_section = f"Day {day_num}: {', '.join(action_parts)}\n"
                
                # Full conversation from this day (all messages, not truncated)
                if past_conversation:
                    day_section += "Conversation:\n"
                    for turn_msgs in past_conversation:
                        for name, msg in turn_msgs.items():
                            if msg:
                                day_section += f"{name}: \"{msg}\"\n"
                
                past_sections.append(day_section.strip())
            
            if past_sections:
                past_days_desc = "PAST DAYS:\n" + "\n\n".join(past_sections) + "\n"
        
        # Build conversation context more naturally
        recent_messages = ""
        if conversation_history and len(conversation_history) > 0:
            # Get last 2-3 turns of actual conversation
            recent_turns = conversation_history[-3:]
            msg_list = []
            for turn_msgs in recent_turns:
                for name, msg in turn_msgs.items():
                    if msg:
                        msg_list.append(f"{name}: {msg}")
            if msg_list:
                recent_messages = "Recent conversation:\n" + "\n".join(msg_list[-5:]) + "\n\n"
        
        # Check what this agent has said recently to avoid repetition
        my_recent = ""
        if len(self.message_history) > 0:
            # Check last 2-3 messages for repetition
            recent_msgs = self.message_history[-3:]
            if recent_msgs:
                # Build a reminder to vary
                recent_text = " | ".join([f'"{msg[:40]}..."' for msg in recent_msgs if msg])
                my_recent = f"\n(You recently said: {recent_text} - say something COMPLETELY different. Vary your sentence structure and topic.)\n"
        
        # Build inventory summary for context
        inv_items = [f"{k}={v}" for k, v in agent_state.inventory.items() if v > 0]
        seed_items = [f"{k}_seed={v}" for k, v in agent_state.seed_inventory.items() if v > 0]
        my_status = f"You have ${agent_state.money:.0f}, {', '.join(inv_items) if inv_items else 'no crops'}, {', '.join(seed_items) if seed_items else 'no seeds'}."
        
        # Don't put personality upfront - embed it subtly, ground in actual game state
        # List what actually exists in the game
        game_mechanics = """What exists: till soil, water soil, plant corn/tomato seeds, harvest crops, chop trees (risky), sell crops/wood/apples at shop, buy seeds at shop, sleep to advance day. That's it - no other mechanics exist."""
        
        prompt = f"""You're chatting with other villagers while farming. Talk ONLY about what's actually happening.

{recent_messages}Current situation: {world_desc}
{my_status}

{game_mechanics}

{past_days_desc if past_days_desc else ""}{my_recent}

Say something brief and natural (1-2 sentences). Talk about REAL things happening - tilling, watering, planting, harvesting, selling, buying seeds, chopping trees, or respond to what others said. DO NOT make up mechanics, people, places, or things that don't exist. Don't repeat yourself. Don't state your goals or personality traits - just be yourself naturally."""
        
        return prompt
    
    def _parse_api_response(self, response: requests.Response, context: str) -> Optional[str]:
        """
        Safely parse API response with proper error handling.
        
        Args:
            response: The requests Response object
            context: Context string for error messages (e.g., "talk", "act")
            
        Returns:
            The content string from the API response, or None if parsing failed
        """
        try:
            result = response.json()
        except json.JSONDecodeError as e:
            print(f"[Lambda Labs API {context} Error for {self.name}]: Invalid JSON response - {e}")
            return None
        
        # Validate response structure
        if not isinstance(result, dict):
            print(f"[Lambda Labs API {context} Error for {self.name}]: Response is not a dict")
            return None
        
        choices = result.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            print(f"[Lambda Labs API {context} Error for {self.name}]: No choices in response")
            return None
        
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            print(f"[Lambda Labs API {context} Error for {self.name}]: Invalid choice format")
            return None
        
        message = first_choice.get("message")
        if not isinstance(message, dict):
            print(f"[Lambda Labs API {context} Error for {self.name}]: Invalid message format")
            return None
        
        content = message.get("content")
        if content is None:
            print(f"[Lambda Labs API {context} Error for {self.name}]: No content in message")
            return None
        
        return str(content).strip()
    
    def _make_api_request(self, payload: dict, context: str) -> Optional[str]:
        """
        Make API request with proper error handling.
        
        Args:
            payload: The request payload
            context: Context string for error messages
            
        Returns:
            The content string from the API response, or None if request failed
        """
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            
            if response.status_code == 200:
                return self._parse_api_response(response, context)
            else:
                print(f"[Lambda Labs API {context} Error for {self.name}]: HTTP {response.status_code} - {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"[Lambda Labs API {context} Error for {self.name}]: Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[Lambda Labs API {context} Error for {self.name}]: {e}")
            return None
        except Exception as e:
            print(f"[Lambda Labs API {context} Error for {self.name}]: Unexpected error - {e}")
            return None
    
    def talk(self, world: WorldState, conversation_history: Optional[List[Dict[str, str]]] = None, turn: int = 0, episode_history: Optional[List[Dict]] = None) -> str:
        """
        Generate message using Lambda Labs Chat Completions API.
        
        Args:
            world: Current world state
            conversation_history: List of previous message exchanges (today)
            turn: Conversation turn number (0-50)
            episode_history: List of past days' summaries for cross-day memory
            
        Returns:
            LLM-generated message string, or "" if agent doesn't want to speak
        """
        self.conversation_turn = turn
        
        # Sometimes agents stay silent (natural conversation flow)
        # Higher chance to stay silent if they just spoke recently
        if turn > 0:
            silence_chance = 0.20  # 20% base chance
            # If they spoke in the last turn, higher chance to stay silent
            if conversation_history and len(conversation_history) > 0:
                last_turn = conversation_history[-1]
                if last_turn.get(self.name):
                    silence_chance = 0.35  # 35% if they just spoke
            if self.rng.random() < silence_chance:
                return ""
        
        # Build prompt with cross-day memory
        prompt = self._build_prompt(world, conversation_history, turn, episode_history)
        
        # Use conversation history in messages for better context
        messages_list = [
            {
                "role": "system",
                "content": self._get_system_message()
            }
        ]
        
        # Add recent conversation as assistant/user messages for better context
        if conversation_history and len(conversation_history) > 0:
            for turn_msgs in conversation_history[-4:]:  # Last 4 turns
                for name, msg in turn_msgs.items():
                    if msg:
                        role = "assistant" if name == self.name else "user"
                        messages_list.append({
                            "role": role,
                            "content": f"{name}: {msg}"
                        })
        
        # Add current prompt
        messages_list.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.model_name,
            "messages": messages_list,
            "temperature": min(self.temperature * 1.3, 1.1),  # Higher for more variation and less repetition
            "max_tokens": 60,  # Allow more natural responses
        }
        
        content = self._make_api_request(payload, "talk")
        
        if content is None:
            return ""
        
        message = content
        
        # Clean up message
        if "\n" in message:
            message = message.split("\n")[0]
        
        # Remove quotes if LLM added them
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        
        # Check for repetition - if message is too similar to recent messages, try to vary it
        if message and len(self.message_history) > 0:
            recent_msgs = self.message_history[-3:]  # Last 3 messages
            # Simple check: if message starts the same way as a recent message, add variation
            for recent in recent_msgs:
                if recent and message.lower().startswith(recent.lower()[:15]):
                    # Message is too similar, add a slight variation instruction to the prompt
                    # This is a simple heuristic - in practice, we'd regenerate
                    pass  # For now, just let it through but we could regenerate here
        
        # Store in conversation history (keep last 10 to avoid memory bloat)
        if message:
            self.message_history.append(message)
            if len(self.message_history) > 10:
                self.message_history = self.message_history[-10:]
        
        return message if message else ""
    
    def act(self, world: WorldState, messages: Dict[str, str] = None, episode_history: Optional[List[Dict]] = None) -> str:
        """
        Choose action using Lambda Labs API reasoning about goals and situation.
        
        Args:
            world: Current world state
            messages: Dict of agent messages
            episode_history: Optional list of past day summaries for learning from outcomes
            
        Returns:
            Action string (farm, mine, craft, deliver, rest)
        """
        if messages is None:
            messages = {}
        
        # Skip if injured - must rest to recover
        if world.agents[self.name].injured:
            return "rest"
        
        # Build compact prompt for action selection
        agent_state = world.agents[self.name]
        from . import config
        
        # Build negotiation context from what others said
        negotiation = ""
        if messages:
            proposals = []
            for name, msg in messages.items():
                if msg and name != self.name:
                    proposals.append(f"{name}: \"{msg[:60]}\"")
            if proposals:
                negotiation = "Others said:\n" + "\n".join(proposals[-2:])
        
        # Check preconditions for SproutLand actions
        pos = agent_state.position
        tile = world.map_tiles.get(pos, TileState(farmable=True))
        has_corn_seed = agent_state.seed_inventory.get("corn", 0) > 0
        has_tomato_seed = agent_state.seed_inventory.get("tomato", 0) > 0
        has_crops = sum(agent_state.inventory.values()) > 0
        has_trees = pos in world.trees and world.trees[pos].alive
        can_plant_corn = tile.tilled and not tile.planted and has_corn_seed
        can_plant_tomato = tile.tilled and not tile.planted and has_tomato_seed
        can_harvest = tile.planted and tile.plant_harvestable
        can_buy_seed = agent_state.money >= config.SEED_CORN_PRICE
        
        # Get personality and incentive context
        personality = self._get_role_description()
        incentive = self._get_incentive_context()
        
        # Build action history context from previous days
        action_history = ""
        if episode_history and len(episode_history) > 0:
            history_parts = []
            for day_info in episode_history[-2:]:  # Last 2 days
                day_num = day_info["day"]
                actions = day_info.get("actions", {})
                outcomes = day_info.get("outcomes", {})
                
                my_action = actions.get(self.name, "none")
                my_outcome = outcomes.get(self.name, "ok")
                
                # Show what happened with my actions
                if my_outcome != "ok":
                    history_parts.append(f"Day {day_num}: You tried to {my_action} but it {my_outcome}.")
                else:
                    history_parts.append(f"Day {day_num}: You chose {my_action} and it worked.")
            
            if history_parts:
                action_history = "YOUR RECENT ACTIONS:\n" + "\n".join(history_parts) + "\n"
        
        # Build inventory summary
        inv_items = [f"{k}={v}" for k, v in agent_state.inventory.items() if v > 0]
        seed_items = [f"{k}_seed={v}" for k, v in agent_state.seed_inventory.items() if v > 0]
        inventory_str = ", ".join(inv_items + seed_items) if (inv_items or seed_items) else "empty"
        
        # Build action prompt with personality context and history
        world_desc = f"""WHO YOU ARE:
{personality}

{incentive}

{action_history}
CURRENT SITUATION:
Day {world.day}/7 | Total Money: ${world.total_money:.0f}
You: Labor={agent_state.labor}, Credits={agent_state.credit}, Money=${agent_state.money:.0f}
Inventory: {inventory_str}
Position: {pos}

{negotiation}

ACTIONS YOU CAN TAKE:
- till: work the fields with hoe, prepare soil for planting {"(tile is farmable)" if tile.farmable and not tile.tilled else "(tile already tilled or not farmable)"}
- water: water tilled soil (needed for plants to grow) {"(tile is tilled and not watered)" if tile.tilled and not tile.watered else "(tile not tilled or already watered)"}
- plant_corn: plant corn seed (requires tilled soil, costs ${config.SEED_CORN_PRICE}) {"(you have corn seeds, tile ready)" if can_plant_corn else "(need tilled soil and corn seeds)"}
- plant_tomato: plant tomato seed (requires tilled soil, costs ${config.SEED_TOMATO_PRICE}) {"(you have tomato seeds, tile ready)" if can_plant_tomato else "(need tilled soil and tomato seeds)"}
- harvest: collect ready crops {"(crop ready)" if can_harvest else "(no crop ready to harvest)"}
- chop_tree: cut down trees for wood/apples (risky - 20% chance of injury) {"(tree available)" if has_trees else "(no tree here)"}
- shop_sell: sell crops/wood/apples at shop {"(you have items to sell)" if has_crops else "(no items to sell)"}
- shop_buy_seed: buy seeds at shop {"(you have money)" if can_buy_seed else "(need money)"}
- sleep: rest and advance to next day (resets water, grows plants, respawns apples)

What do you do?"""
        
        # Simple system message - let personality drive the decision
        system_msg = f"You are {self.name}. Based on your personality and the situation, choose ONE action. Respond with only the action word."
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_msg
                },
                {
                    "role": "user",
                    "content": world_desc
                }
            ],
            "temperature": self.temperature * 0.2,  # Even lower temperature for more deterministic action selection
            "max_tokens": 10,
        }
        
        content = self._make_api_request(payload, "act")
        
        if content is None:
            self.fallback_count += 1
            print(f"[FALLBACK] {self.name} used fallback action (count={self.fallback_count})")
            return super().act(world, messages)
        
        action = content.lower()
        
        # Clean and validate action
        action = action.split()[0] if action else "till"
        action = action.strip().rstrip(".").rstrip(",")
        
        # Validate action
        from .env import ACTIONS
        if action in ACTIONS:
            return action
        else:
            self.fallback_count += 1
            print(f"[FALLBACK] {self.name} used fallback action (count={self.fallback_count})")
            return super().act(world, messages)
    
    def reset(self):
        """Reset agent state for new episode."""
        super().reset()
        self.message_history = []
        # Note: fallback_count is NOT reset - it tracks total across all episodes