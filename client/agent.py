"""
client/agent.py
---------------
Implements the MCP Client and the LangGraph Agent workflow.

CORE RESPONSIBILITIES:
1. Connects to the local MCP Server using stdio transport (official MCP Python SDK).
2. Initializes the MCP protocol session (`initialize`).
3. Dynamically discovers available tools from the MCP server (`tools/list`).
4. Binds discovered MCP tool schemas to the Groq LLM via LangChain.
5. Builds a minimal LangGraph agent (START -> Agent -> Tools -> Agent -> END).
6. Executes tool calls via the MCP protocol (`tools/call`) and feeds results back to Groq.
7. Prints clear observable execution events without exposing internal model thoughts.
"""

import os
from typing import Annotated, Any, Dict, List, Sequence
from typing_extensions import TypedDict
from dotenv import load_dotenv

# LangChain & LangGraph imports
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

# MCP Official Python SDK imports
from mcp import ClientSession

# Load environment variables (.env)
load_dotenv()


# -----------------------------------------------------------------------------
# 1. Define LangGraph State
# -----------------------------------------------------------------------------
# MessagesState keeps a list of chat messages. 'add_messages' appends new messages.
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


from langchain_core.messages import AIMessage


# -----------------------------------------------------------------------------
# Offline Mock LLM (For local verification without an API key)
# -----------------------------------------------------------------------------
class MockChatGroq:
    """
    Simulates Groq LLM tool calling and response generation offline.
    Allows testing the complete LangGraph + MCP state machine without needing an active API key.
    """
    async def ainvoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        # Check if the state already contains a tool result
        has_tool_message = any(isinstance(m, ToolMessage) for m in messages)
        if not has_tool_message:
            # Turn 1: Model decides which MCP tool to call based on the query
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
            # Turn 2: Tool result received via MCP, formulate natural language answer
            return AIMessage(
                content="Based on the movie records retrieved from the MCP Server, Christopher Nolan's highest-rated movie is 'The Dark Knight' (2008) with an IMDb rating of 9.0 / 10."
            )


# -----------------------------------------------------------------------------
# 2. Agent Workflow Builder
# -----------------------------------------------------------------------------
def build_agent_graph(session: ClientSession, mcp_tools: List[Any], use_mock: bool = False):
    """
    Constructs the minimal LangGraph workflow connected to the active MCP session.

    Args:
        session: The active MCP ClientSession connected to the MCP Server.
        mcp_tools: List of Tool objects discovered dynamically from session.list_tools().
        use_mock: If True, uses the offline MockChatGroq instead of ChatGroq.
    """
    if use_mock:
        llm_with_tools = MockChatGroq()
    else:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key or groq_api_key.strip() == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY is not set or still has default placeholder. "
                "Please configure your GROQ_API_KEY in the .env file."
            )

        # Initialize Groq LLM via LangChain (configurable via GROQ_MODEL)
        model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        llm = ChatGroq(
            model=model_name,
            temperature=0.0,
            groq_api_key=groq_api_key,
        )

        # Convert discovered MCP tools into standard tool schemas for Groq/LangChain
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

        # Bind tools to LLM so Groq knows what tools are available and their schemas
        llm_with_tools = llm.bind_tools(groq_tool_schemas)

    # -------------------------------------------------------------------------
    # LangGraph Node 1: Call Model
    # -------------------------------------------------------------------------
    async def call_model(state: AgentState) -> Dict[str, Any]:
        """Node that sends the conversation history to Groq and gets a response."""
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # -------------------------------------------------------------------------
    # LangGraph Node 2: Call MCP Tools
    # -------------------------------------------------------------------------
    async def call_mcp_tools(state: AgentState) -> Dict[str, Any]:
        """
        Node that takes tool calls decided by Groq, executes them via the
        MCP client session over stdio, and returns ToolMessages.
        """
        last_message = state["messages"][-1]
        tool_messages: List[ToolMessage] = []

        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return {"messages": []}

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})
            call_id = tool_call["id"]

            # Observable event logging
            print(f"\n[EVENT] -> Tool call requested by LLM: '{tool_name}'")
            print(f"[EVENT]    Arguments: {tool_args}")
            print(f"[EVENT] -> Dispatching to MCP Server via protocol (tools/call)...")

            # -----------------------------------------------------------------
            # REAL MCP COMMUNICATION (tools/call)
            # -----------------------------------------------------------------
            # The client sends a JSON-RPC 2.0 request 'tools/call' to the MCP server.
            mcp_response = await session.call_tool(tool_name, tool_args)

            # Extract the text content from the MCP response
            content_pieces = []
            for item in mcp_response.content:
                if hasattr(item, "text"):
                    content_pieces.append(item.text)
                else:
                    content_pieces.append(str(item))
            result_text = "\n".join(content_pieces)

            # Observable event logging
            print(f"[EVENT] <- Received MCP Tool Result ({len(result_text)} chars)")
            print(f"[EVENT]    Preview: {result_text.strip()[:140]}...")

            # Create LangChain ToolMessage so Groq can see the tool's output
            tool_messages.append(
                ToolMessage(
                    content=result_text,
                    tool_call_id=call_id,
                    name=tool_name,
                )
            )

        return {"messages": tool_messages}

    # -------------------------------------------------------------------------
    # Conditional Edge: Decide whether to continue or stop
    # -------------------------------------------------------------------------
    def should_continue(state: AgentState) -> str:
        """Determines if the LLM requested a tool call or produced the final answer."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    # -------------------------------------------------------------------------
    # 3. Build & Compile StateGraph
    # -------------------------------------------------------------------------
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", call_mcp_tools)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edge from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # After tools are executed, route back to agent so LLM can formulate final answer
    workflow.add_edge("tools", "agent")

    # Compile the graph into an executable runnable
    app = workflow.compile()
    return app


# -----------------------------------------------------------------------------
SYSTEM_INSTRUCTION = (
    "You are an AI Movie Research Assistant with access to an MCP-powered local movie database.\n"
    "Rules:\n"
    "1. Always check your tools first to answer movie questions from the local database.\n"
    "2. If a movie or director is not found in the database results, do not keep trying repeated tool calls. "
    "Clearly inform the user that the movie/director is not present in the local database.\n"
    "3. If not found in the database, do NOT answer from general knowledge. Simply state that the movie is unavailable."
)


# -----------------------------------------------------------------------------
# 4. Helper function to run a single query through the agent
# -----------------------------------------------------------------------------
async def run_query(app: Any, query: str) -> str:
    """Runs a single user query through the LangGraph agent and prints events."""
    print(f"\n=======================================================")
    print(f"USER QUERY: {query}")
    print(f"=======================================================")

    initial_state = {
        "messages": [
            SystemMessage(content=SYSTEM_INSTRUCTION),
            HumanMessage(content=query),
        ]
    }
    final_state = await app.ainvoke(initial_state)

    final_message = final_state["messages"][-1]
    print(f"\n[EVENT] -> Final response generated by LLM.")
    return final_message.content
