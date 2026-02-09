"""
Integration tests for Agent orchestrating tool calls.

This module contains integration tests that verify:
- Agent orchestration of tool calls
- Tool chaining (detect -> draw)
- Conversation flow
- Error handling
"""

import pytest
import json
import os
from unittest.mock import Mock
from core.agent import Agent
from core.models import Message, Role
from core.tool import ToolUse
from tools.detect_bounding_box import DetectBoundingBox, BoundingBoxOutput, BoundingBox
from tools.draw_bounding_box import DrawBoundingBox, DrawBoundingBoxOutput


class TestSingleToolCallFlow:
    """Test basic agent-tool interaction."""
    
    def test_single_tool_call_flow(self, agent_with_tools, mock_llm_provider, test_image):
        """Test basic agent-tool interaction with single tool call."""
        image_path, width, height = test_image
        
        # Mock LLM responses: first tool use, then text response
        mock_llm_responses = [
            json.dumps({
                "type": "tool_use",
                "tool_uses": [{
                    "name": "detect_bounding_box",
                    "params": {
                        "image_path": image_path,
                        "label": "button"
                    }
                }]
            }),
            json.dumps({
                "type": "text",
                "text": "I found 2 buttons in the image."
            })
        ]
        mock_llm_provider.generate_response.side_effect = mock_llm_responses
        
        # Mock the detect tool's internal model provider to return boxes
        detect_tool = agent_with_tools.tools[0]
        # The detect tool's model provider is already mocked in the fixture
        detect_tool.model_provider.generate_response.return_value = json.dumps({
            "boxes": [
                {"confidence": 0.92, "xyxy": [0.1, 0.2, 0.3, 0.4]},
                {"confidence": 0.85, "xyxy": [0.5, 0.6, 0.7, 0.8]}
            ]
        })
        
        # Execute agent
        user_message = Message(role=Role.USER, content="Detect buttons in this image")
        response = agent_with_tools.run(messages=[user_message])
        
        # Assertions
        assert response.role == Role.ASSISTANT
        assert "found 2 buttons" in response.content.lower()
        assert len(agent_with_tools.conversation_history) >= 3  # User, tool result, final response
        assert mock_llm_provider.generate_response.call_count == 2


class TestToolChaining:
    """Test tool chaining (detect -> draw)."""
    
    def test_tool_chaining_detect_to_draw(self, agent_with_tools, mock_llm_provider, test_image, temp_dir):
        """Test detect -> draw tool chaining."""
        image_path, width, height = test_image
        
        # Mock LLM responses: detect, then draw, then text
        mock_llm_responses = [
            # First iteration: detect
            json.dumps({
                "type": "tool_use",
                "tool_uses": [{
                    "name": "detect_bounding_box",
                    "params": {
                        "image_path": image_path,
                        "label": "button"
                    }
                }]
            }),
            # Second iteration: draw (after seeing detect results)
            json.dumps({
                "type": "tool_use",
                "tool_uses": [{
                    "name": "draw_bounding_box",
                    "params": {
                        "image_path": image_path,
                        "boxes": [
                            {"xyxy": [0.1, 0.2, 0.3, 0.4], "confidence": 0.92},
                            {"xyxy": [0.5, 0.6, 0.7, 0.8], "confidence": 0.85}
                        ],
                        "output_path": os.path.join(temp_dir, "output.png")
                    }
                }]
            }),
            # Third iteration: text response
            json.dumps({
                "type": "text",
                "text": "I've detected and drawn bounding boxes around the buttons."
            })
        ]
        mock_llm_provider.generate_response.side_effect = mock_llm_responses
        
        # Mock the detect tool's internal model provider
        detect_tool = agent_with_tools.tools[0]
        detect_tool.model_provider.generate_response.return_value = json.dumps({
            "boxes": [
                {"confidence": 0.92, "xyxy": [0.1, 0.2, 0.3, 0.4]},
                {"confidence": 0.85, "xyxy": [0.5, 0.6, 0.7, 0.8]}
            ]
        })
        
        # Execute agent
        user_message = Message(role=Role.USER, content="Detect and draw bounding boxes around buttons")
        response = agent_with_tools.run(messages=[user_message])
        
        # Assertions
        assert response.role == Role.ASSISTANT
        assert "detected and drawn" in response.content.lower()
        assert mock_llm_provider.generate_response.call_count == 3
        
        # Verify output file was created
        output_path = os.path.join(temp_dir, "output.png")
        assert os.path.exists(output_path)
        
        # Verify conversation history includes tool results
        tool_result_messages = [
            msg for msg in agent_with_tools.conversation_history
            if "Tool execution results" in msg.content
        ]
        assert len(tool_result_messages) == 2  # One for detect, one for draw


