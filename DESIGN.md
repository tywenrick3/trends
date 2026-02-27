# Trends CLI — Design Document

Sibling to the `polymarket` CLI. Same stack, same architecture, same design language — applied to Google Trends data.

---

## 1. Goals

- **Terminal-native charts**: Render Google Trends line charts in the terminal using `plotext` for the chart body; all surrounding chrome (headers, footers, tables) is rendered with `rich` exactly as in `polymarket`.
- **Agent-first**: TTY detection auto-switches between rich charts (human) and JSON (agent/pipe). All flags are explicit and composable. No interactive prompts.
- **No auth required**: `pytrends` uses the same public data as trends.google.com. No API key.
- **Extensible base**: Commands are cleanly separated. Adding geo heatmaps, watch mode, or export requires no rearchitecting.

---

## 2. Commands (v1)

| Command | Description |
|---|---|
| `trends search <query>` | Plot interest over time — the core chart |
| `trends compare <q1> <q2> ...` | Overlay up to 5 queries on one chart |
| `trends related <query>` | Tables of related topics and related queries |
| `trends trending` | Today's trending searches |

---

## 3. Technology Choices

| Concern | Choice | Rationale |
|---|---|---|
| Language | **Python 3.11+** | Matches `polymarket`; best TUI ecosystem |
| Google Trends | **pytrends** | Widely-used unofficial wrapper; no API key |
| Terminal charting | **plotext** | Renders line charts as ASCII/Unicode in-terminal; dark theme + green |
| Terminal chrome | **rich** | Same as `polymarket` — Tables, Rule, Panel, console.status |
| CLI framework | **typer** | Same as `polymarket`; auto-`--help`, type-safe args |
| Packaging | **uv / pyproject.toml** | `uv tool install` for users; `uv sync` for dev |
| Entrypoint | `trends` binary | Callable from shell and by agents |

---

## 4. Design Language

Identical to `polymarket` with one change: **green** replaces **cyan** as the accent color (matching the Google Trends / inspo aesthetic).

| Element | `polymarket` | `trends` |
|---|---|---|
| Rule / header | `bold cyan` / `cyan dim` | `bold green` / `green dim` |
| Panel border | `style="cyan"` | `style="green"` |
| Table box | `box.SIMPLE_HEAD` | `box.SIMPLE_HEAD` |
| Table header style | `"bold dim"` | `"bold dim"` |
| Table edge | `show_edge=False` | `show_edge=False` |
| Table padding | `pad_edge=True` | `pad_edge=True` |
| Spinner | `console.status("[dim]Fetching…[/dim]", spinner="dots")` | same |
| Delta up | `green` | `green` |
| Delta down | `red` | `red` |
| Secondary text | `dim` | `dim` |
| TTY detection | `if fmt == "json" or not sys.stdout.isatty()` | same |

**Chart chrome** (surrounding the plotext chart body):
```
                                                (rich Rule, bold green)
──────────── TRENDS  "bitcoin"  —  5Y TREND ────────────
  LAST UPDATE: Feb 26, 2026  │  UNITED STATES  │  Feb 2021 – Feb 2026
                                                (plotext, bright green on dark)
  [chart body here]
                                                (rich, dim)
  Peak: 100 (Nov 2021)   Current: 42   Avg: 34
  * Interest indexed to 100 = peak popularity in window
─────────────────────────────────────────────────────────
```

---

## 5. Data Layer — pytrends

### 5.1 Interest Over Time

```python
from pytrends.request import TrendReq
pt = TrendReq(hl="en-US", tz=360)
pt.build_payload(kw_list=["bitcoin"], timeframe="today 5-y", geo="US")
df = pt.interest_over_time()
# DataFrame: index=DatetimeIndex, columns=[kw, ..., "isPartial"], values=0–100
```

### 5.2 Timeframe mapping

| CLI flag | pytrends `timeframe` |
|---|---|
| `1h` | `now 1-H` |
| `4h` | `now 4-H` |
| `1d` | `now 1-d` |
| `7d` | `now 7-d` |
| `1m` | `today 1-m` |
| `3m` | `today 3-m` |
| `1y` | `today 12-m` |
| `5y` | `today 5-y` (default) |
| `10y` | `all` |

### 5.3 Cache

Responses serialized as JSON to `/tmp/trends_cache/{sha256(key)}.json` with 5-minute TTL. Key = `(queries_tuple, timeframe, geo)`. Bypassed with `--no-cache`.

### 5.4 Related & Trending

```python
pt.related_topics()    # {kw: {"top": df, "rising": df}}
pt.related_queries()   # same; "top" values 0–100, "rising" values are "XXX%"
pt.trending_searches(pn="united_states")       # daily trending
pt.realtime_trending_searches(pn="US")         # realtime (--realtime flag)
```

