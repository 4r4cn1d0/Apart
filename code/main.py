import pygame, sys
import os
from settings import *
from level import Level
from ai_agent import AIAgent

class Game:
	def __init__(self, ai_mode=False, api_provider="openai", api_key=None):
		# Initialize pygame WITHOUT mixer (no sounds)
		pygame.init()
		# Disable mixer completely - no sounds
		if pygame.mixer.get_init() is not None:
			pygame.mixer.quit()
		self.screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
		pygame.display.set_caption('Sprout land - AI Controlled' if ai_mode else 'Sprout land')
		self.clock = pygame.time.Clock()
		self.level = Level()
		
		# Initialize AI agent if AI mode is enabled
		if ai_mode:
			try:
				self.ai_agent = AIAgent(api_provider=api_provider, api_key=api_key)
				self.level.player.set_ai_agent(self.ai_agent)
				print(f"AI Agent initialized with {api_provider} API")
				print("AI is now controlling the player!")
			except Exception as e:
				print(f"Failed to initialize AI agent: {e}")
				print("Falling back to manual control...")
				ai_mode = False

	def run(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
  
			dt = self.clock.tick() / 1000
			self.level.run(dt)
			pygame.display.update()

if __name__ == '__main__':
	import argparse
	
	parser = argparse.ArgumentParser(description='Sprout Land - Farming Game')
	parser.add_argument('--ai', action='store_true', help='Enable AI control')
	parser.add_argument('--api', choices=['openai', 'anthropic', 'lambda'], default='openai', 
	                   help='API provider for AI (default: openai)')
	parser.add_argument('--api-key', type=str, default=None, 
	                   help='API key (or set OPENAI_API_KEY, ANTHROPIC_API_KEY, or LAMBDA_API_KEY env var)')
	
	args = parser.parse_args()
	
	# Check for API key in environment if not provided
	if args.ai and not args.api_key:
		env_key = f"{args.api.upper()}_API_KEY"
		args.api_key = os.getenv(env_key)
		if not args.api_key:
			print(f"Warning: {env_key} not set. AI mode requires an API key.")
			print("Set it as an environment variable or use --api-key argument.")
			args.ai = False
	
	game = Game(ai_mode=args.ai, api_provider=args.api, api_key=args.api_key)
	game.run()