class TestMultipleToolsSingleResponse:
    """Test multiple tools executed in a single response."""
    
    def test_multiple_tools_single_response(self, agent_with_tools, mock_llm_provider, test_image, temp_dir):
        """Test agent executing multiple tools in one response."""
        image_path, width, height = test_image
        
        # Create a second test image
        from PIL import Image
        image2_path = os.path.join(temp_dir, "test_image2.png")
        Image.new('RGB', (100, 100), color='blue').save(image2_path)
        
        # Mock LLM to return multiple tool uses
        mock_llm_responses = [
            json.dumps({
                "type": "tool_use",
                "tool_uses": [
                    {
                        "name": "detect_bounding_box",
                        "params": {
                            "image_path": image_path,
                            "label": "button"
                        }
                    },
                    {
                        "name": "detect_bounding_box",
                        "params": {
                            "image_path": image2_path,
                            "label": "button"
                        }
                    }
                ]
            }),
            json.dumps({
                "type": "text",
                "text": "I've detected buttons in both images."
            })
        ]
        mock_llm_provider.generate_response.side_effect = mock_llm_responses
        
        # Mock the detect tool's internal model provider
        detect_tool = agent_with_tools.tools[0]
        detect_tool.model_provider.generate_response.return_value = json.dumps({
            "boxes": [
                {"confidence": 0.92, "xyxy": [0.1, 0.2, 0.3, 0.4]}
            ]
        })
        
        # Execute agent
        user_message = Message(role=Role.USER, content="Detect buttons in both images")
        response = agent_with_tools.run(messages=[user_message])
        
        # Assertions
        assert response.role == Role.ASSISTANT
        assert "both images" in response.content.lower()
        assert mock_llm_provider.generate_response.call_count == 2
        
        # Verify both tools executed (check conversation history for tool results)
        tool_result_messages = [
            msg for msg in agent_with_tools.conversation_history
            if "Tool execution results" in msg.content
        ]
        assert len(tool_result_messages) == 1  # One message with both results
        assert "detect_bounding_box" in tool_result_messages[0].content
        # Should have results from both tool calls
        assert tool_result_messages[0].content.count("detect_bounding_box") == 2


class TestMultiTurnConversation:
    """Test multi-turn conversation with context."""
    
    def test_multi_turn_conversation(self, agent_with_tools, mock_llm_provider, test_image, temp_dir):
        """Test conversation context maintained across multiple turns."""
        image_path, width, height = test_image
        
        # First turn: detect
        mock_llm_responses_turn1 = [
            json.dumps({
                "type": "tool_use",
                "tool_uses": [{
                    "name": "detect_bounding_box",
                    "params": {
                        "image_path": image_path,
                        "label": "button"
                    }
                }]
            }),
            json.dumps({
                "type": "text",
                "text": "I found 2 buttons in the image."
            })
        ]
        
        # Second turn: draw (should remember the image from first turn)
        mock_llm_responses_turn2 = [
            json.dumps({
                "type": "tool_use",
                "tool_uses": [{
                    "name": "draw_bounding_box",
                    "params": {
                        "image_path": image_path,  # Same image from first turn
                        "boxes": [
                            {"xyxy": [0.1, 0.2, 0.3, 0.4], "confidence": 0.92},
                            {"xyxy": [0.5, 0.6, 0.7, 0.8], "confidence": 0.85}
                        ],
                        "output_path": os.path.join(temp_dir, "output.png")
                    }
                }]
            }),
            json.dumps({
                "type": "text",
                "text": "I've drawn the bounding boxes on the image."
            })
        ]
        
        # Mock detect tool's internal provider
        detect_tool = agent_with_tools.tools[0]
        detect_tool.model_provider.generate_response.return_value = json.dumps({
            "boxes": [
                {"confidence": 0.92, "xyxy": [0.1, 0.2, 0.3, 0.4]},
                {"confidence": 0.85, "xyxy": [0.5, 0.6, 0.7, 0.8]}
            ]
        })
        
        # First turn
        mock_llm_provider.generate_response.side_effect = mock_llm_responses_turn1
        user_message1 = Message(role=Role.USER, content="Detect buttons in this image")
        response1 = agent_with_tools.run(messages=[user_message1])
        
        assert "found 2 buttons" in response1.content.lower()
        
        # Second turn
        mock_llm_provider.generate_response.side_effect = mock_llm_responses_turn2
        user_message2 = Message(role=Role.USER, content="Now draw bounding boxes on it")
        response2 = agent_with_tools.run(messages=[user_message2])
        
        # Assertions
        assert response2.role == Role.ASSISTANT
        assert "drawn" in response2.content.lower()
        
        # Verify conversation history includes both turns
        user_messages = [msg for msg in agent_with_tools.conversation_history if msg.role == Role.USER]
        assert len(user_messages) == 2


