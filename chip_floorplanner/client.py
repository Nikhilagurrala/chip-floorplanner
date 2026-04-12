from openenv.core.env_client import EnvClient
from openenv.core.env_client import StepResult
from .models import (
    ChipFloorplannerAction,
    ChipFloorplannerObservation,
    ChipFloorplannerState,
)


class ChipFloorplannerEnv(
    EnvClient[ChipFloorplannerAction, ChipFloorplannerObservation, ChipFloorplannerState]
):
    """Client for Chip Floorplanner environment."""

    def _step_payload(self, action: ChipFloorplannerAction) -> dict:
        return {"x": action.x, "y": action.y, "rotate": action.rotate}

    def _parse_result(self, payload: dict) -> StepResult[ChipFloorplannerObservation]:
        obs = ChipFloorplannerObservation(**payload["observation"])
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> ChipFloorplannerState:
        return ChipFloorplannerState(**payload)
