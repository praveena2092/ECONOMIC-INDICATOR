"""Response models. They drive the Swagger docs and validate the payload shape."""
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["ok", "stale", "unavailable"]


class ErrorBody(BaseModel):
    code: str = Field(examples=["unauthenticated"])
    message: str = Field(examples=["Authentication required."])
    request_id: str | None = Field(None, examples=["a1b2c3d4e5f6"])


class ErrorResponse(BaseModel):
    error: ErrorBody


class Source(BaseModel):
    name: str
    url: str
    is_nse: bool


class Card(BaseModel):
    id: str
    label: str
    value: float | None = Field(None, description="null when the value is not available (shown as ---)")
    unit: str = Field(description="%, $B or L Cr (INR lakh crore)")
    delta: float | None = Field(None, description="change vs previous period; null if not available")
    delta_unit: Literal["pp", "%"]
    period: str | None = None
    basis: str | None = Field(None, description="actual | estimate | revised_estimate")
    flag: str | None = None


class Series(BaseModel):
    key: str
    label: str
    values: list[float | None]
    kind: str | None = Field(None, description="'line' for line series drawn over bars")


class Chart(BaseModel):
    type: Literal["bar", "bar_line", "area", "line", "stacked"]
    y_unit: str
    x: list[str]
    series: list[Series]
    totals: list[float | None] | None = None


class Panel(BaseModel):
    key: str = Field(examples=["gdp_growth"])
    title: str
    subtitle: str | None = None
    status: Status
    as_of: str | None = Field(None, description="date of the latest data point")
    fetched_at: str | None = Field(None, description="when the backend last refreshed this data")
    sources: list[Source]
    cards: list[Card]
    chart: Chart
    notes: list[str]


class TickerItem(BaseModel):
    symbol: str
    label: str
    last: float
    change: float
    pct_change: float
    is_nse: bool


class Ticker(BaseModel):
    status: Status
    as_of: str | None = None
    fetched_at: str | None = None
    items: list[TickerItem]
    sources: list[Source]


class DashboardResponse(BaseModel):
    generated_at: str
    ticker: Ticker
    panels: list[Panel]