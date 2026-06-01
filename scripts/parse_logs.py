"""
P4 — parse_logs.py
Đọc log JSON (logs/YYYY-MM-DD.log) do telemetry sinh ra, tổng hợp thành bảng
token / latency / cost / error.

Cách dùng:
    python scripts/parse_logs.py                 # tự lấy file log mới nhất trong logs/
    python scripts/parse_logs.py --file logs/2026-06-01.log
    python scripts/parse_logs.py --by-run        # tách số liệu theo từng lần chạy agent

Mỗi dòng log là 1 JSON: {"timestamp", "event", "data"}.
Sự kiện dùng tới: AGENT_START (lấy model), LLM_RESPONSE (usage + latency),
TOOL_CALL (tool + observation), PARSE_ERROR, AGENT_END (status).
"""

import os
import sys
import glob
import json
import argparse
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.telemetry.metrics import PerformanceTracker

_PRICER = PerformanceTracker()  # tái dùng bảng giá thật trong metrics.py


def latest_log() -> str:
    files = sorted(glob.glob("logs/*.log"))
    if not files:
        print("❌ Không tìm thấy file log nào trong logs/. Hãy chạy agent/eval trước.")
        sys.exit(1)
    return files[-1]


def load_events(path: str):
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # bỏ qua dòng không phải JSON (vd log dạng text)
    return events


def summarize(events: list) -> dict:
    """Tổng hợp toàn bộ + tách theo từng run (mỗi AGENT_START mở một run)
    + tách theo từng session (mỗi session_id một bucket)."""
    overall = _empty_bucket()
    runs = []
    sessions = {}        # session_id -> bucket tổng hợp của phiên đó
    current = None       # bucket của run đang chạy
    session_id = "unknown"
    model = "unknown"

    def buckets():
        """Các bucket cần cộng dồn cho mỗi event: tổng + run hiện tại + session."""
        return [b for b in (overall, current, sessions.get(session_id)) if b is not None]

    for ev in events:
        etype = ev.get("event")
        data = ev.get("data", {})
        session_id = ev.get("session_id", session_id)
        if session_id not in sessions:
            sessions[session_id] = _empty_bucket()
            sessions[session_id]["session_id"] = session_id

        if etype == "AGENT_START":
            if current:
                runs.append(current)
            model = data.get("model", model)
            current = _empty_bucket()
            current["input"] = data.get("input", "")[:60]
            current["model"] = model
            current["session_id"] = session_id
            sessions[session_id]["runs"] += 1
            sessions[session_id]["model"] = model

        elif etype == "LLM_RESPONSE":
            usage = data.get("usage", {}) or {}
            lat = data.get("latency_ms") or 0
            cost = _PRICER._calculate_cost(model, usage)
            for bucket in buckets():
                bucket["llm_calls"] += 1
                bucket["prompt_tokens"] += usage.get("prompt_tokens", 0)
                bucket["completion_tokens"] += usage.get("completion_tokens", 0)
                bucket["total_tokens"] += usage.get("total_tokens", 0)
                bucket["latency_ms"] += lat
                bucket["cost_usd"] += cost

        elif etype == "TOOL_CALL":
            obs = str(data.get("observation", ""))
            tool = data.get("tool", "?")
            for bucket in buckets():
                bucket["tool_calls"] += 1
                bucket["tools"][tool] += 1
                if obs.startswith("ERROR"):
                    bucket["tool_errors"] += 1

        elif etype == "PARSE_ERROR":
            for bucket in buckets():
                bucket["parse_errors"] += 1

        elif etype == "AGENT_END":
            status = data.get("status", "")
            if current is not None:
                current["status"] = status
            for bucket in (overall, sessions.get(session_id)):
                if bucket is None:
                    continue
                if status in ("max_steps", "timeout"):
                    bucket["timeouts"] += 1
                if status in ("timeout", "error"):
                    bucket["errors"] += 1

    if current:
        runs.append(current)
    return {"overall": overall, "runs": runs, "sessions": sessions}


