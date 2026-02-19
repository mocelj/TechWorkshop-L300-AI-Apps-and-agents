# Reusable Prompt: Expose an Azure AI Foundry Agent as an A2A Agent

> **How to use:** Copy everything below the line into a new conversation with an AI coding assistant (e.g., GitHub Copilot). Replace the `{{PLACEHOLDERS}}` with your specific values.

---

## The Prompt

```
I need to expose an Azure AI Foundry agent as an A2A (Agent-to-Agent protocol by Google) agent. 
Create a complete, standalone FastAPI web application following the architecture below.

## Agent Details

- **Agent Name**: {{AGENT_NAME}}  
  (e.g., "ProductManager", "InventoryAgent", "CustomerSupport")
- **Agent Description**: {{AGENT_DESCRIPTION}}  
  (e.g., "Manages product catalog, recommendations, and descriptions for Zava DIY store")
- **Agent Instructions (System Prompt)**: {{AGENT_INSTRUCTIONS}}  
  (e.g., "You are a product management assistant for Zava, a DIY home improvement store...")
- **Port**: {{PORT}} (default: 8001)
- **App Title**: {{APP_TITLE}} (e.g., "Zava Product Manager")

## Architecture & File Structure

Create the following files under a folder called `{{FOLDER_NAME}}/`:

```
{{FOLDER_NAME}}/
├── __init__.py
├── main.py                  # FastAPI entry point with A2A server mounting
├── gunicorn.conf.py         # Production server config for Azure App Service
├── agent/
│   ├── __init__.py
│   ├── {{AGENT_NAME_SNAKE}}_agent.py   # Agent logic using Microsoft Agent Framework
│   └── a2a_server.py        # A2A protocol server (wraps agent for A2A communication)
├── api/
│   ├── __init__.py
│   └── chat.py              # REST API endpoint for the web UI chat
├── static/
│   ├── css/style.css         # Chat UI styling
│   └── js/chat.js            # Chat UI JavaScript client
└── templates/
    └── index.html            # Chat web interface
```

## Technical Requirements

### 1. Agent File (`agent/{{AGENT_NAME_SNAKE}}_agent.py`)

Use **Microsoft Agent Framework** (`agent-framework` package) with these components:

- **Chat Service Factory**: Support both Azure OpenAI and OpenAI backends
  - Azure OpenAI: Support both API key auth (local dev) and Managed Identity (production)
  - Read config from environment variables: `gpt_endpoint`, `gpt_deployment`, `gpt_api_version`, `gpt_api_key`
  - Use `DefaultAzureCredential` + `get_bearer_token_provider` when no API key is set

- **Structured Response Format** (Pydantic model):
  ```python
  class ResponseFormat(BaseModel):
      status: Literal['input_required', 'completed', 'error'] = 'input_required'
      message: str
  ```

- **Agent Class** with these methods:
  - `__init__()`: Create a `ChatAgent` with the system prompt. The instructions MUST tell the agent to always respond in JSON format with the ResponseFormat schema.
  - `invoke(user_input, session_id) -> dict`: Synchronous A2A call (tasks/send). Returns `{is_task_complete, require_user_input, content}`
  - `stream(user_input, session_id) -> AsyncIterable[dict]`: Streaming A2A call (tasks/sendSubscribe)
  - `_get_agent_response(message) -> dict`: Parse structured JSON from agent into standardized response
  - `_ensure_thread_exists(session_id)`: Manage conversation threads per session
  - `SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']`

- **Tools**: Set `tools=[]` initially (placeholder for future `@ai_function` tools)

### 2. A2A Server File (`agent/a2a_server.py`)

Use the `a2a-sdk` package to create an A2A-compliant server:

- Implement an **Agent Card** with:
  - Agent name, description, version
  - Supported skills/capabilities  
  - Input/output content types
  - URL for the A2A endpoint

- Implement **task handlers**:
  - `tasks/send`: Calls `agent.invoke()` for synchronous requests
  - `tasks/sendSubscribe`: Calls `agent.stream()` for SSE streaming
  - `tasks/get`: Retrieve task status
  - `tasks/cancel`: Cancel running tasks

