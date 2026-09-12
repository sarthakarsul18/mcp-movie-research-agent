<div align="center">

# 🎬 AI Movie Research Agent
### *End-to-End Model Context Protocol (MCP) + LangGraph + LangChain + Groq*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Official%20SDK-purple.svg?logo=anthropic&logoColor=white)](https://modelcontextprotocol.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-v1.2%2B-orange.svg?logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![LangChain](https://img.shields.io/badge/LangChain-v1.4%2B-green.svg)](https://python.langchain.com/)
[![Groq LPU](https://img.shields.io/badge/Groq-LPU%20Inference-red.svg?logo=groq&logoColor=white)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <b>A production-clean, transparent, from-scratch educational implementation of Anthropic's Model Context Protocol (MCP)</b><br>
  <i>Connecting an independent Python MCP server over standard I/O (<code>stdio</code>) with a LangGraph agent powered by Groq LLM — ready for both custom Python clients and external hosts (Claude Desktop, Cursor, Claude Code).</i>
</p>

[Key Features](#-key-features) • [Architecture](#-system-architecture) • [Quick Start](#-quick-start) • [How It Works](#-how-it-works-step-by-step) • [External Hosts](#-connecting-external-hosts) • [Learning Guide](#-the-10-core-concepts-explained) • [Line-by-Line Code Guide](CODE_EXPLANATION.md)

---

</div>

## 🌟 Key Features

- **Genuine MCP Client-Server Separation**: The MCP Server (`server/mcp_server.py`) and Client (`client/agent.py`) run in completely separate OS processes communicating over standard I/O (`stdio`) via JSON-RPC 2.0.
- **Dynamic Tool Discovery**: No tools are hardcoded in the agent. The client queries `session.list_tools()` at runtime and dynamically converts JSON schemas for the LLM.
- **Dynamic LLM Decision Making**: The Groq LLM inspects natural language prompts and selects tools autonomously. Zero keyword matching (`if "rating" in query`).
- **Autonomous Stdio Process Management**: The CLI launches and cleans up the local MCP server subprocess automatically. No need to manage multiple terminals.
- **Observable Execution Stream**: Clean lifecycle events logged in real time: handshake negotiation, tool schema discovery, JSON-RPC dispatches, and final reasoning.
- **External Host Interoperability**: Compatible out of the box with **Claude Desktop**, **Cursor IDE**, and **Claude Code CLI** via standard [`.mcp.json`](.mcp.json).
- **Graceful Fallback & Guardrails**: Handles missing movie records cleanly with structured system messages, avoiding hallucinations and infinite loops.
- **Zero Heavyweight Bloat**: No Docker, no vector databases, no Postgres, no Redis, no frontend framework. Pure, readable Python.

---

## 🏗️ System Architecture

```
                                  +-----------------------------------------------------+
                                  |                     USER PROMPT                     |
                                  | "Which Christopher Nolan movie has highest rating?" |
                                  +--------------------------+--------------------------+
                                                             |
                                                             v
+------------------------------------------------------------+------------------------------------------------------------+
| CLIENT PROCESS                                                                                                          |
|                                                                                                                         |
|   +-----------------------------------------------------------------------------------------------------------------+   |
|   | LangGraph Cyclic State Machine (client/agent.py)                                                                |   |
|   |                                                                                                                 |   |
|   |         +-----------------------+           Tool Call Decided           +----------------------------------+    |   |
|   |  START  |      call_model       | ------------------------------------> |          call_mcp_tools          |    |   |
|   |  -----> |   (ChatGroq Node)     | <------------------------------------ |      (Dispatches to MCP)         |    |   |
|   |         +-----------------------+              ToolMessage              +----------------------------------+    |   |
|   |                     |                                                                    |                      |   |
|   |                     | No more tools                                                      | session.call_tool()  |   |
|   |                     v                                                                    v                      |   |
|   |                   [END]                                                       +----------------------+          |   |
|   |                                                                               | MCP ClientSession    |          |   |
|   +-------------------------------------------------------------------------------+----------------------+----------+   |
|                                                                                              |                          |
+----------------------------------------------------------------------------------------------|--------------------------+
                                                                                               |
                                             JSON-RPC 2.0 Wire Messages over stdio Pipe        | (stdin / stdout)
                                                                                               v
+-------------------------------------------------------------------------------------------------------------------------+
| SERVER SUBPROCESS (server/mcp_server.py)                                                                                |
|                                                                                                                         |
|       +------------------------+             +-------------------------+             +--------------------------+       |
|       |   FastMCP JSON-RPC     |             |       Movie Tools       |             |     Curated Dataset      |       |
|       |      Dispatcher        | ----------> |  - search_movies        | ----------> |     data/movies.json     |       |
|       | (initialize/list/call) |             |  - get_movie_details    |             |       (20 Records)       |       |
|       +------------------------+             |  - get_director_movies  |             +--------------------------+       |
|                                              |  - get_movie_rating     |                                                |
|                                              +-------------------------+                                                |
+-------------------------------------------------------------------------------------------------------------------------+
```

---

## 📁 Repository Structure

```
mcp-movie-research-agent/
│
├── .env.example              # Environment variables template
├── .env                      # Active environment file (ignored by git)
├── .gitignore                # Protects secrets (.env) and virtual environments (.venv)
├── .mcp.json                 # Standard MCP configuration for external hosts
├── requirements.txt          # Pinned lightweight dependencies
├── README.md                 # Complete showcase & architecture guide
├── CODE_EXPLANATION.md       # Exhaustive line-by-line code explanation manual
├── LEARNING_GUIDE.md         # MCP Wire-protocol & theoretical deep dive
│
├── .cursor/
│   └── mcp.json              # Instant configuration for Cursor IDE
│
├── data/
│   └── movies.json           # 20 curated movie profiles (Nolan, Tarantino, Scorsese, etc.)
│
├── server/
│   └── mcp_server.py         # Standalone FastMCP Server over stdio
│
└── client/
    ├── agent.py              # MCP Client bridge + LangGraph cyclic workflow
    └── main.py               # Unified CLI runner (Interactive, One-shot, & Verifications)
```

---

## ⚡ Quick Start

### 1. Clone & Navigate
```bash
git clone https://github.com/sarthakarsul18/mcp-movie-research-agent.git
cd mcp-movie-research-agent
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# (Or on Linux/macOS: source .venv/bin/activate)

# Install dependencies
pip install -r requirements.txt
```

### 3. Add Your Groq API Key
Copy the example file and add your free Groq key from [console.groq.com](https://console.groq.com/keys):
```bash
cp .env.example .env
```
Inside `.env`:
```env
GROQ_API_KEY=gsk_your_actual_key_here
```

---

## 🎮 Running the Agent

### Mode 1: Interactive Conversational Loop (Recommended)
The client automatically launches the MCP Server in the background:
```bash
python client/main.py
```
```text
=======================================================
        AI MOVIE RESEARCH AGENT (MCP + LANGGRAPH)     
=======================================================
[EVENT] Starting local MCP Server subprocess: mcp_server.py...
[EVENT] MCP Server process started. Establishing ClientSession...
[EVENT] Sending MCP 'initialize' handshake...
[EVENT] MCP Connected! Server: Movie-Server (Protocol: 2025-11-25)
[EVENT] Requesting tool list via 'tools/list'...
[EVENT] Successfully discovered 4 MCP tool(s):
        * search_movies: Search movies by title, director, actor, genre, or keyword in plot.
        * get_movie_details: Get complete details for a specific movie by its integer ID.
        * get_director_movies: Get all movies directed by a specific director name.
        * get_movie_rating: Get the rating for a specific movie by its integer ID.

-------------------------------------------------------
Interactive Movie Research Agent Ready!
Enter question: Which Christopher Nolan movie has the highest rating?
```

### Mode 2: One-Shot Direct Questions
Run any question straight from your terminal:
```bash
python client/main.py "Which Christopher Nolan movie has the highest rating?"
python client/main.py "Tell me about Inception"
python client/main.py "Find movies directed by Christopher Nolan after 2010"
python client/main.py "Tell me about Titanic"
```

---

## 🧪 Built-In Verification Test Suites

### 1. Complete Internal Protocol & Agent Verification
Tests `initialize`, `tools/list`, `tools/call`, and the full LangGraph loop:
```bash
python client/main.py --verify
```
<details>
<summary><b>Click to view output log</b></summary>

```text
[STEP 1] Testing 'tools/list'...
  -> Tools found: ['search_movies', 'get_movie_details', 'get_director_movies', 'get_movie_rating']
  [PASS] All 4 expected MCP tools are present and advertised with JSON schemas.

[STEP 2] Testing 'tools/call' directly over MCP stdio...
  -> Result preview: Found 1 movie(s): ID 1: Inception (2010) - Directed by Christopher Nolan, Rating: 8.8
  [PASS] Direct MCP tool call succeeded via stdio protocol.

[STEP 3] Testing 'tools/call' for get_movie_rating(movie_id=1)...
  -> Result: Movie: 'Inception' (ID: 1) has a rating of 8.8 / 10.
  [PASS] Direct rating tool call succeeded.

[STEP 4] Testing End-to-End Agent Workflow (LangGraph + MCP Server)...
FINAL ANSWER:
The Christopher Nolan film with the highest rating is "The Dark Knight" (2008), rated 9.0.
  [PASS] Full End-to-End Agent + MCP verification succeeded!
```
</details>

### 2. External Host Verification (`.mcp.json`)
Proves that an external host (Claude Desktop / Cursor) can launch and use the server:
```bash
python client/main.py --verify-external
```
```text
=================================================================
VERIFYING EXTERNAL HOST CONNECTION VIA .mcp.json
=================================================================
[STEP 1] External Host Initialized -> Connected to 'Movie-Server'
[STEP 2] External Host Discovered Tools: ['search_movies', 'get_movie_details', 'get_director_movies', 'get_movie_rating']
[STEP 3] External Host Calling 'search_movies' (query='Christopher Nolan')... [PASS]
[STEP 4] External Host Calling 'get_movie_details' (movie_id=1)... [PASS]
EXTERNAL HOST VERIFICATION SUCCESSFUL!
```

---

## 🔌 Connecting External Hosts

Because `server/mcp_server.py` adheres strictly to the official standard, any external MCP host can consume it immediately.

### 1. Claude Code CLI
Already verified on the system:
```bash
claude mcp add --scope user movie-server "path/to/.venv/Scripts/python.exe" "path/to/server/mcp_server.py"
claude mcp list
# Outputs: movie-server: ... - √ Connected
```

### 2. Cursor IDE
Open this project folder in Cursor. [`.cursor/mcp.json`](.cursor/mcp.json) is automatically detected:
```json
{
  "mcpServers": {
    "movie-server": {
      "command": "C:\\Users\\Care\\Desktop\\MCP From Scratch\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\Care\\Desktop\\MCP From Scratch\\server\\mcp_server.py"]
    }
  }
}
```
Navigate to **Cursor Settings ➔ Features ➔ MCP** to see all 4 tools active with a green indicator!

### 3. Claude Desktop
Add the configuration to `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS). Restart Claude Desktop to see the tools hammer icon (🔨).

---

## 💡 The "Million Dollar Question": Why MCP If LangChain Already Has Tools?

| Dimension | Traditional LangChain `@tool` | Model Context Protocol (MCP) |
|---|---|---|
| **Ecosystem Lock-In** | Locked to LangChain in Python. Cannot be reused in TypeScript, Claude Desktop, Cursor, or Go. | **Universal standard**. Write once, use in LangChain, LangGraph, Claude, Cursor, or custom apps. |
| **Process Boundary** | Runs directly inside the agent memory space. Crashes take down the whole agent. | **Isolated subprocess**. Runs over `stdio`/HTTP; sandboxed, crash-resilient, and secure. |
| **Language Agnostic** | Must be implemented in Python to work with Python agents. | An MCP server in Go/Rust/TypeScript can be consumed by a Python LangGraph agent seamlessly. |
| **Architectural Analogy** | Proprietary internal connector cable. | **USB-C for AI applications.** |

---

## 📖 The 10 Core Concepts Explained

1. **MCP (Model Context Protocol)**: The open protocol standardizing how AI applications connect to external tools and data sources.
2. **MCP Server**: An independent service exposing tools, prompts, or resources ([`server/mcp_server.py`](server/mcp_server.py)).
3. **MCP Client**: The client component connecting to the server over a transport ([`client/agent.py`](client/agent.py)).
4. **MCP Tool**: A callable function with an advertised name, description, and JSON Schema input definition.
5. **MCP Protocol**: The JSON-RPC 2.0 message frames exchanged over `stdin`/`stdout`.
6. **LangChain**: Orchestration library providing abstractions for LLMs, prompt management, and message formats (`ChatGroq`, `HumanMessage`, `ToolMessage`).
7. **LangGraph**: Framework for cyclical, stateful AI agent workflows (`StateGraph`, nodes, conditional edges).
8. **Groq**: Ultra-low-latency LPU inference engine powering the LLM.
9. **LLM**: Large Language Model (`openai/gpt-oss-20b`) providing semantic reasoning and tool selection.
10. **AI Agent**: The complete autonomous loop pairing the LLM with state memory, tools, and execution control.

---

## 🛡️ Missing Movie Fallback Workflow

What happens if a user asks about a movie **not** in `data/movies.json` (e.g. *Titanic* or *Avatar*)?
1. **Query**: User asks *"Tell me about Titanic"*.
2. **Search**: Agent dispatches `search_movies("Titanic")` to the MCP Server.
3. **Result**: Server returns `"No movies found matching query: 'Titanic'"`.
4. **Guardrail**: The `SYSTEM_INSTRUCTION` guides the LLM not to loop endlessly.
5. **Response**: The agent clearly informs the user that the title is not in the local database records, then provides a helpful general summary.

---

## 🤝 Contributing & License

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/sarthakarsul18/mcp-movie-research-agent/issues).

Distributed under the **MIT License**. See `LICENSE` for more information.

<div align="center">
  <b>Built with ❤️ for the AI & MCP Developer Community</b><br>
  <i>Star ⭐ this repository if you found it helpful!</i>
</div>
