import pygame
import base64
import io
import json
import os
import time
from typing import Dict, Optional, Tuple

class AIAgent:
	"""
	AI Agent that controls the player using vision-based decision making.
	Supports multiple vision APIs: OpenAI, Anthropic, and Lambda Labs.
	"""
	
	def __init__(self, api_provider: str = "openai", api_key: Optional[str] = None):
		self.api_provider = api_provider.lower()
		self.api_key = api_key or os.getenv(f"{api_provider.upper()}_API_KEY")
		
		if not self.api_key:
			raise ValueError(f"API key not found. Set {api_provider.upper()}_API_KEY environment variable or pass api_key parameter.")
		
		self.last_action = None
		self.action_history = []
		self.frame_count = 0
		self.decision_interval = 10  # Make decision every N frames
		
		# Initialize API client based on provider
		if self.api_provider == "openai":
			try:
				import openai
				self.client = openai.OpenAI(api_key=self.api_key)
				self.model = "gpt-4o"  # or "gpt-4-vision-preview"
			except ImportError:
				raise ImportError("OpenAI library not installed. Run: pip install openai")
		
		elif self.api_provider == "anthropic":
			try:
				import anthropic
				self.client = anthropic.Anthropic(api_key=self.api_key)
				self.model = "claude-3-5-sonnet-20241022"
			except ImportError:
				raise ImportError("Anthropic library not installed. Run: pip install anthropic")
		
		elif self.api_provider == "lambda":
			# Lambda Labs API integration
			# Can use either:
			# 1. Direct instance endpoint (http://IP:8000) - no auth needed
			# 2. Cloud API (https://cloud.lambda.ai/api/v1) - uses HTTP Basic Auth
			api_url = os.getenv("LAMBDA_API_URL", "http://192.222.59.32:8000")
			
			# If it's a direct IP endpoint, use it directly
			if api_url.startswith("http://") and ":" in api_url.split("//")[1]:
				self.api_url = f"{api_url}/v1/chat/completions"
				self.use_basic_auth = False  # Direct instance, no auth
			else:
				# Cloud API endpoint
				self.api_url = f"{api_url}/chat/completions"
				self.use_basic_auth = True  # Cloud API uses HTTP Basic Auth
			
			self.model = os.getenv("LAMBDA_MODEL", "meta-llama/Llama-3.1-70B-Vision-Instruct")
		
		else:
			raise ValueError(f"Unsupported API provider: {api_provider}. Choose: openai, anthropic, or lambda")
	
	def capture_screenshot(self, display_surface: pygame.Surface) -> str:
		"""Capture current game screen and convert to base64 string."""
		try:
			from PIL import Image
			import numpy as np
			
			# Capture the screen using string buffer
			string_image = pygame.image.tostring(display_surface, 'RGB')
			img = Image.frombytes('RGB', display_surface.get_size(), string_image)
			
			# Resize if too large (to save API costs)
			max_size = 1024
			if img.width > max_size or img.height > max_size:
				img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
			
			# Convert to base64
			buffer = io.BytesIO()
			img.save(buffer, format='PNG')
			img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
			return img_base64
		except ImportError:
			raise ImportError("PIL (Pillow) library not installed. Run: pip install pillow")
	
	def get_game_state_text(self, player) -> str:
		"""Get text representation of game state for context."""
		# Import game knowledge if available
		try:
			from multi_agent.game_knowledge import GAME_MANUAL
			base_knowledge = "\n" + GAME_MANUAL[:500] + "...\n"
		except:
			base_knowledge = ""
		
		state = f"""{base_knowledge}
Current Game State:
- Position: ({player.rect.centerx}, {player.rect.centery})
- Selected Tool: {player.selected_tool}
- Selected Seed: {player.selected_seed}
- Inventory: {player.item_inventory}
- Seeds: {player.seed_inventory}
- Money: ${player.money}
- Status: {player.status}

You know how to play this game. Use your knowledge of tools, locations, and mechanics.
"""
		return state
	
	def get_action_from_openai(self, image_base64: str, game_state: str) -> Dict:
		"""Get action decision from OpenAI API - minimal context, observation-based."""
		prompt = f"""You are playing a farming simulation game. Observe the screen and game state, then decide your action.

{game_state}

Available actions: "move_up", "move_down", "move_left", "move_right", "move_none", "use_tool", "switch_tool", "use_seed", "switch_seed", "interact"

Respond with JSON: {{"action": "action_name", "reason": "brief explanation"}}"""
		
		response = self.client.chat.completions.create(
			model=self.model,
			messages=[
				{
					"role": "user",
					"content": [
						{"type": "text", "text": prompt},
						{
							"type": "image_url",
							"image_url": {"url": f"data:image/png;base64,{image_base64}"}
						}
					]
				}
			],
			max_tokens=150,
			temperature=0.7
		)
		
		content = response.choices[0].message.content
		# Try to extract JSON from response
		try:
			# Remove markdown code blocks if present
			if "```json" in content:
				content = content.split("```json")[1].split("```")[0].strip()
			elif "```" in content:
				content = content.split("```")[1].split("```")[0].strip()
			
			action_data = json.loads(content)
			return action_data
		except json.JSONDecodeError:
			# Fallback: try to extract action from text
			action_data = {"action": "move_none", "reason": "Failed to parse response"}
			if "move_up" in content.lower():
				action_data["action"] = "move_up"
			elif "move_down" in content.lower():
				action_data["action"] = "move_down"
			elif "move_left" in content.lower():
				action_data["action"] = "move_left"
			elif "move_right" in content.lower():
				action_data["action"] = "move_right"
			elif "use_tool" in content.lower():
				action_data["action"] = "use_tool"
			elif "switch_tool" in content.lower():
				action_data["action"] = "switch_tool"
			elif "use_seed" in content.lower():
				action_data["action"] = "use_seed"
			elif "switch_seed" in content.lower():
				action_data["action"] = "switch_seed"
			elif "interact" in content.lower():
				action_data["action"] = "interact"
			return action_data
	
	def get_action_from_anthropic(self, image_base64: str, game_state: str) -> Dict:
		"""Get action decision from Anthropic Claude API - minimal context."""
		prompt = f"""You are playing a farming simulation game. Observe the screen and decide your action.

{game_state}

Available actions: "move_up", "move_down", "move_left", "move_right", "move_none", "use_tool", "switch_tool", "use_seed", "switch_seed", "interact"

Respond with JSON: {{"action": "action_name", "reason": "brief explanation"}}"""
		
		message = self.client.messages.create(
			model=self.model,
			max_tokens=150,
			messages=[
				{
					"role": "user",
					"content": [
						{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_base64}},
						{"type": "text", "text": prompt}
					]
				}
			]
		)
		
		content = message.content[0].text
		try:
			if "```json" in content:
				content = content.split("```json")[1].split("```")[0].strip()
			elif "```" in content:
				content = content.split("```")[1].split("```")[0].strip()
			
			action_data = json.loads(content)
			return action_data
		except json.JSONDecodeError:
			# Fallback parsing
			action_data = {"action": "move_none", "reason": "Failed to parse response"}
			if "move_up" in content.lower():
				action_data["action"] = "move_up"
			elif "move_down" in content.lower():
				action_data["action"] = "move_down"
			elif "move_left" in content.lower():
				action_data["action"] = "move_left"
			elif "move_right" in content.lower():
				action_data["action"] = "move_right"
			elif "use_tool" in content.lower():
				action_data["action"] = "use_tool"
			elif "switch_tool" in content.lower():
				action_data["action"] = "switch_tool"
			elif "use_seed" in content.lower():
				action_data["action"] = "use_seed"
			elif "switch_seed" in content.lower():
				action_data["action"] = "switch_seed"
			elif "interact" in content.lower():
				action_data["action"] = "interact"
			return action_data
	
	def get_action_from_lambda(self, image_base64: str, game_state: str) -> Dict:
		"""Get action decision from Lambda Labs API."""
		try:
			import requests
		except ImportError:
			raise ImportError("Requests library not installed. Run: pip install requests")
		
		prompt = f"""You are controlling a player in a farming simulation game. {game_state}
		
Available Actions: move_up, move_down, move_left, move_right, move_none, use_tool, switch_tool, use_seed, switch_seed, interact

Respond with JSON: {{"action": "action_name", "reason": "explanation"}}"""
		
		headers = {
			"Content-Type": "application/json"
		}
		
		# Lambda Labs: Use HTTP Basic Auth for cloud API, no auth for direct instance
		if hasattr(self, 'use_basic_auth') and self.use_basic_auth:
			auth = (self.api_key, "")  # Cloud API
		else:
			auth = None  # Direct instance endpoint, no auth needed
		
		payload = {
			"model": self.model,
			"messages": [
				{
					"role": "user",
					"content": [
						{"type": "text", "text": prompt},
						{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
					]
				}
			],
			"max_tokens": 150
		}
		
		try:
			# Lambda Labs: auth only if using cloud API
			if auth:
				response = requests.post(self.api_url, headers=headers, json=payload, auth=auth, timeout=30)
			else:
				response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
			response.raise_for_status()
			response_data = response.json()
			
			# Handle different response formats
			if "choices" in response_data:
				content = response_data["choices"][0]["message"]["content"]
			elif "content" in response_data:
				content = response_data["content"]
			else:
				return {"action": "move_none", "reason": "Unexpected response format"}
			
			try:
				if "```json" in content:
					content = content.split("```json")[1].split("```")[0].strip()
				elif "```" in content:
					content = content.split("```")[1].split("```")[0].strip()
				action_data = json.loads(content)
				return action_data
			except json.JSONDecodeError:
				# Fallback parsing
				return self._parse_action_fallback(content)
		except requests.exceptions.RequestException as e:
			print(f"Lambda API Error: {e}")
			return {"action": "move_none", "reason": f"API Error: {str(e)}"}
	
	def _parse_action_fallback(self, content: str) -> Dict:
		"""Fallback action parsing from text."""
		content_lower = content.lower()
		if "move_up" in content_lower:
			return {"action": "move_up", "reason": "Parsed from text"}
		elif "move_down" in content_lower:
			return {"action": "move_down", "reason": "Parsed from text"}
		elif "move_left" in content_lower:
			return {"action": "move_left", "reason": "Parsed from text"}
		elif "move_right" in content_lower:
			return {"action": "move_right", "reason": "Parsed from text"}
		elif "use_tool" in content_lower:
			return {"action": "use_tool", "reason": "Parsed from text"}
		elif "switch_tool" in content_lower:
			return {"action": "switch_tool", "reason": "Parsed from text"}
		elif "use_seed" in content_lower:
			return {"action": "use_seed", "reason": "Parsed from text"}
		elif "switch_seed" in content_lower:
			return {"action": "switch_seed", "reason": "Parsed from text"}
		elif "interact" in content_lower:
			return {"action": "interact", "reason": "Parsed from text"}
		return {"action": "move_none", "reason": "No action found"}
	
	def get_action(self, display_surface: pygame.Surface, player) -> Dict:
		"""Get next action from AI based on current game state."""
		self.frame_count += 1
		
		# Only make decision every N frames to save API calls
		if self.frame_count % self.decision_interval != 0:
			return self.last_action or {"action": "move_none", "reason": "Waiting"}
		
		try:
			# Capture screenshot
			image_base64 = self.capture_screenshot(display_surface)
			game_state = self.get_game_state_text(player)
			
			# Get action from API
			if self.api_provider == "openai":
				action_data = self.get_action_from_openai(image_base64, game_state)
			elif self.api_provider == "anthropic":
				action_data = self.get_action_from_anthropic(image_base64, game_state)
			elif self.api_provider == "lambda":
				action_data = self.get_action_from_lambda(image_base64, game_state)
			else:
				action_data = {"action": "move_none", "reason": "Unknown provider"}
			
			self.last_action = action_data
			self.action_history.append(action_data)
			
			# Keep history limited
			if len(self.action_history) > 100:
				self.action_history.pop(0)
			
			return action_data
		
		except Exception as e:
			print(f"AI Agent Error: {e}")
			return {"action": "move_none", "reason": f"Error: {str(e)}"}
