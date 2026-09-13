# 🎯 AI Movie Research Agent: Ultimate Technical Interview Masterclass

> **How to use this guide**: This document prepares you to confidently discuss this project in technical interviews for **AI Engineer**, **GenAI Developer**, and **Agentic Systems** roles.
> 
> Each question includes:
> - 🗣️ **How to Speak (Direct, Human & Impressive Answer)**: Conversational, confident English you can say out loud.
> - 💡 **Intuition (In-Depth Hinglish Breakdown)**: Clear mental model so you understand *why* it works that way.
> - 🔍 **Code & Protocol Hook**: The exact files and lines of code to reference.

---

## 📑 Table of Contents
1. [Elevator Pitch & Project Overview](#1-elevator-pitch--project-overview)
2. [Model Context Protocol (MCP) Deep-Dive](#2-model-context-protocol-mcp-deep-dive)
3. [LangGraph & Agent Orchestration](#3-langgraph--agent-orchestration)
4. [Dynamic Tool Discovery vs Hardcoding](#4-dynamic-tool-discovery-vs-hardcoding)
5. [Real-World Query Execution Traces](#5-real-world-query-execution-traces)
6. [Edge Cases, Guardrails & Hallucination Prevention](#6-edge-cases-guardrails--hallucination-prevention)
7. [External Host Interoperability (Claude / Cursor)](#7-external-host-interoperability-claude--cursor)
8. [Real Engineering Challenges & How We Solved Them](#8-real-engineering-challenges--how-we-solved-them)
9. [Scalability, Production Architecture & Trade-Offs](#9-scalability-production-architecture--trade-offs)
10. [Rapid-Fire One-Liner Cheat Sheet](#10-rapid-fire-one-liner-cheat-sheet)

---

## 1. Elevator Pitch & Project Overview

### Q1: "Can you give me a 60-second summary of this project?"

🗣️ **How to Speak:**
> *"I built an end-to-end AI Movie Research Agent designed to explore and implement Anthropic's Model Context Protocol (MCP) from scratch.*
> 
> *The system separates tool execution from agent reasoning: I have an independent Python MCP server running as an isolated subprocess that exposes movie database tools over standard I/O via JSON-RPC 2.0. On the client side, I built a cyclic LangGraph state machine powered by Groq's low-latency LPU inference.*
> 
> *The agent dynamically discovers the server's tools at runtime without hardcoding, binds their JSON schemas to the LLM, and executes tool calls across process boundaries. Furthermore, the exact same MCP server is consumable by external hosts like Claude Desktop, Claude Code, and Cursor IDE through standard configuration."*

💡 **Intuition:**
Interviewers want to see that you didn't just build a "wrapper around OpenAI". You built a **decoupled distributed architecture**:
- **Server**: Knows nothing about LangGraph or Groq; only knows JSON-RPC and movie data.
- **Client**: Knows how to orchestrate conversations and dynamically talk to any MCP server over stdio.

🔍 **Files to Reference**: [`server/mcp_server.py`](server/mcp_server.py), [`client/agent.py`](client/agent.py), [`client/main.py`](client/main.py).

---

### Q2: "Why didn't you just use a database like PostgreSQL or a Vector DB?"

🗣️ **How to Speak:**
> *"The primary objective was mastering the Model Context Protocol and agent lifecycle without infrastructure overhead. Using an embedded JSON dataset allowed me to keep the project completely portable, deterministic, and zero-dependency, while still providing realistic filtering queries like temporal lookups, director aggregations, and rating comparisons.*
> 
> *Because of the clean MCP boundary, swapping `movies.json` for PostgreSQL or SQLite requires changing only 10 lines in `server/mcp_server.py`. The MCP protocol contract, LangGraph agent, and Groq integration remain 100% untouched."*

---

## 2. Model Context Protocol (MCP) Deep-Dive

### Q3: "The Million-Dollar Question: Why do we need MCP when LangChain already has tools?"

🗣️ **How to Speak:**
> *"LangChain `@tool` functions are tightly coupled to a single language runtime and framework. If you write a tool in Python for LangChain, you cannot share it with a TypeScript backend, Cursor IDE, or Claude Desktop without completely rewriting it.*
> 
> *MCP solves the 'M x N connector problem'. Think of MCP as **USB-C for AI**:*
> 1. *It establishes a language-agnostic JSON-RPC 2.0 standard.*
> 2. *It runs tools in isolated processes, so a failing tool never crashes the host agent.*
> 3. *It enables write-once-use-anywhere: my movie server can be consumed by my LangGraph Python agent today, and by Claude Desktop or Cursor tomorrow without modifying a single line of server code."*

💡 **Intuition:**
- **LangChain tool**: In-process Python function. Proprietary to LangChain.
- **MCP tool**: Standard JSON-RPC microservice over `stdio` or `HTTP/SSE`. Works with any AI system in the world.

---

### Q4: "How does the MCP protocol handshake work over stdio?"

🗣️ **How to Speak:**
> *"When the client launches `server/mcp_server.py` as a child process with piped standard I/O, three sequential phases occur:*
> 1. ***`initialize`**: The client sends a JSON-RPC request containing its protocol version and capabilities. The server validates the version and responds with its capabilities and server info (`Movie-Server`).*
> 2. ***`tools/list`**: The client requests available tools. The server responds with an array of tool objects, each containing a name, description, and auto-generated JSON Schema.*
> 3. ***`tools/call`**: When the LLM decides to invoke a tool, the client dispatches a JSON-RPC request with arguments. The server executes the Python function, packages the return value into an MCP `CallToolResult`, and streams it back to `stdout`."*

🔍 **Wire Protocol Packets:**
```json
// tools/call request
{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_movie_details", "arguments": {"movie_id": 1}}}

// tools/call response
{"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "Title: Inception (2010)..."}]}}
```

---

### Q5: "What is FastMCP, and what does it handle vs what your code handles?"

🗣️ **How to Speak:**
> *"FastMCP is the high-level server interface in the official MCP Python SDK, analogous to FastAPI for REST.*
> 
> *It handles all boilerplate:*
> - *Spawns and manages standard I/O streaming.*
> - *Parses and serializes JSON-RPC 2.0 envelopes.*
> - *Inspects Python type annotations (`query: str`, `movie_id: int`) and docstrings to automatically generate standard JSON Schemas for LLM function calling.*
> 
> *My code only implements the domain logic: loading the dataset, performing substring/director matching, and formatting clean textual outputs."*

---

### Q6: "Why is `print()` strictly prohibited inside an MCP stdio server?"

🗣️ **How to Speak:**
> *"In stdio transport, standard input (`stdin`) and standard output (`stdout`) are strictly reserved as the bidirectional JSON-RPC 2.0 communication channel.*
> 
> *If you call standard `print("debug message")` inside the server, that raw string is written directly to `stdout`. The MCP client's parser expects a valid JSON-RPC frame and will immediately crash with a JSON parse error. If you need logging in an MCP server, you must write to `sys.stderr` or use standard Python logging."*

---

## 3. LangGraph & Agent Orchestration

### Q7: "Why use LangGraph instead of a simple linear LangChain chain or AgentExecutor?"

🗣️ **How to Speak:**
> *"Real-world agentic reasoning is fundamentally **cyclic**, not linear. A model might invoke tool A, inspect the result, realize it needs tool B, and only then formulate the answer.*
> 
> *LangChain's legacy `AgentExecutor` was a black-box loop with limited control. LangGraph models agent workflows as explicit directed state graphs using Pregel architecture:*
> 1. *It gives you full transparency over State transitions.*
> 2. *It allows fine-grained conditional routing via edges (`should_continue`).*
> 3. *It makes adding human-in-the-loop approvals, checkpoints, or multi-turn memory trivial."*

💡 **Intuition:**
Linear chain = `Input -> LLM -> Output` (Aise kaam nahi chalta agar tool call ka result wapas model ko dikhana ho).
LangGraph = `START -> Agent -> Conditional Edge (Tool call?) -> Tools Node -> Agent -> END`.

---

### Q8: "Explain the `AgentState` and the role of `add_messages`."

🗣️ **How to Speak:**
> *"In LangGraph, state is maintained as a typed dictionary:*
> ```python
> class AgentState(TypedDict):
>     messages: Annotated[Sequence[BaseMessage], add_messages]
> ```
> *The `Annotated[..., add_messages]` is a reducer pattern. By default in Python, updating a dictionary key overwrites its value. `add_messages` tells LangGraph: 'Do not overwrite the conversation; append incoming `HumanMessage`, `AIMessage`, and `ToolMessage` instances to the historical sequence.' This preserves the complete multi-turn dialogue context required for tool calling."*

🔍 **File Hook**: [`client/agent.py`](client/agent.py#L38-L40).

---

## 4. Dynamic Tool Discovery vs Hardcoding

### Q9: "How does the agent know which tool to call? Did you write if-else logic?"

🗣️ **How to Speak:**
> *"No, there is zero hardcoded keyword matching like `if 'rating' in query`. That anti-pattern breaks as soon as a user uses synonyms or a new tool is added.*
> 
> *Instead, the agent uses dynamic tool discovery:*
> 1. *During initialization, the client calls `session.list_tools()` over MCP.*
> 2. *The server returns JSON schemas for `search_movies`, `get_movie_details`, `get_director_movies`, and `get_movie_rating`.*
> 3. *The client dynamically binds these schemas to `ChatGroq` via `llm.bind_tools()`.*
> 4. *Groq's LLM reads the user prompt, matches semantic intent against the tool descriptions, and emits a structured `tool_calls` payload containing the chosen tool and arguments."*

---

## 5. Real-World Query Execution Traces

### Q10: "Walk me step-by-step through: 'Which Christopher Nolan movie has the highest rating?'"

🗣️ **How to Speak:**
> *"Here is the complete trace:*
> 1. ***User Prompt***: *Enters question in CLI.*
> 2. ***LangGraph State***: *Places `SystemMessage` and `HumanMessage` into `AgentState['messages']`.*
> 3. ***Model Node (`call_model`)***: *`ChatGroq` receives the prompt along with the 4 MCP tool schemas. It recognizes it needs movies directed by Nolan and emits `AIMessage(tool_calls=[{'name': 'get_director_movies', 'args': {'director': 'Christopher Nolan'}}])`.*
> 4. ***Conditional Routing (`should_continue`)***: *Detects `tool_calls` and branches to `'tools'` node.*
> 5. ***MCP Dispatch (`call_mcp_tools`)***: *Client writes a JSON-RPC `tools/call` frame across the stdio pipe to `server/mcp_server.py`.*
> 6. ***Server Execution***: *`mcp_server.py` runs `get_director_movies('Christopher Nolan')`, filters `data/movies.json`, and finds 10 movies (The Dark Knight 9.0, Oppenheimer 8.9, Inception 8.8, etc.).*
> 7. ***Response Stream***: *Server writes the result to `stdout`. Client wraps it into a LangChain `ToolMessage`.*
> 8. ***Loop Back to Model***: *LangGraph loops back to `call_model`. Groq receives the movie list with ratings, compares the numbers, identifies The Dark Knight with 9.0, and outputs the final natural-language response.*
> 9. ***Termination***: *`should_continue` detects no new tool calls and routes to `END`."*

---

## 6. Edge Cases, Guardrails & Hallucination Prevention

### Q11: "What happens if a user asks for a movie not in your dataset, like Titanic?"

🗣️ **How to Speak:**
> *"This was a critical design challenge. Without guardrails, an LLM receiving `'No movies found matching query: Titanic'` might enter an infinite loop trying different queries, or hallucinate that the movie was in our dataset.*
> 
> *To solve this, I designed a strict `SYSTEM_INSTRUCTION` in `client/agent.py`:*
> 1. *It mandates that the agent must query tools first.*
> 2. *If the tool returns no match, it instructs the LLM not to retry repeatedly.*
> 3. *It enforces that the LLM must explicitly disclose to the user that the title is not present in the local database.*
> 
> *In live testing for 'Tell me about Titanic', the agent calls `search_movies('Titanic')`, receives 'No movies found', and responds: 'I couldn't find a record for Titanic in the local database. However, from general knowledge: Titanic (1997) was directed by James Cameron...' This maintains complete honesty and prevents hallucinations."*

---

## 7. External Host Interoperability (Claude / Cursor)

### Q12: "How can Cursor IDE or Claude Desktop use your movie tools without your LangGraph client?"

🗣️ **How to Speak:**
> *"Because `server/mcp_server.py` strictly follows the MCP specification, any external MCP host can connect to it. I created standard configuration files: `.mcp.json` and `.cursor/mcp.json`.*
> 
> *These files tell the external host:*
> ```json
> {
>   "mcpServers": {
>     "movie-server": {
>       "command": "C:/path/to/.venv/Scripts/python.exe",
>       "args": ["server/mcp_server.py"]
>     }
>   }
> }
> ```
> *When Cursor or Claude Desktop launches, it reads this file, boots our Python script as a child process, negotiates the protocol, and makes our 4 tools available in their native AI chat interface. We verified this live with Claude Code CLI, which reports `movie-server: ... - √ Connected`."*

---

## 8. Real Engineering Challenges & How We Solved Them

### Q13: "Tell me about a couple of unexpected technical bugs you faced and how you debugged them."

🗣️ **How to Speak (This demonstrates deep real-world experience):**

> *"I faced three interesting engineering hurdles:*
> 
> 1. ***The FastMCP v1 vs v2 Renaming Breaking Change***:
>    *When installing the latest `mcp` SDK (v2.x), importing `from mcp.server.fastmcp import FastMCP` threw a `ModuleNotFoundError` because Anthropic renamed the class to `MCPServer` in v2.*
>    *I implemented a resilient fallback:*
>    ```python
>    try:
>        from mcp.server.fastmcp import FastMCP
>    except (ImportError, ModuleNotFoundError):
>        from mcp.server import MCPServer as FastMCP
>    ```
>    *This made the server immediately forward and backward compatible across SDK versions.*
> 
> 2. ***Windows Console `charmap` Codec Crash***:
>    *On Windows, PowerShell's default stdout encoding is legacy `charmap` (Windows-1252). Groq models often emit modern Unicode characters (like narrow non-breaking space `\u202f` or curly quotes). When printing the answer, Python crashed with a `UnicodeEncodeError`.*
>    *I resolved this by reconfiguring stdout at the entry point:*
>    ```python
>    if sys.platform == "win32":
>        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
>    ```
> 
> 3. ***Subprocess Stream Deadlocking***:
>    *Managing background server processes manually across multiple terminals creates port conflicts and dangling processes. I utilized `mcp.client.stdio.stdio_client` context managers, allowing the client to spawn the server subprocess, establish bidirectional async pipes, and clean up the process tree automatically upon exit."*

---

## 9. Scalability, Production Architecture & Trade-Offs

### Q14: "If you had to scale this to 10 million movies and 10,000 concurrent users, what would change?"

🗣️ **How to Speak:**
> *"I would evolve three layers:*
> 1. ***Transport Layer***: *`stdio` transport is designed for single-user local hosts (desktop apps, CLI tools). For web scale, I would transition the MCP server to **Streamable HTTP** or **Server-Sent Events (SSE)** running behind an API gateway with JWT/OAuth2 authentication.*
> 2. ***Data Layer***: *Replace `data/movies.json` with PostgreSQL containing pgvector for hybrid semantic search, backed by Redis for caching frequent tool queries.*
> 3. ***Agent Orchestration***: *Deploy LangGraph with Postgres Checkpointer for asynchronous long-running thread persistence, allowing users to pause, resume, and review historical conversations across distributed workers."*

---

## 10. Rapid-Fire One-Liner Cheat Sheet

| Question | Winning One-Liner Answer |
|---|---|
| **What is MCP?** | An open JSON-RPC standard by Anthropic connecting AI models to external tools and context providers like a universal USB-C. |
| **What transport do you use?** | `stdio` (standard input/output pipes), because it requires zero network configuration, has zero port collision risk, and is ultra-fast for local processes. |
| **How does tool calling work in LangGraph?** | The model outputs tool calls in an `AIMessage`, a conditional edge branches to the `tools` node, and the result loops back to the model as a `ToolMessage`. |
| **Why is Groq used?** | Groq's custom LPU hardware delivers ultra-low-latency inference, reducing agent loop execution times to milliseconds. |
| **Can external tools use this server?** | Yes, any MCP host like Claude Desktop or Cursor can connect directly via `.mcp.json`. |
| **How do you prevent hallucination?** | With a strict system prompt enforcing database-first tool execution and clear disclosure when a record is absent. |

---

<div align="center">
  <b>Practice these out loud, speak with confidence, and you will ace any AI Systems interview! 🚀</b>
</div>
