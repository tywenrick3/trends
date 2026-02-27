import json
import sys
from typing import Annotated

import typer

from trends_cli.api.trends import fetch_interest
from trends_cli.display.chart import render_compare_chart, console
from trends_cli.display.format import cli_to_pytrends

app = typer.Typer()

VALID_TIMEFRAMES = ["1h", "4h", "1d", "7d", "1m", "3m", "1y", "5y", "10y"]


@app.callback(invoke_without_command=True)
def compare(
    queries: Annotated[list[str], typer.Argument(help="2–5 search terms to compare")],
    timeframe: Annotated[str, typer.Option("--timeframe", "-t", help="1h 4h 1d 7d 1m 3m 1y 5y 10y")] = "5y",
    geo: Annotated[str, typer.Option("--geo", "-g", help="Country code, e.g. US, GB")] = "US",
    fmt: Annotated[str, typer.Option("--format", help="chart or json")] = "chart",
    no_cache: Annotated[bool, typer.Option("--no-cache", help="Bypass 5-min cache")] = False,
) -> None:
    """Compare up to 5 search terms on a single chart."""

    if len(queries) < 2:
        console.print("[red]Provide at least 2 queries to compare.[/red]")
        raise typer.Exit(1)

    if len(queries) > 5:
        console.print("[yellow]Google Trends supports up to 5 queries — using first 5.[/yellow]")
        queries = queries[:5]

    if timeframe not in VALID_TIMEFRAMES:
        console.print(f"[red]Invalid timeframe:[/red] {timeframe}")
        raise typer.Exit(1)

    tf = cli_to_pytrends(timeframe)

    with console.status(f"[dim]Fetching {len(queries)} queries…[/dim]", spinner="dots"):
        series_list = fetch_interest(queries, tf, geo, no_cache)

    if not series_list:
        console.print("[yellow]No data returned.[/yellow]")
        raise typer.Exit(1)

    if fmt == "json" or not sys.stdout.isatty():
        out = [
            {
                "query":         s.query,
                "timeframe":     s.timeframe,
                "geo":           s.geo,
                "peak_value":    s.peak_value,
                "peak_date":     s.peak_date,
                "current_value": s.current_value,
                "avg_value":     s.avg_value,
                "series":        [{"date": dp.date, "value": dp.value} for dp in s.series],
            }
            for s in series_list
        ]
        print(json.dumps(out, indent=2))
    else:
        render_compare_chart(series_list)
