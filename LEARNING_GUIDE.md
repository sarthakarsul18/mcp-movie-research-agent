# 🎓 MCP & Agentic AI: The Ultimate From-Scratch Learning Guide

This document is an exhaustive educational companion to the **AI Movie Research Agent**. It walks through every architectural decision, wire protocol packet, and line of code across the system.

---

## 📑 Table of Contents
1. [The Big Picture](#1-the-big-picture)
2. [Deep Dive: The Model Context Protocol (MCP)](#2-deep-dive-the-model-context-protocol-mcp)
3. [The MCP Wire Protocol (JSON-RPC 2.0 Behind the Scenes)](#3-the-mcp-wire-protocol-json-rpc-20-behind-the-scenes)
4. [Line-by-Line Code Breakdown](#4-line-by-line-code-breakdown)
   - `server/mcp_server.py`
   - `client/agent.py`
   - `client/main.py`
5. [LangGraph Cyclic State Machine Anatomy](#5-langgraph-cyclic-state-machine-anatomy)
6. [Dynamic Tool Discovery vs Hardcoding](#6-dynamic-tool-discovery-vs-hardcoding)
7. [System Prompts, Hallucination Prevention & Guardrails](#7-system-prompts-hallucination-prevention--guardrails)
8. [External Host Integration Architecture](#8-external-host-integration-architecture)

---

## 1. The Big Picture

When building AI applications with tool calling, developers often wonder:
> *"Why can't the LLM just execute functions directly?"*

Large Language Models (LLMs) are **pure text prediction engines**. They have no internet access, no filesystem access, and no database socket.
To execute a tool:
1. The developer passes a **JSON Schema** describing the tool to the LLM.
2. The LLM produces a structured text payload: `{"name": "search_movies", "arguments": {"query": "Nolan"}}`.
3. An **orchestrator** intercepts that text, executes the actual code, and passes the result back to the LLM.

Before MCP, every AI framework invented its own way of defining and running tools. MCP replaces that chaos with a universal standard.

---

## 2. Deep Dive: The Model Context Protocol (MCP)

### What is MCP?
MCP is an open standard designed by Anthropic that defines how AI hosts (clients) connect to context providers and tools (servers).

### The Client-Server Relationship:
- **MCP Server**: Owns resources, prompts, and tools. Exposes them over standard transports (`stdio`, SSE, Streamable HTTP). Has **zero** awareness of what AI model or framework connects to it.
- **MCP Client**: Initiates connection, performs handshake negotiation, queries schemas, and sends execution requests.
- **MCP Host**: The application embedding the client (e.g. LangGraph CLI, Claude Desktop, Cursor IDE).

---

## 3. The MCP Wire Protocol (JSON-RPC 2.0 Behind the Scenes)

All communication over `stdio` consists of newline-delimited JSON-RPC 2.0 objects.

### Phase 1: Handshake (`initialize`)
The client launches the server subprocess and sends:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-11-25",
    "capabilities": {},
    "clientInfo": {"name": "python-mcp-client", "version": "1.0.0"}
  }
}
```
The server responds:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-11-25",
    "capabilities": {"tools": {}},
    "serverInfo": {"name": "Movie-Server", "version": "1.0.0"}
  }
}
```

### Phase 2: Tool Discovery (`tools/list`)
Client queries what tools are available:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```
Server responds with JSON Schemas generated automatically from your Python function signatures:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "search_movies",
        "description": "Search movies by title, director, actor, genre, or keyword in plot.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {"type": "string", "description": "Search term"}
          },
          "required": ["query"]
        }
      }
    ]
  }
}
```

### Phase 3: Tool Execution (`tools/call`)
When the LLM decides to call a tool, the client dispatches:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search_movies",
    "arguments": {"query": "Inception"}
  }
}
```
Server executes the Python function and returns:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 1 movie(s):\nID 1: Inception (2010) - Directed by Christopher Nolan, Rating: 8.8"
      }
    ]
  }
}
```

---

## 4. Line-by-Line Code Breakdown

### `server/mcp_server.py`

- **Import Compatibility**:
  ```python
  try:
      from mcp.server.fastmcp import FastMCP
  except (ImportError, ModuleNotFoundError):
      from mcp.server import MCPServer as FastMCP
  ```
  *Why*: In MCP Python SDK 1.x, the high-level server was `FastMCP`. In 2.x, it was renamed to `MCPServer`. This pattern makes the server compatible with any environment version.

- **FastMCP Tool Registration**:
  ```python
  @mcp.tool()
  def search_movies(query: str) -> str:
      """Search movies by title, director, actor, genre, or keyword in plot."""
  ```
  *Why*: The decorator inspects `query: str` (type annotation) and the docstring. It automatically converts them to JSON Schema properties without you writing manual JSON schemas!

- **Stdio Transport**:
  ```python
  if __name__ == "__main__":
      mcp.run(transport="stdio")
  ```
  *Why*: Binds the server to `sys.stdin` and `sys.stdout`. Crucial rule: **never call `print()` in an stdio MCP server**, because rogue text corrupts the JSON-RPC packet stream!

---

### `client/agent.py`

- **LangGraph State Definition**:
  ```python
  class AgentState(TypedDict):
      messages: Annotated[Sequence[BaseMessage], add_messages]
  ```
  *Why*: LangGraph requires explicit state definition. `add_messages` is a reducer function that appends incoming messages (human query, AI tool calls, tool responses) to history instead of overwriting.

- **Dynamic Tool Schema Translation**:
  ```python
  groq_tool_schemas = [
      {
          "type": "function",
          "function": {
              "name": tool.name,
              "description": tool.description or "",
              "parameters": getattr(tool, "input_schema", getattr(tool, "inputSchema", {})),
          },
      }
      for tool in mcp_tools
  ]
  llm_with_tools = llm.bind_tools(groq_tool_schemas)
  ```
  *Why*: Zero hardcoding. Whatever tools the MCP server advertises, the client maps directly into OpenAI/Groq function calling format.

- **Cyclic Execution Loop**:
  ```python
  workflow = StateGraph(AgentState)
  workflow.add_node("agent", call_model)
  workflow.add_node("tools", call_mcp_tools)
  workflow.set_entry_point("agent")
  workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
  workflow.add_edge("tools", "agent")
  ```
  *Why*: Sets up the agent cycle:
  `Agent (LLM)` ➔ checks if `tool_calls` present ➔ `Tools Node` dispatches across MCP ➔ returns result to `Agent (LLM)` ➔ no more tools ➔ `END`.

---

## 5. LangGraph Cyclic State Machine Anatomy

Unlike simple linear pipelines (LangChain LCEL `prompt | llm | parser`), AI agents require **cycles**:
1. The model might call tool A.
2. The result might reveal that tool B is needed.
3. The model might need to iterate until it has all necessary data.

LangGraph implements this using a directed graph where state transitions are explicit, debuggable, and interruptible.

---

## 6. Dynamic Tool Discovery vs Hardcoding

### ❌ The Anti-Pattern (Hardcoding):
```python
# Hardcoded client - fragile and violates MCP philosophy:
if "rating" in user_query:
    call_mcp("get_movie_rating")
```
Problems: Breaks if the user uses synonyms ("how good is Inception?"), breaks if new tools are added to the server, and tightly couples client to server.

### ✅ The MCP Standard (Dynamic Discovery):
1. Client connects and asks: `tools/list`.
2. Server returns all registered tools with descriptions.
3. Client registers them dynamically with the LLM.
4. The LLM chooses tools based on semantic reasoning.

---

## 7. System Prompts, Hallucination Prevention & Guardrails

When a user asks for a movie not present in `movies.json` (e.g. *Titanic*):
Without a `SystemMessage`, the model may get confused after receiving `"No movies found"` and enter an infinite retry loop or hallucinate.

Our solution in `client/agent.py`:
```python
SYSTEM_INSTRUCTION = (
    "You are an AI Movie Research Assistant with access to an MCP-powered local movie database.\n"
    "Rules:\n"
    "1. Always check your tools first to answer movie questions from the local database.\n"
    "2. If a movie or director is not found in the database results, do not keep trying repeated tool calls. "
    "Clearly inform the user that the movie/director is not present in the local database.\n"
    "3. You may provide a brief helpful summary from your general knowledge, but you MUST explicitly state "
    "that this movie is not in your database records."
)
```
This produces transparent, honest, and grounded AI responses.

---

## 8. External Host Integration Architecture

Because `server/mcp_server.py` implements the standard protocol, any external host can consume it using [`.mcp.json`](.mcp.json):

```
+-------------------+
|  Claude Desktop   |
|   or Cursor IDE   |
+---------+---------+
          |
          | Reads .mcp.json:
          | command: .venv/Scripts/python.exe
          | args: ["server/mcp_server.py"]
          v
+-------------------+
|  MCP Server       |
| (mcp_server.py)   |
+-------------------+
```

This is the ultimate promise of MCP: **Write your tool server once; consume it anywhere.**
