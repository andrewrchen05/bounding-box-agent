"""
Shared pytest fixtures for integration tests.
"""

import pytest
from unittest.mock import Mock, patch
from core.agent import Agent
from tools.detect_bounding_box import DetectBoundingBox
from tools.draw_bounding_box import DrawBoundingBox
from providers.base import ModelProvider


@pytest.fixture
def mock_llm_provider():
    """
    Create a mock LLM provider that can be configured with response sequences.
    
    Returns:
        Mock ModelProvider instance
    """
    provider = Mock(spec=ModelProvider)
    provider.generate_response = Mock()
    return provider


@pytest.fixture
def agent_with_tools(mock_llm_provider, test_image):
    """
    Create an Agent instance with detect and draw tools, with mocked LLM provider.
    
    Args:
        mock_llm_provider: Mock LLM provider fixture
        test_image: Test image fixture from parent conftest
        
    Returns:
        Agent instance with tools and mocked LLM
    """
    # Create a separate mock for the detect tool's internal provider
    detect_tool_mock_provider = Mock(spec=ModelProvider)
    detect_tool_mock_provider.generate_response = Mock()
    
    # Create tools
    detect_tool = DetectBoundingBox(model_provider=detect_tool_mock_provider)
    draw_tool = DrawBoundingBox()
    
    # Create agent and patch the LLM client
    agent = Agent(tools=[detect_tool, draw_tool])
    agent.llm_client = mock_llm_provider
    
    return agent


@pytest.fixture
def agent_without_tools(mock_llm_provider):
    """
    Create an Agent instance with no tools, with mocked LLM provider.
    
    Args:
        mock_llm_provider: Mock LLM provider fixture
        
    Returns:
        Agent instance without tools and mocked LLM
    """
    agent = Agent(tools=[])
    agent.llm_client = mock_llm_provider
    return agent
