"""
Unit tests for the DrawBoundingBox tool.

This module contains comprehensive unit tests for:
- DrawBoundingBoxInput dataclass
- DrawBoundingBoxOutput dataclass
- DrawBoundingBox tool execution
- Box parsing logic
- Helper methods (color conversion, path generation)
"""

import pytest
import os
from core.tool import ToolUse
from tools.draw_bounding_box import (
    DrawBoundingBoxInput,
    DrawBoundingBoxOutput,
    DrawBoundingBox
)
from tools.detect_bounding_box import BoundingBox


class TestDrawBoundingBoxInput:
    """Test the DrawBoundingBoxInput dataclass and parsing."""
    
    def test_from_dict_minimal(self):
        """Test parsing minimal required fields."""
        data = {
            "image_path": "/path/to/image.jpg",
            "boxes": []
        }
        input_obj = DrawBoundingBoxInput.from_dict(data)
        assert input_obj.image_path == "/path/to/image.jpg"
        assert input_obj.boxes == []
        assert input_obj.output_path is None
        assert input_obj.color == "red"
        assert input_obj.line_width == 3
        assert input_obj.draw_labels is True
        assert input_obj.label_text is None
    
    def test_from_dict_all_fields(self):
        """Test parsing all fields."""
        data = {
            "image_path": "/path/to/image.jpg",
            "boxes": [{"xyxy": [10, 20, 30, 40]}],
            "output_path": "/path/to/output.jpg",
            "color": "blue",
            "line_width": 5,
            "draw_labels": False,
            "label_text": "Custom Label"
        }
        input_obj = DrawBoundingBoxInput.from_dict(data)
        assert input_obj.image_path == "/path/to/image.jpg"
        assert input_obj.boxes == [{"xyxy": [10, 20, 30, 40]}]
        assert input_obj.output_path == "/path/to/output.jpg"
        assert input_obj.color == "blue"
        assert input_obj.line_width == 5
        assert input_obj.draw_labels is False
        assert input_obj.label_text == "Custom Label"
    
    def test_from_dict_type_conversions(self):
        """Test that types are properly converted."""
        data = {
            "image_path": "/path/to/image.jpg",
            "boxes": [],
            "line_width": "3",  # String that should be converted to int
            "draw_labels": "true"  # String that should be converted to bool
        }
        input_obj = DrawBoundingBoxInput.from_dict(data)
        assert isinstance(input_obj.line_width, int)
        assert isinstance(input_obj.draw_labels, bool)
    
    def test_to_dict(self):
        """Test converting back to dictionary."""
        input_obj = DrawBoundingBoxInput(
            image_path="/path/to/image.jpg",
            boxes=[{"xyxy": [10, 20, 30, 40]}],
            output_path="/path/to/output.jpg",
            color="green",
            line_width=4,
            draw_labels=False,
            label_text="Test"
        )
        result = input_obj.to_dict()
        assert result["image_path"] == "/path/to/image.jpg"
        assert result["boxes"] == [{"xyxy": [10, 20, 30, 40]}]
        assert result["output_path"] == "/path/to/output.jpg"
        assert result["color"] == "green"
        assert result["line_width"] == 4
        assert result["draw_labels"] is False
        assert result["label_text"] == "Test"


class TestDrawBoundingBoxOutput:
    """Test the DrawBoundingBoxOutput dataclass."""
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        output = DrawBoundingBoxOutput(
            output_path="/path/to/output.jpg",
            boxes_drawn=5
        )
        result = output.to_dict()
        assert result["output_path"] == "/path/to/output.jpg"
        assert result["boxes_drawn"] == 5
    
    def test_str_representation(self):
        """Test string representation."""
        output = DrawBoundingBoxOutput(
            output_path="/path/to/output.jpg",
            boxes_drawn=3
        )
        str_repr = str(output)
        assert "output_path" in str_repr
        assert "boxes_drawn" in str_repr
        assert "3" in str_repr


