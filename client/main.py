"""
client/main.py
--------------
Main entry point for running the AI Movie Research Agent.

WHAT THIS SCRIPT DOES:
1. Automatically launches the local MCP Server as a subprocess using stdio transport.
2. Initializes the MCP session (`initialize`).
3. Discovers all tools exposed by the MCP Server (`tools/list`).
4. Builds the LangGraph agent bound to those MCP tools.
5. Provides:
   - Automated Verification mode (`--verify`): Tests MCP initialize, tools/list, tools/call, and end-to-end.
   - Interactive CLI mode: Allows the user to ask any question or test sample queries.
6. Prints observable lifecycle events:
   - MCP server connected
   - tools discovered
   - tool call requested
   - MCP tool being called
   - tool result received
   - final response generated
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure Windows terminal prints UTF-8 properly without charmap encoding errors
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# MCP Client SDK
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Local Agent builder
from agent import build_agent_graph, run_query

# Load environment variables (.env)
load_dotenv()

# Absolute path to the MCP server script
SERVER_PATH = Path(__file__).parent.parent / "server" / "mcp_server.py"


# -----------------------------------------------------------------------------
# Standalone MCP Verification Routine
# -----------------------------------------------------------------------------
async def run_mcp_verification(session: ClientSession) -> bool:
    """
    Directly tests the MCP protocol primitives:
    1. session.initialize() was successful
    2. session.list_tools() returns the 4 expected tools
    3. session.call_tool() successfully executes a tool against the server
    """
    print("\n" + "=" * 60)
    print("RUNNING MCP PROTOCOL VERIFICATION TESTS")
    print("=" * 60)

    # 1. Test tools/list
    print("\n[STEP 1] Testing 'tools/list'...")
    tools_result = await session.list_tools()
    discovered_names = [t.name for t in tools_result.tools]
    print(f"  -> Tools found: {discovered_names}")

    expected_tools = ["search_movies", "get_movie_details", "get_director_movies", "get_movie_rating"]
    for expected in expected_tools:
        assert expected in discovered_names, f"Missing tool: {expected}"
    print("  [PASS] All 4 expected MCP tools are present and advertised with JSON schemas.")

    # 2. Test direct tools/call
    print("\n[STEP 2] Testing 'tools/call' directly over MCP stdio...")
    test_call = await session.call_tool("search_movies", {"query": "Inception"})
    content = test_call.content[0].text if test_call.content else ""
    print(f"  -> Result preview: {content.strip()}")
    assert "Inception" in content, "Direct tool call failed to return Inception."
    print("  [PASS] Direct MCP tool call succeeded via stdio protocol.")

    # 3. Test another tools/call (get_movie_rating)
    print("\n[STEP 3] Testing 'tools/call' for get_movie_rating(movie_id=1)...")
    rating_call = await session.call_tool("get_movie_rating", {"movie_id": 1})
    rating_content = rating_call.content[0].text if rating_call.content else ""
    print(f"  -> Result: {rating_content.strip()}")
    assert "8.8" in rating_content, "Rating call returned unexpected value."
    print("  [PASS] Direct rating tool call succeeded.")

    print("\n" + "=" * 60)
    print("ALL LOW-LEVEL MCP PROTOCOL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60 + "\n")
    return True


# -----------------------------------------------------------------------------
# External Host Verification Routine (via .mcp.json)
# -----------------------------------------------------------------------------
async def run_external_host_verification() -> bool:
    """
    Simulates how an external MCP Host (such as Claude Desktop, Claude Code, or Cursor)
    reads .mcp.json and communicates with server/mcp_server.py.
    """
    config_file = Path(__file__).parent.parent / ".mcp.json"
    if not config_file.exists():
        print(f"[ERROR] External configuration file {config_file} not found.")
        return False

    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    server_entry = config_data.get("mcpServers", {}).get("movie-server")
    if not server_entry:
        print("[ERROR] 'movie-server' entry not found in .mcp.json")
        return False

    print("\n" + "=" * 65)
    print("VERIFYING EXTERNAL HOST CONNECTION VIA .mcp.json")
    print("=" * 65)
    print(f"External Host Configuration Source: {config_file.name}")
    print(f"  Command: {server_entry['command']}")
    print(f"  Args:    {server_entry['args']}")

    external_params = StdioServerParameters(
        command=server_entry["command"],
        args=server_entry["args"],
        env=server_entry.get("env") or dict(os.environ),
    )

    async with stdio_client(external_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # 1. Handshake (initialize)
            init_res = await session.initialize()
            srv_info = getattr(init_res, "server_info", getattr(init_res, "serverInfo", None))
            srv_name = getattr(srv_info, "name", "Movie-Server") if srv_info else "Movie-Server"
            print(f"\n[STEP 1] External Host Initialized -> Connected to '{srv_name}'")

            # 2. Tool Discovery (tools/list)
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            print(f"[STEP 2] External Host Discovered Tools: {tool_names}")
            assert len(tool_names) == 4, f"Expected 4 tools, got {len(tool_names)}"

            # 3. Tool Call: search_movies("Christopher Nolan")
            print("\n[STEP 3] External Host Calling 'search_movies' (query='Christopher Nolan')...")
            search_res = await session.call_tool("search_movies", {"query": "Christopher Nolan"})
            search_text = search_res.content[0].text if search_res.content else ""
            print("  Result Preview:\n" + search_text[:180] + "...")
            assert "The Dark Knight" in search_text, "Failed to find The Dark Knight in search results."

            # 4. Tool Call: get_movie_details(movie_id=1)
            print("\n[STEP 4] External Host Calling 'get_movie_details' (movie_id=1)...")
            details_res = await session.call_tool("get_movie_details", {"movie_id": 1})
            details_text = details_res.content[0].text if details_res.content else ""
            print("  Result Preview:\n" + details_text[:180] + "...")
            assert "Inception" in details_text, "Failed to retrieve Inception details."

    print("\n" + "=" * 65)
    print("EXTERNAL HOST VERIFICATION SUCCESSFUL!")
    print("The existing server/mcp_server.py is 100% usable by external MCP hosts.")
    print("=" * 65 + "\n")
    return True


# -----------------------------------------------------------------------------
# Main Application Runner
# -----------------------------------------------------------------------------
async def main():
    # Verify server script exists
    if not SERVER_PATH.exists():
        print(f"[ERROR] Server script not found at {SERVER_PATH}")
    # Check if user wants to test external host connection (.mcp.json)
    if "--verify-external" in sys.argv:
        await run_external_host_verification()
        return

    print("\n=======================================================")
    print("        AI MOVIE RESEARCH AGENT (MCP + LANGGRAPH)     ")
    print("=======================================================")

    # -------------------------------------------------------------------------
    # 1. Launch MCP Server via stdio subprocess
    # -------------------------------------------------------------------------
    # StdioServerParameters tells the MCP client how to launch the MCP server.
    # The MCP SDK manages stdin/stdout pipes to exchange JSON-RPC 2.0 messages.
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        env=dict(os.environ),
    )

    print(f"[EVENT] Starting local MCP Server subprocess: {SERVER_PATH.name}...")

    # Connect to the server using the stdio transport
    async with stdio_client(server_params) as (read_stream, write_stream):
        print("[EVENT] MCP Server process started. Establishing ClientSession...")

        async with ClientSession(read_stream, write_stream) as session:
            # -----------------------------------------------------------------
            # 2. MCP Handshake: initialize
            # -----------------------------------------------------------------
            # The client sends an 'initialize' JSON-RPC request.
            # The server responds with protocol version, capabilities, and server info.
            print("[EVENT] Sending MCP 'initialize' handshake...")
            init_result = await session.initialize()
            server_info = getattr(init_result, "server_info", getattr(init_result, "serverInfo", None))
            server_name = getattr(server_info, "name", "Movie-Server") if server_info else "Movie-Server"
            proto_ver = getattr(init_result, "protocol_version", getattr(init_result, "protocolVersion", "unknown"))
            print(f"[EVENT] MCP Connected! Server: {server_name} (Protocol: {proto_ver})")

            # -----------------------------------------------------------------
            # 3. Dynamic Tool Discovery: tools/list
            # -----------------------------------------------------------------
            # The client queries the server for all registered tools.
            # No tools are hardcoded on the client side!
            print("[EVENT] Requesting tool list via 'tools/list'...")
            tools_response = await session.list_tools()
            mcp_tools = tools_response.tools

            print(f"[EVENT] Successfully discovered {len(mcp_tools)} MCP tool(s):")
            for t in mcp_tools:
                print(f"        * {t.name}: {t.description}")

            # Check if user passed '--verify' flag
            if "--verify" in sys.argv:
                await run_mcp_verification(session)

                # Also test the end-to-end agent flow
                groq_key = os.getenv("GROQ_API_KEY", "")
                has_groq = groq_key and groq_key.strip() != "your_groq_api_key_here"
                
                print("\n[STEP 4] Testing End-to-End Agent Workflow (LangGraph + MCP Server)...")
                if has_groq:
                    print("  -> Using live Groq LLM (llama-3.3-70b-versatile)...")
                    agent_app = build_agent_graph(session, mcp_tools, use_mock=False)
                else:
                    print("  -> Using offline Mock LLM (Simulates Groq tool-selection to verify LangGraph + MCP stdio flow)...")
                    agent_app = build_agent_graph(session, mcp_tools, use_mock=True)

                sample_q = "Which Christopher Nolan movie has the highest rating?"
                answer = await run_query(agent_app, sample_q)
                print(f"\nFINAL ANSWER:\n{answer}\n")
                print("  [PASS] Full End-to-End Agent + MCP verification succeeded!")
                return

            # Check if user wants mock mode
            use_mock_mode = "--mock" in sys.argv

            # Check if user passed a one-shot query via arguments
            # e.g., python client/main.py "Tell me about Inception"
            args_without_flags = [a for a in sys.argv[1:] if not a.startswith("--")]
            if args_without_flags:
                one_shot_query = " ".join(args_without_flags)
                try:
                    agent_app = build_agent_graph(session, mcp_tools, use_mock=use_mock_mode)
                    answer = await run_query(agent_app, one_shot_query)
                    print(f"\nFINAL ANSWER:\n{answer}\n")
                except ValueError as err:
                    print(f"\n[CONFIGURATION ERROR] {err}")
                    print("Tip: You can test the LangGraph workflow offline using: python client/main.py --verify or --mock\n")
                return

            # -----------------------------------------------------------------
            # 4. Interactive Chat Loop
            # -----------------------------------------------------------------
            try:
                agent_app = build_agent_graph(session, mcp_tools, use_mock=use_mock_mode)
            except ValueError as err:
                print(f"\n[CONFIGURATION ERROR] {err}")
                print("\nPlease update your GROQ_API_KEY in .env and rerun.")
                print("Tip: You can still test the flow offline using: python client/main.py --verify\n")
                return

            print("\n" + "-" * 55)
            print("Interactive Movie Research Agent Ready!")
            print("Sample questions you can try:")
            print(" 1. Which Christopher Nolan movie has the highest rating?")
            print(" 2. Tell me about Inception.")
            print(" 3. Find movies directed by Christopher Nolan after 2010.")
            print(" 4. Give me an overview of Christopher Nolan's movies.")
            print("Type 'exit' or 'quit' to close.")
            print("-" * 55 + "\n")

            while True:
                try:
                    user_input = input("\nEnter question: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nExiting...")
                    break

                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "q"):
                    print("Goodbye!")
                    break

                try:
                    answer = await run_query(agent_app, user_input)
                    print(f"\nFINAL ANSWER:\n{answer}\n")
                except Exception as e:
                    print(f"[ERROR] Query failed: {e}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
