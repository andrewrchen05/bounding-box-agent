# AI Tool Calling from Scratch - Submission

## Overview
This project implements a multimodal AI agent system with tool calling capabilities from scratch. The agent can detect bounding boxes around items in images using vision models, demonstrating a practical implementation of agentic workflows without relying on pre-built tool calling frameworks.

---

## Functional Requirements

The system implements the following core functionalities:

### 1. Agent System
- **Message Processing**: Handles multi-turn conversations with support for text and image inputs
- **Tool Execution**: Automatically detects when tools are needed and executes them. Each tool has a description of what it does, how to call it. This instruction is included in the orchestrator agent that calls tools.
- **Tool Chaining**: Supports automatic sequential tool calls where the output of one tool feeds into another. You can ask the agent to give you only bounding box coordinates or ask it to draw coordinates having provided the coordinates yourself.
- **Response Generation**: Uses LLM providers (Gemini, extensible to others) to generate intelligent responses

### 2. Bounding Box Detection
- **Image Analysis**: Processes images to detect specific objects/items based on text labels
- **Coordinate Extraction**: Returns normalized bounding box coordinates (x1, y1, x2, y2) in [0.0, 1.0] range
- **Confidence Scores**: Provides confidence scores for each detected bounding box
- **Multi-object Detection**: Handles multiple instances of the same object in a single image

### 3. Bounding Box Visualization
- **Box Drawing**: Draws detected bounding boxes on images with colored rectangles
- **Label Display**: Adds text labels with confidence scores above bounding boxes
- **Output Generation**: Saves annotated images to disk for visual verification

### 4. Conversation Management
- **History Tracking**: Maintains conversation history across multiple turns
- **Persistent Logging**: Saves conversations to JSON files with timestamps
- **Session Management**: Supports conversation reset and continuation

---

## Non-Functional Requirements

### 1. Extensibility
- **Provider-Agnostic Architecture**: Abstract `ModelProvider` interface allows adding new LLM providers (OpenAI, Claude, etc.) without modifying core logic
- **Tool Framework**: Generic `Tool` base class enables easy creation of new tools with custom functionality

### 2. Maintainability
- **Modular Design**: Clear separation of concerns across modules:
  - `core/` - Agent logic and core models
  - `providers/` - LLM provider implementations
  - `tools/` - Tool implementations
  - `prompt/` - Prompt engineering
  - `utils/` - Utilities like conversation logging
- **Type Safety**: Uses dataclasses and type hints for structured data (Message, ToolUse, BoundingBox, etc.)
- **Single Responsibility**: Each class has a focused purpose

### 3. Robustness
- **Error Handling**: Comprehensive try-except blocks with informative error messages
- **Input Validation**: Validates tool parameters and image paths before execution
- **Infinite Loop Prevention**: Max iteration limit prevents tool chaining loops

### 4. Determinism
- **Structured Output**: Forces LLM to respond in JSON format for deterministic parsing
- **Multiple Parsing Strategies**: Implements fallback JSON extraction (direct parse → regex extraction → raw text)
- **No Built-in Tool Calling**: Uses pure prompt engineering to achieve tool calling, ensuring full control

### 5. Observability
- **Conversation Logging**: Automatic logging of all messages, tool executions, and responses
- **Debug Output**: Console output for tool execution steps
- **Timestamped History**: JSON logs with timestamps for debugging and analysis

---

## Major Design Decisions

### 1. **JSON-Based Tool Calling Protocol**
**Decision**: Force the LLM to respond with structured JSON in one of two formats:
```json
{"type": "text", "text": "response"}
{"type": "tool_use", "tool_uses": [{"name": "...", "params": {...}}]}
```

**Rationale**:
- Provides deterministic parsing without relying on provider-specific tool calling APIs
- Makes the system provider-agnostic (works with any LLM)
- Enables full control over tool execution logic
- Simplifies debugging by making LLM decisions explicit
- **JSON over XML**: JSON is superior to XML for tool calling with modern LLMs for several reasons:
  - **Better LLM Training**: Modern LLMs are trained on significantly more JSON data than XML, making JSON generation more natural and accurate
  - **Compactness**: JSON is less verbose than XML (no closing tags, no attributes), reducing token usage and parsing complexity
  - **Native Parsing**: JSON parsing is simpler and more robust (single `json.loads()` vs. complex XML parsing with namespaces, attributes, etc.)
  - **API Standard**: JSON is the de facto standard for modern APIs, so LLMs see more examples of well-formed JSON in their training data
  - **Error Recovery**: JSON parsing errors are easier to handle - we can extract JSON objects from markdown code blocks or use regex fallbacks, whereas malformed XML often requires complex recovery logic
  - **Type Safety**: JSON maps naturally to Python dicts/lists with proper type coercion, while XML requires custom mapping logic

