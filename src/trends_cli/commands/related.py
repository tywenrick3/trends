import json
import sys
from typing import Annotated

import typer

from trends_cli.api.trends import fetch_related
from trends_cli.display.tables import render_related, console

app = typer.Typer()


@app.callback(invoke_without_command=True)
def related(
    query: Annotated[str, typer.Argument(help="Search term")],
    geo: Annotated[str, typer.Option("--geo", "-g", help="Country code, e.g. US, GB")] = "US",
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results per section")] = 10,
    fmt: Annotated[str, typer.Option("--format", help="table or json")] = "table",
    no_cache: Annotated[bool, typer.Option("--no-cache", help="Bypass 5-min cache")] = False,
) -> None:
    """Show related queries and topics for a search term."""

    with console.status(f"[dim]Fetching related \"{query}\"…[/dim]", spinner="dots"):
        data = fetch_related(query, geo, no_cache)

    if fmt == "json" or not sys.stdout.isatty():
        out = {
            "query": query,
            "geo":   geo,
            "top_queries":    [{"title": i.title, "value": i.value} for i in data.get("top_queries", [])[:limit]],
            "rising_queries": [{"title": i.title, "value": i.value} for i in data.get("rising_queries", [])[:limit]],
            "top_topics":     [{"title": i.title, "value": i.value} for i in data.get("top_topics", [])[:limit]],
            "rising_topics":  [{"title": i.title, "value": i.value} for i in data.get("rising_topics", [])[:limit]],
        }
        print(json.dumps(out, indent=2))
    else:
        render_related(query, geo, data, limit)
