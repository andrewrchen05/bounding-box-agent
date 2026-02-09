# AI Tool Calling from Scratch

## Overview
This project implements a multimodal AI agent system with tool calling capabilities from scratch. The agent can detect bounding boxes around items in images using llm and Pillow library, demonstrating a practical implementation of agentic workflows without relying on pre-built tool calling frameworks.

---

## Functional Requirements

The system implements the following core functionalities:

### 1. Agent System
- **Message Processing**: The system shall handle multi-turn conversations with support for text and image inputs
- **Tool Execution**: The system shall automatically detect when tools are needed and execute them. Each tool shall have a description of what it does and how to call it.
- **Tool Chaining**: The system shall support automatic sequential tool calls where the output of one tool feeds into another. The system shall allow users to ask the agent to give only bounding box coordinates or to draw coordinates having provided the coordinates themselves.
- **Response Generation**: The system shall use LLM providers (Gemini for p0, extensible to others) to generate intelligent responses

### 2. Bounding Box Detection
- **Image Analysis**: The system shall process images to detect specific objects/items based on text labels
- **Coordinate Extraction**: The system shall return normalized bounding box coordinates (x1, y1, x2, y2) in [0.0, 1.0] range
- **Multi-object Detection**: The system shall handle multiple instances of objects in a single image

### 3. Bounding Box Visualization
- **Box Drawing**: The system shall draw detected bounding boxes on images with colored rectangles
- **Output Generation**: The system shall save annotated images to disk for visual verification

### 4. Conversation Management
- **History Tracking**: The system shall maintain conversation history across multiple turns
- **Persistent Logging**: The system shall save conversations to JSON files with timestamps

---

## Non-Functional Requirements

### 1. **Accuracy**
The system shall achieve a minimum mean Intersection-over-Union (mIoU) of ≥ 0.75 on a representative validation dataset for bounding box detection tasks.

### 2. **Latency**
- The system shall return bounding box predictions within 300 ms at p95 for images up to 1920×1080 resolution
- Tool execution overhead (excluding LLM inference time) shall not exceed 50 ms per tool call
- End-to-end agent response time shall be ≤ 5 seconds at p99 for single-tool workflows

### 4. **Scalability**
- The system shall process images up to 4K resolution (3840×2160) without memory exhaustion

### 5. **Reliability**
- The system shall implement graceful degradation when external dependencies (LLM APIs) are unavailable
- Tool execution failures shall not crash the agent process

### 6. **Determinism**
- Tool execution shall be idempotent - multiple calls with identical inputs shall produce identical results

### 7. **Robustness**
- The system shall gracefully handle malformed images and return structured error responses without crashing
- The system shall validate image file formats and reject unsupported types with clear error messages
- The system shall handle edge cases including empty images, extremely small/large images, and corrupt files
- LLM response parsing shall include fallback strategies for malformed JSON

### 8. **Resolution Invariance**
The system shall produce consistent normalized bounding box outputs (coordinates in [0.0, 1.0] range) regardless of input image resolution, ensuring portability across different image sizes.

### 9. **Security**
- The system shall validate and sanitize all image inputs to prevent malformed payload or decompression-bomb attacks
- File paths shall be validated to prevent directory traversal attacks
- API keys shall never be logged or exposed in error messages
- The system shall limit maximum image file size to prevent resource exhaustion (default: 50 MB)

### 10. **Observability**
- The system shall emit structured logs including timestamps, request IDs, and execution context
- The system shall track and log key metrics: LLM token usage, tool execution latency, error rates, and bounding box confidence scores
- The system shall persist conversation history in JSON format for debugging and audit purposes
- Error logs shall include sufficient context for root cause analysis without exposing sensitive data

### 11. **Cost Efficiency**
- The system shall include configurable token limits to prevent runaway costs from infinite tool loops
- The system shall optimize prompt engineering to minimize token usage while maintaining accuracy

### 12. **Model Versioning**
- The system shall support explicit model version selection via configuration
- The system shall log model version metadata with each inference request for reproducibility
- The system architecture shall support rollback to previous model versions without service downtime

### 13. **Maintainability**
- The codebase shall maintain ≥ 80% code coverage with automated tests
- All public APIs shall include type hints and docstrings
- Core modules shall have cyclomatic complexity ≤ 10

### 14. **Extensibility**
- Adding new LLM providers shall require implementing a single abstract interface
- The system shall support plugin-based tool discovery without recompilation