- Store tasks in an SQLite-backed task store (via `a2a-sdk[sqlite]`)

### 3. Main Application (`main.py`)

- FastAPI app with **lifespan** context manager for startup/shutdown
- On startup: create `httpx.AsyncClient`, initialize `A2AServer`, mount at `/a2a`
- On shutdown: close the httpx client
- Endpoints:
  - `GET /` → Serve chat HTML interface
  - `GET /health` → Health check for Azure App Service
  - `GET /agent-card` → Expose A2A Agent Card for discovery
- Mount static files at `/static`
- Include chat API router at `/api`

### 4. Chat API (`api/chat.py`)

- FastAPI router with `POST /chat/message` endpoint
- Accepts `{message: str, session_id: str}`
- Instantiates the agent, calls `invoke()`, returns `{response: str, session_id: str}`

### 5. Web UI (`templates/index.html`, `static/js/chat.js`, `static/css/style.css`)

- Clean chat interface with:
  - Header with agent name, "New Chat" button, connection status indicator
  - Welcome message with feature highlights and example prompts
  - Message area with user/assistant bubbles and timestamps
  - Typing indicator animation
  - Input textarea with character counter and send button
- JavaScript: `fetch('/api/chat/message')` to communicate via REST (not WebSocket)
- Responsive design for mobile

### 6. Gunicorn Config (`gunicorn.conf.py`)

```python
import os
bind = f"0.0.0.0:{os.environ.get('PORT', '{{PORT}}')}"
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 300
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "-"
errorlog = "-"
capture_output = True
enable_stdio_inheritance = True
```

## Environment Variables Needed

```
gpt_endpoint=https://your-resource.openai.azure.com/
gpt_deployment=gpt-4o
gpt_api_version=2025-01-01-preview
gpt_api_key=your-key-here          # Optional: omit for Managed Identity
HOST=0.0.0.0
PORT={{PORT}}
DEBUG=false
```

## Python Dependencies

```
agent-framework --pre
a2a-sdk[sqlite]
azure-identity
openai
fastapi
uvicorn[standard]
httpx
python-dotenv
sse-starlette
starlette
pydantic
```

## Key Design Principles

1. **Structured outputs only**: The agent MUST always return JSON matching `ResponseFormat`. This is enforced via both the system prompt instructions AND `response_format=ResponseFormat` in the agent's `run()` call.

2. **Dual interface**: The agent is accessible via:
   - A2A protocol (at `/a2a`) for agent-to-agent communication
   - REST API + Web UI (at `/` and `/api`) for human interaction

3. **Session management**: Each conversation gets a unique `session_id` that maps to an `AgentThread`, enabling multi-turn context.

4. **Auth flexibility**: API key for local development, Managed Identity for Azure production — determined automatically at startup.

5. **Production-ready**: Gunicorn config, health check endpoint, proper logging, graceful shutdown.
```

---

## Placeholder Reference

| Placeholder | Example | Description |
|---|---|---|
| `{{AGENT_NAME}}` | `ProductManager` | PascalCase agent name |
| `{{AGENT_NAME_SNAKE}}` | `product_management` | snake_case for filenames |
| `{{AGENT_DESCRIPTION}}` | `Manages product catalog...` | One-line description |
| `{{AGENT_INSTRUCTIONS}}` | `You are a product management...` | Full system prompt |
| `{{PORT}}` | `8001` | Port number (avoid 8000 if main app uses it) |
| `{{APP_TITLE}}` | `Zava Product Manager` | Display name in UI |
| `{{FOLDER_NAME}}` | `a2a_product_manager` | Root folder name |

## Example: Filled In for an Inventory Agent

```
- Agent Name: InventoryAgent
- Agent Name Snake: inventory
- Agent Description: Tracks product stock levels, manages reorders, and provides real-time inventory status for Zava stores
- Agent Instructions: You are an inventory management assistant for Zava. You help employees check stock levels, find products across store locations, and manage reorder requests. Always be precise with quantities and location data.
- Port: 8002
- App Title: Zava Inventory Agent
- Folder Name: a2a_inventory
```
