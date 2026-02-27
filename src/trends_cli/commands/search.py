import json
import sys
from typing import Annotated

import typer

from trends_cli.api.trends import fetch_interest
from trends_cli.display.chart import render_search_chart, console
from trends_cli.display.format import cli_to_pytrends

app = typer.Typer()

VALID_TIMEFRAMES = ["1h", "4h", "1d", "7d", "1m", "3m", "1y", "5y", "10y"]


@app.callback(invoke_without_command=True)
def search(
    query: Annotated[str, typer.Argument(help="Search term")],
    timeframe: Annotated[str, typer.Option("--timeframe", "-t", help="1h 4h 1d 7d 1m 3m 1y 5y 10y")] = "5y",
    geo: Annotated[str, typer.Option("--geo", "-g", help="Country code, e.g. US, GB")] = "US",
    fmt: Annotated[str, typer.Option("--format", help="chart or json")] = "chart",
    no_cache: Annotated[bool, typer.Option("--no-cache", help="Bypass 5-min cache")] = False,
) -> None:
    """Plot Google Trends interest over time for a search term."""

    if timeframe not in VALID_TIMEFRAMES:
        console.print(f"[red]Invalid timeframe:[/red] {timeframe}. Choose from: {', '.join(VALID_TIMEFRAMES)}")
        raise typer.Exit(1)

    tf = cli_to_pytrends(timeframe)

    with console.status(f"[dim]Fetching \"{query}\"…[/dim]", spinner="dots"):
        series_list = fetch_interest([query], tf, geo, no_cache)

    if not series_list:
        console.print(f"[yellow]No data returned for:[/yellow] {query}")
        raise typer.Exit(1)

    series = series_list[0]

    if fmt == "json" or not sys.stdout.isatty():
        out = {
            "query":         series.query,
            "timeframe":     series.timeframe,
            "geo":           series.geo,
            "fetched_at":    series.fetched_at,
            "peak_value":    series.peak_value,
            "peak_date":     series.peak_date,
            "current_value": series.current_value,
            "avg_value":     series.avg_value,
            "series":        [{"date": dp.date, "value": dp.value} for dp in series.series],
        }
        print(json.dumps(out, indent=2))
    else:
        render_search_chart(series)
