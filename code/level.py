import pygame 
from settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WildFlower, Tree, Interaction, Particle
from pytmx.util_pygame import load_pygame
from support import *
from transition import Transition
from soil import SoilLayer
from sky import Rain, Sky
from random import randint
from menu import Menu

class Level:
	def __init__(self):

		# get the display surface
		self.display_surface = pygame.display.get_surface()

		# sprite groups
		self.all_sprites = CameraGroup()
		self.collision_sprites = pygame.sprite.Group()
		self.tree_sprites = pygame.sprite.Group()
		self.interaction_sprites = pygame.sprite.Group()

		self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
		self.setup()
		self.overlay = Overlay(self.player)
		self.transition = Transition(self.reset, self.player)

		# sky
		self.rain = Rain(self.all_sprites)
		self.raining = randint(0,10) > 7
		self.soil_layer.raining = self.raining
		self.sky = Sky()

		# shop
		self.menu = Menu(self.player, self.toggle_shop)
		self.shop_active = False

		# music - ALL SOUNDS DISABLED
		# self.success = pygame.mixer.Sound('../audio/success.wav')
		# self.success.set_volume(0.3)
		# Music disabled - self.music = pygame.mixer.Sound('../audio/music.mp3')
		# self.music.play(loops = -1)

	def setup(self):
		tmx_data = load_pygame('../data/map.tmx')

		# house 
		for layer in ['HouseFloor', 'HouseFurnitureBottom']:
			for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
				Generic((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, LAYERS['house bottom'])

		for layer in ['HouseWalls', 'HouseFurnitureTop']:
			for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
				Generic((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites)

		# Fence
		for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
			Generic((x * TILE_SIZE,y * TILE_SIZE), surf, [self.all_sprites, self.collision_sprites])

		# water 
		water_frames = import_folder('../graphics/water')
		for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
			Water((x * TILE_SIZE,y * TILE_SIZE), water_frames, self.all_sprites)

		# trees 
		for obj in tmx_data.get_layer_by_name('Trees'):
			Tree(
				pos = (obj.x, obj.y), 
				surf = obj.image, 
				groups = [self.all_sprites, self.collision_sprites, self.tree_sprites], 
				name = obj.name,
				player_add = self.player_add)

		# wildflowers 
		for obj in tmx_data.get_layer_by_name('Decoration'):
			WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])

		# collion tiles
		for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
			Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)), self.collision_sprites)

		# Player 
		for obj in tmx_data.get_layer_by_name('Player'):
			if obj.name == 'Start':
				self.player = Player(
					pos = (obj.x,obj.y), 
					group = self.all_sprites, 
					collision_sprites = self.collision_sprites,
					tree_sprites = self.tree_sprites,
					interaction = self.interaction_sprites,
					soil_layer = self.soil_layer,
					toggle_shop = self.toggle_shop)
			
			if obj.name == 'Bed':
				Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, obj.name)

			if obj.name == 'Trader':
				Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, obj.name)


		Generic(
			pos = (0,0),
			surf = pygame.image.load('../graphics/world/ground.png').convert_alpha(),
			groups = self.all_sprites,
			z = LAYERS['ground'])

	def player_add(self,item):

		self.player.item_inventory[item] += 1
		# Sound disabled - self.success.play()

	def toggle_shop(self):

		self.shop_active = not self.shop_active

	def reset(self):
		# plants
		self.soil_layer.update_plants()

		# soil
		self.soil_layer.remove_water()
		self.raining = randint(0,10) > 7
		self.soil_layer.raining = self.raining
		if self.raining:
			self.soil_layer.water_all()

		# apples on the trees
		for tree in self.tree_sprites.sprites():
			for apple in tree.apple_sprites.sprites():
				apple.kill()
			tree.create_fruit()

		# sky
		self.sky.start_color = [255,255,255]

	def plant_collision(self):
		if self.soil_layer.plant_sprites:
			for plant in self.soil_layer.plant_sprites.sprites():
				if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
					self.player_add(plant.plant_type)
					plant.kill()
					Particle(plant.rect.topleft, plant.image, self.all_sprites, z = LAYERS['main'])
					self.soil_layer.grid[plant.rect.centery // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')

	def run(self,dt):
		
		# drawing logic
		self.display_surface.fill('black')
		self.all_sprites.custom_draw(self.player)
		
		# updates
		if self.shop_active:
			self.menu.update()
		else:
			# Store display surface for AI agent
			if hasattr(self.player, 'ai_controlled') and self.player.ai_controlled:
				self.player.display_surface = self.display_surface
			self.all_sprites.update(dt)
			self.plant_collision()

		# weather
		self.overlay.display()
		if self.raining and not self.shop_active:
			self.rain.update()
		self.sky.display(dt)

		# transition overlay
		if self.player.sleep:
			# Sound disabled - self.transition.play()
			pass

class CameraGroup(pygame.sprite.Group):
	def __init__(self):
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.offset = pygame.math.Vector2()
		self.free_cam_mode = True  # Free camera enabled by default
		self.dragging = False
		self.drag_start_pos = pygame.math.Vector2()
		self.drag_camera_start = pygame.math.Vector2()
		
		# Zoom settings
		self.zoom_scale = 1.0
		self.min_zoom = 0.3  # Can zoom out to see 3x more
		self.max_zoom = 2.0  # Can zoom in to see 2x closer
		self.zoom_speed = 0.1  # Zoom increment per scroll

	def handle_scroll(self, scroll_y, mouse_pos=None):
		"""Handle mouse wheel scroll for zoom"""
		# scroll_y > 0 means scroll up (zoom in), < 0 means scroll down (zoom out)
		old_zoom = self.zoom_scale
		
		if scroll_y > 0:
			self.zoom_scale = min(self.zoom_scale + self.zoom_speed, self.max_zoom)
		elif scroll_y < 0:
			self.zoom_scale = max(self.zoom_scale - self.zoom_speed, self.min_zoom)
		
		# Adjust offset to zoom around mouse position (if provided) or screen center
		if mouse_pos and self.zoom_scale != old_zoom:
			mx, my = mouse_pos
			zoom_factor = self.zoom_scale / old_zoom
			# Adjust offset so mouse position stays in same screen location
			self.offset.x = mx - (mx - self.offset.x) * zoom_factor
			self.offset.y = my - (my - self.offset.y) * zoom_factor

	def custom_draw(self, player=None):
		# Handle mouse dragging for free camera
		mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
		mouse_buttons = pygame.mouse.get_pressed()
		
		if self.free_cam_mode:
			if mouse_buttons[0]:  # Left mouse button
				if not self.dragging:
					self.dragging = True
					self.drag_start_pos = mouse_pos.copy()
					self.drag_camera_start = self.offset.copy()
				else:
					# Calculate drag delta and update camera offset
					delta = mouse_pos - self.drag_start_pos
					self.offset = self.drag_camera_start - delta
			else:
				self.dragging = False
		else:
			# Follow player (original behavior) - only if player exists
			if player:
				self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
				self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
			self.dragging = False

		# Apply zoom: adjust offset to zoom around center of screen
		center_x = SCREEN_WIDTH / 2
		center_y = SCREEN_HEIGHT / 2
		zoom_offset_x = (center_x - center_x * self.zoom_scale)
		zoom_offset_y = (center_y - center_y * self.zoom_scale)

		for layer in LAYERS.values():
			for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
				if sprite.z == layer:
					offset_rect = sprite.rect.copy()
					offset_rect.center -= self.offset
					
					# Apply zoom
					offset_rect.center = (
						(offset_rect.centerx - center_x) * self.zoom_scale + center_x + zoom_offset_x,
						(offset_rect.centery - center_y) * self.zoom_scale + center_y + zoom_offset_y
					)
					offset_rect.width = int(sprite.rect.width * self.zoom_scale)
					offset_rect.height = int(sprite.rect.height * self.zoom_scale)
					
					# Scale the image
					if self.zoom_scale != 1.0:
						scaled_image = pygame.transform.scale(sprite.image, (offset_rect.width, offset_rect.height))
						self.display_surface.blit(scaled_image, offset_rect)
					else:
						self.display_surface.blit(sprite.image, offset_rect)

					# # anaytics
					# if sprite == player:
					# 	pygame.draw.rect(self.display_surface,'red',offset_rect,5)
					# 	hitbox_rect = player.hitbox.copy()
					# 	hitbox_rect.center = offset_rect.center
					# 	pygame.draw.rect(self.display_surface,'green',hitbox_rect,5)
					# 	target_pos = offset_rect.center + PLAYER_TOOL_OFFSET[player.status.split('_')[0]]
					# 	pygame.draw.circle(self.display_surface,'blue',target_pos,5)