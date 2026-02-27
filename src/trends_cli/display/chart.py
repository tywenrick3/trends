"""Smooth braille chart renderer — no plotext, pure Rich output."""

from datetime import datetime

from rich.console import Console
from rich.rule import Rule
from rich.text import Text

from trends_cli.models import TrendSeries
from trends_cli.display.format import (
    fmt_timeframe,
    fmt_geo,
    fmt_date,
    fmt_date_range,
    fmt_today,
)

console = Console()

COMPARE_COLORS = ["green", "cyan", "yellow", "red", "white"]

# Unicode braille dot bit positions within a 2-col × 4-row cell
# _BITS[sub_row][sub_col] = bitmask
_BITS = [
    [0x01, 0x08],
    [0x02, 0x10],
    [0x04, 0x20],
    [0x40, 0x80],
]

_CHART_H = 18  # character rows (= 72 pixel rows)
_Y_AXIS_W = 5  # chars reserved for "  100"


# ---------------------------------------------------------------------------
# Core braille renderer
# ---------------------------------------------------------------------------

def _interp(values: list[float], px_w: int) -> list[float]:
    """Linear interpolation of values to exactly px_w pixel columns."""
    n = len(values)
    if n == 0:
        return [0.0] * px_w
    if n == 1:
        return [float(values[0])] * px_w
    out = []
    for i in range(px_w):
        t = i / (px_w - 1) * (n - 1)
        lo = int(t)
        hi = min(lo + 1, n - 1)
        out.append(values[lo] + (values[hi] - values[lo]) * (t - lo))
    return out


def _val_to_px_row(v: float, px_h: int, y_max: float = 100.0) -> int:
    """Map a 0–y_max value to a pixel row (0 = top, px_h-1 = bottom)."""
    p = max(0.0, min(1.0, v / y_max))
    return int((1.0 - p) * (px_h - 1))


def _render_series(
    all_values: list[list[float]],
    colors: list[str],
    char_w: int,
    char_h: int,
) -> list[Text]:
    """
    Render one or more data series as a filled braille chart.
    Returns one Rich Text object per character row.

    Each braille cell is 2px wide × 4px tall.
    Line pixels are styled bold <color>; fill pixels dim <color>.
    Series rendered in reverse order so series[0] appears on top.
    """
    px_w = char_w * 2
    px_h = char_h * 4

    # grid[px_row][px_col] = (kind, series_idx) or None
    # kind: 1 = line, 0 = fill
    grid: list[list[tuple[int, int] | None]] = [
        [None] * px_w for _ in range(px_h)
    ]

    for s_idx in reversed(range(len(all_values))):
        px_cols = _interp(all_values[s_idx], px_w)
        for px_x, v in enumerate(px_cols):
            y_row = _val_to_px_row(v, px_h)

            # Line pixel — never overwrite another series' line
            if grid[y_row][px_x] is None or grid[y_row][px_x][0] == 0:
                grid[y_row][px_x] = (1, s_idx)

            # Fill below the line
            for r in range(y_row + 1, px_h):
                if grid[r][px_x] is None:
                    grid[r][px_x] = (0, s_idx)

    # Convert pixel grid → Rich Text rows
    rows: list[Text] = []
    for cy in range(char_h):
        text = Text()
        for cx in range(char_w):
            # Accumulate bits per (kind, series_idx)
            buckets: dict[tuple[int, int], int] = {}
            for sr in range(4):
                for sc in range(2):
                    cell = grid[cy * 4 + sr][cx * 2 + sc]
                    if cell is not None:
                        buckets[cell] = buckets.get(cell, 0) | _BITS[sr][sc]

            if not buckets:
                text.append(" ")
            else:
                # Dominant bucket: line (kind=1) beats fill (kind=0);
                # lower series index wins ties.
                dominant = min(buckets, key=lambda k: (-k[0], k[1]))
                all_bits = 0
                for bits in buckets.values():
                    all_bits |= bits

                char = chr(0x2800 + all_bits)
                kind, s_idx = dominant
                color = colors[s_idx % len(colors)]
                style = f"bold {color}" if kind == 1 else f"dim {color}"
                text.append(char, style=style)

        rows.append(text)
    return rows


# ---------------------------------------------------------------------------
# Axis helpers
# ---------------------------------------------------------------------------

