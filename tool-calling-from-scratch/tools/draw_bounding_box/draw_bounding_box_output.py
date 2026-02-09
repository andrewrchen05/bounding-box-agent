from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class DrawBoundingBoxOutput:
    """Output result from drawing bounding boxes."""
    output_path: str
    boxes_drawn: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "output_path": self.output_path,
            "boxes_drawn": self.boxes_drawn
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"DrawBoundingBoxOutput(output_path={self.output_path}, boxes_drawn={self.boxes_drawn})"
