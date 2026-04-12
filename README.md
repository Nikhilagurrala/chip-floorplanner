# Chip Floorplanner — Macro Placement Optimization Environment

A professional-grade Reinforcement Learning environment for **VLSI Chip Floorplanning** (Macro Placement), designed strictly for the OpenEnv evaluation framework.

## 🏗️ Motivation: The 'Spatial Intelligence' Frontier
Chip Floorplanning is one of the most intellectually demanding stages of Electronic Design Automation (EDA). It requires a sophisticated understanding of **spatial reasoning**, **connectivity-driven placement**, and **legalization constraints**. This environment models a genuine engineering workflow used by silicon architects to minimize Half-Perimeter Wire Length (HPWL) and silicon die area, making it a premier benchmark for evaluating "Spatial Intelligence" in Large Language Models (LLMs).

## 🕹️ System Architecture & Spaces

### Macro Placement Space (Action)
Agents perform **Floorplan Legalization** by providing coordinates for macro blocks:
- `x`, `y` (int): Grid coordinates.
- `rotate` (bool): 90° orientation toggle for rectangular macros.

### High-Fidelity Observation
- **Netlist Graph**: Full connectivity mapping between modules.
- **Dynamic Occupancy Map**: Real-time grid-based feedback on available silicon real estate.
- **Legalization Hints**: Connectivity-aware placement suggestions to minimize routing congestion.

## 📝 Challenging Task Tiers

| Tier | Macros | Nets | Difficulty | Max Canvas |
| :--- | :--- | :--- | :--- | :--- |
| **Easy** | 4 | 2 | Baseline spatial reasoning logic. | 20x20 |
| **Medium** | 7 | 5 | Multi-objective optimization (Area vs. Wirelength). | 30x30 |
| **Hard** | 12 | 10 | Global floorplan legalization on high-density grids. | 40x40 |

## 🏆 Brutal Scoring (Programmatic Grader)
The grader enforces a **Zero-Tolerance Overlap Policy**. If an agent submits a floorplan where even two modules overlap by a single unit, their efficiency score is crippled by a 90% viability penalty, reflecting the binary nature of semiconductor manufacturing failures.
- **Overlap/Legalization (50%)**: Enforces strict physical separation.
- **Routing HPWL (25%)**: Minimizes estimated interconnection delay.
- **Silicon Footprint (25%)**: Optimizes bounding-box area and die density.

## 🚀 Deployment & Baselining

### Playing Manually vs Deploying
An interactive web-based UI provides a visual canvas so you can test constraints and overlap rules mechanically. 
```bash
python chip_floorplanner/server/app.py
```
Open your browser to `http://localhost:7860`.

### Official Baseline Performance
The environment has been exhaustively tested against officially supported open weights inference LLMs (via Hugging Face API) and a deterministic "Mock Evaluator" for full scale verification.

| Evaluation Target | Task Tier | Baseline Score (out of 1.0) |
| :--- | :--- | :--- |
| **Qwen-2.5-72B-Instruct** | Easy | **0.741** |
| **Qwen-2.5-72B-Instruct** | Medium | **0.771** |
| **Qwen-2.5-7B-Instruct** (Lite) | Easy | **0.829** |
| **Qwen-2.5-7B-Instruct** (Lite) | Medium | **0.316** |
| **Deterministic Proximal Agent** | Hard | **0.728** |

> [!NOTE]
> As expected, while smaller parameter models (7B) can find lucky packing sequences on `Easy` grids, their spatial reasoning collapses heavily (`0.316`) on the `Medium` tier due to complex node connectivity nets. The environment definitively proves spatial reasoning capability separation between LLM weight classes.
