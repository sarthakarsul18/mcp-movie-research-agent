# 📖 Complete Line-by-Line Code Explanation & Architecture Manual

This document provides a comprehensive, line-by-line breakdown of **every single file and every single line of code** in the entire project.

For each file, you will find:
1. **The Code Block**: Exact lines from the source.
2. **Kyun Use Kiya? (Why it was written)**: The core rationale and problem it solves.
3. **Kaise Kaam Karta Hai? (How it works under the hood)**: Low-level mechanics and protocol details.
4. **Aage Kya Use Hai? (Future uses & production relevance)**: How this pattern scales in real-world systems.

---

## 📑 File Navigation
1. [`requirements.txt`](#1-requirementstxt)
2. [`.env.example`](#2-envexample)
3. [`.gitignore`](#3-gitignore)
4. [`.mcp.json`](#4-mcpjson)
5. [`.cursor/mcp.json`](#5-cursormcpjson)
6. [`data/movies.json`](#6-datamoviesjson)
7. [`server/mcp_server.py`](#7-servermcp_serverpy)
8. [`client/agent.py`](#8-clientagentpy)
9. [`client/main.py`](#9-clientmainpy)

---

# 1. `requirements.txt`

```text
# Model Context Protocol (MCP) Official SDK
mcp>=1.3.0

# LangChain & LangGraph
langchain>=0.3.0
langchain-core>=0.3.0
langchain-groq>=0.2.0
langgraph>=0.2.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
```

### Line-by-Line Breakdown:
- **`mcp>=1.3.0`**:
  - *Kyun*: Anthropic ka official Model Context Protocol SDK hai. Yeh stdio transport, JSON-RPC 2.0 frames, aur server/client session primitives provide karta hai.
  - *Aage Use*: Kisi bhi MCP-compatible tool, server, ya client ko Python me banane ke liye yeh foundation library hai.
- **`langchain>=0.3.0` & `langchain-core>=0.3.0`**:
  - *Kyun*: Base message types (`HumanMessage`, `AIMessage`, `ToolMessage`, `SystemMessage`) aur tool bindings ka standard format provide karta hai.
  - *Aage Use*: Multi-modal LLM integrations, prompt templates, aur output parsing ke liye universal standard.
- **`langchain-groq>=0.2.0`**:
  - *Kyun*: Groq ke high-speed LPU inference engine ko LangChain ke `ChatGroq` class ke sath connect karta hai.
  - *Aage Use*: Ultra-low latency tool calling (sub-second responses) ke liye production me use hota hai.
- **`langgraph>=0.2.0`**:
  - *Kyun*: State machine graph banata hai (`StateGraph`, `START`, `END`). Cyclic agent workflows (LLM -> Tool -> LLM) ko handle karta hai.
  - *Aage Use*: Complex multi-step reasoning, human-in-the-loop approvals, aur persistent session checkpoints ke liye industry standard hai.
- **`python-dotenv>=1.0.0`**:
  - *Kyun*: `.env` file se sensitive environment variables (jaise `GROQ_API_KEY`) ko `os.environ` me load karta hai bina code me hardcode kiye.
  - *Aage Use*: Secrets security (12-Factor App methodology).
- **`pydantic>=2.0.0`**:
  - *Kyun*: MCP tools ke input arguments ka JSON Schema generate aur validate karta hai.
  - *Aage Use*: Type-safety aur API data validation.

---

# 2. `.env.example`

```bash
# Groq API Key for LangChain Groq model
# Get your free API key at: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here
```

### Line-by-Line Breakdown:
- **`GROQ_API_KEY=your_groq_api_key_here`**:
  - *Kyun*: Ek safe placeholder template hai. Yeh batata hai ki project ko chalane ke liye kaunsi key chahiye.
  - *Aage Use*: GitHub par `.env` push nahi hota, lekin `.env.example` dekh kar koi bhi naya developer samajh jata hai ki use `.env` me kya rakhna hai.

---

# 3. `.gitignore`

```text
.venv/
__pycache__/
*.pyc
.env
.DS_Store
.claude/
```

### Line-by-Line Breakdown:
- **`.venv/`**: Virtual environment ke heavy binaries (Python interpreter, pip packages) ko git me commit hone se rokta hai.
- **`__pycache__/` & `*.pyc`**: Python ke compiled bytecode cache ko git se bahar rakhta hai taaki repo clean rahe.
- **`.env`**: **Sabse critical line!** Isme user ki private Groq API key hoti hai. Is line ki wajah se API key kabhi bhi public GitHub repo me leak nahi hoti.
- **`.DS_Store`**: macOS metadata junk files ko ignore karta hai.
- **`.claude/`**: Claude CLI ki machine-specific local settings ko gitignore karta hai.

---

# 4. `.mcp.json`

```json
{
  "mcpServers": {
    "movie-server": {
      "type": "stdio",
      "command": "C:\\Users\\Care\\Desktop\\MCP From Scratch\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\Care\\Desktop\\MCP From Scratch\\server\\mcp_server.py"
      ],
      "env": {}
    }
  }
}
```

### Line-by-Line Breakdown:
- **`"mcpServers"`**: Anthropic MCP ka universal configuration key hai jise Claude Desktop, Cursor, aur Claude Code recognise karte hain.
- **`"movie-server"`**: Server ka friendly identifier name.
- **`"type": "stdio"`**: Transport mechanism batata hai ki communication standard input/output streams ke through hogi (koi network port block hone ka issue nahi).
- **`"command"`**: Virtual environment ke Python binary ka absolute path. Yeh ensure karta hai ki sahi Python environment execute ho jisme `mcp` installed hai.
- **`"args"`**: Python script ka path jo execute honi hai (`server/mcp_server.py`).
- **`"env": {}`**: Server process ke liye custom environment variables (agar chahiye ho).
- *Aage Use*: Koi bhi external tool (Cursor, Claude Desktop, VS Code extension) is single file ko dekh kar aapke MCP server se connect ho sakta hai.

---

# 5. `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "movie-server": {
      "command": "C:\\Users\\Care\\Desktop\\MCP From Scratch\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\Care\\Desktop\\MCP From Scratch\\server\\mcp_server.py"
      ]
    }
  }
}
```

### Line-by-Line Breakdown:
- *Kyun*: Cursor IDE project-level MCP configurations ke liye `.cursor/mcp.json` path expect karta hai.
- *Aage Use*: Jaise hi aap is project ko Cursor me open karte hain, Cursor automatically `movie-server` ko detect karke green status dikha deta hai aur Cursor AI composer me `@movie-server` tool available ho jata hai.

---

# 6. `data/movies.json`

```json
[
  {
    "id": 1,
    "title": "Inception",
    "year": 2010,
    "director": "Christopher Nolan",
    "genre": ["Action", "Sci-Fi", "Thriller"],
    "rating": 8.8,
    "actors": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page", "Tom Hardy"],
    "plot": "A thief who steals corporate secrets through the use of dream-sharing technology..."
  },
  ...
]
```

### Line-by-Line Breakdown:
- **`id` (int)**: Unique identifier. Tool calls jaise `get_movie_details(movie_id=1)` aur `get_movie_rating(movie_id=1)` ke liye primary key ka kaam karta hai.
- **`title` & `director` (str)**: Search matching aur filtering ke liye use hote hain.
- **`year` (int)**: Temporal queries jaise *"after 2010"* ko answer karne me madad karta hai.
- **`rating` (float)**: Numerical comparison queries jaise *"highest rating"* ka calculation allow karta hai.
- **`actors` & `genre` (list of str)**: Substring filtering aur category matching ke liye.
- **`plot` (str)**: Semantic context summary.
- *Aage Use*: Heavy SQL database (PostgreSQL/MySQL) ke bina ek lightweight, portable, deterministic data source provide karta hai.

---

# 7. `server/mcp_server.py`

### Block 1: Imports & Version Compatibility (Lines 24–33)
```python
import json
import os
from pathlib import Path
from typing import Any, Dict, List
try:
    # MCP v1.x import
    from mcp.server.fastmcp import FastMCP
except (ImportError, ModuleNotFoundError):
    # MCP v2.x import (FastMCP was renamed to MCPServer in mcp 2.x)
    from mcp.server import MCPServer as FastMCP
```
- **Line 24–27**: Standard library imports:
  - `json`: `movies.json` ko parse karne ke liye.
  - `Path`: Cross-platform (Windows/Linux/Mac) file paths handle karne ke liye.
  - `typing`: Type annotations ke liye jo MCP me auto-schema banate hain.
- **Line 28–33 (`try/except`)**:
  - *Kyun*: MCP Python SDK v1.x me class ka naam `FastMCP` tha. v2.x me Anthropic ne ise rename karke `MCPServer` kar diya.
  - *Fayda*: Yeh 5 lines code ko 100% backward aur forward compatible bana deti hain. Chahe koi purana version chalaye ya naya, code crash nahi hoga.

---

### Block 2: Server Initialization & Data Loading (Lines 40–51)
```python
mcp = FastMCP("Movie-Server")
DATA_FILE = Path(__file__).parent.parent / "data" / "movies.json"

def _load_movies() -> List[Dict[str, Any]]:
    """Helper function to load movie records from data/movies.json."""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
```
- **Line 40 (`mcp = FastMCP("Movie-Server")`)**:
  - *Kyun*: FastMCP server application instance create karta hai. `"Movie-Server"` identifier client ko handshake ke dauran bheja jata hai.
- **Line 43 (`DATA_FILE = ...`)**:
  - *Kyun*: Path ko current file ke relative calculate karta hai. Agar server ko kisi aur folder se bhi run kiya jaye, tab bhi path fail nahi hota.
- **Line 46–51 (`_load_movies()`)**:
  - *Kyun*: Data safety helper. Agar file miss ho to empty list return karta hai, crash nahi hone deta. Har call par fresh read allow karta hai.

---

### Block 3: Tool 1 — `search_movies` (Lines 63–96)
```python
@mcp.tool()
def search_movies(query: str) -> str:
    """Search movies by title, director, actor, genre, or keyword in plot."""
    movies = _load_movies()
    q = query.strip().lower()
    matches = []

    for m in movies:
        if q in m["title"].lower() or q in m["director"].lower():
            matches.append(m)
            continue
        if any(q in actor.lower() for actor in m.get("actors", [])):
            matches.append(m)
            continue
        if any(q in genre.lower() for genre in m.get("genre", [])):
            matches.append(m)
            continue
        if q in m.get("plot", "").lower():
            matches.append(m)
            continue

    if not matches:
        return f"No movies found matching query: '{query}'"

    results = [
        f"ID {m['id']}: {m['title']} ({m['year']}) - Directed by {m['director']}, Rating: {m['rating']}"
        for m in matches
    ]
    return f"Found {len(matches)} movie(s):\n" + "\n".join(results)
```
- **Line 63 (`@mcp.tool()`)**:
  - *Kyun*: Function ko MCP tool ke taur par register karta hai. FastMCP is function ka naam, docstring, aur `query: str` ko inspect karke valid JSON Schema auto-generate karta hai.
- **Line 66–87**:
  - Case-insensitive substring matching perform karta hai across: Title, Director, Actors, Genre, aur Plot.
- **Line 88–89**:
  - Agar koi match nahi milta, toh standard string return karta hai taaki LLM ko pata chale ki data nahi hai.
- **Line 92–96**:
  - LLM ke token budget ko dhyan me rakhte hue ek concise, high-signal summary string format karta hai (ID, Title, Year, Director, Rating).

---

### Block 4: Tool 2 — `get_movie_details` (Lines 100–114)
```python
@mcp.tool()
def get_movie_details(movie_id: int) -> str:
    """Get complete details for a specific movie by its integer ID."""
    movies = _load_movies()
    for m in movies:
        if m["id"] == movie_id:
            return (
                f"Title: {m['title']} ({m['year']})\n"
                f"ID: {m['id']}\n"
                f"Director: {m['director']}\n"
                f"Rating: {m['rating']} / 10\n"
                f"Genres: {', '.join(m.get('genre', []))}\n"
                f"Actors: {', '.join(m.get('actors', []))}\n"
                f"Plot: {m.get('plot', 'N/A')}"
            )
    return f"Error: Movie with ID {movie_id} was not found."
```
- **Line 100 (`movie_id: int`)**:
  - Type hint `int` hone ki wajah se FastMCP JSON Schema me `"type": "integer"` declare karta hai. LLM string ke bajaye number pass karta hai.
- **Line 105–113**:
  - Jab user specific movie ki deep information mangta hai (jaise *"Tell me about Inception"*), toh yeh full plot, actors, genres, aur rating return karta hai.

---

### Block 5: Tool 3 — `get_director_movies` (Lines 118–131)
```python
@mcp.tool()
def get_director_movies(director: str) -> str:
    """Get all movies directed by a specific director name."""
    movies = _load_movies()
    d_query = director.strip().lower()
    matches = [m for m in movies if d_query in m["director"].lower()]

    if not matches:
        return f"No movies found directed by '{director}'"

    results = [
        f"- ID {m['id']}: {m['title']} ({m['year']}) | Rating: {m['rating']} | Genres: {', '.join(m.get('genre', []))}"
        for m in matches
    ]
    return f"Movies directed by {matches[0]['director']} ({len(matches)} total):\n" + "\n".join(results)
```
- **Kyun**: Queries jaise *"Which Christopher Nolan movie has the highest rating?"* ke liye yeh most optimal tool hai.
- Ek hi request me us director ki saari movies ratings ke sath return kar deta hai, jisse LLM turant compare karke highest rating determine kar leta hai.

---

### Block 6: Tool 4 — `get_movie_rating` (Lines 135–141)
```python
@mcp.tool()
def get_movie_rating(movie_id: int) -> str:
    """Get the rating for a specific movie by its integer ID."""
    movies = _load_movies()
    for m in movies:
        if m["id"] == movie_id:
            return f"Movie: '{m['title']}' (ID: {m['id']}) has a rating of {m['rating']} / 10."
    return f"Error: Movie with ID {movie_id} was not found."
```
- **Kyun**: Jab user sirf rating poochna chahe (e.g. *"What is the rating of movie ID 2?"*), toh plot aur cast ka unnecessary token payload bhej kar context window waste karne ki zaroorat nahi hoti.

---

### Block 7: Server Entrypoint (Lines 147–150)
```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```
- **Line 147–150**:
  - `transport="stdio"`: Server standard input se JSON-RPC 2.0 requests read karta hai aur standard output par responses likhta hai.
  - **Golden Rule of MCP**: Stdio server ke andar normal `print()` nahi lagana chahiye, kyunki standard print stdout stream ko corrupt kar dega jisse JSON-RPC frame parse error aa jayega.

---

# 8. `client/agent.py`

### Block 1: Imports & Setup (Lines 16–31)
```python
import os
from typing import Annotated, Any, Dict, List, Sequence
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from mcp import ClientSession

load_dotenv()
```
- `Annotated` & `add_messages`: LangGraph state management me messages list ko append karne ke liye reducer.
- `ClientSession`: MCP SDK ka core client class jo server se handshake aur tool calling karta hai.
- `load_dotenv()`: `.env` file se API keys memory me load karta hai.

---

### Block 2: LangGraph State Definition (Lines 38–40)
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
```
- **Kyun**: LangGraph ek stateful graph hai. Is state me `messages` store hoti hain.
- `add_messages` ka role: Jab naya message aata hai (jaise user ka sawaal, LLM ka tool call decision, ya tool ka result), toh purani list replace nahi hoti, balki naya message end me jud (append) jata hai.

---

### Block 3: Offline Mock LLM (Lines 48–72)
```python
class MockChatGroq:
    async def ainvoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        has_tool_message = any(isinstance(m, ToolMessage) for m in messages)
        if not has_tool_message:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_director_movies",
                        "args": {"director": "Christopher Nolan"},
                        "id": "mock_call_001",
                    }
                ],
            )
        else:
            return AIMessage(
                content="Based on the movie records retrieved from the MCP Server, Christopher Nolan's highest-rated movie is 'The Dark Knight' (2008) with an IMDb rating of 9.0 / 10."
            )
```
- **Kyun**: Testing aur offline verification ke liye.
- Agar kisi ke paas internet ya Groq API key na ho, tab bhi yeh LangGraph ke state machine aur real MCP stdio tool calling loop ko locally verify karta hai.

---

### Block 4: Building the Graph & Dynamic Tool Binding (Lines 78–120)
```python
def build_agent_graph(session: ClientSession, mcp_tools: List[Any], use_mock: bool = False):
    if use_mock:
        llm_with_tools = MockChatGroq()
    else:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key or groq_api_key.strip() == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY is not set...")

        model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        llm = ChatGroq(
            model=model_name,
            temperature=0.0,
            groq_api_key=groq_api_key,
        )

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
- **Line 98 (`temperature=0.0`)**: Deterministic and accurate tool calls ke liye temperature 0 rakha jata hai taaki model hallucinate na kare.
- **Line 105–116 (`Dynamic Tool Schemas`)**:
  - Har MCP tool object me `tool.name`, `tool.description`, aur `tool.inputSchema` hota hai.
  - Hum is schema ko directly OpenAI/Groq function-calling specification me map karte hain.
- **Line 119 (`llm.bind_tools(...)`)**: LLM ko pata chal jata hai ki kaun-kaun se tools available hain aur unke arguments kya hain.

---

### Block 5: LangGraph Node 1 — `call_model` (Lines 124–128)
```python
async def call_model(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}
```
- State me maujood chat history Groq LLM ko pass karta hai.
- Groq ya toh text response deta hai ya `AIMessage.tool_calls` request karta hai.

---

### Block 6: LangGraph Node 2 — `call_mcp_tools` (Lines 133–182)
```python
async def call_mcp_tools(state: AgentState) -> Dict[str, Any]:
    last_message = state["messages"][-1]
    tool_messages: List[ToolMessage] = []

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"messages": []}

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        call_id = tool_call["id"]

        print(f"\n[EVENT] -> Tool call requested by LLM: '{tool_name}'")
        print(f"[EVENT]    Arguments: {tool_args}")
        print(f"[EVENT] -> Dispatching to MCP Server via protocol (tools/call)...")

        # REAL MCP COMMUNICATION:
        mcp_response = await session.call_tool(tool_name, tool_args)

        content_pieces = []
        for item in mcp_response.content:
            if hasattr(item, "text"):
                content_pieces.append(item.text)
            else:
                content_pieces.append(str(item))
        result_text = "\n".join(content_pieces)

        print(f"[EVENT] <- Received MCP Tool Result ({len(result_text)} chars)")
        print(f"[EVENT]    Preview: {result_text.strip()[:140]}...")

        tool_messages.append(
            ToolMessage(
                content=result_text,
                tool_call_id=call_id,
                name=tool_name,
            )
        )

    return {"messages": tool_messages}
```
- **Line 158 (`session.call_tool(...)`)**:
  - Yeh line **asli MCP client-server magic** hai!
  - Yeh memory me local function call nahi karta, balki client pipe se server process ko JSON-RPC `tools/call` message bhejta hai.
- **Line 173–180**:
  - Result ko `ToolMessage` me pack karta hai jisme `tool_call_id` match hoti hai taaki LLM ko pata chale yeh kis tool call ka response hai.

---

### Block 7: Conditional Edge & Graph Compilation (Lines 187–221)
```python
def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_mcp_tools)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
workflow.add_edge("tools", "agent")
app = workflow.compile()
```
- **`should_continue`**:
  - Agar last message me `tool_calls` hain, toh graph `"tools"` node par jata hai.
  - Agar tool calls nahi hain (final answer ready hai), toh `"end"` (`END`) par jata hai.
- **`workflow.add_edge("tools", "agent")`**:
  - Tool execution ke baad graph wapas `"agent"` node par loop karta hai taaki LLM result ko dekh kar natural language final answer generate kar sake.

---

### Block 8: System Instruction & Query Execution (Lines 225–254)
```python
SYSTEM_INSTRUCTION = (
    "You are an AI Movie Research Assistant with access to an MCP-powered local movie database.\n"
    "Rules:\n"
    "1. Always check your tools first to answer movie questions from the local database.\n"
    "2. If a movie or director is not found in the database results, do not keep trying repeated tool calls. "
    "Clearly inform the user that the movie/director is not present in the local database.\n"
    "3. If not found in the database, do NOT answer from general knowledge. Simply state that the movie is unavailable."
)

async def run_query(app: Any, query: str) -> str:
    initial_state = {
        "messages": [
            SystemMessage(content=SYSTEM_INSTRUCTION),
            HumanMessage(content=query),
        ]
    }
    final_state = await app.ainvoke(initial_state)
    final_message = final_state["messages"][-1]
    return final_message.content
```
- **`SYSTEM_INSTRUCTION`**: Guardrail jo hallucination aur infinite retry loops ko rokta hai jab koi aisi movie poochna chahe jo database me nahi hai.
- **`run_query`**: StateGraph ko trigger karta hai aur final message ka content return karta hai.

---

# 9. `client/main.py`

### Block 1: Windows Console UTF-8 Reconfiguration (Lines 29–36)
```python
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
```
- **Kyun**: Windows PowerShell default me `charmap` (Windows-1252) encoding use karta hai. Jab LLM UTF-8 special characters (jaise `\u202f`, quotes, emojis) return karta hai, toh Windows console crash ho jata hai.
- Yeh code standard output ko UTF-8 me reconfigure kar deta hai, jisse 0 crash guarantee hoti hai.

---

### Block 2: Low-Level MCP Verification (`run_mcp_verification`) (Lines 55–96)
```python
async def run_mcp_verification(session: ClientSession) -> bool:
    tools_result = await session.list_tools()
    ...
    test_call = await session.call_tool("search_movies", {"query": "Inception"})
    ...
    rating_call = await session.call_tool("get_movie_rating", {"movie_id": 1})
    ...
```
- **Kyun**: LLM ke bina pure protocol ko test karta hai:
  - Step 1: `tools/list` returns all 4 tools.
  - Step 2: `tools/call` for `search_movies("Inception")` works.
  - Step 3: `tools/call` for `get_movie_rating(1)` returns 8.8.
- Yeh prove karta hai ki networking/stdio layers 100% healthy hain.

---

### Block 3: External Host Verification (`run_external_host_verification`) (Lines 102–165)
```python
async def run_external_host_verification() -> bool:
    config_file = Path(__file__).parent.parent / ".mcp.json"
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    server_entry = config_data.get("mcpServers", {}).get("movie-server")
    external_params = StdioServerParameters(
        command=server_entry["command"],
        args=server_entry["args"],
    )
    ...
```
- **Kyun**: External host simulation.
- Yeh verify karta hai ki [`.mcp.json`](.mcp.json) configuration file me koi path ya syntax error toh nahi hai, aur Cursor ya Claude Desktop bina kisi dikkat ke server se jud sakte hain ya nahi.

---

### Block 4: Autonomous Server Launch & Stdio Transport (Lines 186–212)
```python
server_params = StdioServerParameters(
    command=sys.executable,
    args=[str(SERVER_PATH)],
    env=dict(os.environ),
)

async with stdio_client(server_params) as (read_stream, write_stream):
    async with ClientSession(read_stream, write_stream) as session:
        init_result = await session.initialize()
        ...
        tools_response = await session.list_tools()
        mcp_tools = tools_response.tools
```
- **Line 186–193**: `sys.executable` use karke running virtual environment ka Python use karta hai aur `mcp_server.py` ko sub-process banata hai.
- **Line 198**: `stdio_client` stdin aur stdout pipes open karta hai.
- **Line 201**: `ClientSession` manage karta hai.
- **Line 208 (`session.initialize()`)**: Protocol handshake negotiation complete karta hai.
- **Line 220 (`session.list_tools()`)**: Tools discover karta hai.

---

### Block 5: CLI Arguments & Interactive Chat Loop (Lines 227–305)
```python
if "--verify" in sys.argv:
    await run_mcp_verification(session)
    ...
if "--verify-external" in sys.argv:
    await run_external_host_verification()
    ...

while True:
    user_input = input("\nEnter question: ").strip()
    if user_input.lower() in ("exit", "quit", "q"):
        break
    answer = await run_query(agent_app, user_input)
    print(f"\nFINAL ANSWER:\n{answer}\n")
```
- **Line 227–248**: `--verify` flag handling.
- **Line 176–178**: `--verify-external` flag handling.
- **Line 254–264**: One-shot terminal arguments (e.g. `python client/main.py "Tell me about Inception"`).
- **Line 287–305**: Interactive REPL loop jisme user continuous questions pooch sakta hai.

---

### Block 6: Async Entrypoint (Lines 307–310)
```python
if __name__ == "__main__":
    asyncio.run(main())
```
- Starts the top-level asyncio event loop for non-blocking I/O execution.

---

## 🎯 Summary Matrix

| File | Primary Role | Key Protocol / Architecture Concept |
|---|---|---|
| `requirements.txt` | Dependency Specification | Official `mcp` SDK + `langgraph` + `langchain-groq` |
| `.env.example` | Security Template | Protects API credentials via 12-Factor principles |
| `.gitignore` | Version Control Hygiene | Prevents secret leakage (`.env`) and bloat (`.venv`) |
| `.mcp.json` | Universal MCP Host Config | Portable config for Claude Code & external tools |
| `.cursor/mcp.json` | Cursor IDE Integration | Instant workspace tool discovery in Cursor |
| `data/movies.json` | Authoritative Data Layer | 20 curated movie profiles with ratings & metadata |
| `server/mcp_server.py` | Standalone MCP Server | FastMCP auto-schema generator & stdio JSON-RPC 2.0 dispatcher |
| `client/agent.py` | Agent & MCP Client Bridge | LangGraph cyclic StateGraph + Dynamic tool schema binding |
| `client/main.py` | Autonomous CLI Runner | Automatic subprocess management, UTF-8 console fix, verification suite |