class TestToolExecutionErrorHandling:
    """Test error handling in tool execution."""
    
    def test_tool_execution_error(self, agent_with_tools, mock_llm_provider, test_image):
        """Test agent handles tool execution errors gracefully."""
        image_path, width, height = test_image
        
        # Mock LLM to call a tool
        mock_llm_responses = [
            json.dumps({
                "type": "tool_use",
                "tool_uses": [{
                    "name": "detect_bounding_box",
                    "params": {
                        "image_path": image_path,
                        "label": "button"
                    }
                }]
            }),
            json.dumps({
                "type": "text",
                "text": "I encountered an error while processing the image."
            })
        ]
        mock_llm_provider.generate_response.side_effect = mock_llm_responses
        
        # Make the detect tool's internal provider raise an error
        detect_tool = agent_with_tools.tools[0]
        detect_tool.model_provider.generate_response.side_effect = Exception("API Error")
        
        # Execute agent
        user_message = Message(role=Role.USER, content="Detect buttons in this image")
        response = agent_with_tools.run(messages=[user_message])
        
        # Assertions
        assert response.role == Role.ASSISTANT
        # Should have error in tool results
        tool_result_messages = [
            msg for msg in agent_with_tools.conversation_history
            if "Tool execution results" in msg.content
        ]
        assert len(tool_result_messages) == 1
        assert "Error" in tool_result_messages[0].content
    
    def test_tool_not_found_error(self, agent_with_tools, mock_llm_provider, test_image):
        """Test agent handles non-existent tool errors."""
        image_path, width, height = test_image
        
        # Mock LLM to call a non-existent tool
        mock_llm_responses = [
            json.dumps({
                "type": "tool_use",
                "tool_uses": [{
                    "name": "nonexistent_tool",
                    "params": {"param1": "value1"}
                }]
            }),
            json.dumps({
                "type": "text",
                "text": "I tried to use a tool that doesn't exist."
            })
        ]
        mock_llm_provider.generate_response.side_effect = mock_llm_responses
        
        # Execute agent
        user_message = Message(role=Role.USER, content="Use a tool that doesn't exist")
        response = agent_with_tools.run(messages=[user_message])
        
        # Assertions
        assert response.role == Role.ASSISTANT
        # Should have error in tool results
        tool_result_messages = [
            msg for msg in agent_with_tools.conversation_history
            if "Tool execution results" in msg.content
        ]
        assert len(tool_result_messages) == 1
        assert "Error" in tool_result_messages[0].content
        assert "not found" in tool_result_messages[0].content.lower()


