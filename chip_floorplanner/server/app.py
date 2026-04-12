import sys
import os
sys.path.insert(0, os.getcwd())

import gradio as gr
from openenv.core.env_server import create_fastapi_app
from chip_floorplanner.models import ChipFloorplannerAction, ChipFloorplannerObservation
from chip_floorplanner.server.environment import ChipFloorplannerEnvironment, _overlaps

# --- Shared Env for UI ---
_env = ChipFloorplannerEnvironment()

app = create_fastapi_app(
    ChipFloorplannerEnvironment,
    ChipFloorplannerAction,
    ChipFloorplannerObservation,
)

COLORS = {
    "A":"#FF6B6B","B":"#4ECDC4","C":"#45B7D1","D":"#96CEB4",
    "E":"#FFEAA7","F":"#DDA0DD","G":"#98D8C8","H":"#F7DC6F",
    "I":"#BB8FCE","J":"#85C1E9","K":"#F0B27A","L":"#82E0AA",
}

# --- UI Logic ---

def get_current_obs():
    return _env._make_obs(_env._state.step_reward if hasattr(_env._state, 'step_reward') else 0.0)

def ui_reset(task):
    obs = _env.reset(task=task)
    # Update sliders to match task size
    max_x = _env._canvas_w - (obs.current_module['width'] if obs.current_module else 1)
    max_y = _env._canvas_h - (obs.current_module['height'] if obs.current_module else 1)
    return (
        build_state(obs), 
        build_canvas(obs), 
        gr.update(maximum=max_x, value=0), 
        gr.update(maximum=max_y, value=0),
        gr.update(visible=not obs.done)
    )

def ui_step(x, y, rotate):
    if _env._done:
        return build_state(get_current_obs()), build_canvas(get_current_obs()), gr.update(), gr.update(), gr.update(visible=False)
    
    obs = _env.step(ChipFloorplannerAction(x=int(x), y=int(y), rotate=bool(rotate)))
    
    # Prep for next module
    if not obs.done:
        mod = obs.current_module
        max_x = _env._canvas_w - (mod['height'] if rotate else mod['width'])
        max_y = _env._canvas_h - (mod['width']  if rotate else mod['height'])
        return build_state(obs), build_canvas(obs), gr.update(maximum=max_x, value=0), gr.update(maximum=max_y, value=0), gr.update(visible=True)
    else:
        return build_state(obs), build_canvas(obs), gr.update(), gr.update(), gr.update(visible=False)

def ui_preview(x, y, rotate):
    obs = get_current_obs()
    if obs.done or not obs.current_module:
        return build_canvas(obs)
    
    # Create a ghost module for the preview
    mod = obs.current_module
    pw = mod['height'] if rotate else mod['width']
    ph = mod['width']  if rotate else mod['height']
    
    ghost = {"id": mod['id'], "x": int(x), "y": int(y), "width": pw, "height": ph, "is_ghost": True}
    
    # Check for overlaps
    has_overlap = False
    for pm in obs.placed_modules:
        if _overlaps(ghost['x'], ghost['y'], ghost['width'], ghost['height'],
                     pm['x'], pm['y'], pm['width'], pm['height']):
            has_overlap = True
            break
    
    ghost["color"] = "#FF4444" if has_overlap else "#44FF44"
    return build_canvas(obs, ghost=ghost)

def ui_autosnap(rotate):
    obs = get_current_obs()
    if obs.done or not obs.current_module:
        return gr.update(), gr.update()
    
    mod = obs.current_module
    pw = mod['height'] if rotate else mod['width']
    ph = mod['width']  if rotate else mod['height']
    
    sx, sy = _env.find_safe_position(pw, ph)
    return gr.update(value=sx), gr.update(value=sy)

def build_state(obs):
    lines = [
        f"Task: {obs.task_name.upper() if hasattr(obs, 'task_name') else 'N/A'}",
        f"Canvas : {obs.canvas_width} x {obs.canvas_height}",
        f"Placed : {len(obs.placed_modules)} / {obs.total_modules}",
        f"Last Reward : {obs.reward:.4f}",
        f"Final Score : {_env.get_final_score():.4f}",
        f"Overlaps: {_env._state.total_overlap_count}",
        f"Wirelength: {_env._state.current_wirelength:.1f}",
        f"Area Footprint: {_env._state.current_bounding_area:.0f}",
        "",
        f"MESSAGE: {obs.message}",
    ]
    return "\n".join(lines)

