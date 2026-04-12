import uuid, sys, os
sys.path.insert(0, '/app')

from typing import List, Dict
from openenv.core.env_server import Environment
from chip_floorplanner.models import (
    ChipFloorplannerAction,
    ChipFloorplannerObservation,
    ChipFloorplannerState,
)

TASKS = {
    "easy": {
        "canvas": (20, 20),
        "modules": [
            {"id": "A", "width": 4, "height": 3},
            {"id": "B", "width": 5, "height": 2},
            {"id": "C", "width": 3, "height": 4},
            {"id": "D", "width": 2, "height": 3},
        ],
        "netlist": [["A", "B"], ["C", "D"]],
    },
    "medium": {
        "canvas": (30, 30),
        "modules": [
            {"id": "A", "width": 6, "height": 4},
            {"id": "B", "width": 5, "height": 5},
            {"id": "C", "width": 4, "height": 3},
            {"id": "D", "width": 3, "height": 6},
            {"id": "E", "width": 7, "height": 2},
            {"id": "F", "width": 2, "height": 4},
            {"id": "G", "width": 5, "height": 3},
        ],
        "netlist": [["A","B","C"],["B","D"],["C","E","F"],["D","G"],["A","E","G"]],
    },
    "hard": {
        "canvas": (40, 40),
        "modules": [
            {"id": "A", "width": 8, "height": 5},
            {"id": "B", "width": 6, "height": 6},
            {"id": "C", "width": 5, "height": 4},
            {"id": "D", "width": 4, "height": 7},
            {"id": "E", "width": 7, "height": 3},
            {"id": "F", "width": 3, "height": 5},
            {"id": "G", "width": 6, "height": 4},
            {"id": "H", "width": 4, "height": 4},
            {"id": "I", "width": 5, "height": 6},
            {"id": "J", "width": 3, "height": 3},
            {"id": "K", "width": 7, "height": 5},
            {"id": "L", "width": 2, "height": 8},
        ],
        "netlist": [
            ["A","B","C"],["B","D","E"],["C","F"],
            ["D","G","H"],["E","I"],["F","G","J"],
            ["H","I","K"],["J","K","L"],
            ["A","D","L"],["B","F","I","K"],
        ],
    },
}


def _overlaps(x1, y1, w1, h1, x2, y2, w2, h2):
    return not (x1+w1<=x2 or x2+w2<=x1 or y1+h1<=y2 or y2+h2<=y1)


def _hpwl(placed, netlist):
    total = 0.0
    for net in netlist:
        centers = [
            (placed[m]["x"]+placed[m]["w"]/2, placed[m]["y"]+placed[m]["h"]/2)
            for m in net if m in placed
        ]
        if len(centers) >= 2:
            xs = [c[0] for c in centers]
            ys = [c[1] for c in centers]
            total += (max(xs)-min(xs)) + (max(ys)-min(ys))
    return total


def grade_floorplan(placed, task_config):
    if not placed:
        return 0.0
    n = len(task_config["modules"])
    cw, ch = task_config["canvas"]
    
    # 1. Completion (5%)
    completion = len(placed) / n
    
    # 2. Overlap Strictness (50%) - Crucial for chip viability
    overlaps = sum(
        1 for i in range(len(placed)) for j in range(i+1, len(placed))
        if _overlaps(placed[i]["x"], placed[i]["y"], placed[i]["w"], placed[i]["h"],
                     placed[j]["x"], placed[j]["y"], placed[j]["w"], placed[j]["h"])
    )
    # Fatal flaw: 1 overlap = 50% penalty to this section. 2 overlaps = 100% penalty.
    overlap_score = max(0.0, 1.0 - (overlaps / 2.0))
    
    # Calculate performance metrics
    max_x = max(m["x"]+m["w"] for m in placed)
    max_y = max(m["y"]+m["h"] for m in placed)
    bbox_area = max_x * max_y
    sum_mod_area = sum(m["w"]*m["h"] for m in placed)
    
    # Clamping density: Stacking modules does NOT increase efficiency
    density = min(sum_mod_area / max(bbox_area, 1), 1.0)
    footprint_ratio = 1.0 - (bbox_area / (cw * ch))
    
    # 3. Area Efficiency (20%)
    area_score = (0.6 * density) + (0.4 * footprint_ratio)
    
    # 4. Wirelength (25%)
    hpwl = _hpwl({m["id"]: m for m in placed}, task_config["netlist"])
    realistic_max_hpwl = (cw + ch) * 0.4 * len(task_config["netlist"])
    wl_score = max(0.0, 1.0 - (hpwl / max(realistic_max_hpwl, 1)))
    
    # BRUTAL TRUTH: If there are overlaps, the area and wirelength are IRRELEVANT.
    # We apply a 'Viability Multiplier'
    viability = 1.0 if overlaps == 0 else 0.1
    
    final_score = (0.05 * completion) + (0.50 * overlap_score) + (0.20 * area_score * viability) + (0.25 * wl_score * viability)
    return round(min(max(final_score, 0.0), 1.0), 4)