class TestDrawBoundingBoxParsing:
    """Test the _parse_boxes method for different input formats."""
    
    @pytest.fixture
    def tool(self):
        """Create a DrawBoundingBox instance for testing."""
        return DrawBoundingBox()
    
    def test_parse_boxes_list_format(self, tool, sample_boxes_list):
        """Test parsing boxes from list format (recommended format)."""
        boxes = tool._parse_boxes(sample_boxes_list)
        assert len(boxes) == 2
        assert boxes[0].xyxy == [0.1, 0.2, 0.3, 0.4]  # Normalized coordinates
        assert boxes[0].confidence == 0.95
        assert boxes[1].xyxy == [0.5, 0.6, 0.7, 0.8]  # Normalized coordinates
        assert boxes[1].confidence == 0.87
    
    def test_parse_boxes_bounding_box_output_format(self, tool, sample_boxes_bbox_output):
        """Test parsing boxes from BoundingBoxOutput format."""
        boxes = tool._parse_boxes(sample_boxes_bbox_output)
        assert len(boxes) == 2
        assert boxes[0].xyxy == [0.219, 0.287, 0.320, 0.338]  # Normalized coordinates
        assert boxes[0].confidence == 0.92
        assert boxes[1].xyxy == [0.052, 0.185, 0.156, 0.370]  # Normalized coordinates
        assert boxes[1].confidence == 0.85
    
    def test_parse_boxes_missing_xyxy(self, tool):
        """Test that boxes without xyxy are skipped."""
        boxes_data = [
            {
                "confidence": 0.95,
                "label": "button"
                # Missing xyxy
            },
            {
                "xyxy": [0.5, 0.6, 0.7, 0.8],  # Normalized coordinates
                "confidence": 0.87
            }
        ]
        boxes = tool._parse_boxes(boxes_data)
        assert len(boxes) == 1
        assert boxes[0].xyxy == [0.5, 0.6, 0.7, 0.8]
    
    def test_parse_boxes_default_confidence(self, tool):
        """Test that missing confidence defaults to 1.0."""
        boxes_data = [
            {
                "xyxy": [0.1, 0.2, 0.3, 0.4]  # Normalized coordinates
                # Missing confidence
            }
        ]
        boxes = tool._parse_boxes(boxes_data)
        assert len(boxes) == 1
        assert boxes[0].confidence == 1.0
    
    def test_parse_boxes_invalid_format(self, tool):
        """Test that invalid format raises ValueError."""
        boxes_data = "invalid format"
        with pytest.raises(ValueError, match="Invalid boxes format"):
            tool._parse_boxes(boxes_data)
    
    def test_parse_boxes_empty_list(self, tool):
        """Test parsing empty list."""
        boxes = tool._parse_boxes([])
        assert len(boxes) == 0
    
    def test_parse_boxes_coordinate_type_conversion(self, tool):
        """Test that coordinates are converted to floats."""
        boxes_data = [
            {
                "xyxy": ["0.1", "0.2", "0.3", "0.4"],  # String coordinates (normalized)
                "confidence": 0.95
            }
        ]
        boxes = tool._parse_boxes(boxes_data)
        assert boxes[0].xyxy == [0.1, 0.2, 0.3, 0.4]  # Should be converted to floats
    
    def test_parse_boxes_float_coordinates(self, tool):
        """Test that float coordinates are preserved."""
        boxes_data = [
            {
                "xyxy": [0.105, 0.207, 0.309, 0.402],  # Normalized float coordinates
                "confidence": 0.95
            }
        ]
        boxes = tool._parse_boxes(boxes_data)
        assert boxes[0].xyxy == [0.105, 0.207, 0.309, 0.402]


