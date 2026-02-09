from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class DrawBoundingBoxInput:
    """Input parameters for drawing bounding boxes on an image."""
    image_path: str
    boxes: Union[List[Dict[str, Any]], Dict[str, Any]]  # Can be list of boxes or BoundingBoxOutput dict
    output_path: Optional[str] = None
    color: str = "red"
    line_width: int = 3
    draw_labels: bool = True
    label_text: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DrawBoundingBoxInput":
        """Create DrawBoundingBoxInput from a dictionary."""
        return cls(
            image_path=data.get("image_path", ""),
            boxes=data.get("boxes", []),
            output_path=data.get("output_path"),
            color=data.get("color", "red"),
            line_width=int(data.get("line_width", 3)),
            draw_labels=bool(data.get("draw_labels", True)),
            label_text=data.get("label_text")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "image_path": self.image_path,
            "boxes": self.boxes,
            "output_path": self.output_path,
            "color": self.color,
            "line_width": self.line_width,
            "draw_labels": self.draw_labels,
            "label_text": self.label_text
        }
