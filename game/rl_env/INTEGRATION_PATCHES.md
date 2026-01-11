# Integration Patches for RL Environment

This document contains the exact code modifications needed to integrate the RL environment with your game code.

## IMPORTANT: Backup Your Files First!

Before applying these patches, create backups of:
- `code/player.py`
- `code/level.py`
- `code/menu.py`

## Patch 1: Modify `code/player.py`

### Step 1.1: Add agent controls attribute (after line 64)

**Location**: After `self.toggle_shop = toggle_shop`

**Add this code**:
```python
		# RL agent controls
		self.use_agent_controls = False
		self.agent_controls = None  # Will be set by Level
```

### Step 1.2: Refactor input() method (replace lines 110-167)

**Replace the entire `input()` method** with:

```python
	def input(self):
		# ADAPT THIS BLOCK: Use agent controls if enabled
		if hasattr(self, 'use_agent_controls') and self.use_agent_controls and self.agent_controls:
			self._process_agent_input()
		else:
			self._process_keyboard_input()

	def _process_keyboard_input(self):
		"""Original keyboard input processing"""
		keys = pygame.key.get_pressed()

		if not self.timers['tool use'].active and not self.sleep:
			# directions 
			if keys[pygame.K_UP]:
				self.direction.y = -1
				self.status = 'up'
			elif keys[pygame.K_DOWN]:
				self.direction.y = 1
				self.status = 'down'
			else:
				self.direction.y = 0

			if keys[pygame.K_RIGHT]:
				self.direction.x = 1
				self.status = 'right'
			elif keys[pygame.K_LEFT]:
				self.direction.x = -1
				self.status = 'left'
			else:
				self.direction.x = 0

			# tool use
			if keys[pygame.K_SPACE]:
				self.timers['tool use'].activate()
				self.direction = pygame.math.Vector2()
				self.frame_index = 0

			# change tool
			if keys[pygame.K_q] and not self.timers['tool switch'].active:
				self.timers['tool switch'].activate()
				self.tool_index += 1
				self.tool_index = self.tool_index if self.tool_index < len(self.tools) else 0
				self.selected_tool = self.tools[self.tool_index]

			# seed use
			if keys[pygame.K_LCTRL]:
				self.timers['seed use'].activate()
				self.direction = pygame.math.Vector2()
				self.frame_index = 0

			# change seed 
			if keys[pygame.K_e] and not self.timers['seed switch'].active:
				self.timers['seed switch'].activate()
				self.seed_index += 1
				self.seed_index = self.seed_index if self.seed_index < len(self.seeds) else 0
				self.selected_seed = self.seeds[self.seed_index]

			if keys[pygame.K_RETURN]:
				collided_interaction_sprite = pygame.sprite.spritecollide(self,self.interaction,False)
				if collided_interaction_sprite:
					if collided_interaction_sprite[0].name == 'Trader':
						self.toggle_shop()
					else:
						self.status = 'left_idle'
						self.sleep = True

	def _process_agent_input(self):
		"""Process agent controls (RL environment)"""
		controls = self.agent_controls
		
		# Reset direction at start of frame
		self.direction = pygame.math.Vector2(0, 0)
		
		if not self.timers['tool use'].active and not self.sleep:
			# Movement (only if not in shop - checked at level)
			move = controls.move
			if move == 1:  # up
				self.direction.y = -1
				self.status = 'up'
			elif move == 2:  # down
				self.direction.y = 1
				self.status = 'down'
			elif move == 3:  # left
				self.direction.x = -1
				self.status = 'left'
			elif move == 4:  # right
				self.direction.x = 1
				self.status = 'right'
			
			# Tool actions
			tool_action = controls.tool_action
			if tool_action == 1 and not self.timers['tool switch'].active:  # switch_tool
				self.timers['tool switch'].activate()
				self.tool_index += 1
				self.tool_index = self.tool_index if self.tool_index < len(self.tools) else 0
				self.selected_tool = self.tools[self.tool_index]
			elif tool_action == 2:  # use_tool
				self.timers['tool use'].activate()
				self.direction = pygame.math.Vector2()
				self.frame_index = 0
			
			# Seed actions
			seed_action = controls.seed_action
			if seed_action == 1 and not self.timers['seed switch'].active:  # switch_seed
				self.timers['seed switch'].activate()
				self.seed_index += 1
				self.seed_index = self.seed_index if self.seed_index < len(self.seeds) else 0
				self.selected_seed = self.seeds[self.seed_index]
			elif seed_action == 2:  # plant_seed
				self.timers['seed use'].activate()
				self.direction = pygame.math.Vector2()
				self.frame_index = 0
			
			# Interact
			if controls.interact == 1:
				collided_interaction_sprite = pygame.sprite.spritecollide(self, self.interaction, False)
				if collided_interaction_sprite:
					if collided_interaction_sprite[0].name == 'Trader':
						self.toggle_shop()
					else:
						self.status = 'left_idle'
						self.sleep = True
```

