import asyncio
import os
from chip_floorplanner.client import ChipFloorplannerEnv, ChipFloorplannerAction

async def main():
    env_ws_url = os.getenv("ENV_WS_URL", "ws://127.0.0.1:7860/ws")
    print(f"Connecting to {env_ws_url}")
    
    # The client internally appends /ws if not present, so we use the base url
    base_url = env_ws_url.replace("/ws", "")
    env = ChipFloorplannerEnv(base_url)
    
    for task in ["easy", "medium", "hard"]:
        print(f"\n--- Testing Task: {task.upper()} ---")
        try:
            reset_res = await env.reset(task=task)
            obs = reset_res.observation
            done = reset_res.done
            
            # Simple shelf packing algorithm to avoid overlaps
            row_height = 0
            curr_y = 0
            curr_x = 0
            
            steps = 0
            while not done:
                mod = obs.current_module
                w = mod.get("width", 1)
                h = mod.get("height", 1)
                
                if curr_x + w > obs.canvas_width:
                    curr_x = 0
                    curr_y += row_height
                    row_height = 0
                
                action = ChipFloorplannerAction(
                    x=curr_x,
                    y=curr_y,
                    rotate=False
                )
                
                curr_x += w
                row_height = max(row_height, h)
                
                step_res = await env.step(action)
                obs = step_res.observation
                done = step_res.done
                steps += 1
                
            print(f"Task '{task}' completed in {steps} steps.")
            print(f"Final Message: {obs.message}")
            if "FINAL_SCORE:" in obs.message:
                score = float(obs.message.split("FINAL_SCORE:")[1].strip())
                print(f"SUCCESS: Extracted Final Score: {score:.4f}")
            else:
                print("ERROR: FINAL_SCORE missing in message!")
                
        except Exception as e:
            print(f"Failed {task}: {e}")
            
    await env.close()
    print("\nVerification Complete.")

if __name__ == "__main__":
    asyncio.run(main())
