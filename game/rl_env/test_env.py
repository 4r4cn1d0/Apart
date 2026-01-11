"""
Simple test script to verify the SproutLand RL environment works correctly.
Run this to test that the environment initializes and can execute steps.
"""

from sproutland_env import SproutLandEnv

env = SproutLandEnv(render_mode="human", max_steps=1000)
obs, info = env.reset()
print("Observation space:", env.observation_space)
print("Action space:", env.action_space)

# Run a few random steps
for i in range(10):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"Step {i}: Reward={reward:.3f}, Money=${info['money']}")
    if terminated or truncated:
        break

env.close()
