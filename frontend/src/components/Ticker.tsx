import type { Ticker as TickerData } from "../api/types";
import { formatQuote, MISSING } from "../utils/format";

export function Ticker({ ticker }: { ticker: TickerData | undefined }) {
  const items = ticker?.items ?? [];
  const status = ticker?.status ?? "unavailable";
  const loop = [...items, ...items];   // duplicated so the CSS marquee loops seamlessly
  return (
    <div className="ticker" role="region" aria-label="Live market ticker">
      <span className={`ticker__live ticker__live--${status}`}>
        <i /> {status === "ok" ? "LIVE" : status === "stale" ? "STALE" : "OFFLINE"}
      </span>
      <div className="ticker__viewport">
        {items.length === 0 ? (
          <span className="ticker__empty">Market data unavailable {MISSING}</span>
        ) : (
          <ul className="ticker__track">
            {loop.map((q, i) => {
              const dir = q.change > 0 ? "up" : q.change < 0 ? "down" : "flat";
              return (
                <li key={`${q.symbol}-${i}`} aria-hidden={i >= items.length}
                    title={`${q.is_nse ? "NSE" : "Non-NSE source"} · ${ticker?.sources.map((s) => s.name).join(", ")}`}>
                  <b>{q.label}</b> <span>{formatQuote(q.last)}</span>{" "}
                  <span className={`chg chg--${dir}`}>
                    {q.change >= 0 ? "+" : "-"}{formatQuote(Math.abs(q.change))} ({q.pct_change >= 0 ? "+" : ""}{q.pct_change.toFixed(2)}%)
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
