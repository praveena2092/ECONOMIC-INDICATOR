import { useEffect, useState } from "react";
import { api, parseError, tokenStore } from "../api/client";
import type { Ticker } from "../api/types";
import { API_BASE_URL, TICKER_POLL_FALLBACK_MS } from "../config";

/**
 * Live ticker over Server-Sent Events. EventSource cannot send an Authorization header, so the stream is
 * read with fetch(). If the stream drops it reconnects with backoff, and /ticker is polled as a fallback.
 */
export function useTickerStream(initial: Ticker | undefined): Ticker | undefined {
  const [ticker, setTicker] = useState<Ticker | undefined>(initial);

  useEffect(() => { if (initial) setTicker((cur) => cur ?? initial); }, [initial]);

  useEffect(() => {
    let stopped = false;
    let ctrl = new AbortController();
    let retry = 1000;

    const poll = setInterval(() => {
      api<Ticker>("/api/v1/ticker").then((t) => !stopped && setTicker(t)).catch(() => undefined);
    }, TICKER_POLL_FALLBACK_MS);

    async function connect() {
      while (!stopped) {
        ctrl = new AbortController();
        try {
          const res = await fetch(`${API_BASE_URL}/api/v1/stream/ticker`, {
            headers: { Authorization: `Bearer ${tokenStore.get() ?? ""}`, Accept: "text/event-stream" },
            signal: ctrl.signal,
          });
          if (!res.ok || !res.body) throw await parseError(res);
          retry = 1000;
          const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
          let buf = "";
          for (;;) {
            const { value, done } = await reader.read();
            if (done) break;
            buf += value;
            let idx: number;
            while ((idx = buf.indexOf("\n\n")) >= 0) {
              const block = buf.slice(0, idx);
              buf = buf.slice(idx + 2);
              const line = block.split("\n").find((l) => l.startsWith("data: "));
              if (line) {
                try { setTicker(JSON.parse(line.slice(6)) as Ticker); } catch { /* ignore malformed event */ }
              }
            }
          }
        } catch (e) {
          if (stopped || (e as Error).name === "AbortError") return;
        }
        await new Promise((r) => setTimeout(r, retry));
        retry = Math.min(retry * 2, 30_000);
      }
    }
    void connect();
    return () => { stopped = true; ctrl.abort(); clearInterval(poll); };
  }, []);

  return ticker;
}