def build_canvas(obs, ghost=None):
    cw, ch = obs.canvas_width, obs.canvas_height
    cell = max(10, min(25, 500 // max(cw, ch)))
    svg_w, svg_h = cw * cell, ch * cell
    
    out = f'<rect width="{svg_w}" height="{svg_h}" fill="#0f172a" />'
    
    # Grid lines
    for ry in range(ch + 1):
        out += f'<line x1="0" y1="{ry*cell}" x2="{svg_w}" y2="{ry*cell}" stroke="#1e293b" stroke-width="0.5"/>'
    for rx in range(cw + 1):
        out += f'<line x1="{rx*cell}" y1="0" x2="{rx*cell}" y2="{svg_h}" stroke="#1e293b" stroke-width="0.5"/>'

    # Placed Modules
    for m in obs.placed_modules:
        color = COLORS.get(m["id"], "#64748b")
        x,y,w,h = m["x"]*cell, m["y"]*cell, m["width"]*cell, m["height"]*cell
        out += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" fill-opacity="0.9" stroke="#fff" stroke-width="1.5" rx="3"/>'
        fs = max(10, cell)
        out += f'<text x="{x+w//2}" y="{y+h//2+fs//3}" text-anchor="middle" font-size="{fs}" font-family="monospace" font-weight="bold" fill="#000">{m["id"]}</text>'
    
    # Connectivity
    pd = {m["id"]: m for m in obs.placed_modules}
    drawn = set()
    for net in obs.netlist:
        for i in range(len(net)):
            for j in range(i+1, len(net)):
                a, b = net[i], net[j]
                if a in pd and b in pd:
                    pair = tuple(sorted([a,b]))
                    if pair not in drawn:
                        drawn.add(pair)
                        x1, y1 = (pd[a]["x"]+pd[a]["width"]/2)*cell, (pd[a]["y"]+pd[a]["height"]/2)*cell
                        x2, y2 = (pd[b]["x"]+pd[b]["width"]/2)*cell, (pd[b]["y"]+pd[b]["height"]/2)*cell
                        out += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#f43f5e" stroke-width="2" stroke-dasharray="5,5" opacity="0.6"/>'

    # Ghost Preview
    if ghost:
        gx, gy, gw, gh = ghost["x"]*cell, ghost["y"]*cell, ghost["width"]*cell, ghost["height"]*cell
        out += f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" fill="{ghost["color"]}" fill-opacity="0.3" stroke="{ghost["color"]}" stroke-width="3" stroke-dasharray="4" rx="3"/>'
        out += f'<text x="{gx+gw//2}" y="{gy+gh//2}" text-anchor="middle" font-size="16" font-family="monospace" fill="{ghost["color"]}" font-weight="bold">{ghost["id"]}?</text>'

    return f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">{out}</svg>'

# --- UI Layout ---

with gr.Blocks(title="Chip Floorplanner Pro", theme=gr.themes.Default(primary_hue="indigo")) as demo:
    gr.Markdown("# 🧩 Chip Floorplanner Pro")
    gr.Markdown("Place circuit modules efficiently. **Green Ghost** = Safe | **Red Ghost** = Overlap.")
    
    with gr.Row():
        with gr.Column(scale=1):
            task_dd   = gr.Dropdown(["easy","medium","hard"], value="easy", label="1. Select Task")
            reset_btn = gr.Button("Reset Environment", variant="primary")
            
            with gr.Group(visible=True) as controls:
                gr.Markdown("### 2. Manual Placement")
                x_sl      = gr.Slider(0, 19, value=0, step=1, label="X Position")
                y_sl      = gr.Slider(0, 19, value=0, step=1, label="Y Position")
                rotate_cb = gr.Checkbox(label="Rotate Module (90°)", value=False)
                
                with gr.Row():
                    snap_btn  = gr.Button("🪄 Find Safe Spot", variant="secondary")
                    step_btn  = gr.Button("✅ Place Module", variant="primary")
            
            gr.Markdown("""
            **Scoring Rules:**
            - 🚫 **Overlap**: 50% penalty (FATAL)
            - 📏 **Wirelength**: 25% reward (keep connected modules close)
            - 📦 **Area**: 20% reward (tight footprints)
            """)
            
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("Visual Floorplan"):
                    canvas_out = gr.HTML()
                with gr.TabItem("Detailed Metrics"):
                    state_box  = gr.Textbox(label="System Output", lines=18, interactive=False, elem_id="state_code")
    
    # Event wiring
    reset_btn.click(ui_reset, inputs=[task_dd], outputs=[state_box, canvas_out, x_sl, y_sl, controls])
    step_btn.click(ui_step,   inputs=[x_sl, y_sl, rotate_cb], outputs=[state_box, canvas_out, x_sl, y_sl, controls])
    snap_btn.click(ui_autosnap, inputs=[rotate_cb], outputs=[x_sl, y_sl])
    
    # Live Preview Triggers
    preview_inputs = [x_sl, y_sl, rotate_cb]
    for inp in preview_inputs:
        inp.change(ui_preview, inputs=preview_inputs, outputs=[canvas_out])
    
    # Initial load
    demo.load(ui_reset, inputs=[task_dd], outputs=[state_box, canvas_out, x_sl, y_sl, controls])

# Mounting
app = gr.mount_gradio_app(app, demo, path="/ui")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
