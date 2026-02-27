import json
import sys
from typing import Annotated

import typer

from trends_cli.api.trends import fetch_trending
from trends_cli.display.tables import render_trending, console

app = typer.Typer()


@app.callback(invoke_without_command=True)
def trending(
    geo: Annotated[str, typer.Option("--geo", "-g", help="Country code, e.g. US, GB")] = "US",
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 20,
    realtime: Annotated[bool, typer.Option("--realtime", help="Use realtime trending (last 24h)")] = False,
    fmt: Annotated[str, typer.Option("--format", help="table or json")] = "table",
    no_cache: Annotated[bool, typer.Option("--no-cache", help="Bypass 5-min cache")] = False,
) -> None:
    """Show today's trending searches."""

    label = "realtime trending" if realtime else "trending searches"
    with console.status(f"[dim]Fetching {label}…[/dim]", spinner="dots"):
        searches = fetch_trending(geo, realtime, no_cache)

    searches = searches[:limit]

    if not searches:
        console.print("[yellow]No trending data returned.[/yellow]")
        raise typer.Exit(1)

    if fmt == "json" or not sys.stdout.isatty():
        out = [{"rank": s.rank, "title": s.title, "traffic": s.traffic} for s in searches]
        print(json.dumps(out, indent=2))
    else:
        render_trending(geo, searches, realtime)
