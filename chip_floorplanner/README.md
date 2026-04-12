---
title: Chip Floorplanner
emoji: 🔲
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
tags:
  - openenv
pinned: false
---

# Chip Floorplanner — OpenEnv Environment

Real-world VLSI chip floorplanning: place rectangular circuit modules on a
2D canvas to minimize wire length and bounding box area. A genuine
EDA (Electronic Design Automation) task used in semiconductor chip design.

## Why Chip Floorplanning?

Floorplanning determines performance, power, and area of integrated circuits.
Real chip designers spend days on this task. This environment lets AI agents
practice core spatial reasoning on a real engineering problem.

## Tasks

| Task   | Modules | Canvas | Nets | Difficulty |
|--------|---------|--------|------|------------|
| easy   | 4       | 20×20  | 2    | Easy       |
| medium | 7       | 30×30  | 5    | Medium     |
| hard   | 12      | 40×40  | 10   | Hard       |

## Action Space

- `x` (int): X coordinate (left edge of module)
- `y` (int): Y coordinate (top edge of module)
- `rotate` (bool): Swap module width and height if true

## Observation Space

- `canvas_width`, `canvas_height`: Canvas dimensions
- `current_module`: Module to place now (id, width, height)
- `placed_modules`: Already placed modules with positions
- `modules_remaining`: Modules not yet placed
- `netlist`: List of nets (connected module groups)
- `step_number`, `total_modules`, `message`, `done`, `reward`

## Reward Function

**Per step:** `0.5 - wirelength_penalty(0.25) - area_penalty(0.15) - overlap_penalty(0.30×n) ± bonuses`
- No-overlap bonus each step: +0.1
- Final perfect placement bonus: +0.2

**Final score (0–1):**
- 40% overlap score
- 25% area efficiency
- 25% wirelength (HPWL)
- 10% completion

## Baseline Scores (Qwen/Qwen2.5-72B-Instruct)

| Task   | Avg Reward | Steps |
|--------|------------|-------|
| easy   | 0.448      | 4     |
| medium | 0.425      | 7     |
| hard   | 0.363      | 12    |

## API

- `GET  /health` → `{"status": "healthy"}`
- `POST /reset`  → observation (`{"task": "easy|medium|hard"}`)
- `POST /step`   → step result (`{"x": 0, "y": 0, "rotate": false}`)
- `WS   /ws`     → WebSocket connection (OpenEnv protocol)
- `GET  /docs`   → Swagger UI

## Setup

```bash
pip install openenv-core openai
export HF_TOKEN=your_token
export ENV_BASE_URL=https://diva29-chip-floorplanner.hf.space
python inference.py
```
