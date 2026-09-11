"""
server/mcp_server.py
--------------------
A standalone Model Context Protocol (MCP) server for movie data.

WHAT THIS SERVER DOES:
1. Loads movie records from `data/movies.json`.
2. Uses the official MCP Python SDK (`FastMCP`) to expose 4 movie tools over stdio.
3. Handles JSON-RPC 2.0 requests:
   - `initialize`: Handshake and capability negotiation.
   - `tools/list`: Returns JSON schemas of available tools.
   - `tools/call`: Executes the requested tool with arguments and returns the result.

WHAT THE SDK DOES FOR US:
- Manages standard input/output (stdio) streaming.
- Parses and serializes JSON-RPC 2.0 messages.
- Converts Python function signatures and docstrings into standard JSON Schema.

WHAT OUR APPLICATION CODE DOES:
- Loads the local JSON movie database.
- Implements the actual business logic for searching and retrieving movie information.
"""

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

# -----------------------------------------------------------------------------
# 1. Initialize FastMCP Server
# -----------------------------------------------------------------------------
# FastMCP is the high-level server interface provided by the official MCP SDK.
# "Movie-Server" is the server identifier sent during MCP initialization.
mcp = FastMCP("Movie-Server")

# Path to the local movies JSON file
DATA_FILE = Path(__file__).parent.parent / "data" / "movies.json"


def _load_movies() -> List[Dict[str, Any]]:
    """Helper function to load movie records from data/movies.json."""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------------------------------------------------------
# 2. Expose MCP Tools
# -----------------------------------------------------------------------------
# Using the @mcp.tool() decorator registers each function as an MCP tool.
# FastMCP inspects:
# - Function name -> Tool name in MCP
# - Docstring     -> Tool description for LLM
# - Type hints    -> JSON Schema parameters for tool arguments

@mcp.tool()
def search_movies(query: str) -> str:
    """Search movies by title, director, actor, genre, or keyword in plot."""
    movies = _load_movies()
    q = query.strip().lower()
    matches = []

    for m in movies:
        # Check title and director
        if q in m["title"].lower() or q in m["director"].lower():
            matches.append(m)
            continue
        # Check actors
        if any(q in actor.lower() for actor in m.get("actors", [])):
            matches.append(m)
            continue
        # Check genre
        if any(q in genre.lower() for genre in m.get("genre", [])):
            matches.append(m)
            continue
        # Check plot summary
        if q in m.get("plot", "").lower():
            matches.append(m)
            continue

    if not matches:
        return f"No movies found matching query: '{query}'"

    # Format a concise summary of matches
    results = [
        f"ID {m['id']}: {m['title']} ({m['year']}) - Directed by {m['director']}, Rating: {m['rating']}"
        for m in matches
    ]
    return f"Found {len(matches)} movie(s):\n" + "\n".join(results)


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


@mcp.tool()
def get_movie_rating(movie_id: int) -> str:
    """Get the rating for a specific movie by its integer ID."""
    movies = _load_movies()
    for m in movies:
        if m["id"] == movie_id:
            return f"Movie: '{m['title']}' (ID: {m['id']}) has a rating of {m['rating']} / 10."
    return f"Error: Movie with ID {movie_id} was not found."


# -----------------------------------------------------------------------------
# 3. Run Server on stdio
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # When run as main, start the MCP server listening on stdio (stdin/stdout).
    # All JSON-RPC communication travels through stdin and stdout.
    mcp.run(transport="stdio")