class TestMaxIterationsLimit:
    """Test max iterations limit to prevent infinite loops."""
    
    def test_max_iterations_limit(self, agent_with_tools, mock_llm_provider):
        """Test agent stops after max iterations."""
        # Mock LLM to always return tool use (never text)
        mock_llm_provider.generate_response.return_value = json.dumps({
            "type": "tool_use",
            "tool_uses": [{
                "name": "detect_bounding_box",
                "params": {
                    "image_path": "/fake/path.png",
                    "label": "button"
                }
            }]
        })
        
        # Execute agent with low max_iterations
        user_message = Message(role=Role.USER, content="Detect buttons")
        response = agent_with_tools.run(messages=[user_message], max_iterations=3)
        
        # Assertions
        assert response.role == Role.ASSISTANT
        assert "Maximum tool execution iterations" in response.content
        assert mock_llm_provider.generate_response.call_count == 3


class TestToolResultFormatting:
    """Test tool result formatting for LLM consumption."""
    
    def test_tool_result_formatting(self, agent_with_tools, mock_llm_provider, test_image):
        """Test tool results are formatted correctly as JSON."""
        image_path, width, height = test_image
        
        # Mock LLM responses
        mock_llm_responses = [
            json.dumps({
                "type": "tool_use",
                "tool_uses": [{
                    "name": "detect_bounding_box",
                    "params": {
                        "image_path": image_path,
                        "label": "button"
                    }
                }]
            }),
            json.dumps({
                "type": "text",
                "text": "I received the detection results."
            })
        ]
        mock_llm_provider.generate_response.side_effect = mock_llm_responses
        
        # Mock detect tool's internal provider
        detect_tool = agent_with_tools.tools[0]
        detect_tool.model_provider.generate_response.return_value = json.dumps({
            "boxes": [
                {"confidence": 0.92, "xyxy": [0.1, 0.2, 0.3, 0.4]},
                {"confidence": 0.85, "xyxy": [0.5, 0.6, 0.7, 0.8]}
            ]
        })
        
        # Execute agent
        user_message = Message(role=Role.USER, content="Detect buttons")
        response = agent_with_tools.run(messages=[user_message])
        
        # Assertions
        assert response.role == Role.ASSISTANT
        
        # Verify tool result is formatted as JSON
        tool_result_messages = [
            msg for msg in agent_with_tools.conversation_history
            if "Tool execution results" in msg.content
        ]
        assert len(tool_result_messages) == 1
        
        # Check that the result contains JSON-formatted data
        result_content = tool_result_messages[0].content
        assert "detect_bounding_box" in result_content
        # Should contain structured data (width, height, boxes)
        assert "width" in result_content or "boxes" in result_content


class TestConversationHistoryManagement:
    """Test conversation history is maintained correctly."""
    
    def test_conversation_history_management(self, agent_with_tools, mock_llm_provider, test_image):
        """Test conversation history includes all messages in correct order."""
        image_path, width, height = test_image
        
        # Mock LLM responses
        mock_llm_responses = [
            json.dumps({
                "type": "tool_use",
                "tool_uses": [{
                    "name": "detect_bounding_box",
                    "params": {
                        "image_path": image_path,
                        "label": "button"
                    }
                }]
            }),
            json.dumps({
                "type": "text",
                "text": "Done!"
            })
        ]
        mock_llm_provider.generate_response.side_effect = mock_llm_responses
        
        # Mock detect tool's internal provider
        detect_tool = agent_with_tools.tools[0]
        detect_tool.model_provider.generate_response.return_value = json.dumps({
            "boxes": [
                {"confidence": 0.92, "xyxy": [0.1, 0.2, 0.3, 0.4]}
            ]
        })
        
        # Execute agent
        user_message = Message(role=Role.USER, content="Detect buttons")
        response = agent_with_tools.run(messages=[user_message])
        
        # Assertions
        history = agent_with_tools.conversation_history
        
        # Should have at least: user message, tool result, final response
        assert len(history) >= 3
        
        # First message should be user message
        user_messages = [msg for msg in history if msg.role == Role.USER]
        assert len(user_messages) >= 1
        assert user_messages[0].content == "Detect buttons"
        
        # Should have tool result message
        tool_result_messages = [
            msg for msg in history
            if msg.role == Role.ASSISTANT and "Tool execution results" in msg.content
        ]
        assert len(tool_result_messages) == 1
        
        # Final response should be assistant message
        assert response.role == Role.ASSISTANT
        assert response.content == "Done!"
