import { describe, expect, it } from "vitest";
import { formatAsOf, formatDelta, formatValue, MISSING } from "../utils/format";

describe("format", () => {
  it("shows --- for missing values", () => {
    expect(formatValue(null, "%")).toBe(MISSING);
    expect(formatValue(Number.NaN, "%")).toBe(MISSING);
    expect(formatDelta(null, "pp").text).toBe(MISSING);
    expect(formatAsOf(null)).toBe(MISSING);
  });
  it("formats units", () => {
    expect(formatValue(4.8, "%")).toBe("4.80%");
    expect(formatValue(382.94, "$B")).toBe("$382.9 B");
    expect(formatValue(22.08, "L Cr")).toBe("₹22.08 L Cr");
  });
  it("derives direction from sign", () => {
    expect(formatDelta(-0.2, "pp")).toEqual({ text: "▼ 0.20pp", dir: "down" });
    expect(formatDelta(1.5, "%").dir).toBe("up");
  });
});
