"""Date, value, and geo formatting helpers."""

from datetime import datetime, date

TIMEFRAME_LABELS = {
    "now 1-H":    "1H",
    "now 4-H":    "4H",
    "now 1-d":    "1D",
    "now 7-d":    "7D",
    "today 1-m":  "1M",
    "today 3-m":  "3M",
    "today 12-m": "1Y",
    "today 5-y":  "5Y",
    "all":        "10Y",
}

GEO_NAMES = {
    "":   "WORLDWIDE",
    "US": "UNITED STATES",
    "GB": "UNITED KINGDOM",
    "CA": "CANADA",
    "AU": "AUSTRALIA",
    "DE": "GERMANY",
    "FR": "FRANCE",
    "JP": "JAPAN",
    "IN": "INDIA",
    "BR": "BRAZIL",
    "MX": "MEXICO",
}

CLI_TO_PYTRENDS = {
    "1h":  "now 1-H",
    "4h":  "now 4-H",
    "1d":  "now 1-d",
    "7d":  "now 7-d",
    "1m":  "today 1-m",
    "3m":  "today 3-m",
    "1y":  "today 12-m",
    "5y":  "today 5-y",
    "10y": "all",
}


def cli_to_pytrends(tf: str) -> str:
    """Convert CLI timeframe flag to pytrends timeframe string."""
    return CLI_TO_PYTRENDS.get(tf, "today 5-y")


def fmt_timeframe(pytrends_tf: str) -> str:
    """'today 5-y' → '5Y TREND'"""
    label = TIMEFRAME_LABELS.get(pytrends_tf, pytrends_tf.upper())
    return f"{label} TREND"


def fmt_geo(geo: str) -> str:
    """'US' → 'UNITED STATES'"""
    return GEO_NAMES.get(geo.upper(), geo.upper())


def fmt_date(d: str) -> str:
    """'2021-11-14' → 'Nov 14, 2021'"""
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%b %d, %Y")
    except ValueError:
        return d


def fmt_date_range(series_dates: list[str]) -> str:
    """First and last date in the series → 'Feb 2021 – Feb 2026'"""
    if not series_dates:
        return ""
    try:
        start = datetime.strptime(series_dates[0], "%Y-%m-%d").strftime("%b %Y")
        end   = datetime.strptime(series_dates[-1], "%Y-%m-%d").strftime("%b %Y")
        return f"{start} – {end}"
    except ValueError:
        return f"{series_dates[0]} – {series_dates[-1]}"


def fmt_today() -> str:
    return date.today().strftime("%b %d, %Y")


def geo_to_pn(geo: str) -> str:
    """Convert geo code to pytrends pn parameter for trending_searches."""
    mapping = {
        "US": "united_states",
        "GB": "united_kingdom",
        "CA": "canada",
        "AU": "australia",
        "DE": "germany",
        "FR": "france",
        "JP": "japan",
        "IN": "india",
        "BR": "brazil",
        "MX": "mexico",
    }
    return mapping.get(geo.upper(), "united_states")
