"""
Shared pytest fixtures for unit tests.

This module provides common fixtures used across multiple test files,
such as test images, temporary directories, and tool instances.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from PIL import Image


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files.
    
    Yields:
        str: Path to temporary directory
        
    The directory is automatically cleaned up after the test.
    """
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def test_image(temp_dir):
    """
    Create a simple test image for testing.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        tuple: (image_path, width, height) where image_path is the path to the test image
    """
    width, height = 100, 100
    image = Image.new('RGB', (width, height), color='white')
    image_path = os.path.join(temp_dir, "test_image.png")
    image.save(image_path)
    return image_path, width, height


@pytest.fixture
def test_image_large(temp_dir):
    """
    Create a larger test image for testing coordinate scaling.
    
    Args:
        temp_dir: Temporary directory fixture
        
    Returns:
        tuple: (image_path, width, height) where image_path is the path to the test image
    """
    width, height = 1920, 1080
    image = Image.new('RGB', (width, height), color='white')
    image_path = os.path.join(temp_dir, "test_image_large.png")
    image.save(image_path)
    return image_path, width, height


@pytest.fixture
def sample_boxes_list():
    """
    Sample bounding boxes in list format (recommended format).
    Uses normalized coordinates (0.0 to 1.0) as required by BoundingBox class.
    
    Returns:
        list: List of box dictionaries with normalized xyxy coordinates
    """
    return [
        {
            "xyxy": [0.1, 0.2, 0.3, 0.4],  # Normalized coordinates
            "confidence": 0.95,
            "label": "button"
        },
        {
            "xyxy": [0.5, 0.6, 0.7, 0.8],  # Normalized coordinates
            "confidence": 0.87
        }
    ]


@pytest.fixture
def sample_boxes_bbox_output():
    """
    Sample bounding boxes in BoundingBoxOutput format.
    Uses normalized coordinates (0.0 to 1.0) as required by BoundingBox class.
    
    Returns:
        dict: BoundingBoxOutput dictionary with width, height, and boxes keys
    """
    return {
        "width": 1920,
        "height": 1080,
        "boxes": [
            {
                "xyxy": [0.219, 0.287, 0.320, 0.338],  # Normalized: 420/1920, 310/1080, etc.
                "confidence": 0.92
            },
            {
                "xyxy": [0.052, 0.185, 0.156, 0.370],  # Normalized: 100/1920, 200/1080, etc.
                "confidence": 0.85
            }
        ]
    }


@pytest.fixture
def sample_boxes_normalized():
    """
    Sample bounding boxes with normalized coordinates (0.0 to 1.0).
    
    Returns:
        list: List of box dictionaries with normalized xyxy coordinates
    """
    return [
        {
            "xyxy": [0.1, 0.2, 0.3, 0.4],
            "confidence": 0.95
        },
        {
            "xyxy": [0.5, 0.6, 0.7, 0.8],
            "confidence": 0.87
        }
    ]
