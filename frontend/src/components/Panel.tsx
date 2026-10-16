import { AlertTriangle, DatabaseZap } from "lucide-react";
import type { Panel as PanelData } from "../api/types";
import { formatAsOf } from "../utils/format";
import { IndicatorChart } from "./charts/IndicatorChart";
import { StatCard } from "./StatCard";

export function Panel({ panel }: { panel: PanelData }) {
  const unavailable = panel.status === "unavailable";
  return (
    <section className={`panel panel--${panel.status}`} aria-labelledby={`h-${panel.key}`}>
      <header className="panel__head">
        <h2 id={`h-${panel.key}`}>{panel.title}{panel.subtitle && <span> {panel.subtitle}</span>}</h2>
        {panel.status === "stale" && (
          <span className="badge badge--stale" title="The last refresh failed; showing the last valid data.">
            <AlertTriangle size={12} /> Stale
          </span>
        )}
      </header>

      <div className="panel__cards">{panel.cards.map((c) => <StatCard key={c.id} card={c} />)}</div>

      {unavailable ? (
        <div className="panel__empty" role="status">
          <DatabaseZap size={28} />
          <p>Data currently unavailable</p>
          <small>The source has not returned valid data yet. Values show as ---.</small>
        </div>
      ) : (
        <IndicatorChart chart={panel.chart} />
      )}

      <footer className="panel__foot">
        <span>
          Source: {panel.sources.map((s, i) => (
            <span key={s.name}>{i > 0 && ", "}<a href={s.url} target="_blank" rel="noreferrer noopener">{s.name}</a>{!s.is_nse && " (non-NSE)"}</span>
          ))}
        </span>
        <span>As of {formatAsOf(panel.as_of)}</span>
        {panel.notes.length > 0 && <span className="panel__note" title={panel.notes.join(" ")}>ⓘ Notes</span>}
      </footer>
    </section>
  );
}
