import { Banknote, Building2, Coins, Globe2, Landmark, Percent, Target, Truck, Ship, Receipt, type LucideIcon } from "lucide-react";
import type { Card } from "../api/types";
import { formatDelta, formatValue, MISSING } from "../utils/format";

const ICONS: Record<string, LucideIcon> = {
  india: Landmark, world: Globe2, us: Landmark, exports: Ship, imports: Truck, collections: Receipt,
  average: Coins, rate: Percent, target: Target, total: Banknote, capital: Building2,
};

function Flag({ code }: { code?: string }) {
  if (code === "IN") return (
    <svg className="flag" viewBox="0 0 24 24" aria-label="India"><clipPath id="fi"><circle cx="12" cy="12" r="11" /></clipPath>
      <g clipPath="url(#fi)"><rect width="24" height="8" fill="#ff9933" /><rect y="8" width="24" height="8" fill="#fff" />
        <rect y="16" width="24" height="8" fill="#138808" /><circle cx="12" cy="12" r="2.4" fill="none" stroke="#1a3a8f" strokeWidth="0.8" /></g></svg>);
  if (code === "US") return (
    <svg className="flag" viewBox="0 0 24 24" aria-label="United States"><clipPath id="fu"><circle cx="12" cy="12" r="11" /></clipPath>
      <g clipPath="url(#fu)"><rect width="24" height="24" fill="#fff" />
        {[0, 4, 8, 12, 16, 20].map((y) => <rect key={y} y={y} width="24" height="2" fill="#d22f3a" />)}
        <rect width="12" height="13" fill="#2b3f8f" /></g></svg>);
  return null;
}

export function StatCard({ card }: { card: Card }) {
  const Icon = ICONS[card.id] ?? Coins;
  const delta = formatDelta(card.delta, card.delta_unit);
  const estimate = card.basis && card.basis !== "actual";
  return (
    <div className="stat">
      <div className="stat__main">
        <div className="stat__label">
          <Flag code={card.flag} />
          <span>{card.label}</span>
          {estimate && <em title={card.basis ?? ""}>{card.basis === "revised_estimate" ? "RE" : "Est."}</em>}
        </div>
        <div className="stat__value" aria-label={`${card.label} ${formatValue(card.value, card.unit)}`}>
          {formatValue(card.value, card.unit)}
        </div>
        <span className={`delta delta--${delta.dir}`} title={card.period ? `vs previous period (latest: ${card.period})` : undefined}>
          {delta.text === MISSING ? MISSING : delta.text}
        </span>
      </div>
      <div className="stat__art" aria-hidden="true"><Icon size={34} strokeWidth={1.6} /></div>
    </div>
  );
}
