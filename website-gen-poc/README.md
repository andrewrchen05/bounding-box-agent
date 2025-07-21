# Frontend Generation Agent POC

A proof-of-concept agent architecture using LangGraph that can generate complete TypeScript/React projects from high-level user requests like "Create a personal blog."

**Two Generation Modes Available:**
- **Multi-Agent Workflow** (default): Structured approach using specialized agents
- **Single-Context Generation**: Fast, comprehensive generation in one LLM call

## Architecture Overview

This POC implements two generation approaches:

### Multi-Agent Workflow (Default)
A structured approach using LangGraph's routing patterns:

```
User Request → Requirements Agent → Architecture Agent → Component Generator → Integration Agent → Complete Project
```

### Single-Context Generation (New)
A streamlined approach generating everything in one comprehensive pass:

```
User Request → Single Context Generator → Complete Project
```

### Agents

1. **Requirements Agent**: Analyzes user requests and converts them into detailed technical specifications
2. **Architecture Agent**: Designs project structure, dependencies, and build configuration  
3. **Component Agent**: Generates React/TypeScript components based on specifications
4. **Integration Agent**: Assembles all files into a complete, runnable project

### Key Features

- **LangGraph Workflow**: Uses conditional routing and state management
- **End-to-End Generation**: From idea to running localhost project
- **TypeScript/React**: Modern development stack with Vite
- **Tailwind CSS**: Built-in styling framework
- **Error Handling**: Robust error handling and validation

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Anthropic API Key**
   ```bash
   export ANTHROPIC_API_KEY="your_api_key_here"
   # Or create a .env file with ANTHROPIC_API_KEY=your_key
   ```

3. **Ensure Node.js is Installed** (for running generated projects)
   ```bash
   node --version  # Should be v16+ 
   npm --version
   ```

## Usage

### Command Line

```bash
# Generate a project using multi-agent workflow (default)
python3 main.py "Create a personal blog"

# Generate a project using single-context mode
python3 main.py --single-context "Create a personal blog"

# Enter request interactively
python3 main.py

# Compare both generation modes
python3 test_single_context.py --compare
```