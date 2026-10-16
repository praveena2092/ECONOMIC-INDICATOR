export const MISSING = "---";

export function formatValue(value: number | null | undefined, unit: string): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return MISSING;
  switch (unit) {
    case "%": return `${value.toFixed(2)}%`;
    case "$B": return `$${value.toFixed(1)} B`;
    case "L Cr": return `₹${value.toFixed(2)} L Cr`;
    default: return String(value);
  }
}

export function formatDelta(delta: number | null | undefined, unit: "pp" | "%"): { text: string; dir: "up" | "down" | "flat" | "none" } {
  if (delta === null || delta === undefined || !Number.isFinite(delta)) return { text: MISSING, dir: "none" };
  const dir = delta > 0 ? "up" : delta < 0 ? "down" : "flat";
  const arrow = dir === "up" ? "▲" : dir === "down" ? "▼" : "■";
  return { text: `${arrow} ${Math.abs(delta).toFixed(2)}${unit}`, dir };
}

export function formatAxisValue(v: number | null | undefined, unit: string): string {
  if (v === null || v === undefined) return "";
  return unit === "%" ? `${v}%` : String(v);
}

export function formatQuote(n: number): string {
  return n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatAsOf(iso: string | null): string {
  if (!iso) return MISSING;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return MISSING;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}