## Patch 2: Modify `code/level.py`

### Step 2.1: Add agent controls attributes (after line 39)

**Location**: After `self.shop_active = False`

**Add this code**:
```python
		# RL agent controls
		self.use_agent_controls = False
		self.agent_controls = None  # AgentControls dataclass from env
		self.env_events = []  # Event list for reward computation
		self.day_count = 0  # Track days for episode termination
```

### Step 2.2: Pass agent_controls to player (modify setup method)

**Location**: In `setup()` method, where Player is created (around line 88)

**Find**:
```python
				self.player = Player(
					pos = (obj.x,obj.y), 
					group = self.all_sprites, 
					collision_sprites = self.collision_sprites,
					tree_sprites = self.tree_sprites,
					interaction = self.interaction_sprites,
					soil_layer = self.soil_layer,
					toggle_shop = self.toggle_shop)
```

**Add after Player creation** (right after the Player instantiation):
```python
				# ADAPT THIS BLOCK: Set agent controls reference
				self.player.use_agent_controls = self.use_agent_controls
				self.player.agent_controls = self.agent_controls
```

### Step 2.3: Modify player_add() to emit events (replace lines 110-113)

**Replace**:
```python
	def player_add(self,item):

		self.player.item_inventory[item] += 1
		self.success.play()
```

**With**:
```python
	def player_add(self,item):

		self.player.item_inventory[item] += 1
		self.success.play()
		# ADAPT THIS BLOCK: Emit harvest event for RL rewards
		if hasattr(self, 'env_events'):
			if item in ['corn', 'tomato']:
				self.env_events.append('harvest')
```

### Step 2.4: Modify reset() to track days (modify reset method)

**Location**: In `reset()` method (starting at line 119)

**Add at the beginning of reset()**:
```python
	def reset(self):
		# ADAPT THIS BLOCK: Track day count
		self.day_count += 1
		
		# plants
		self.soil_layer.update_plants()
		# ... rest of existing code ...
```

### Step 2.5: Emit events in soil_layer methods

**We need to modify soil.py to emit events. See Patch 4 below.**

## Patch 3: Modify `code/soil.py`

### Step 3.1: Add event emission to get_hit() (modify get_hit method)

**Location**: In `get_hit()` method (around line 100)

**Find**:
```python
	def get_hit(self, point):
		for rect in self.hit_rects:
			if rect.collidepoint(point):
				self.hoe_sound.play()

				x = rect.x // TILE_SIZE
				y = rect.y // TILE_SIZE

				if 'F' in self.grid[y][x]:
					self.grid[y][x].append('X')
					self.create_soil_tiles()
					if self.raining:
						self.water_all()
```

**Replace with**:
```python
	def get_hit(self, point):
		for rect in self.hit_rects:
			if rect.collidepoint(point):
				self.hoe_sound.play()

				x = rect.x // TILE_SIZE
				y = rect.y // TILE_SIZE

				if 'F' in self.grid[y][x]:
					self.grid[y][x].append('X')
					self.create_soil_tiles()
					if self.raining:
						self.water_all()
					# ADAPT THIS BLOCK: Emit till_success event
					# We need to access level.env_events - soil_layer needs reference to level
					# This will be set when soil_layer is created in level.py
```

**Note**: For event emission, we need soil_layer to have access to level. See Step 3.2.

### Step 3.2: Store level reference in SoilLayer (modify __init__)