**Trade-offs**:
- Requires careful prompt engineering to ensure JSON compliance
- LLM may occasionally fail to format correctly (handled by fallback parsing strategies)
- **Token Usage**: Slightly higher token usage compared to native tool calling APIs because:
  - We include JSON schema/format instructions in the system prompt (native APIs have this built-in)
  - The model generates explicit JSON structure rather than using provider-specific compact formats
  - However, this overhead is minimal (~50-100 tokens) and is offset by the benefits of provider-agnostic design and full control

### 2. **Automatic Tool Chaining with Iteration Loop**
**Decision**: Implement an automatic tool chaining loop in `Agent.run()` that continues until a text response is received or max iterations is reached.

**Rationale**:
- Enables complex multi-step workflows without manual orchestration
- Allows tools to feed results to subsequent tool calls
- Provides a more natural agent experience

**Implementation**:
```python
while iteration < max_iterations:
    response = self._generate_response_from_history()
    if response.is_text():
        return response  # Final answer
    elif response.is_tool_use():
        results = execute_tools()
        add_results_to_history()
        continue  # Generate next response
```

**Trade-offs**:
- Can consume more tokens in multi-step workflows
- Makes debugging more complex for long chains

### 4. **Provider Abstraction with Factory Pattern**
**Decision**: Create abstract `ModelProvider` interface with concrete implementations (`GeminiModelProvider`) and factory function.

**Rationale**:
- **Extensibility**: Easy to add OpenAI, Claude, or custom providers
- **Dependency Inversion**: Core agent doesn't depend on specific provider implementations
- **Clean Initialization**: Factory pattern centralizes provider creation logic

**Structure**:
```python
# base.py - Abstract interface
class ModelProvider(ABC):
    @abstractmethod
    def generate_response(messages, system_prompt, tools_description) -> str

# gemini.py - Concrete implementation
class GeminiModelProvider(ModelProvider):
    def generate_response(...) -> str

# factory.py - Creation logic
def create_model_provider(client: str) -> ModelProvider
```

### 5. **Structured Input/Output Classes**
**Decision**: Use dataclasses for all tool inputs and outputs instead of raw dictionaries.

**Examples**:
```python
@dataclass
class BoundingBoxInput:
    image_path: str
    label: str

@dataclass  
class BoundingBox:
    confidence: float
    xyxy: List[float]  # [x1, y1, x2, y2]

@dataclass
class BoundingBoxOutput:
    width: int
    height: int
    boxes: List[BoundingBox]
```

**Rationale**:
- **Type Safety**: Catches errors at development time
- **Self-Documenting**: Clear contracts for tool inputs/outputs
- **IDE Support**: Enables autocomplete and refactoring
- **Serialization**: Easy conversion to/from JSON via `to_dict()` methods

### 7. **Conversation Logging System**
**Decision**: Implement automatic conversation logging to JSON files in `conversation_history/` directory.

**What's Logged**:
- All messages (user, assistant, system)
- Tool execution requests and results
- Errors and failures
- Timestamps for all events

**Rationale**:
- **Debugging**: Essential for understanding agent behavior
- **Analysis**: Enables post-hoc analysis of agent decisions
- **Compliance**: Provides audit trail for production systems
- **Testing**: Can replay conversations for testing

### 8. **Normalized Bounding Box Coordinates**
**Decision**: Use normalized coordinates [0.0, 1.0] rather than pixel coordinates.

**Format**: `[x1, y1, x2, y2]` where (x1, y1) is top-left and (x2, y2) is bottom-right

**Rationale**:
- **Resolution-Independent**: Works across different image sizes
- **Industry Standard**: Matches formats used by YOLO, etc.
- **Scaling**: Easy to convert to any target resolution
- **LLM-Friendly**: Simpler for models to learn than pixel coordinates

**Conversion**:
```python
# Normalized to pixel coordinates:
pixel_x1 = normalized_x1 * image_width
pixel_y1 = normalized_y1 * image_height
```

---

### Module Structure
```
tool-calling-from-scratch/
├── core/                    # Core agent system
│   ├── agent.py            # Main Agent class with tool chaining
│   ├── models.py           # Message, Role, AssistantResponse
│   └── tool.py             # Tool base class and ToolUse
├── providers/               # LLM provider implementations
│   ├── base.py             # Abstract ModelProvider interface
│   ├── factory.py          # Provider factory function
│   └── gemini.py           # Gemini implementation
├── tools/                   # Tool implementations
│   ├── detect_bounding_box/ # Bounding box detection tool
│   │   ├── detect_bounding_box.py
│   │   ├── bounding_box.py
│   │   ├── bounding_box_input.py
│   │   └── bounding_box_output.py
│   └── draw_bounding_box.py # Visualization tool
├── prompt/                  # Prompt engineering
│   ├── system_prompt.py    # Agent-level system prompt
│   └── bounding_box_prompt.py # Tool-specific prompt
├── utils/                   # Utilities
│   └── conversation_logger.py
└── chat.py                 # Example usage / entry point
```