class ChipFloorplannerEnvironment(Environment):

    def __init__(self):
        super().__init__()
        self._task_name = "easy"
        self._task_config = TASKS["easy"]
        self._canvas_w = 20
        self._canvas_h = 20
        self._modules: List[Dict] = []
        self._placed: List[Dict] = []
        self._current_idx = 0
        self._done = False
        self._state = ChipFloorplannerState(episode_id=str(uuid.uuid4()))

    def reset(self, seed=None, episode_id=None, **kwargs):
        task = kwargs.get("task", "easy")
        if task not in TASKS:
            task = "easy"
        self._task_name = task
        self._task_config = TASKS[task]
        self._canvas_w, self._canvas_h = self._task_config["canvas"]
        self._modules = [{**m} for m in self._task_config["modules"]]
        self._placed = []
        self._current_idx = 0
        self._done = False
        self._state = ChipFloorplannerState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            task_name=task,
        )
        return self._make_obs(0.0)

    def step(self, action: ChipFloorplannerAction, **kwargs):
        # Guard: if done OR index out of range, return done
        if self._done or self._current_idx >= len(self._modules):
            self._done = True
            obs = self._make_obs(0.0)
            obs.done = True
            return obs

        self._state.step_count += 1
        module = self._modules[self._current_idx]
        w = module["height"] if action.rotate else module["width"]
        h = module["width"]  if action.rotate else module["height"]

        # Out-of-bounds penalty
        oob = -0.2 if (
            action.x < 0 or action.y < 0 or
            action.x + w > self._canvas_w or
            action.y + h > self._canvas_h
        ) else 0.0

        # Clamp to canvas
        x = max(0, min(action.x, self._canvas_w - w))
        y = max(0, min(action.y, self._canvas_h - h))

        # Overlap penalty: -0.30 per overlap (strict)
        overlap_pen = 0.0
        for pm in self._placed:
            if _overlaps(x, y, w, h, pm["x"], pm["y"], pm["w"], pm["h"]):
                overlap_pen -= 0.30
                self._state.total_overlap_count += 1

        # Place module
        self._placed.append({"id": module["id"], "x": x, "y": y, "w": w, "h": h})
        self._current_idx += 1
        self._state.placed_count = len(self._placed)

        # Wirelength reward
        pd = {m["id"]: m for m in self._placed}
        hpwl = _hpwl(pd, self._task_config["netlist"])
        max_hpwl = (self._canvas_w + self._canvas_h) * len(self._task_config["netlist"])
        wl_reward = -0.25 * (hpwl / max(max_hpwl, 1))

        # Area reward
        max_x = max(m["x"]+m["w"] for m in self._placed)
        max_y = max(m["y"]+m["h"] for m in self._placed)
        bbox = max_x * max_y
        area_reward = -0.15 * (bbox / (self._canvas_w * self._canvas_h))

        # No-overlap bonus
        no_overlap_bonus = 0.1 if self._state.total_overlap_count == 0 else 0.0

        self._state.current_wirelength = hpwl
        self._state.current_bounding_area = float(bbox)

        # Base 0.5 + adjustments, min 0.05 so reward is never 0 for valid placements
        step_reward = 0.5 + wl_reward + area_reward + overlap_pen + oob + no_overlap_bonus
        step_reward = round(max(0.05, min(1.0, step_reward)), 4)

        # Final bonus: all placed with no overlaps
        if self._current_idx >= len(self._modules):
            self._done = True
            if self._state.total_overlap_count == 0:
                step_reward = min(1.0, step_reward + 0.2)

        return self._make_obs(step_reward)

    @property
    def state(self):
        return self._state

    def _make_obs(self, reward):
        remaining = self._modules[self._current_idx:] if not self._done else []
        current = None
        msg = "All modules placed. Episode complete."
        if not self._done and self._current_idx < len(self._modules):
            current = self._modules[self._current_idx]
            msg = (f"Place module {current['id']} "
                   f"({current['width']}x{current['height']}) — "
                   f"avoid overlaps, minimize wire length!")

            # Wire hints for current module
            wire_hints = []
            for net in self._task_config["netlist"]:
                if current["id"] in net:
                    for m_id in net:
                        if m_id != current["id"]:
                            for pm in self._placed:
                                if pm["id"] == m_id:
                                    cx = pm["x"] + pm["w"] // 2
                                    cy = pm["y"] + pm["h"] // 2
                                    wire_hints.append(
                                        f"Place near {pm['id']} at ({cx},{cy})"
                                    )
            if wire_hints:
                msg += " | HINTS: " + "; ".join(wire_hints)

        if self._done:
            final_grade = self.get_final_score()
            msg = f"All modules placed. Episode complete. FINAL_SCORE: {final_grade:.4f}"
        
        return ChipFloorplannerObservation(
            done=self._done,
            reward=reward,
            canvas_width=self._canvas_w,
            canvas_height=self._canvas_h,
            current_module=current,
            placed_modules=[
                {"id": m["id"], "x": m["x"], "y": m["y"],
                 "width": m["w"], "height": m["h"]}
                for m in self._placed
            ],
            modules_remaining=[
                {"id": m["id"], "width": m["width"], "height": m["height"]}
                for m in remaining
            ],
            netlist=self._task_config["netlist"],
            step_number=self._state.step_count,
            total_modules=len(self._modules),
            message=msg,
        )

    def get_final_score(self):
        return grade_floorplan(self._placed, self._task_config)

    def find_safe_position(self, mod_w, mod_h):
        """Shelf-packing algorithm - returns (x, y) that is guaranteed overlap-free."""
        def overlaps_any(px, py, pw, ph):
            for pm in self._placed:
                if not (px + pw <= pm["x"] or pm["x"] + pm["width"] <= px or
                        py + ph <= pm["y"] or pm["y"] + pm["height"] <= py):
                    return True
            return False

        row_y = 0
        while row_y + mod_h <= self._canvas_h:
            col_x = 0
            while col_x + mod_w <= self._canvas_w:
                if not overlaps_any(col_x, row_y, mod_w, mod_h):
                    return col_x, row_y
                col_x += 1
            row_y += 1
        return 0, 0
