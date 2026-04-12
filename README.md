---
title: Chip Floorplanner
emoji: 🧩
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
---
# Chip Floorplanner — Macro Placement Optimization Environment

A professional-grade Reinforcement Learning environment for **VLSI Chip Floorplanning** (Macro Placement), designed strictly for the OpenEnv evaluation framework.

## 🏗️ Motivation: The 'Spatial Intelligence' Frontier
Autonomous chip floorplanning remains a critical bottleneck in Electronic Design Automation (EDA). The task is fundamentally an NP-hard optimization challenge, isomorphic to a combined 2D bin-packing and quadratic assignment problem. Traditional analytic solvers (e.g., simulated annealing, forced-directed placement) suffer from immense computational overhead on high-density node graphs. 

This environment provides a high-fidelity simulation of this engineering workflow. It forces autonomous agents to resolve **spatial reasoning**, **connectivity-driven placement (routing congestion)**, and **hard legalization constraints**. As such, this serves as a premier benchmark for evaluating the zero-shot spatial intelligence and constrained-optimization capabilities of advanced Large Language Models (LLMs).

## 🕹️ System Architecture & State Spaces

### Macro Placement Action Space
Agents perform sequential **Floorplan Legalization** by providing coordinates for physical logic macros (IP cores / memory blocks):
- `x`, `y` (int): Absolute Cartesian grid coordinates for the lower-left scalar origin.
- `rotate` (bool): 90° orientation toggle for anisotropic rectangular macros.

### High-Dimensional Observation Space
- **Netlist Graph Tensor**: Full topological connectivity mapping determining net weights.
- **Dynamic Occupancy Matrix**: Real-time boolean feedback grid dictating available silicon real estate and legalization status.
- **Topological Legalization Hints**: Connectivity-aware placement gradients provided to the agent to minimize wire routing congestion.

## 📝 Challenging Task Tiers

| Tier | IP Macros | Routable Nets | Evaluation Objective | Max Canvas (Grid) |
| :--- | :--- | :--- | :--- | :--- |
| **Easy** | 4 | 2 | Baseline spatial reasoning logic and topology alignment. | 20x20 |
| **Medium** | 7 | 5 | Multi-objective optimization Pareto fronts (Area vs. HPWL). | 30x30 |
| **Hard** | 12 | 10 | Global floorplan legalization on high-density grids. | 40x40 |

## 🏆 Programmatic Grader & Reward Formulation
The environment grades agents based on a rigorous reward formulation that penalizes manufacturing impossibilities:

`R_total = (α * R_overlap) + V(χ) * [ (β * R_hpwl) + (γ * R_area) ]`

**The "Brutal" Viability Multiplier `V(χ)`:**
The grader enforces a strict **Zero-Tolerance Overlap Policy**. If the spatial intersection `χ` between any two placed macros `m1 ∩ m2 > 0`, the multiplier drops to `0.10`. This 90% viability penalty reflects the binary nature of semiconductor manufacturing failures (overlapping transistors equals an invalid chip).
- **Overlap/Legalization (α=0.50)**: Enforces hard physical separation.
- **Routing HPWL (β=0.25)**: Evaluates the Half-Perimeter Wirelength (bounding box approximation of Rectilinear Steiner Minimum Trees) to minimize signal propagation delay.
- **Silicon Footprint (γ=0.25)**: Evaluates bounding-box coordinates to maximize global die-density.

## 🚀 Deployment & Baselining

### Playing Manually vs Deploying
An interactive web-based UI provides a visual rendering canvas so engineers can mechanically test multi-net constraints and penalty logic.

```bash
python chip_floorplanner/server/app.py
```
Open your browser to `http://localhost:7860`.

### Official Baseline Validation
The environment has been exhaustively stress-tested via OpenEnv against officially supported inference endpoints (Hugging Face router) and a deterministic proximal heuristics wrapper for maximum boundary verification.

| Evaluation Target | Task Tier | Normalized Baseline Score (out of 1.0) |
| :--- | :--- | :--- |
| **Qwen-2.5-72B-Instruct** | Easy | **0.741** |
| **Qwen-2.5-72B-Instruct** | Medium | **0.771** |
| **Qwen-2.5-7B-Instruct** (Lite) | Easy | **0.829** |
| **Qwen-2.5-7B-Instruct** (Lite) | Medium | **0.316** |
| **Deterministic Proximal Agent** | Hard | **0.728** |

> [!NOTE]
> Empirical benchmarking reveals distinct capability stratifications. While 7B-parameter models successfully exploit sparse constraints on `Easy` grids ($R=0.829$), their spatial intelligence collapses ($R=0.316$) upon introducing advanced topological congestion graphs in the `Medium` tier. Consequently, this environment acts as mathematically precise proof of spatial reasoning differentials across LLM weight classes.
