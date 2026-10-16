import { useMemo, useState } from "react";
import {
  Area, Bar, CartesianGrid, ComposedChart, Line, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { Chart } from "../../api/types";
import { formatAxisValue, MISSING } from "../../utils/format";

export const SERIES_COLORS: Record<string, string> = {
  india: "#1f8fc9", world: "#f0a53a", imports: "#1f8fc9", exports: "#f0a53a", balance: "#37d67a",
  collections: "#1f8fc9", average: "#f4d44a", rate: "#2cb5e8", revenue: "#2f6fe0", capital: "#f0a53a",
};
const AXIS = { fill: "#c9d3e6", fontSize: 11 };

function Legend({ chart, hidden, toggle }: { chart: Chart; hidden: Set<string>; toggle: (k: string) => void }) {
  if (chart.type === "area" || chart.type === "line") return null;
  return (
    <ul className="legend" aria-label="Chart legend">
      {chart.series.map((s) => (
        <li key={s.key}>
          <button type="button" aria-pressed={!hidden.has(s.key)} className={hidden.has(s.key) ? "is-off" : ""}
                  onClick={() => toggle(s.key)}>
            <i className={s.kind === "line" ? "legend__line" : "legend__box"} style={{ background: SERIES_COLORS[s.key] }} />
            {s.label}
          </button>
        </li>
      ))}
    </ul>
  );
}

function TooltipBox({ active, payload, label, unit }: { active?: boolean; payload?: any[]; label?: string; unit: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tip">
      <strong>{label}</strong>
      {payload.map((p) => (
        <div key={p.dataKey}><i style={{ background: p.color || p.stroke || p.fill }} />
          {p.name}: {p.value === null || p.value === undefined ? MISSING : `${p.value}${unit === "%" ? "%" : ` ${unit}`}`}
        </div>
      ))}
    </div>
  );
}

export function IndicatorChart({ chart }: { chart: Chart }) {
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const toggle = (k: string) => setHidden((h) => { const n = new Set(h); n.has(k) ? n.delete(k) : n.add(k); return n; });

  const data = useMemo(() => chart.x.map((x, i) => {
    const row: Record<string, string | number | null> = { x };
    chart.series.forEach((s) => { row[s.key] = s.values[i] ?? null; });
    if (chart.totals) row.__total = chart.totals[i] ?? null;
    return row;
  }), [chart]);

  const visible = chart.series.filter((s) => !hidden.has(s.key));
  // A period where every visible series is null is rendered as '---' under its tick.
  const missing = chart.x.map((_, i) => visible.length > 0 && visible.every((s) => s.values[i] == null));
  const tick = (props: any) => (
    <g transform={`translate(${props.x},${props.y})`}>
      <text dy={14} textAnchor="middle" {...AXIS}>{props.payload.value}</text>
      {missing[props.index] && <text dy={28} textAnchor="middle" fill="#7f8bab" fontSize={10}>{MISSING}</text>}
    </g>
  );

  const isBars = chart.type === "bar" || chart.type === "bar_line" || chart.type === "stacked";
  const domain: [any, any] = isBars
    ? [0, (max: number) => Math.max(1, Math.ceil(max * 1.15))]
    : [(m: number) => Math.max(0, Math.floor((m - 2) / 5) * 5), (m: number) => Math.ceil((m + 2) / 5) * 5];
  const label = (v: unknown) => (v === null || v === undefined ? "" : String(v));
  const bars = chart.series.filter((s) => s.kind !== "line");
  const ordered = chart.type === "stacked" ? [...bars].reverse() : bars;   // first series sits on top of the stack

  return (
    <div className="chart">
      <Legend chart={chart} hidden={hidden} toggle={toggle} />
      <div className="chart__plot">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 22, right: 8, bottom: 6, left: 0 }} barGap={2} barCategoryGap="18%">
            <defs>
              <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2cb5e8" stopOpacity={0.55} />
                <stop offset="100%" stopColor="#2cb5e8" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="rgba(160,180,220,0.12)" />
            <XAxis dataKey="x" tick={tick} tickLine={false} axisLine={{ stroke: "rgba(160,180,220,0.25)" }} height={34} interval={0} />
            <YAxis tick={AXIS} tickLine={false} axisLine={false} width={42} domain={domain} allowDecimals={false}
                   tickFormatter={(v) => formatAxisValue(v, chart.y_unit)} />
            <Tooltip content={<TooltipBox unit={chart.y_unit} />} cursor={{ fill: "rgba(255,255,255,0.05)" }} />

            {isBars && ordered.map((s) => !hidden.has(s.key) && (
              <Bar key={s.key} dataKey={s.key} name={s.label} fill={SERIES_COLORS[s.key]}
                   stackId={chart.type === "stacked" ? "a" : undefined} radius={chart.type === "stacked" ? 0 : [3, 3, 0, 0]}
                   maxBarSize={32} isAnimationActive={false}>
                {chart.type === "stacked" ? (
                  <>
                    <LabelList dataKey={s.key} position="center" fill="#fff" fontSize={9} formatter={label} />
                    {s.key === "revenue" && (
                      <LabelList dataKey="__total" position="top" fill="#e6ecfa" fontSize={10} formatter={label} />
                    )}
                  </>
                ) : (
                  <LabelList dataKey={s.key} position="top" fill="#e6ecfa" fontSize={10} formatter={label} />
                )}
              </Bar>
            ))}

            {chart.type === "bar_line" && chart.series.filter((s) => s.kind === "line" && !hidden.has(s.key)).map((s) => (
              <Line key={s.key} dataKey={s.key} name={s.label} stroke={SERIES_COLORS[s.key]} strokeWidth={2}
                    dot={{ r: 3, fill: SERIES_COLORS[s.key] }} connectNulls={false} isAnimationActive={false} />
            ))}

            {chart.type === "area" && chart.series.map((s) => (
              <Area key={s.key} dataKey={s.key} name={s.label} type="monotone" stroke="#2cb5e8" strokeWidth={2}
                    fill="url(#areaFill)" connectNulls={false} dot={{ r: 2.5, fill: "#9fdcf5" }} isAnimationActive={false} />
            ))}

            {chart.type === "line" && chart.series.map((s) => (
              <Line key={s.key} dataKey={s.key} name={s.label} type="monotone" stroke={SERIES_COLORS[s.key]} strokeWidth={2}
                    dot={{ r: 2.5, fill: "#9fdcf5" }} connectNulls={false} isAnimationActive={false}>
                <LabelList dataKey={s.key} position="top" fill="#e6ecfa" fontSize={10} formatter={label} />
              </Line>
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