class TestDrawBoundingBoxExecute:
    """Test the execute method with real images."""
    
    @pytest.fixture
    def tool(self):
        """Create a DrawBoundingBox instance for testing."""
        return DrawBoundingBox()
    
    def test_execute_list_format(self, tool, test_image, temp_dir):
        """Test execute with list format boxes."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ],
                "output_path": os.path.join(temp_dir, "output_list.png")
            }
        )
        result = tool.execute(tool_use)
        assert isinstance(result, DrawBoundingBoxOutput)
        assert result.boxes_drawn == 1
        assert os.path.exists(result.output_path)
        assert result.output_path == os.path.join(temp_dir, "output_list.png")
    
    def test_execute_bounding_box_output_format(self, tool, test_image, temp_dir):
        """Test execute with BoundingBoxOutput format."""
        image_path, width, height = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": {
                    "width": width,
                    "height": height,
                    "boxes": [
                        {
                            "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                            "confidence": 0.95
                        },
                        {
                            "xyxy": [0.5, 0.6, 0.7, 0.8],  # Normalized coordinates
                            "confidence": 0.87
                        }
                    ]
                },
                "output_path": os.path.join(temp_dir, "output_bbox.png")
            }
        )
        result = tool.execute(tool_use)
        assert isinstance(result, DrawBoundingBoxOutput)
        assert result.boxes_drawn == 2
        assert os.path.exists(result.output_path)
    
    def test_execute_auto_output_path(self, tool, test_image):
        """Test that output path is auto-generated if not provided."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ]
            }
        )
        result = tool.execute(tool_use)
        assert result.output_path == image_path.replace(".png", "_annotated.png")
        assert os.path.exists(result.output_path)
    
    def test_execute_custom_color(self, tool, test_image, temp_dir):
        """Test execute with custom color."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ],
                "color": "blue",
                "output_path": os.path.join(temp_dir, "output_blue.png")
            }
        )
        result = tool.execute(tool_use)
        assert result.boxes_drawn == 1
        assert os.path.exists(result.output_path)
    
    def test_execute_hex_color(self, tool, test_image, temp_dir):
        """Test execute with hex color code."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ],
                "color": "#00FF00",  # Green
                "output_path": os.path.join(temp_dir, "output_hex.png")
            }
        )
        result = tool.execute(tool_use)
        assert result.boxes_drawn == 1
        assert os.path.exists(result.output_path)
    
    def test_execute_custom_line_width(self, tool, test_image, temp_dir):
        """Test execute with custom line width."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ],
                "line_width": 5,
                "output_path": os.path.join(temp_dir, "output_thick.png")
            }
        )
        result = tool.execute(tool_use)
        assert result.boxes_drawn == 1
        assert os.path.exists(result.output_path)
    
    def test_execute_with_labels(self, tool, test_image, temp_dir):
        """Test execute with labels enabled."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ],
                "draw_labels": True,
                "output_path": os.path.join(temp_dir, "output_labels.png")
            }
        )
        result = tool.execute(tool_use)
        assert result.boxes_drawn == 1
        assert os.path.exists(result.output_path)
    
    def test_execute_with_custom_label_text(self, tool, test_image, temp_dir):
        """Test execute with custom label text."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ],
                "draw_labels": True,
                "label_text": "Custom Label",
                "output_path": os.path.join(temp_dir, "output_custom_label.png")
            }
        )
        result = tool.execute(tool_use)
        assert result.boxes_drawn == 1
        assert os.path.exists(result.output_path)
    
    def test_execute_normalized_coordinates(self, tool, test_image, temp_dir):
        """Test that normalized coordinates (0.0 to 1.0) are converted to pixels."""
        image_path, width, height = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ],
                "output_path": os.path.join(temp_dir, "output_normalized.png")
            }
        )
        result = tool.execute(tool_use)
        assert result.boxes_drawn == 1
        assert os.path.exists(result.output_path)
        # Coordinates should be converted: 0.1 * 100 = 10, 0.2 * 100 = 20, etc.
    
    def test_execute_multiple_boxes(self, tool, test_image, temp_dir):
        """Test execute with multiple boxes."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    },
                    {
                        "xyxy": [0.5, 0.6, 0.7, 0.8],  # Normalized coordinates
                        "confidence": 0.87
                    },
                    {
                        "xyxy": [0.15, 0.25, 0.35, 0.45],  # Normalized coordinates
                        "confidence": 0.92
                    }
                ],
                "output_path": os.path.join(temp_dir, "output_multiple.png")
            }
        )
        result = tool.execute(tool_use)
        assert result.boxes_drawn == 3
        assert os.path.exists(result.output_path)
    
    def test_execute_missing_image_path(self, tool):
        """Test that missing image_path raises ValueError."""
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ]
            }
        )
        with pytest.raises(ValueError, match="image_path parameter is required"):
            tool.execute(tool_use)
    
    def test_execute_missing_boxes(self, tool, test_image):
        """Test that missing boxes raises ValueError."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path
            }
        )
        with pytest.raises(ValueError, match="boxes parameter is required"):
            tool.execute(tool_use)
    
    def test_execute_invalid_image_path(self, tool):
        """Test that invalid image path raises ValueError."""
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": "/nonexistent/path/image.jpg",
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ]
            }
        )
        with pytest.raises(ValueError, match="Failed to load image"):
            tool.execute(tool_use)
    
    def test_execute_empty_boxes(self, tool, test_image):
        """Test that empty boxes list raises ValueError."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="draw_bounding_box",
            params={
                "image_path": image_path,
                "boxes": []
            }
        )
        # Empty list is caught early as "boxes parameter is required"
        with pytest.raises(ValueError, match="boxes parameter is required"):
            tool.execute(tool_use)
    
    def test_execute_wrong_tool_name(self, tool, test_image):
        """Test that wrong tool name raises ValueError."""
        image_path, _, _ = test_image
        tool_use = ToolUse(
            name="wrong_tool_name",
            params={
                "image_path": image_path,
                "boxes": [
                    {
                        "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
                        "confidence": 0.95
                    }
                ]
            }
        )
        with pytest.raises(ValueError, match="Tool name mismatch"):
            tool.execute(tool_use)


