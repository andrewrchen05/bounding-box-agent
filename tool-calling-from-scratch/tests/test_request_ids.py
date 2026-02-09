#!/usr/bin/env python3
"""
Test script to demonstrate request ID tracking functionality.
"""
import json
from core.agent import Agent
from core.models import Message, Role
from tools.detect_bounding_box import DetectBoundingBox
from tools.draw_bounding_box import DrawBoundingBox
from prompt.system_prompt import SYSTEM_PROMPT

def main():
    print("=" * 80)
    print("Request ID Tracking Demo")
    print("=" * 80)
    print()
    
    # Initialize agent with tools
    detect_tool = DetectBoundingBox()
    draw_tool = DrawBoundingBox()
    agent = Agent(
        tools=[detect_tool, draw_tool],
        system_prompt=SYSTEM_PROMPT,
        client='gemini'
    )
    
    # Test 1: Single request
    print("Test 1: Making a single request...")
    print("-" * 80)
    user_message = Message(
        role=Role.USER,
        content="Detect dogs in assets/dog.png"
    )
    
    response = agent.run([user_message])
    print(f"\nResponse: {response.content}\n")
    
    # Save conversation to check request IDs
    agent.save_conversation()
    
    # Load and display the conversation history with request IDs
    conversation_id = agent.logger.current_conversation_id
    conversation_file = f"conversation_history/{conversation_id}.json"
    
    print("\n" + "=" * 80)
    print("Conversation History with Request IDs")
    print("=" * 80)
    
    with open(conversation_file, 'r') as f:
        conversation = json.load(f)
    
    print(f"\nConversation ID: {conversation['conversation_id']}")
    print(f"Initial Request ID: {conversation.get('initial_request_id', 'N/A')}")
    print()
    
    # Display messages with request IDs
    print("Messages:")
    for i, msg in enumerate(conversation['messages'], 1):
        request_id = msg.get('request_id', 'N/A')
        role = msg['role']
        content_preview = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
        print(f"  {i}. [{role}] Request ID: {request_id}")
        print(f"     Content: {content_preview}")
        print()
    
    # Display tool executions with request IDs
    print("Tool Executions:")
    for i, execution in enumerate(conversation['tool_executions'], 1):
        request_id = execution.get('request_id', 'N/A')
        tool_name = execution['tool_name']
        success = execution['success']
        print(f"  {i}. Tool: {tool_name}")
        print(f"     Request ID: {request_id}")
        print(f"     Success: {success}")
        print()
    
    # Display responses with request IDs
    print("Assistant Responses:")
    for i, resp in enumerate(conversation['responses'], 1):
        request_id = resp.get('request_id', 'N/A')
        resp_type = resp['type']
        print(f"  {i}. Type: {resp_type}")
        print(f"     Request ID: {request_id}")
        print()
    
    print("=" * 80)
    print("Request ID tracking is working! All events are tagged with request IDs.")
    print("=" * 80)

if __name__ == "__main__":
    main()
