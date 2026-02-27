"""pytrends wrapper with JSON cache."""

import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path

from pytrends.request import TrendReq

from trends_cli.models import DataPoint, RelatedItem, TrendSeries, TrendingSearch
from trends_cli.display.format import geo_to_pn

_CACHE_DIR = Path("/tmp/trends_cache")
_CACHE_TTL = 300  # 5 minutes


def _cache_path(key: str) -> Path:
    digest = hashlib.sha256(key.encode()).hexdigest()
    return _CACHE_DIR / f"{digest}.json"


def _cache_read(key: str) -> dict | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        if time.time() - data.get("_ts", 0) > _CACHE_TTL:
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _cache_write(key: str, data: dict) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["_ts"] = time.time()
    path = _cache_path(key)
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def _pt() -> TrendReq:
    return TrendReq(hl="en-US", tz=360)


# ---------------------------------------------------------------------------
# Interest over time
# ---------------------------------------------------------------------------

def fetch_interest(
    queries: list[str],
    timeframe: str,
    geo: str,
    no_cache: bool = False,
) -> list[TrendSeries]:
    """Fetch interest over time for one or more queries.

    Returns one TrendSeries per query, normalized together (Google Trends
    always returns relative values across the full query set).
    """
    cache_key = json.dumps({"q": sorted(queries), "tf": timeframe, "geo": geo})

    cached = None if no_cache else _cache_read(cache_key)

    if cached is None:
        pt = _pt()
        pt.build_payload(kw_list=queries, timeframe=timeframe, geo=geo)
        df = pt.interest_over_time()
        if df.empty:
            return []

        # Drop the isPartial column
        df = df.drop(columns=["isPartial"], errors="ignore")

        raw: dict[str, list] = {}
        for col in df.columns:
            raw[str(col)] = [
                {"date": str(idx.date()), "value": int(val)}
                for idx, val in zip(df.index, df[col])
            ]

        fetched_at = datetime.utcnow().isoformat()
        payload = {"raw": raw, "fetched_at": fetched_at, "timeframe": timeframe, "geo": geo}
        _cache_write(cache_key, payload)
        cached = payload

    result = []
    for q in queries:
        # Match by original query (pytrends uses the query as column name)
        col_data = cached["raw"].get(q)
        if col_data is None:
            # pytrends may truncate/alter the key; try case-insensitive match
            for k, v in cached["raw"].items():
                if k.lower() == q.lower():
                    col_data = v
                    break
        if col_data is None:
            continue

        series = [DataPoint(date=d["date"], value=d["value"]) for d in col_data]
        values = [dp.value for dp in series]

        if not values:
            continue

        peak_val = max(values)
        peak_idx = values.index(peak_val)
        peak_date = series[peak_idx].date

        result.append(TrendSeries(
            query=q,
            timeframe=cached["timeframe"],
            geo=cached["geo"],
            fetched_at=cached["fetched_at"],
            series=series,
            peak_value=peak_val,
            peak_date=peak_date,
            current_value=values[-1],
            avg_value=round(sum(values) / len(values), 1),
        ))

    return result


# ---------------------------------------------------------------------------
# Related topics & queries
# ---------------------------------------------------------------------------

def fetch_related(
    query: str,
    geo: str,
    no_cache: bool = False,
) -> dict[str, list[RelatedItem]]:
    """Return {"top_queries", "rising_queries", "top_topics", "rising_topics"}."""
    cache_key = json.dumps({"related": query, "geo": geo})
    cached = None if no_cache else _cache_read(cache_key)

    if cached is None:
        pt = _pt()
        pt.build_payload(kw_list=[query], timeframe="today 12-m", geo=geo)

        def _df_to_list(df, title_col: str) -> list[dict]:
            if df is None or not hasattr(df, "iterrows") or df.empty:
                return []
            rows = []
            for _, row in df.iterrows():
                try:
                    title = str(row.get(title_col) or row.get("query") or "")
                    val   = str(row.get("value", ""))
                    if title:
                        rows.append({"title": title, "value": val})
                except Exception:
                    continue
            return rows

        q_top: list[dict] = []
        q_rising: list[dict] = []
        t_top: list[dict] = []
        t_rising: list[dict] = []

        try:
            queries = pt.related_queries()
            q_top   = _df_to_list(queries.get(query, {}).get("top"), "query")
            q_rising = _df_to_list(queries.get(query, {}).get("rising"), "query")
        except Exception:
            pass

        try:
            topics  = pt.related_topics()
            t_top   = _df_to_list(topics.get(query, {}).get("top"), "topic_title")
            t_rising = _df_to_list(topics.get(query, {}).get("rising"), "topic_title")
        except Exception:
            pass

        payload = {
            "top_queries":     q_top,
            "rising_queries":  q_rising,
            "top_topics":      t_top,
            "rising_topics":   t_rising,
        }
        _cache_write(cache_key, payload)
        cached = payload

    def _to_items(lst: list[dict]) -> list[RelatedItem]:
        return [RelatedItem(title=d["title"], value=str(d["value"])) for d in lst]

    return {
        "top_queries":    _to_items(cached.get("top_queries", [])),
        "rising_queries": _to_items(cached.get("rising_queries", [])),
        "top_topics":     _to_items(cached.get("top_topics", [])),
        "rising_topics":  _to_items(cached.get("rising_topics", [])),
    }


# ---------------------------------------------------------------------------
# Trending searches
# ---------------------------------------------------------------------------

def fetch_trending(
    geo: str,
    realtime: bool = False,
    no_cache: bool = False,
) -> list[TrendingSearch]:
    """Fetch trending searches. Uses realtime endpoint; falls back to top searches."""
    cache_key = json.dumps({"trending": geo, "realtime": realtime})
    cached = None if no_cache else _cache_read(cache_key)

    if cached is None:
        pt = _pt()
        rows: list[dict] = []

        try:
            df = pt.realtime_trending_searches(pn=geo.upper() or "US")
            if not df.empty:
                title_col = "title" if "title" in df.columns else df.columns[0]
                for i, row in enumerate(df.itertuples(), 1):
                    title = getattr(row, title_col, str(row[1]))
                    rows.append({"rank": i, "title": str(title), "traffic": ""})
        except Exception:
            pass

        if not rows:
            # Fallback: top searches for the query "news" in the geo
            try:
                pt.build_payload(kw_list=["news"], timeframe="now 7-d", geo=geo)
                rq = pt.related_queries()
                top_df = rq.get("news", {}).get("top")
                if top_df is not None and not top_df.empty:
                    for i, r in enumerate(top_df.itertuples(), 1):
                        title = getattr(r, "query", str(r[1]))
                        rows.append({"rank": i, "title": str(title), "traffic": ""})
            except Exception:
                pass

        payload = {"rows": rows}
        _cache_write(cache_key, payload)
        cached = payload

    return [
        TrendingSearch(rank=r["rank"], title=r["title"], traffic=r.get("traffic", ""))
        for r in cached.get("rows", [])
    ]