def _y_label_rows(char_h: int, y_max: float = 100.0) -> dict[int, str]:
    """Map character row index → Y-axis label for 0, 20, 40, 60, 80, 100."""
    px_h = char_h * 4
    labels: dict[int, str] = {}
    for v in range(0, int(y_max) + 1, 20):
        px_row  = _val_to_px_row(float(v), px_h, y_max)
        char_row = min(char_h - 1, px_row // 4)
        labels[char_row] = str(v)
    return labels


def _x_label_str(dates: list[str], char_w: int, timeframe: str, n: int = 5) -> str:
    """Build the x-axis date label line."""
    if not dates:
        return ""
    total = len(dates)
    indices = (
        [int(i * (total - 1) / (n - 1)) for i in range(n)]
        if total >= n
        else list(range(total))
    )

    long_tf = timeframe in ("today 5-y", "all")

    def _fmt(d: str) -> str:
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
            return dt.strftime("%Y") if long_tf else dt.strftime("%b '%y")
        except ValueError:
            return d

    buf = [" "] * char_w
    for idx in indices:
        label = _fmt(dates[idx])
        pos = int(idx / (total - 1) * (char_w - len(label))) if total > 1 else 0
        pos = max(0, min(char_w - len(label), pos))
        for i, ch in enumerate(label):
            if pos + i < char_w:
                buf[pos + i] = ch
    return "".join(buf)


# ---------------------------------------------------------------------------
# Print chart with axes
# ---------------------------------------------------------------------------

def _print_chart_block(
    rows: list[Text],
    dates: list[str],
    timeframe: str,
    char_w: int,
    char_h: int,
) -> None:
    """Print Y-labeled chart rows then the X-axis date line."""
    y_labels = _y_label_rows(char_h)

    for row_idx, row_text in enumerate(rows):
        label = y_labels.get(row_idx, "")
        line = Text()
        line.append(label.rjust(_Y_AXIS_W), style="dim")
        line.append(" ")
        line.append_text(row_text)
        console.print(line)

    x_str = _x_label_str(dates, char_w, timeframe)
    console.print(Text(" " * (_Y_AXIS_W + 1) + x_str, style="dim"))


def _chart_w() -> int:
    return max(40, (console.width or 120) - _Y_AXIS_W - 2)


# ---------------------------------------------------------------------------
# Public render functions
# ---------------------------------------------------------------------------

def render_search_chart(series: TrendSeries) -> None:
    iso_dates  = [dp.date for dp in series.series]
    values     = [float(dp.value) for dp in series.series]
    tf_label   = fmt_timeframe(series.timeframe)
    geo_label  = fmt_geo(series.geo)
    date_range = fmt_date_range(iso_dates)
    today      = fmt_today()
    title      = f'TRENDS  "{series.query.upper()}"  —  {tf_label}'
    char_w     = _chart_w()

    console.print()
    console.print(Rule(f"[bold green]{title}[/bold green]", style="green dim"))
    console.print(f"  [dim]LAST UPDATE: {today}  │  {geo_label}  │  {date_range}[/dim]")
    console.print()
    console.print("  [dim]Interest Over Time[/dim]")
    console.print()

    rows = _render_series([values], ["green"], char_w, _CHART_H)
    _print_chart_block(rows, iso_dates, series.timeframe, char_w, _CHART_H)

    console.print()
    _print_stats(series)
    console.print("  [dim]* Interest indexed to 100 = peak popularity in window[/dim]")
    console.print()
    console.print(Rule(style="green dim"))
    console.print()


def render_compare_chart(series_list: list[TrendSeries]) -> None:
    if not series_list:
        return

    iso_dates    = [dp.date for dp in series_list[0].series]
    all_values   = [[float(dp.value) for dp in s.series] for s in series_list]
    tf_label     = fmt_timeframe(series_list[0].timeframe)
    geo_label    = fmt_geo(series_list[0].geo)
    date_range   = fmt_date_range(iso_dates)
    today        = fmt_today()
    queries_lbl  = "  vs  ".join(f'"{s.query.upper()}"' for s in series_list)
    title        = f"TRENDS  {queries_lbl}  —  {tf_label}"
    char_w       = _chart_w()

    console.print()
    console.print(Rule(f"[bold green]{title}[/bold green]", style="green dim"))
    console.print(f"  [dim]LAST UPDATE: {today}  │  {geo_label}  │  {date_range}[/dim]")
    console.print()
    console.print("  [dim]Interest Over Time[/dim]")
    console.print()

    rows = _render_series(all_values, COMPARE_COLORS, char_w, _CHART_H)
    _print_chart_block(rows, iso_dates, series_list[0].timeframe, char_w, _CHART_H)

    console.print()
    for i, s in enumerate(series_list):
        c        = COMPARE_COLORS[i % len(COMPARE_COLORS)]
        peak_str = f"peak: {s.peak_value} ({fmt_date(s.peak_date)})"
        console.print(
            f"  [{c}]●[/{c}] [bold]{s.query}[/bold]"
            f"   [dim]current:[/dim] {s.current_value}"
            f"   [dim]{peak_str}[/dim]"
        )

    console.print()
    console.print("  [dim]* Interest indexed to 100 = peak popularity in window[/dim]")
    console.print()
    console.print(Rule(style="green dim"))
    console.print()


def _print_stats(series: TrendSeries) -> None:
    peak_str = f"Peak: [bold]{series.peak_value}[/bold] ({fmt_date(series.peak_date)})"
    curr_str = f"Current: [bold]{series.current_value}[/bold]"
    avg_str  = f"Avg: [bold]{series.avg_value:.0f}[/bold]"
    console.print(f"  {peak_str}   {curr_str}   {avg_str}")
