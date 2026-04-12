import sys
import os

# Use proper package imports
from chip_floorplanner.server.environment import ChipFloorplannerEnvironment
from chip_floorplanner.models import ChipFloorplannerAction

env = ChipFloorplannerEnvironment()

print("=" * 50)
print("LOCAL LOGIC TEST — All 3 Tasks")
print("=" * 50)

for task in ["easy", "medium", "hard"]:
    obs = env.reset(task=task)
    print(f"OK {task}: canvas={obs.canvas_width}x{obs.canvas_height}, "
          f"modules={obs.total_modules}, first={obs.current_module['id']}")

# Place easy task manually — non-overlapping positions
print("\nEasy episode test:")
obs = env.reset(task="easy")
# Modules in easy: A(4,3), B(5,2), C(3,4), D(2,3)
placements = [(0,0,False), (5,0,False), (0,4,False), (4,4,False)]
rewards = []
for x, y, r in placements:
    action = ChipFloorplannerAction(x=x, y=y, rotate=r)
    result = env.step(action)
    rewards.append(result.reward)
    print(f"  Placed {action} -> reward={result.reward:.4f}, done={result.done}")

print(f"\n  Avg reward:    {sum(rewards)/len(rewards):.4f}")
print(f"  Final score:   {env.get_final_score():.4f}")
print(f"  Overlaps:      {env._state.total_overlap_count}")
print(f"  Wirelength:    {env._state.current_wirelength:.2f}")

if env._state.total_overlap_count == 0 and env.get_final_score() > 0.4:
    print("\nOK Local test passed!")
else:
    print("\nFAIL Local test failed or needs adjustment.")