---

## 6. Command Design

### 6.1 `trends search <query>`

```
$ trends search "bitcoin" [--timeframe 5y] [--geo US] [--format chart|json] [--no-cache]
```

Human output:
```
──────────── TRENDS  "BITCOIN"  —  5Y TREND ────────────
  LAST UPDATE: Feb 26, 2026  │  UNITED STATES  │  Feb 2021 – Feb 2026

  [plotext chart: bright green line, dark background, y=0–100]

  Peak: 100 (Nov 2021)   Current: 42   Avg: 34
  * Interest indexed to 100 = peak popularity in window
─────────────────────────────────────────────────────────
```

JSON (piped):
```json
{
  "query": "bitcoin",
  "timeframe": "today 5-y",
  "geo": "US",
  "peak_value": 100,
  "peak_date": "2021-11-14",
  "current_value": 42,
  "avg_value": 34.2,
  "series": [{"date": "2021-02-07", "value": 14}, ...]
}
```

### 6.2 `trends compare <q1> <q2> [q3] [q4] [q5]`

Same flags as `search`. Overlays up to 5 queries on one chart. Each line uses a distinct color. Legend after chart shows `current` and `peak` per query.

### 6.3 `trends related <query>`

```
$ trends related "bitcoin" [--geo US] [--limit 10] [--format table|json]
```

Two `box.SIMPLE_HEAD` tables (stacked): **Top Queries** and **Rising Queries** (matching `polymarket`'s single-event detail layout with multiple tables per screen).

### 6.4 `trends trending`

```
$ trends trending [--geo US] [--limit 20] [--realtime] [--format table|json]
```

Single `box.SIMPLE_HEAD` table: rank, topic, traffic estimate.

---

## 7. Project Structure

```
trends/
├── pyproject.toml
├── DESIGN.md
└── src/
    └── trends_cli/
        ├── __init__.py
        ├── main.py              # typer app, command registration
        ├── api/
        │   ├── __init__.py
        │   └── trends.py        # pytrends wrapper + cache
        ├── commands/
        │   ├── __init__.py
        │   ├── search.py
        │   ├── compare.py
        │   ├── related.py
        │   └── trending.py
        ├── display/
        │   ├── __init__.py
        │   ├── chart.py         # plotext chart builders
        │   ├── tables.py        # rich table builders (SIMPLE_HEAD, console)
        │   └── format.py        # date / value / geo formatting
        └── models.py
```

---

## 8. Data Models

```python
@dataclass
class DataPoint:
    date: str   # "YYYY-MM-DD"
    value: int  # 0–100

@dataclass
class TrendSeries:
    query: str
    timeframe: str
    geo: str
    fetched_at: str
    series: list[DataPoint]
    peak_value: int
    peak_date: str
    current_value: int
    avg_value: float

@dataclass
class RelatedItem:
    title: str
    type: str        # "topic" or "query"
    value: str       # "72" for top; "+3400%" for rising

@dataclass
class TrendingSearch:
    rank: int
    title: str
    traffic: str
```

---

## 9. Installation

```bash
# Development
cd trends
uv sync
uv run trends search "bitcoin"

# End-user
uv tool install trends-cli
trends search "bitcoin"
```

---

## 10. Design Decisions

### plotext for charts, rich for chrome
plotext renders via `plt.show()` (stdout, ANSI codes). All headers, footers, tables, spinners, and panels go through rich's `Console`. The two coexist fine in a TTY. When not a TTY, the chart is skipped entirely and JSON is emitted.

### Synchronous (no asyncio)
pytrends is synchronous. Unlike `polymarket` (which needs `asyncio` for concurrent httpx calls), `trends` has no concurrent HTTP benefit — Google Trends returns all queried keywords in a single response. Keeping it sync is simpler.

### TTY detection = agent-friendly by default
`if fmt == "json" or not sys.stdout.isatty()`: agents calling `trends search "bitcoin"` in a shell get JSON automatically, including the full `series[]` array for downstream processing.

### Why not the official Google Trends API?
Deprecated and requires whitelisting. pytrends uses the same public endpoint as trends.google.com.

---

## 11. Future Work (v2+)

| Feature | Notes |
|---|---|
| `trends geo <query>` | Interest by region — ranked table of countries/states |
| `trends watch <query>` | Auto-refresh chart every N seconds |
| `trends export` | Save series to CSV |
| MCP server | Expose all commands as MCP tools for Claude agents |
| Shell completions | `trends --install-completion` |
| Config file | `~/.config/trends/config.toml` for default geo, timeframe |
