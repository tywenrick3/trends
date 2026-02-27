"""Rich table builders for related and trending commands."""

from rich.console import Console
from rich.table import Table
from rich.rule import Rule
from rich import box

from trends_cli.models import RelatedItem, TrendingSearch
from trends_cli.display.format import fmt_geo, fmt_today

console = Console()


def _base_table() -> Table:
    return Table(
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold dim",
        pad_edge=True,
        expand=False,
        show_edge=False,
    )


def render_related(query: str, geo: str, data: dict[str, list[RelatedItem]], limit: int) -> None:
    """Render top queries and rising queries tables."""
    console.print()
    console.print(
        Rule(
            f"[bold green]RELATED[/bold green]  [dim]\"{query}\"  │  {fmt_geo(geo)}[/dim]",
            style="green dim",
        )
    )
    console.print()

    sections = [
        ("Top Queries",    data.get("top_queries", [])[:limit]),
        ("Rising Queries", data.get("rising_queries", [])[:limit]),
    ]

    for title, items in sections:
        if not items:
            continue
        console.print(f"  [bold]{title}[/bold]")
        tbl = _base_table()
        tbl.add_column("#",     style="dim", width=3,  justify="right", no_wrap=True)
        tbl.add_column("Query",              width=38,                   no_wrap=True)
        tbl.add_column("Value",              width=10, justify="right",  no_wrap=True)

        for rank, item in enumerate(items, 1):
            # Rising values come as "3400%" — color them green
            val_text = item.value
            try:
                num = int(item.value.replace("%", "").replace("+", "").replace(",", ""))
                if "%" in item.value:
                    val_text = f"[green]+{num:,}%[/green]"
            except ValueError:
                pass
            tbl.add_row(str(rank), _truncate(item.title, 38), val_text)

        console.print(tbl)

    console.print()
    console.print(Rule(style="green dim"))
    console.print()


def render_trending(geo: str, searches: list[TrendingSearch], realtime: bool) -> None:
    """Render trending searches table."""
    label = "REALTIME TRENDING" if realtime else "TRENDING SEARCHES"
    today = fmt_today()

    console.print()
    console.print(
        Rule(
            f"[bold green]{label}[/bold green]  [dim]{today}  │  {fmt_geo(geo)}[/dim]",
            style="green dim",
        )
    )
    console.print()

    tbl = _base_table()
    tbl.add_column("#",      style="dim", width=3,  justify="right", no_wrap=True)
    tbl.add_column("Topic",              width=50,                   no_wrap=True)
    if any(s.traffic for s in searches):
        tbl.add_column("Traffic", width=10, justify="right", no_wrap=True)

    show_traffic = any(s.traffic for s in searches)
    for s in searches:
        row = [str(s.rank), _truncate(s.title, 50)]
        if show_traffic:
            row.append(s.traffic)
        tbl.add_row(*row)

    console.print(tbl)
    console.print()
    console.print(Rule(style="green dim"))
    console.print()


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"