**Location**: In `SoilLayer.__init__()` (around line 58)

**Find**:
```python
class SoilLayer:
	def __init__(self, all_sprites, collision_sprites):
```

**Change to**:
```python
class SoilLayer:
	def __init__(self, all_sprites, collision_sprites, level=None):
		self.level = level  # ADAPT THIS BLOCK: Store level reference for events
```

**Then in `code/level.py`**, modify SoilLayer creation (around line 26):

**Find**:
```python
		self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites)
```

**Replace with**:
```python
		# ADAPT THIS BLOCK: Pass level reference to soil_layer
		self.soil_layer = SoilLayer(self.all_sprites, self.collision_sprites, level=self)
```

**Now update get_hit() in soil.py**:
```python
					# ADAPT THIS BLOCK: Emit till_success event
					if self.level and hasattr(self.level, 'env_events'):
						self.level.env_events.append('till_success')
```

### Step 3.3: Add event emission to water() method (around line 114)

**Find**:
```python
	def water(self, target_pos):
		for soil_sprite in self.soil_sprites.sprites():
			if soil_sprite.rect.collidepoint(target_pos):

				x = soil_sprite.rect.x // TILE_SIZE
				y = soil_sprite.rect.y // TILE_SIZE
				self.grid[y][x].append('W')

				pos = soil_sprite.rect.topleft
				surf = choice(self.water_surfs)
				WaterTile(pos, surf, [self.all_sprites, self.water_sprites])
```

**Replace with**:
```python
	def water(self, target_pos):
		for soil_sprite in self.soil_sprites.sprites():
			if soil_sprite.rect.collidepoint(target_pos):

				x = soil_sprite.rect.x // TILE_SIZE
				y = soil_sprite.rect.y // TILE_SIZE
				self.grid[y][x].append('W')

				pos = soil_sprite.rect.topleft
				surf = choice(self.water_surfs)
				WaterTile(pos, surf, [self.all_sprites, self.water_sprites])
				# ADAPT THIS BLOCK: Emit water_success event
				if self.level and hasattr(self.level, 'env_events'):
					self.level.env_events.append('water_success')
				break  # Only water one tile
```

### Step 3.4: Add event emission to plant_seed() method (around line 154)

**Find**:
```python
	def plant_seed(self, target_pos, seed):
		for soil_sprite in self.soil_sprites.sprites():
			if soil_sprite.rect.collidepoint(target_pos):
				self.plant_sound.play()

				x = soil_sprite.rect.x // TILE_SIZE
				y = soil_sprite.rect.y // TILE_SIZE

				if 'P' not in self.grid[y][x]:
					self.grid[y][x].append('P')
					Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite, self.check_watered)
```

**Replace with**:
```python
	def plant_seed(self, target_pos, seed):
		for soil_sprite in self.soil_sprites.sprites():
			if soil_sprite.rect.collidepoint(target_pos):
				self.plant_sound.play()

				x = soil_sprite.rect.x // TILE_SIZE
				y = soil_sprite.rect.y // TILE_SIZE

				if 'P' not in self.grid[y][x]:
					self.grid[y][x].append('P')
					Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite, self.check_watered)
					# ADAPT THIS BLOCK: Emit plant_success event
					if self.level and hasattr(self.level, 'env_events'):
						self.level.env_events.append('plant_success')
				break  # Only plant one seed
```

## Patch 4: Modify `code/menu.py`

### Step 4.1: Add agent control support to input() method

**Location**: In `input()` method (around line 54)

**Replace the entire `input()` method** with:

```python
	def input(self):
		# ADAPT THIS BLOCK: Check if using agent controls
		if hasattr(self.player, 'use_agent_controls') and self.player.use_agent_controls:
			if hasattr(self.player, 'agent_controls') and self.player.agent_controls:
				self._process_agent_input()
			else:
				return  # No agent controls available
		else:
			self._process_keyboard_input()

	def _process_keyboard_input(self):
		"""Original keyboard input processing"""
		keys = pygame.key.get_pressed()
		self.timer.update()

		if keys[pygame.K_ESCAPE]:
			self.toggle_menu()

		if not self.timer.active:
			if keys[pygame.K_UP]:
				self.index -= 1
				self.timer.activate()

			if keys[pygame.K_DOWN]:
				self.index += 1
				self.timer.activate()

			if keys[pygame.K_SPACE]:
				self.timer.activate()

				# get item
				current_item = self.options[self.index]

				# sell
				if self.index <= self.sell_border:
					if self.player.item_inventory[current_item] > 0:
						self.player.item_inventory[current_item] -= 1
						self.player.money += SALE_PRICES[current_item]

				# buy
				else:
					seed_price = PURCHASE_PRICES[current_item]
					if self.player.money >= seed_price:
						self.player.seed_inventory[current_item] += 1
						self.player.money -= PURCHASE_PRICES[current_item]

		# clamp the values
		if self.index < 0:
			self.index = len(self.options) - 1
		if self.index > len(self.options) - 1:
			self.index = 0

	def _process_agent_input(self):
		"""Process agent menu controls"""
		controls = self.player.agent_controls
		self.timer.update()
		
		menu_action = controls.menu_action
		
		if menu_action == 4:  # exit
			self.toggle_menu()
		
		if not self.timer.active:
			if menu_action == 1:  # up
				self.index -= 1
				self.timer.activate()
			
			if menu_action == 2:  # down
				self.index += 1
				self.timer.activate()
			
			if menu_action == 3:  # select
				self.timer.activate()
				
				# get item
				current_item = self.options[self.index]
				
				# sell
				if self.index <= self.sell_border:
					if self.player.item_inventory[current_item] > 0:
						self.player.item_inventory[current_item] -= 1
						self.player.money += SALE_PRICES[current_item]
				
				# buy
				else:
					seed_price = PURCHASE_PRICES[current_item]
					if self.player.money >= seed_price:
						self.player.seed_inventory[current_item] += 1
						self.player.money -= PURCHASE_PRICES[current_item]
		
		# clamp the values
		if self.index < 0:
			self.index = len(self.options) - 1
		if self.index > len(self.options) - 1:
			self.index = 0
```

## Patch 5: Modify `code/level.py` - Handle agent controls in run()

### Step 5.1: Modify run() to use agent controls conditionally

**Location**: In `run()` method (around line 148)

**Find**:
```python
	def run(self,dt):
		
		# drawing logic
		self.display_surface.fill('black')
		self.all_sprites.custom_draw(self.player)
		
		# updates
		if self.shop_active:
			self.menu.update()
		else:
			self.all_sprites.update(dt)
			self.plant_collision()
```

**Replace with**:
```python
	def run(self,dt):
		
		# drawing logic
		self.display_surface.fill('black')
		self.all_sprites.custom_draw(self.player)
		
		# updates
		if self.shop_active:
			self.menu.update()
		else:
			# ADAPT THIS BLOCK: Only update sprites if not using agent controls
			# or if agent controls are set (will be consumed by player.input())
			self.all_sprites.update(dt)
			self.plant_collision()
		
		# Note: Player.input() is called in player.update() which is called by
		# all_sprites.update(dt). Agent controls are consumed there.
```

## Summary of Changes

1. **player.py**: 
   - Add `use_agent_controls` and `agent_controls` attributes
   - Refactor `input()` into `_process_keyboard_input()` and `_process_agent_input()`

2. **level.py**:
   - Add `use_agent_controls`, `agent_controls`, `env_events`, `day_count` attributes
   - Pass agent controls to player
   - Emit events in `player_add()`
   - Track day count in `reset()`
   - Pass level reference to soil_layer

3. **soil.py**:
   - Add `level` parameter to `__init__`
   - Emit events in `get_hit()`, `water()`, `plant_seed()`

4. **menu.py**:
   - Refactor `input()` to support agent controls
   - Add `_process_agent_input()` method

## Testing

After applying patches:

1. Test that original keyboard controls still work (set `use_agent_controls=False`)
2. Test RL environment initialization
3. Test that events are emitted correctly
4. Test that agent controls work when enabled

## Notes

- All "ADAPT THIS BLOCK" comments mark code that needs to be integrated
- The patches maintain backward compatibility - original keyboard controls still work
- Event emission is optional (checks `hasattr` for safety)
- Agent controls are only used when `use_agent_controls=True` and `agent_controls` is set
