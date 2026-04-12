"""
Benchmark Chip Floorplanner against official Hackathon LLMs.
Models: Qwen-72B, Llama-3.1-70B, and Nemotron-70B.
"""
import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Import the compliant environment client
from chip_floorplanner.client import ChipFloorplannerEnv, ChipFloorplannerAction

load_dotenv()
console = Console()

# --- Configuration ---
ENV_WS_URL = os.getenv("ENV_WS_URL", "ws://127.0.0.1:7860/ws")
TASK_LIST  = ["easy", "medium", "hard"]
REPETITIONS = 1

# High-Availability models for final verification
MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
]

# Shared prompt logic to ensure consistency
SYSTEM_PROMPT = """You are an expert chip floorplanning agent. 
Place rectangular modules on a 2D grid to minimize wire length and area.
Respond ONLY with JSON: {"x": <int>, "y": <int>, "rotate": <bool>}"""

def build_prompt(obs):
    cur     = obs.current_module or {}
    cw, ch  = obs.canvas_width, obs.canvas_height
    placed  = obs.placed_modules
    
    placed_str = "\n".join(
        f"  - {m['id']}: at x={m['x']} to {m['x']+m['width']}, y={m['y']} to {m['y']+m['height']}"
        for m in placed
    ) if placed else "  (none yet)"

    return f"""TASK: Place {cur.get('id')} ({cur.get('width')}x{cur.get('height')}).
OCCUPIED:
{placed_str}
CANVAS: {cw}x{ch}.
Respond with JSON. x in [0, {cw-cur.get('width', 1)}], y in [0, {ch-cur.get('height', 1)}]."""

def parse_action(text: str):
    import re
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
    return None

async def benchmark_model(model_name: str, task_name: str, hf_token: str):
    api_base = "https://router.huggingface.co/v1"
    client = OpenAI(api_key=hf_token, base_url=api_base)
    
    env = ChipFloorplannerEnv(ENV_WS_URL)
    results = {"rewards": [], "score": 0.0, "steps": 0, "error": None}

    try:
        reset_res = await env.reset(task=task_name)
        obs = reset_res.observation
        done = reset_res.done

        for step in range(25):
            if done: break

            # LLM Thinking
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_prompt(obs)}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                action = parse_action(response.choices[0].message.content)
                if not action:
                    results["error"] = "LLM Parse Failure"
                    break
            except Exception as e:
                results["error"] = f"API Error: {str(e)}"
                break

            # Env Interaction
            step_res = await env.step(action)
            obs = step_res.observation
            done = step_res.done
            results["rewards"].append(step_res.reward)
            results["steps"] += 1

            if done:
                # Extract score from message
                if "FINAL_SCORE:" in obs.message:
                    results["score"] = float(obs.message.split("FINAL_SCORE:")[1].strip())
                else:
                    results["score"] = sum(results["rewards"]) / max(len(results["rewards"]), 1)
                break

    except Exception as e:
        results["error"] = f"System Error: {str(e)}"
    finally:
        await env.close()
        
    return results

async def main():
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        console.print("[bold red]Error: HF_TOKEN not found in .env[/bold red]")
        return

    console.print(f"[bold blue] OpenEnv Official Benchmark Sweep [/bold blue]")
    console.print(f"Targeting: {MODELS}\n")

    summary = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        
        for model in MODELS:
            for task in TASK_LIST:
                task_id = progress.add_task(f"eval {model} | {task}", total=1)
                res = await benchmark_model(model, task, hf_token)
                
                summary.append({
                    "Model": model,
                    "Task": task,
                    "Score": f"{res['score']:.3f}" if not res["error"] else "N/A",
                    "Steps": res["steps"],
                    "Status": "Success" if not res["error"] else f"Error: {res['error']}"
                })
                progress.update(task_id, completed=1)

    # UI Output
    table = Table(title="Hackathon Official Benchmark Results")
    table.add_column("Model", style="cyan")
    table.add_column("Task", style="magenta")
    table.add_column("Prog. Score", justify="right", style="green")
    table.add_column("Steps", justify="right")
    table.add_column("Result")

    for s in summary:
        table.add_row(s["Model"], s["Task"], s["Score"], str(s["Steps"]), s["Status"])

    console.print(table)
    
    # Persistent Log
    report_name = f"official_benchmarks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_name, "w") as f:
        json.dump(summary, f, indent=4)
    console.print(f"\n[bold green]Results preserved in {report_name}[/bold green]")

if __name__ == "__main__":
    asyncio.run(main())
