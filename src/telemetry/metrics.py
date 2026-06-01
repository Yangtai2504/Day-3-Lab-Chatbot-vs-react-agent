import json
import re
import sys
import warnings
from typing import Dict, Any, List


class PerformanceTracker:
    """Tracking industry-standard metrics for LLMs."""

    def __init__(self, output_path: str = "metrics.txt"):
        self.session_metrics: List[Dict[str, Any]] = []
        self._output_path = output_path
        self._out = None   # file handle, opened in parse_session_log

    def _write(self, line: str = ""):
        """Write a line to both stdout and the output file."""
        print(line)
        if self._out:
            self._out.write(line + "\n")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_session_log(self, log_source: str) -> List[Dict[str, Any]]:
        """
        Accept either:
          - a file path (str ending with .log / .json, or an existing path), OR
          - raw multi-event log text (one JSON object per block).

        Correlates AGENT_START model names with their LLM_RESPONSE events,
        calls track_request for each matched response, and returns all parsed
        event dicts.
        """
        # --- resolve input: file path vs raw text ---
        raw_log = self._load_raw(log_source)

        events: List[Dict] = []
        # Support both formats:
        #   1. NDJSON — one JSON object per line  {"event": ...}\n{"event": ...}
        #   2. Pretty-printed — multi-line blocks separated by blank lines / \n{
        # Strategy: try each line as a standalone JSON object first (NDJSON).
        # If a line starts mid-object (indented), accumulate until the object closes.
        buffer = ""
        depth = 0
        for raw_line in raw_log.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Fast path: entire object on one line
            if not buffer and line.startswith("{") and line.endswith("}"):
                try:
                    events.append(json.loads(line))
                    continue
                except json.JSONDecodeError:
                    pass  # fall through to accumulation

            # Accumulation path for pretty-printed blocks
            buffer += raw_line + "\n"
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                block = buffer.strip()
                buffer = ""
                depth = 0
                if block:
                    try:
                        events.append(json.loads(block))
                    except json.JSONDecodeError as exc:
                        self._write(f"[WARN] Skipping malformed JSON block: {exc}", file=sys.stderr)

        # Flush any remaining buffer
        if buffer.strip():
            try:
                events.append(json.loads(buffer.strip()))
            except json.JSONDecodeError as exc:
                self._write(f"[WARN] Skipping trailing malformed JSON: {exc}", file=sys.stderr)

        # Group events into per-agent-run chunks so each run is processed
        # independently. A run spans from AGENT_START to AGENT_END (inclusive).
        runs: List[List[Dict]] = []
        current_run: List[Dict] = []

        for event in events:
            evt_type = event.get("event")
            if evt_type == "AGENT_START":
                current_run = [event]
            elif current_run:
                current_run.append(event)
                if evt_type == "AGENT_END":
                    runs.append(current_run)
                    current_run = []

        # Flush any dangling run (no AGENT_END)
        if current_run:
            runs.append(current_run)

        self._out = open(self._output_path, "w", encoding="utf-8")
        self._write(f"\n{'='*60}")
        self._write(f"  SESSION LOG SUMMARY  —  {len(runs)} agent run(s) found")
        self._write(f"{'='*60}\n")

        for run_idx, run_events in enumerate(runs, start=1):
            self._process_run(run_idx, run_events)

        self.print_session_summary()
        if self._out:
            self._out.close()
            self._out = None
            self._write(f"\n  Results written to: {self._output_path}")
        return events

    def track_request(
        self,
        provider: str,
        model: str,
        usage: Dict[str, int],
        latency_ms: int,
        run_id: int = 0,
        step: int = 0,
    ):
        """Log a single request metric."""
        cost = self._calculate_cost(model, usage)
        metric = {
            "run_id": run_id,
            "step": step,
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_usd": cost,
        }
        self.session_metrics.append(metric)
        return metric

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_raw(self, log_source: str) -> str:
        """Return raw log text whether log_source is a path or inline text."""
        import os
        # Normalise Windows-style backslashes
        normalised = log_source.replace("\\", "/")
        if os.path.exists(normalised) or os.path.exists(log_source):
            path = normalised if os.path.exists(normalised) else log_source
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read()
        # Treat as raw log text
        return log_source

    def _process_run(self, run_idx: int, run_events: List[Dict]):
        """Process one agent run and print its metrics."""
        # Extract model from AGENT_START
        model = "unknown"
        task_input = ""
        for ev in run_events:
            if ev.get("event") == "AGENT_START":
                model = ev.get("data", {}).get("model", "unknown")
                task_input = ev.get("data", {}).get("input", "")
                break

        # Determine provider
        provider = self._infer_provider(model)

        # Collect LLM_RESPONSE events
        llm_responses = [ev for ev in run_events if ev.get("event") == "LLM_RESPONSE"]

        # Determine run status
        status = "unknown"
        total_steps = 0
        for ev in run_events:
            if ev.get("event") == "AGENT_END":
                status = ev.get("data", {}).get("status", "unknown")
                total_steps = ev.get("data", {}).get("steps", 0)

        self._write(f"  Run #{run_idx}")
        self._write(f"  {'─'*56}")
        self._write(f"  Task   : {task_input[:80]}")
        self._write(f"  Model  : {model}  ({provider})")
        self._write(f"  Status : {status}   Steps: {total_steps}")

        if not llm_responses:
            self._write(f"  ⚠  No LLM_RESPONSE events recorded for this run.\n")
            return

        run_prompt_tokens = 0
        run_completion_tokens = 0
        run_total_tokens = 0
        run_latency_ms = 0
        run_cost = 0.0

        for resp_ev in llm_responses:
            data = resp_ev.get("data", {})
            usage = data.get("usage", {})
            latency = data.get("latency_ms", 0)
            step = data.get("step", 0)

            metric = self.track_request(
                provider, model, usage, latency,
                run_id=run_idx, step=step
            )

            run_prompt_tokens     += metric["prompt_tokens"]
            run_completion_tokens += metric["completion_tokens"]
            run_total_tokens      += metric["total_tokens"]
            run_latency_ms        += metric["latency_ms"]
            run_cost              += metric["cost_usd"]

            # Per-step detail (only shown when >1 step)
            if len(llm_responses) > 1:
                self._write(
                    f"    Step {step}: tokens=({metric['prompt_tokens']}p "
                    f"+ {metric['completion_tokens']}c = {metric['total_tokens']}), "
                    f"latency={latency}ms, cost=${metric['cost_usd']:.8f}"
                )

        self._write(f"  Tokens : {run_prompt_tokens} prompt + "
              f"{run_completion_tokens} completion = {run_total_tokens} total")
        self._write(f"  Latency: {run_latency_ms} ms  (sum across steps)")
        cost_str = f"${run_cost:.8f}" if run_cost > 0 else "N/A (model not in pricing table)"
        self._write(f"  Cost   : {cost_str}\n")

    @staticmethod
    def _infer_provider(model: str) -> str:
        provider_map = {
            "gemini": "google",
            "gpt": "openai",
            "claude": "anthropic",
            "qwen": "alibaba",
            "phi": "microsoft",
            "llama": "meta",
            "mistral": "mistral",
        }
        m = model.lower()
        return next((v for k, v in provider_map.items() if m.startswith(k)), "unknown")

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Estimate API cost in USD based on per-million-token pricing."""
        PRICING: Dict[str, Dict[str, float]] = {
            # Gemini 2.5 Flash variants (Google AI Studio)
            "gemini-2.5-flash":         {"input": 0.30,  "output": 2.50},
            "gemini-2.5-flash-lite":    {"input": 0.10,  "output": 0.40},  # lite tier

            # Qwen 2.5 (via OpenRouter / self-hosted proxy rates)
            "qwen2.5-math-7b":          {"input": 0.23,  "output": 0.23},
            "qwen2.5-math-72b":         {"input": 0.36,  "output": 0.40},

            # OpenAI
            "gpt-4o":                   {"input": 2.50,  "output": 10.00},
            "gpt-4o-mini":              {"input": 0.15,  "output": 0.60},
            "gpt-4-turbo":              {"input": 10.00, "output": 30.00},

            # Anthropic
            "claude-opus-4-6":          {"input": 15.00, "output": 75.00},
            "claude-sonnet-4-6":        {"input": 3.00,  "output": 15.00},
            "claude-haiku-4-5":         {"input": 0.80,  "output": 4.00},

            # Microsoft / Azure
            "phi-3-mini-4k-instruct-q4": {"input": 0.10, "output": 0.10},

            # Meta (via providers)
            "llama-3.1-8b-instruct":    {"input": 0.18,  "output": 0.18},
            "llama-3.1-70b-instruct":   {"input": 0.88,  "output": 0.88},

            # Mistral
            "mistral-7b-instruct":      {"input": 0.25,  "output": 0.25},
            "mistral-large-latest":     {"input": 2.00,  "output": 6.00},
        }

        model_key = model.lower().strip()
        rates = PRICING.get(model_key)

        if rates is None:
            warnings.warn(
                f"No pricing data for model '{model}'. Cost defaults to 0.0. "
                "Add it to the PRICING table in _calculate_cost().",
                UserWarning,
                stacklevel=3,
            )
            return 0.0

        input_cost  = (usage.get("prompt_tokens",     0) / 1_000_000) * rates["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1_000_000) * rates["output"]
        return round(input_cost + output_cost, 10)

    def print_session_summary(self):
        """Print aggregate statistics across all tracked requests."""
        if not self.session_metrics:
            self._write("No metrics recorded.")
            return

        n                 = len(self.session_metrics)
        total_prompt      = sum(m["prompt_tokens"]     for m in self.session_metrics)
        total_completion  = sum(m["completion_tokens"] for m in self.session_metrics)
        total_tokens      = sum(m["total_tokens"]      for m in self.session_metrics)
        latencies         = [m["latency_ms"] for m in self.session_metrics]
        costs             = [m["cost_usd"]   for m in self.session_metrics]
        total_latency     = sum(latencies)
        total_cost        = sum(costs)
        priced            = [c for c in costs if c > 0]

        def fmt_cost(v: float) -> str:
            return f"${v:.8f}" if v > 0 else "N/A"

        self._write(f"\n{'='*60}")
        self._write("  SESSION AGGREGATE METRICS")
        self._write(f"{'='*60}")
        self._write(f"  Requests tracked : {n}")
        self._write(f"  Prompt tokens    : {total_prompt:,}")
        self._write(f"  Completion tokens: {total_completion:,}")
        self._write(f"  Total tokens     : {total_tokens:,}")
        self._write(f"  {'─'*56}")
        self._write(f"  Latency (ms)")
        self._write(f"    Total          : {total_latency:,}")
        self._write(f"    Avg            : {total_latency / n:.0f}")
        self._write(f"    Min            : {min(latencies):,}")
        self._write(f"    Max            : {max(latencies):,}")
        self._write(f"  {'─'*56}")
        self._write(f"  Cost (USD est.)")
        self._write(f"    Total          : {fmt_cost(total_cost)}")
        self._write(f"    Avg            : {fmt_cost(total_cost / n)}")
        if priced:
            self._write(f"    Min            : {fmt_cost(min(priced))}")
            self._write(f"    Max            : {fmt_cost(max(priced))}")
        else:
            self._write(f"    Min / Max      : N/A  (add model to pricing table)")
        self._write(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Usage: python performance_tracker.py [log_file_or_inline_text]
    # Defaults to the sample log embedded below if no argument is given

    import os
    log_input = sys.argv[1]
    if os.path.exists(log_input.replace('\\', '/')):
        base = os.path.splitext(os.path.basename(log_input.replace('\\', '/')))[0]
        out_path = f"{base}_metrics.txt"
    else:
        out_path = "metrics.txt"
    tracker = PerformanceTracker(output_path=out_path)
    tracker.parse_session_log(log_input)