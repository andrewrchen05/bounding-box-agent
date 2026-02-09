"""
Unit tests for the DetectBoundingBox tool.

This module contains critical unit tests for:
- BoundingBox dataclass (validation logic)
- DetectBoundingBox tool execution
- JSON extraction from LLM responses
"""

import pytest
from unittest.mock import Mock
from core.tool import ToolUse
from tools.detect_bounding_box import (
    DetectBoundingBox,
    BoundingBox,
    BoundingBoxOutput
)


@pytest.fixture
def mock_model_provider():
    """Create a mock model provider for testing."""
    provider = Mock()
    provider.generate_response = Mock(return_value='{"boxes": []}')
    return provider


class TestBoundingBox:
    """Test the BoundingBox dataclass validation logic."""
    
    def test_validation_errors(self):
        """Test that invalid confidence and coordinates raise ValueError."""
        # Test valid box first
        box = BoundingBox(confidence=0.95, xyxy=[0.1, 0.2, 0.3, 0.4])
        assert box.confidence == 0.95
        assert box.xyxy == [0.1, 0.2, 0.3, 0.4]
        
        # Test confidence < 0.0
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            BoundingBox(confidence=-0.1, xyxy=[0.1, 0.2, 0.3, 0.4])
        
        # Test confidence > 1.0
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            BoundingBox(confidence=1.1, xyxy=[0.1, 0.2, 0.3, 0.4])
        
        # Test xyxy length != 4
        with pytest.raises(ValueError, match="xyxy must contain exactly 4 coordinates"):
            BoundingBox(confidence=0.9, xyxy=[0.1, 0.2, 0.3])
        
        # Test coordinate < 0.0
        with pytest.raises(ValueError, match="Normalized coordinates must be between 0.0 and 1.0"):
            BoundingBox(confidence=0.9, xyxy=[-0.1, 0.2, 0.3, 0.4])
        
        # Test coordinate > 1.0
        with pytest.raises(ValueError, match="Normalized coordinates must be between 0.0 and 1.0"):
            BoundingBox(confidence=0.9, xyxy=[0.1, 0.2, 0.3, 1.1])


class TestDetectBoundingBoxExtractJson:
    """Test the _extract_json_from_response method."""
    
    @pytest.fixture
    def tool(self, mock_model_provider):
        """Create a DetectBoundingBox instance for testing."""
        return DetectBoundingBox(model_provider=mock_model_provider)
    
    def test_extract_json_markdown_code_block(self, tool):
        """Test extracting JSON from markdown code block."""
        response = '```json\n{"boxes": [{"confidence": 0.9, "xyxy": [0.1, 0.2, 0.3, 0.4]}]}\n```'
        result = tool._extract_json_from_response(response)
        assert "boxes" in result
        assert len(result["boxes"]) == 1
        assert result["boxes"][0]["confidence"] == 0.9
    
    def test_extract_json_invalid_json_raises_error(self, tool):
        """Test that invalid JSON raises ValueError."""
        response = '{"boxes": [invalid json}'
        with pytest.raises(ValueError, match="Failed to parse JSON from response"):
            tool._extract_json_from_response(response)


class TestDetectBoundingBoxExecute:
    """Test the execute method with mocked model provider."""
    
    @pytest.fixture
    def tool(self, mock_model_provider):
        """Create a DetectBoundingBox instance for testing."""
        return DetectBoundingBox(model_provider=mock_model_provider)
    
    def test_execute_successful_detection(self, tool, test_image, mock_model_provider):
        """Test execute with successful detection."""
        image_path, width, height = test_image
        mock_model_provider.generate_response.return_value = '{"boxes": [{"confidence": 0.92, "xyxy": [0.1, 0.2, 0.3, 0.4]}]}'
        
        tool_use = ToolUse(
            name="detect_bounding_box",
            params={
                "image_path": image_path,
                "label": "button"
            }
        )
        result = tool.execute(tool_use)
        
        assert isinstance(result, BoundingBoxOutput)
        assert result.width == width
        assert result.height == height
        assert len(result.boxes) == 1
        assert result.boxes[0].confidence == 0.92
        assert result.boxes[0].xyxy == [0.1, 0.2, 0.3, 0.4]
    
    def test_execute_missing_image_path(self, tool):
        """Test that missing image_path raises ValueError."""
        tool_use = ToolUse(
            name="detect_bounding_box",
            params={
                "label": "button"
            }
        )
        with pytest.raises(ValueError, match="image_path parameter is required"):
            tool.execute(tool_use)
    
    def test_execute_invalid_image_path(self, tool):
        """Test that invalid image path raises ValueError."""
        tool_use = ToolUse(
            name="detect_bounding_box",
            params={
                "image_path": "/nonexistent/path/image.jpg",
                "label": "button"
            }
        )
        with pytest.raises(ValueError, match="Failed to load image"):
            tool.execute(tool_use)
    
    def test_execute_model_provider_error(self, tool, test_image, mock_model_provider):
        """Test that model provider errors raise RuntimeError."""
        image_path, _, _ = test_image
        mock_model_provider.generate_response.side_effect = Exception("API Error")
        
        tool_use = ToolUse(
            name="detect_bounding_box",
            params={
                "image_path": image_path,
                "label": "button"
            }
        )
        with pytest.raises(RuntimeError, match="Failed to call Gemini API"):
            tool.execute(tool_use)
    
    def test_execute_invalid_json_response(self, tool, test_image, mock_model_provider):
        """Test that invalid JSON response raises ValueError."""
        image_path, _, _ = test_image
        mock_model_provider.generate_response.return_value = 'invalid json response'
        
        tool_use = ToolUse(
            name="detect_bounding_box",
            params={
                "image_path": image_path,
                "label": "button"
            }
        )
        with pytest.raises(ValueError, match="Failed to parse bounding box response"):
            tool.execute(tool_use)
