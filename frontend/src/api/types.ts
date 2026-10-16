export type Status = "ok" | "stale" | "unavailable";
export type ChartType = "bar" | "bar_line" | "area" | "line" | "stacked";

export interface Source { name: string; url: string; is_nse: boolean }
export interface Card {
  id: string; label: string; value: number | null; unit: string;
  delta: number | null; delta_unit: "pp" | "%"; period: string | null; basis: string | null; flag?: string;
}
export interface Series { key: string; label: string; values: (number | null)[]; kind?: "line" }
export interface Chart { type: ChartType; y_unit: string; x: string[]; series: Series[]; totals?: (number | null)[] }
export interface Panel {
  key: string; title: string; subtitle: string | null; status: Status;
  as_of: string | null; fetched_at: string | null; sources: Source[]; cards: Card[]; chart: Chart; notes: string[];
}
export interface TickerItem { symbol: string; label: string; last: number; change: number; pct_change: number; is_nse: boolean }
export interface Ticker { status: Status; as_of: string | null; fetched_at: string | null; items: TickerItem[]; sources: Source[] }
export interface DashboardData { generated_at: string; ticker: Ticker; panels: Panel[] }