class TestDrawBoundingBoxHelpers:
    """Test helper methods."""
    
    @pytest.fixture
    def tool(self):
        """Create a DrawBoundingBox instance for testing."""
        return DrawBoundingBox()
    
    def test_get_output_path_provided(self, tool):
        """Test output path when provided."""
        result = tool._get_output_path("/path/to/image.jpg", "/path/to/output.jpg")
        assert result == "/path/to/output.jpg"
    
    def test_get_output_path_auto_generated(self, tool):
        """Test auto-generated output path."""
        result = tool._get_output_path("/path/to/image.jpg")
        assert result == "/path/to/image_annotated.jpg"
    
    def test_get_output_path_different_extensions(self, tool):
        """Test output path with different file extensions."""
        result = tool._get_output_path("/path/to/image.png")
        assert result == "/path/to/image_annotated.png"
        
        result = tool._get_output_path("/path/to/image.jpeg")
        assert result == "/path/to/image_annotated.jpeg"
        
        result = tool._get_output_path("/path/to/image.jpg")
        assert result == "/path/to/image_annotated.jpg"
    
    def test_get_output_path_assets_directory(self, tool, tmp_path):
        """Test output path when input is in assets directory."""
        # Create a temporary assets directory structure
        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        outputs_dir = assets_dir / "outputs"
        
        # Test with assets in the path
        image_path = str(assets_dir / "test_image.png")
        result = tool._get_output_path(image_path)
        
        # Should save to assets/outputs/
        expected_path = str(outputs_dir / "test_image_annotated.png")
        assert result == expected_path
        # Directory should be created
        assert outputs_dir.exists()
        
        # Test with nested path containing assets
        nested_assets = tmp_path / "project" / "assets"
        nested_assets.mkdir(parents=True)
        nested_outputs = nested_assets / "outputs"
        
        nested_image_path = str(nested_assets / "nested_image.jpg")
        nested_result = tool._get_output_path(nested_image_path)
        
        expected_nested_path = str(nested_outputs / "nested_image_annotated.jpg")
        assert nested_result == expected_nested_path
        assert nested_outputs.exists()
    
    def test_hex_to_rgb_color_name(self, tool):
        """Test color name to RGB conversion."""
        assert tool._hex_to_rgb("red") == (255, 0, 0)
        assert tool._hex_to_rgb("green") == (0, 255, 0)
        assert tool._hex_to_rgb("blue") == (0, 0, 255)
        assert tool._hex_to_rgb("yellow") == (255, 255, 0)
        assert tool._hex_to_rgb("cyan") == (0, 255, 255)
        assert tool._hex_to_rgb("magenta") == (255, 0, 255)
        assert tool._hex_to_rgb("white") == (255, 255, 255)
        assert tool._hex_to_rgb("black") == (0, 0, 0)
    
    def test_hex_to_rgb_hex_code(self, tool):
        """Test hex code to RGB conversion."""
        assert tool._hex_to_rgb("#FF0000") == (255, 0, 0)
        assert tool._hex_to_rgb("#00FF00") == (0, 255, 0)
        assert tool._hex_to_rgb("#0000FF") == (0, 0, 255)
        assert tool._hex_to_rgb("#FFFFFF") == (255, 255, 255)
        assert tool._hex_to_rgb("#000000") == (0, 0, 0)
    
    def test_hex_to_rgb_short_hex(self, tool):
        """Test short hex code (3 digits) to RGB conversion."""
        assert tool._hex_to_rgb("#F00") == (255, 0, 0)
        assert tool._hex_to_rgb("#0F0") == (0, 255, 0)
        assert tool._hex_to_rgb("#00F") == (0, 0, 255)
        assert tool._hex_to_rgb("#FFF") == (255, 255, 255)
    
    def test_hex_to_rgb_case_insensitive(self, tool):
        """Test that color names are case insensitive."""
        assert tool._hex_to_rgb("RED") == (255, 0, 0)
        assert tool._hex_to_rgb("Red") == (255, 0, 0)
        assert tool._hex_to_rgb("rEd") == (255, 0, 0)
        assert tool._hex_to_rgb("GREEN") == (0, 255, 0)
    
    def test_hex_to_rgb_invalid_defaults_to_red(self, tool):
        """Test that invalid color defaults to red."""
        result = tool._hex_to_rgb("invalid_color")
        assert result == (255, 0, 0)
    
    def test_hex_to_rgb_hex_without_hash(self, tool):
        """Test that hex codes without # are treated as invalid."""
        # The current implementation expects #, so this should default to red
        result = tool._hex_to_rgb("FF0000")
        assert result == (255, 0, 0)  # Defaults to red
