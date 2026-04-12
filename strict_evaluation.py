import asyncio
import json
import sys
import os

# Ensure local imports work
sys.path.append(os.getcwd())

from chip_floorplanner.server.environment import ChipFloorplannerEnvironment
from inference import find_safe_position
from chip_floorplanner.models import ChipFloorplannerAction

async def run_strict_eval():
    env = ChipFloorplannerEnvironment()
    results = {}
    
    # We test two scenarios:
    # 1. Expert Agent (Shelf-Packing) - Should get high score
    # 2. Greedy Agent (All at 0,0) - Should get near zero
    
    scenarios = ["expert", "greedy"]
    levels = ["easy", "medium", "hard"]
    
    table_data = []

    for level in levels:
        for scenario in scenarios:
            env.reset(task=level)
            done = False
            
            while not done:
                cur = env._modules[env._current_idx]
                if scenario == "expert":
                    sx, sy = find_safe_position(
                        [{"x":m["x"], "y":m["y"], "width":m["w"], "height":m["h"]} for m in env._placed],
                        env._canvas_w, env._canvas_h, cur['width'], cur['height']
                    )
                else: # Greedy / Bad agent
                    sx, sy = 0, 0
                
                action = ChipFloorplannerAction(x=sx, y=sy, rotate=False)
                obs = env.step(action)
                done = obs.done
                
            final_score = env.get_final_score()
            table_data.append({
                "Level": level,
                "Scenario": scenario,
                "Score": final_score,
                "Overlaps": env._state.total_overlap_count,
                "Wirelength": f"{env._state.current_wirelength:.1f}",
                "Area": f"{env._state.current_bounding_area:.1f}"
            })

    print("\n" + "="*80)
    print(f"{'BRUTAL SCORING TRUTH TABLE':^80}")
    print("="*80)
    print(f"{'Level':<10} | {'Scenario':<10} | {'Score':<10} | {'Overlaps':<10} | {'Wirelength':<12} | {'Area':<10}")
    print("-" * 80)
    for r in table_data:
        print(f"{r['Level']:<10} | {r['Scenario']:<10} | {r['Score']:<10.4f} | {r['Overlaps']:<10} | {r['Wirelength']:<12} | {r['Area']:<10}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(run_strict_eval())
