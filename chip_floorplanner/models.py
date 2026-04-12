from typing import List, Optional, Dict, Any
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field, ConfigDict


class ChipFloorplannerAction(Action):
    """
    Action model for placing a circuit module on the floorplan.
    The (x, y) coordinates represent the top-left corner of the module.
    """
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={"example": {"x": 5, "y": 3, "rotate": False}}
    )

    x: int = Field(0, description="X coordinate (left edge) for module placement. Range: [0, canvas_width - module_width].")
    y: int = Field(0, description="Y coordinate (top edge) for module placement. Range: [0, canvas_height - module_height].")
    rotate: bool = Field(False, description="If true, swaps width and height of the module before placement.")


class ChipFloorplannerObservation(Observation):
    """
    Detailed observation of the current chip floorplan state.
    """
    canvas_width: int = Field(0, description="Total width of the available chip canvas.")
    canvas_height: int = Field(0, description="Total height of the available chip canvas.")
    current_module: Optional[Dict[str, Any]] = Field(None, description="Metadata of the module currently being placed: {'id': str, 'width': int, 'height': int}.")
    placed_modules: List[Dict[str, Any]] = Field(default_factory=list, description="List of modules already placed: [{'id', 'x', 'y', 'width', 'height'}].")
    modules_remaining: List[Dict[str, Any]] = Field(default_factory=list, description="Queue of modules yet to be placed.")
    netlist: List[List[str]] = Field(default_factory=list, description="Connectivity graph. Each list of module IDs represents a 'net' that should be placed close together to minimize wire length.")
    step_number: int = Field(0, description="Current step index (1-based).")
    total_modules: int = Field(0, description="Total number of modules in this task.")
    message: str = Field("", description="Environmental feedback, legalization hints, or final scoring results.")


class ChipFloorplannerState(State):
    """
    Internal environment state tracking persistent metrics for grading.
    """
    task_name: str = Field("easy", description="The difficulty tier.")
    placed_count: int = Field(0, description="Number of modules placed so far.")
    total_overlap_count: int = Field(0, description="Aggregated count of physically overlapping module pairs (MUST be zero for high score).")
    current_bounding_area: float = Field(0.0, description="Total area of the bounding box spanning all placed modules.")
    current_wirelength: float = Field(0.0, description="Total Half-Perimeter Wire Length (HPWL) of all connections.")