---

## Out of Scope

The following features and capabilities are explicitly out of scope for this implementation:

- Supporting models beyond Gemini 3.0 Flash
- Video processing or video stream analysis
- Parallel tool execution (tools execute sequentially only)
- Image segmentation beyond bounding boxes
- Optical character recognition (OCR)
- Image generation or editing beyond annotation
- Caching LLM responses for repeated queries
- User authentication or authorization
- Rate limiting or quota management
- Monitoring or alerting capabilities
- Retry logic with exponential backoff for API failures
- Specialized Guardrails library, currently relying on Agent model to make judgement

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
**Decision**: Implement an automatic tool chaining loop that continues until a text response is received or max iterations is reached.

**Rationale**:
- Enables complex multi-step workflows without manual orchestration
- Allows tools to feed results to subsequent tool calls
- Provides a more natural agent experience

**Trade-offs**:
- Can consume more tokens in multi-step workflows
- Makes debugging more complex for long chains

### 3. **Provider Abstraction with Factory Pattern**
**Decision**: Create abstract `ModelProvider` interface with concrete implementations and factory function.

**Rationale**:
- **Extensibility**: Easy to add OpenAI, Claude, or custom providers
- **Dependency Inversion**: Core agent doesn't depend on specific provider implementations
- **Clean Initialization**: Factory pattern centralizes provider creation logic

### 4. **Structured Input/Output Classes**
**Decision**: Use dataclasses for all tool inputs and outputs instead of raw dictionaries.

**Rationale**:
- **Type Safety**: Catches errors at development time
- **Self-Documenting**: Clear contracts for tool inputs/outputs
- **IDE Support**: Enables autocomplete and refactoring
- **Serialization**: Easy conversion to/from JSON via `to_dict()` methods

### 5. **Normalized Bounding Box Coordinates**
**Decision**: Use normalized coordinates [0.0, 1.0] rather than pixel coordinates.

**Format**: `[x1, y1, x2, y2]` where (x1, y1) is top-left and (x2, y2) is bottom-right

**Rationale**:
- **Resolution-Independent**: Works across different image sizes
- **Industry Standard**: Matches formats used by YOLO, etc.
- **Scaling**: Easy to convert to any target resolution
- **LLM-Friendly**: Simpler for models to learn than pixel coordinates. Reduced hallucination as LLMs could only approximate the right dimension for the image.

---

## Implementation Details

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

### Tool Chaining Implementation
The automatic tool chaining is implemented in `Agent.run()` using an iteration loop:
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

### Provider Abstraction Implementation
The provider abstraction uses an abstract base class pattern:
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

### Structured Data Classes Implementation
Tool inputs and outputs use dataclasses:
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

### Coordinate Normalization Implementation
Normalized coordinates are converted to pixel coordinates as needed:
```python
# Normalized to pixel coordinates:
pixel_x1 = normalized_x1 * image_width
pixel_y1 = normalized_y1 * image_height
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

## Conversation History Structure

**Conversation History Structure:**
```json
{
  "conversation_id": "20260117_143052_a7b8c9d0",
  "initial_request_id": "8a3f5c1e-4b2d-4a9f-b8e7-1c2d3e4f5a6b",
  "messages": [
    {"request_id": "8a3f5c1e...", "role": "user", "content": "...", "timestamp": "..."}
  ],
  "tool_executions": [
    {"request_id": "8a3f5c1e...", "tool_name": "detect_bounding_box", "success": true}
  ]
}
```

---

## Limitations and Future Improvements

### Current Limitations
1. **Single Provider**: Only Gemini implemented (OpenAI/Claude coming)
2. **Tool Chaining Depth**: Limited to max_iterations parameter
3. **Image-Only Vision**: No video processing support
4. No Guardrails framework beyond Agent LLM prompt.
5. No robust method to check work
6. Single agent framework

### Potential Enhancements
1. **Additional Providers**: OpenAI GPT-4V, Claude Sonnet, etc.
2. **More Tools**: Image segmentation, OCR, image generation
3. **Async Execution**: Parallel tool execution for independent tools
5. **Tool Dependencies**: Declare dependencies between tools
6. **Caching**: Cache LLM responses for repeated queries
7. **Metrics**: Track token usage, latency, success rates
8. Harden system against hallucations e.g generating non normalized coordinates
9. Confidence score usage?

---
