"""
Chip Floorplanner — Macro Placement Optimization
Standardized Inference Script for OpenEnv Hackathon.
Produces mandatory [START]/[STEP]/[END] logs.
"""
import asyncio
import os
import json
import re
import sys
import textwrap
from typing import List, Optional

from openai import OpenAI
from dotenv import load_dotenv

# Import the environment client
try:
    from chip_floorplanner.client import ChipFloorplannerEnv, ChipFloorplannerAction
except ImportError:
    # Fallback for local testing if path is not set
    sys.path.append(os.getcwd())
    from chip_floorplanner.client import ChipFloorplannerEnv, ChipFloorplannerAction

load_dotenv()

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

# For local testing vs HF Space deployment
IMAGE_NAME   = os.getenv("LOCAL_IMAGE_NAME") # Optional for local docker testing
ENV_WS_URL   = os.getenv("ENV_WS_URL", "ws://127.0.0.1:7860/ws") 

BENCHMARK    = "chip_floorplanner"
TASK_LIST    = ["easy", "medium", "hard"]
MAX_STEPS    = 20
TEMPERATURE  = 0.1
MAX_TOKENS   = 400

SYSTEM_PROMPT = """You are an expert chip floorplanning agent.
Place rectangular modules on a 2D grid canvas to minimize wire length and area.
Respond ONLY with valid JSON: {"x": <int>, "y": <int>, "rotate": <bool>}
No explanation. No markdown. Just the JSON."""

# --- Logging Utils ---

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Aligning to example script: exactly one space after [STEP]
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_val = str(success).lower()
    # Aligning to example script: exactly one space after [END]
    print(f"[END] success={success_val} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def debug(msg: str):
    print(f"[DEBUG] {msg}", file=sys.stderr, flush=True)

# --- Helper Logic ---

def make_canvas_grid(placed_modules, canvas_w, canvas_h):
    scale = 2
    gw, gh = canvas_w // scale, canvas_h // scale
    grid = [['.' for _ in range(gw)] for _ in range(gh)]
    for m in placed_modules:
        x, y = m.get('x', 0), m.get('y', 0)
        w, h = m.get('width', 1), m.get('height', 1)
        x1, y1 = x // scale, y // scale
        x2 = min((x + w + scale - 1) // scale, gw)
        y2 = min((y + h + scale - 1) // scale, gh)
        for gy in range(y1, y2):
            for gx in range(x1, x2):
                if 0 <= gy < gh and 0 <= gx < gw:
                    grid[gy][gx] = '#'
    return '\n'.join(''.join(row) for row in grid)

def build_prompt(obs):
    placed  = obs.placed_modules
    cur     = obs.current_module or {}
    cw, ch  = obs.canvas_width, obs.canvas_height
    
    canvas_str = make_canvas_grid(placed, cw, ch)
    placed_str = "\n".join(
        f"  - {m['id']}: at x={m['x']} to {m['x']+m['width']}, y={m['y']} to {m['y']+m['height']}"
        for m in placed
    ) if placed else "  (none yet)"

    lines = [
        f"TASK: Place module {cur.get('id')} ({cur.get('width')}x{cur.get('height')}).",
        "OCCUPIED REGIONS:",
        placed_str,
        "",
        "CANVAS GRID (#=occupied, .=free, 2:1 scale):",
        canvas_str,
        "",
        f"CONSTRAINTS: x in [0, {cw - cur.get('width', 1)}], y in [0, {ch - cur.get('height', 1)}]",
        'Respond ONLY with JSON: {"x": <int>, "y": <int>, "rotate": <bool>}',
    ]
    return "\n".join(lines)

def parse_action(text: str):
    m = re.search(r'\{[^}]+\}', text, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group())
            return ChipFloorplannerAction(
                x=int(d.get("x", 0)),
                y=int(d.get("y", 0)),
                rotate=bool(d.get("rotate", False))
            )
        except: pass
    return ChipFloorplannerAction(x=0, y=0, rotate=False)

async def run_task(task_name: str, client: OpenAI):
    # Determine environment connection method
    if IMAGE_NAME:
        env = await ChipFloorplannerEnv.from_docker_image(IMAGE_NAME)
    else:
        env = ChipFloorplannerEnv(ENV_WS_URL)
    
    rewards: List[float] = []
    steps_taken, score, success = 0, 0.0, False
    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Reset with task config
        reset_result = await env.reset(task=task_name)
        obs = reset_result.observation
        done = reset_result.done

        for step in range(1, MAX_STEPS + 1):
            if done: break

            # Generate LLM response
            prompt = build_prompt(obs)
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            raw_text = completion.choices[0].message.content or ""
            action = parse_action(raw_text)
            action_json = json.dumps({"x": action.x, "y": action.y, "rotate": action.rotate})

            # Step
            step_result = await env.step(action)
            obs = step_result.observation
            reward = float(step_result.reward or 0.0)
            done = step_result.done
            
            rewards.append(reward)
            steps_taken = step
            log_step(step, action_json, reward, done, None)

            if done:
                # Extract final score from message if available
                if "FINAL_SCORE:" in obs.message:
                    try:
                        score = float(obs.message.split("FINAL_SCORE:")[1].strip())
                    except:
                        score = sum(rewards) / len(rewards)
                else:
                    score = sum(rewards) / len(rewards)
                break

        score = min(max(score, 0.0), 1.0)
        success = score >= 0.1 # Standard success threshold

    except Exception as e:
        debug(f"Error in task {task_name}: {e}")
    finally:
        try: await env.close()
        except: pass
        log_end(success, steps_taken, score, rewards)

async def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    for task in TASK_LIST:
        await run_task(task, client)

if __name__ == "__main__":
    asyncio.run(main())
