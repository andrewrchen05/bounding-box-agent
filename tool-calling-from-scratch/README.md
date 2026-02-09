# AI Tool Calling from Scratch

A multimodal AI agent system with tool calling capabilities implemented from scratch. This project demonstrates how to build an agentic workflow system that can detect bounding boxes around items in images using LLMs and the Pillow library, without relying on pre-built tool calling frameworks.

## Features

- **Multi-turn Conversations**: Handle text and image inputs in conversational workflows
- **Automatic Tool Execution**: Agent automatically detects when tools are needed and executes them
- **Tool Chaining**: Support for sequential tool calls where output from one tool feeds into another
- **Bounding Box Detection**: Detect and visualize bounding boxes around objects in images
- **Provider Agnostic**: Extensible architecture supporting multiple LLM providers (currently Gemini, extensible to OpenAI, Claude, etc.)
- **Structured I/O**: Type-safe tool inputs and outputs using dataclasses

## Quick Start

### Prerequisites
- Python 3.8+
- Gemini API key (get from [Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd tool-calling-from-scratch
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up API key**:
Create a `.env` file in the project root:
```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

Or export as environment variable:
```bash
export GEMINI_API_KEY=your_api_key_here
```

### Usage

Start the interactive chatbot:
```bash
python chat.py
```

Then provide instructions like:
```
You: Detect the dog in assets/dog.png and draw a bounding box around it
AI: [Executes detect_bounding_box → draw_bounding_box → Returns result]
```

For more detailed documentation, architecture decisions, and examples, see [DOCUMENTATION.md](DOCUMENTATION.md).