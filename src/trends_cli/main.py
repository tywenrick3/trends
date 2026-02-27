import typer

from trends_cli.commands.search import search
from trends_cli.commands.compare import compare
from trends_cli.commands.related import related
from trends_cli.commands.trending import trending

app = typer.Typer(
    name="trends",
    help="Terminal CLI for Google Trends.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.command("search",   help="Plot interest over time for a search term")(search)
app.command("compare",  help="Compare up to 5 search terms on one chart")(compare)
app.command("related",  help="Related queries and topics for a search term")(related)
app.command("trending", help="Today's trending searches")(trending)


if __name__ == "__main__":
    app()
