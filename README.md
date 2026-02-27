# Trends CLI

A terminal interface for Google Trends. Search any topic and get an interactive chart of interest over time, compare multiple terms head-to-head, discover related queries, and see what's trending — all without leaving the shell.

No API key required. Data is the same public data Google Trends uses.

---

## Installation

Requires Python 3.11+.

```bash
git clone <repo>
cd trends
pip3 install -e .
```

Verify:

```bash
trends --help
```

---

## Commands

### `search` — Interest over time

Fetches and plots Google Trends interest for a single search term. Interest is indexed 0–100 where 100 = peak popularity within the selected time window.

```bash
trends search "artificial intelligence"
trends search "housing market" --timeframe 10y
trends search "taylor swift" --timeframe 1y --geo GB
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--timeframe` / `-t` | `5y` | Time window — see [Timeframes](#timeframes) below |
| `--geo` / `-g` | `US` | Country code, e.g. `US`, `GB`, `DE` — see [Geo codes](#geo-codes) |
| `--format` | `chart` | `chart` for the visual, `json` to get raw data |
| `--no-cache` | off | Bypass the 5-minute response cache and fetch fresh data |

```bash
trends search "bitcoin"
trends search "recession" --timeframe 10y
trends search "premier league" --geo GB --timeframe 1y
trends search "nvidia" --no-cache
```

**What the chart shows:**

```
──────────────── TRENDS  "BITCOIN"  —  5Y TREND ─────────────────
  LAST UPDATE: Feb 26, 2026  │  UNITED STATES  │  Feb 2021 – Feb 2026

  Interest Over Time

  100 ⢰⡆
      ⢸⡇
   80 ⣸⡇ ⡆
      ⣿⣇⣼⡄         ⡄
   60 ⣿⣿⣿⣧          ⣷
      ⣿⣿⣿⣿⣦         ⣿⣆                            ⣴
   40 ⣿⣿⣿⣿⣿⣄  ⢠⣦⡄  ⢰⣿⣦   ⢀                    ⢀⣾⣿⡄
      ⣿⣿⣿⣿⣿⣿⣀⣿⣿⣿⣀⣸⣿⣿⣧⣀⣼⡆⢰⣦⣄           ⡀  ⢀⣼⣿⣿⣿⣿⡀
   20 ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣤⣴⣶⣤⣤⣤⣼⣤⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿
    0 ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
      2021             2022            2023            2026

  Peak: 100 (Nov 2021)   Current: 33   Avg: 30
  * Interest indexed to 100 = peak popularity in window
──────────────────────────────────────────────────────────────────
```

The line is rendered using Unicode braille characters at 2×4 sub-character pixel resolution. The bright line is current interest; the dim fill below shows the trend shape over time. Peak, current, and average interest are shown below the chart.

---

### `compare` — Compare up to 5 terms

Overlays multiple search terms on a single chart. Google Trends normalizes all terms together, so the values are comparable — 100 means peak popularity *relative to all terms in the set*.

```bash
trends compare "bitcoin" "ethereum"
trends compare "python" "javascript" "rust" --timeframe 3y
trends compare "pepsi" "coca cola" "mountain dew" --geo US --timeframe 5y
```

**Options:** same as `search` — `--timeframe`, `--geo`, `--format`, `--no-cache`.

- Minimum 2 terms, maximum 5 (Google Trends limit).
- A legend below the chart shows each term's current value and peak with date.
- Each series gets a distinct color: green, cyan, yellow, red, white.

```bash
trends compare "openai" "anthropic" "google deepmind" --timeframe 2y
trends compare "iphone" "android" --geo GB --timeframe 5y
```

---

### `related` — Related queries and topics

Shows what people search alongside your term — useful for understanding context, finding adjacent topics, and spotting what's rising fast.

```bash
trends related "electric vehicles"
trends related "bitcoin" --limit 15
trends related "real estate" --geo CA
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--geo` / `-g` | `US` | Country code |
| `--limit` / `-n` | `10` | Max results per section |
| `--format` | `table` | `table` for display, `json` for raw data |
| `--no-cache` | off | Bypass cache |

Output is two tables: **Top Queries** (most popular related searches, scored 0–100) and **Rising Queries** (fastest growing, shown as percentage increase). Rising queries labeled `+5000%` or higher indicate breakout search interest.

```bash
trends related "inflation"
trends related "ai coding" --limit 20
trends related "nba finals" --format json | jq '.rising_queries'
```

---

### `trending` — Today's trending searches

Shows what's trending right now in a given country.

```bash
trends trending
trends trending --geo GB
trends trending --limit 10
trends trending --realtime
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--geo` / `-g` | `US` | Country code |
| `--limit` / `-n` | `20` | Max results |
| `--realtime` | off | Use the realtime trending endpoint (last 24 hours) instead of daily |
| `--format` | `table` | `table` or `json` |
| `--no-cache` | off | Bypass cache |

```bash
trends trending
trends trending --geo JP --limit 15
trends trending --realtime --format json
```

---

## Timeframes

The `--timeframe` flag accepts these shorthand values:

| Flag | Range | Resolution |
|------|-------|------------|
| `1h` | Last hour | Minute |
| `4h` | Last 4 hours | Minute |
| `1d` | Last day | Hourly |
| `7d` | Last 7 days | Hourly |
| `1m` | Last month | Daily |
| `3m` | Last 3 months | Daily |
| `1y` | Last 12 months | Weekly |
| `5y` | Last 5 years | Weekly (default) |
| `10y` | Since 2004 | Monthly |

**Tip:** Longer timeframes (`5y`, `10y`) are best for spotting macro trends and identifying when interest in a topic peaked. Shorter ones (`1d`, `7d`) are better for tracking breaking news and viral moments.

```bash
trends search "bird flu" --timeframe 7d      # how fast is it spreading this week?
trends search "housing crash" --timeframe 10y  # how does current interest compare to 2008?
trends search "super bowl" --timeframe 1y    # see the annual spike pattern
```

---

## Geo codes

Pass any ISO 3166-1 alpha-2 country code to `--geo`. Leave it blank (empty string `""`) for worldwide data.

Common codes:

| Code | Country |
|------|---------|
| `US` | United States (default) |
| `GB` | United Kingdom |
| `CA` | Canada |
| `AU` | Australia |
| `DE` | Germany |
| `FR` | France |
| `JP` | Japan |
| `IN` | India |
| `BR` | Brazil |
| `MX` | Mexico |

```bash
trends search "cricket" --geo IN
trends search "cycling" --geo FR --timeframe 1y
trends compare "labour party" "tory" --geo GB
```

For worldwide data, pass an empty geo string:
```bash
trends search "world cup" --geo ""
```

---

## JSON output & piping

Every command outputs **JSON automatically when piped** to another process — no flags needed. This makes it easy to use with `jq`, scripts, or AI agents.

```bash
# Get the peak date and value for a term
trends search "bitcoin" | jq '{peak_date, peak_value, current_value}'

# Extract the full time series as CSV-style output
trends search "inflation" --timeframe 10y | jq -r '.series[] | "\(.date),\(.value)"'

# Compare two terms and get current values
trends compare "python" "javascript" | jq '.[].{query, current_value, peak_value}'

# Get top 10 rising queries as a list
trends related "ai" | jq '[.rising_queries[].title]'

# Check what's trending and filter by keyword
trends trending --format json | jq '[.[] | select(.title | test("Trump"; "i"))]'
```

You can also force JSON output in a terminal with `--format json` (or `--format chart` forces the chart even when piped):

```bash
trends search "bitcoin" --format json | jq .
trends search "bitcoin" --format json > bitcoin_trends.json
```

**JSON shape for `search` and `compare`:**

```json
{
  "query": "bitcoin",
  "timeframe": "today 5-y",
  "geo": "US",
  "fetched_at": "2026-02-26T18:00:00",
  "peak_value": 100,
  "peak_date": "2021-11-14",
  "current_value": 33,
  "avg_value": 30.2,
  "series": [
    { "date": "2021-02-21", "value": 86 },
    { "date": "2021-02-28", "value": 58 }
  ]
}
```

`compare` returns an array of these objects, one per query.

**JSON shape for `related`:**

```json
{
  "query": "bitcoin",
  "geo": "US",
  "top_queries":    [{ "title": "bitcoin price", "value": "100" }],
  "rising_queries": [{ "title": "how to buy bitcoin", "value": "9650" }],
  "top_topics":     [],
  "rising_topics":  []
}
```

**JSON shape for `trending`:**

```json
[
  { "rank": 1, "title": "Super Bowl", "traffic": "" },
  { "rank": 2, "title": "Elon Musk",  "traffic": "" }
]
```

---

## Caching

Responses are cached locally for 5 minutes in `/tmp/trends_cache/`. This means:

- Running the same query twice in 5 minutes is instant — no network request.
- Useful when piping the same data to multiple tools.
- Pass `--no-cache` to always fetch fresh data.

```bash
# First call hits Google Trends (~1–3 seconds)
trends search "bitcoin"

# Second call within 5 minutes is instant
trends search "bitcoin"

# Force a fresh fetch
trends search "bitcoin" --no-cache
```

---

## Tips

**Spot the news cycle:** Short timeframes show the moment a topic explodes into search. Compare `7d` and `1y` to see if current interest is a spike or a sustained shift.

```bash
trends search "deepseek" --timeframe 3m    # when did it blow up?
trends search "deepseek" --timeframe 1y    # is it still elevated?
```

**Find what people actually search (not what you assume):** Use `related` to discover the real queries driving interest in a topic.

```bash
trends related "weight loss"    # probably not what you expect
trends related "electric cars"  # rising queries show what's new
```

**Compare trends that aren't obvious competitors:**

```bash
trends compare "buy gold" "buy bitcoin" --timeframe 5y   # flight-to-safety correlation?
trends compare "layoffs" "job openings" --timeframe 3y   # labor market pulse
trends compare "rent" "buy house" --timeframe 10y        # affordability sentiment
```

**Check if a trend is seasonal:**

```bash
trends search "sunscreen" --timeframe 5y    # clear summer spikes
trends search "flu symptoms" --timeframe 5y # winter cycles
trends search "tax return" --timeframe 3y   # April every year
```

**Use with `watch` for a live feed:**

```bash
watch -n 300 trends search "earthquake" --timeframe 1d --no-cache
```

**Use in shell scripts:**

```bash
#!/bin/bash
# Alert if current interest in a topic exceeds 80
CURRENT=$(trends search "bank run" --timeframe 1m | jq '.current_value')
if [ "$CURRENT" -gt 80 ]; then
  echo "⚠️  'bank run' search interest at $CURRENT/100 — elevated"
fi
```

---

## How interest is scored

Google Trends does not return raw search volumes. All values are **relative interest**, indexed from 0 to 100:

- **100** = peak popularity for that term within the selected time window and region.
- **50** = half the search volume of the peak.
- **0** = negligible search volume relative to the peak.

This means:
- Values are **not** comparable across different `search` calls. To compare two terms, use `compare` — it normalizes them together in a single request.
- A value of 100 for `"bitcoin"` and 100 for `"coffee"` does **not** mean they have the same search volume.
- Changing `--timeframe` changes the baseline. `bitcoin --timeframe 1y` and `bitcoin --timeframe 10y` will show different values for the same date.

---

## Requirements

- Python 3.11+
- Dependencies (installed automatically): `typer`, `rich`, `pytrends`, `plotext`
- No API key, no account, no rate limit beyond Google's standard throttling

Data comes from Google Trends via `pytrends`, an unofficial wrapper around the same public endpoint that `trends.google.com` uses.

---

## Development

```bash
git clone <repo>
cd trends
pip3 install -e .

# Run directly
trends search "bitcoin"
trends compare "python" "javascript" --timeframe 3y
trends related "housing market"
trends trending
```