def _empty_bucket() -> dict:
    return {
        "model": "", "input": "", "status": "", "session_id": "", "runs": 0,
        "llm_calls": 0, "tool_calls": 0, "tool_errors": 0,
        "parse_errors": 0, "timeouts": 0, "errors": 0,
        "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
        "latency_ms": 0, "cost_usd": 0.0,
        "tools": Counter(),
    }


def print_report(summary: dict, by_run: bool):
    o = summary["overall"]
    runs = summary["runs"]

    print("=" * 70)
    print("TELEMETRY REPORT — token / latency / cost / error")
    print("=" * 70)
    print(f"  Số session               : {len(summary.get('sessions', {}))}")
    print(f"  Số lần chạy agent (runs) : {len(runs)}")
    print(f"  Số lần gọi LLM           : {o['llm_calls']}")
    print(f"  Số lần gọi tool          : {o['tool_calls']}  (lỗi tool: {o['tool_errors']})")
    print(f"  Parse errors             : {o['parse_errors']}")
    print(f"  Timeouts (max_steps/30s) : {o['timeouts']}")
    print(f"  Lỗi (agent error)        : {o['errors']}")
    print("-" * 70)
    print(f"  Prompt tokens            : {o['prompt_tokens']:,}")
    print(f"  Completion tokens        : {o['completion_tokens']:,}")
    print(f"  Total tokens             : {o['total_tokens']:,}")
    avg_lat = o["latency_ms"] // o["llm_calls"] if o["llm_calls"] else 0
    print(f"  Tổng latency             : {o['latency_ms']:,} ms  (trung bình {avg_lat} ms/call)")
    print(f"  Chi phí ước tính         : ${o['cost_usd']:.6f}")
    print("-" * 70)
    print("  Tần suất dùng tool:")
    for tool, n in o["tools"].most_common():
        print(f"    {tool:<24}: {n}")
    print("=" * 70)

    if by_run and runs:
        print("\nCHI TIẾT THEO TỪNG RUN")
        print("-" * 70)
        header = f"{'#':<3} {'steps':>5} {'tok':>7} {'ms':>7} {'$':>10} {'status':<10} query"
        print(header)
        for i, r in enumerate(runs, 1):
            print(
                f"{i:<3} {r['llm_calls']:>5} {r['total_tokens']:>7} {r['latency_ms']:>7} "
                f"{r['cost_usd']:>10.6f} {r['status']:<10} {r['input']}"
            )
        print("-" * 70)


def print_by_session(summary: dict):
    sessions = summary.get("sessions", {})
    if not sessions:
        return
    print("\nCHI TIẾT THEO TỪNG SESSION")
    print("-" * 88)
    header = (
        f"{'session':<24} {'runs':>4} {'llm':>4} {'tok':>8} "
        f"{'ms':>8} {'$':>10} {'err':>4} {'tmo':>4}"
    )
    print(header)
    for sid, s in sessions.items():
        print(
            f"{sid:<24} {s['runs']:>4} {s['llm_calls']:>4} {s['total_tokens']:>8} "
            f"{s['latency_ms']:>8} {s['cost_usd']:>10.6f} {s['errors']:>4} {s['timeouts']:>4}"
        )
    print("-" * 88)


def main():
    parser = argparse.ArgumentParser(description="Parse telemetry logs thành bảng số liệu")
    parser.add_argument("--file", help="Đường dẫn file log (mặc định: file mới nhất trong logs/)")
    parser.add_argument("--session", help="Chỉ đọc 1 session: logs/sessions/<id>.log")
    parser.add_argument("--by-run", action="store_true", help="In chi tiết theo từng lần chạy agent")
    parser.add_argument("--by-session", action="store_true", help="In chi tiết theo từng session")
    args = parser.parse_args()

    if args.session:
        path = os.path.join("logs", "sessions", f"{args.session}.log")
    else:
        path = args.file or latest_log()
    print(f"Đọc log: {path}\n")
    events = load_events(path)
    if not events:
        print("⚠️  File log rỗng hoặc không có dòng JSON hợp lệ.")
        return
    summary = summarize(events)
    print_report(summary, by_run=args.by_run)
    if args.by_session:
        print_by_session(summary)


if __name__ == "__main__":
    main()