### Data Flow
```
User Input → Agent.run() 
  → Generate Response (LLM with system prompt + tools description)
  → Parse JSON Response
  → If tool_use: Execute Tools → Add Results to History → Loop
  → If text: Return Final Response
```

---

## How to Run the Agent

### Prerequisites
- Python 3.8+
- Gemini API key (get from [Google AI Studio](https://aistudio.google.com/))

### Installation

1. **Clone the repository**:
```bash
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

### Basic Usage

#### 1. Interactive Chat (Recommended)
Start the interactive chatbot:
```bash
python chat.py
```

Then provide instructions like:
```
You: Detect the dog in assets/dog.png and draw a bounding box around it
AI: [Executes detect_bounding_box → draw_bounding_box → Returns result]

You: exit
```

#### 2. Programmatic Usage
```python
from core import Agent, Message, Role
from tools.detect_bounding_box import DetectBoundingBox
from tools.draw_bounding_box import DrawBoundingBox
from prompt.system_prompt import SYSTEM_PROMPT

# Initialize agent with tools
agent = Agent(
    tools=[DetectBoundingBox(), DrawBoundingBox()],
    system_prompt=SYSTEM_PROMPT
)

# Create user message with image
message = Message(
    role=Role.USER,
    content="Detect the dog in this image and draw a bounding box",
    image_path="assets/dog.png"
)

# Run agent (automatic tool chaining)
response = agent.run(messages=[message])
print(response.content)
```

### Example Workflows

#### Bounding Box Detection Only
```python
from core import Agent, Message, Role
from tools.detect_bounding_box import DetectBoundingBox

agent = Agent(tools=[DetectBoundingBox()])

message = Message(
    role=Role.USER,
    content="Find all cars",
    image_path="assets/cars.png"
)

response = agent.run(messages=[message])
# Returns: BoundingBoxOutput with coordinates
```

#### Detection + Visualization
```python
agent = Agent(
    tools=[DetectBoundingBox(), DrawBoundingBox()],
    system_prompt=SYSTEM_PROMPT
)

message = Message(
    role=Role.USER, 
    content="Detect soldiers and draw boxes on them"
)
# Agent will automatically:
# 1. Call detect_bounding_box with image
# 2. Call draw_bounding_box with detection results
# 3. Save annotated image to output_boxes.png
```

### Configuration

#### Change LLM Provider
```python
agent = Agent(
    tools=[...],
    client='gemini'  # Currently only Gemini supported
)
```

#### Adjust Max Iterations
```python
# Prevent long tool chains
response = agent.run(messages=[...], max_iterations=5)
```

### Output Files

- **Annotated Images**: `output_boxes.png` (or custom path)
- **Conversation Logs**: `conversation_history/<timestamp>.json`

Example log structure:
```json
{
  "conversation_id": "20260115_143022_abc123",
  "start_time": "2026-01-15T14:30:22.123456",
  "messages": [
    {
      "role": "user",
      "content": "Detect dog in image",
      "timestamp": "..."
    },
    {
      "type": "tool_execution",
      "tool_name": "detect_bounding_box",
      "params": {"image_path": "...", "label": "dog"},
      "result": {"boxes": [...]},
      "timestamp": "..."
    }
  ]
}
```

### Testing

Run the test suite:
```bash
pytest tests/
```

Run specific test:
```bash
python test_draw_boxes.py
```

---

## Limitations and Future Improvements

### Current Limitations
1. **Single Provider**: Only Gemini implemented (OpenAI/Claude coming)
2. **Tool Chaining Depth**: Limited to max_iterations parameter
3. **Image-Only Vision**: No video processing support
4. **English-Only**: Prompts optimized for English

### Potential Enhancements
1. **Additional Providers**: OpenAI GPT-4V, Claude Sonnet, etc.
2. **More Tools**: Image segmentation, OCR, image generation
3. **Async Execution**: Parallel tool execution for independent tools
4. **Streaming Responses**: Real-time token streaming
5. **Tool Dependencies**: Declare dependencies between tools
6. **Caching**: Cache LLM responses for repeated queries
7. **Metrics**: Track token usage, latency, success rates

---

## Design Philosophy

This implementation prioritizes:

1. **Simplicity**: Avoid over-engineering; use simple patterns where possible
2. **Explicitness**: Make agent decisions and data flow visible
3. **Extensibility**: Easy to add new providers, tools, and capabilities
4. **Maintainability**: Clear code structure with good separation of concerns
5. **Control**: Full control over tool calling logic vs. black-box APIs

The goal is to demonstrate that sophisticated agentic behavior can be achieved through careful prompt engineering and clean system design, without relying on proprietary tool calling frameworks.

---

## Conclusion

This project successfully implements a multimodal AI agent system with tool calling capabilities from scratch. The architecture balances simplicity with extensibility, demonstrating that complex agentic workflows can be built using fundamental patterns: abstract interfaces, prompt engineering, and structured outputs.

The bounding box detection use case showcases the system's ability to handle vision tasks, tool chaining, and structured output parsing - all key requirements for practical AI agent applications.
