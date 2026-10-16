import { LogOut, RefreshCw } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useDashboard } from "../hooks/useDashboard";
import { useTickerStream } from "../hooks/useTickerStream";
import { formatAsOf } from "../utils/format";
import { Panel } from "./Panel";
import { Ticker } from "./Ticker";

const ORDER = ["gdp_growth", "debt_gdp", "trade", "gst", "inflation", "gov_expenditure"];

export function Dashboard() {
  const { logout } = useAuth();
  const { data, loading, error, reload } = useDashboard();
  const ticker = useTickerStream(data?.ticker);
  const panels = data ? [...data.panels].sort((a, b) => ORDER.indexOf(a.key) - ORDER.indexOf(b.key)) : [];

  return (
    <div className="dash">
      <header className="dash__head">
        <h1>ECONOMIC INDICATOR</h1>
        <button className="signout" onClick={logout} aria-label="Sign out"><LogOut size={14} /> Sign out</button>
      </header>
      <Ticker ticker={ticker} />

      {error && data && (
        <div className="banner" role="alert">
          Couldn't refresh ({error.message}). Showing data loaded {formatAsOf(data.generated_at)}.
          <button onClick={reload}><RefreshCw size={12} /> Retry</button>
        </div>
      )}

      {loading && !data && (
        <div className="grid" aria-busy="true" aria-label="Loading dashboard">
          {ORDER.map((k) => <div key={k} className="panel panel--skeleton" />)}
        </div>
      )}

      {!loading && !data && error && (
        <div className="fatal" role="alert">
          <h2>We couldn't load the dashboard</h2>
          <p>{error.message}</p>
          {error.requestId && <small>Reference: {error.requestId}</small>}
          <button onClick={reload}><RefreshCw size={14} /> Try again</button>
        </div>
      )}

      {data && <main className="grid">{panels.map((p) => <Panel key={p.key} panel={p} />)}</main>}
    </div>
  );
}
