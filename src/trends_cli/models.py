from dataclasses import dataclass, field


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
    series: list[DataPoint] = field(default_factory=list)
    peak_value: int = 0
    peak_date: str = ""
    current_value: int = 0
    avg_value: float = 0.0


@dataclass
class RelatedItem:
    title: str
    value: str  # "72" for top; "+3400%" for rising


@dataclass
class TrendingSearch:
    rank: int
    title: str
    traffic: str = ""
