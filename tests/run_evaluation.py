"""
P5 — run_evaluation.py
Chạy toàn bộ test cases qua Chatbot và ReAct Agent, xuất bảng so sánh.

Cách dùng:
    python -X utf8 tests/run_evaluation.py

Phụ thuộc: P1 (agent.py) + P2 (edu_tools.py) phải hoàn chỉnh.
Nếu agent chưa implement, script vẫn chạy được nhưng agent column sẽ báo NOT_IMPLEMENTED.
"""

import os
import sys
import time
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from tests.test_cases import (
    ALL_TEST_CASES, SIMPLE_CASES, MULTI_CASES, GOLDEN_CASES,
    FAILURE_TRIGGERS, EDGE_CASES,
)
from src.tools.edu_tools import EDU_TOOLS

load_dotenv()

# ── Provider builder ──────────────────────────────────────────────────────────
def build_provider():
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai")
    model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    if provider_name == "google":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider(model, os.getenv("GEMINI_API_KEY"))
    from src.core.openai_provider import OpenAIProvider
    return OpenAIProvider(model, os.getenv("OPENAI_API_KEY"))


# ── Chatbot runner ────────────────────────────────────────────────────────────
def run_chatbot(llm, query: str) -> dict:
    system_prompt = (
        "Ban la tro ly hoc vu cua truong dai hoc. "
        "Hay tra loi truc tiep cau hoi cua sinh vien. "
        "Chi dua ra thong tin chinh xac, khong bịa so lieu."
    )
    t0 = time.time()
    try:
        result = llm.generate(query, system_prompt=system_prompt)
        latency = int((time.time() - t0) * 1000)
        return {
            "answer": result["content"],
            "latency_ms": latency,
            "tokens": result.get("usage", {}).get("total_tokens", 0),
            "error": None,
        }
    except Exception as e:
        return {"answer": "", "latency_ms": 0, "tokens": 0, "error": str(e)}


# ── Agent runner ──────────────────────────────────────────────────────────────
def run_agent(llm, query: str) -> dict:
    from src.agent.agent import ReActAgent
    agent = ReActAgent(llm=llm, tools=EDU_TOOLS, max_steps=7)
    t0 = time.time()
    try:
        answer = agent.run(query)
        latency = int((time.time() - t0) * 1000)
        return {
            "answer": answer,
            "latency_ms": latency,
            "tokens": 0,  # P4 sẽ lấy từ logs
            "error": None,
        }
    except Exception as e:
        return {"answer": "", "latency_ms": 0, "tokens": 0, "error": str(e)}


# ── Judge: heuristic correctness check ───────────────────────────────────────
def heuristic_correct(answer: str, golden: str) -> bool:
    """
    Kiểm tra đơn giản: golden answer keywords có xuất hiện trong câu trả lời không.
    P5 cần review thủ công kết quả cuối.
    """
    if not answer or not golden:
        return False
    keywords = [kw.strip() for kw in golden.replace("|", ",").split(",") if len(kw.strip()) > 3]
    hits = sum(1 for kw in keywords if kw.lower() in answer.lower())
    return hits >= max(1, len(keywords) // 2)


# ── Single case evaluator ─────────────────────────────────────────────────────
def evaluate_case(case: dict, llm) -> dict:
    query = case["query"]
    golden = case.get("golden_answer", "")

    print(f"  [{case['id']}] {query[:70]}...")

    chatbot_result = run_chatbot(llm, query)
    agent_result   = run_agent(llm, query)

    chatbot_ok = heuristic_correct(chatbot_result["answer"], golden)
    agent_ok   = heuristic_correct(agent_result["answer"], golden)

    if agent_ok and not chatbot_ok:
        winner = "AGENT"
    elif chatbot_ok and not agent_ok:
        winner = "CHATBOT"
    elif chatbot_ok and agent_ok:
        winner = "DRAW"
    else:
        winner = "BOTH_FAIL"

    return {
        "id":            case["id"],
        "type":          case["type"],
        "query":         query,
        "golden":        golden,
        "chatbot_ans":   chatbot_result["answer"][:200],
        "agent_ans":     agent_result["answer"][:200],
        "chatbot_ok":    chatbot_ok,
        "agent_ok":      agent_ok,
        "winner":        winner,
        "chatbot_ms":    chatbot_result["latency_ms"],
        "agent_ms":      agent_result["latency_ms"],
        "chatbot_tokens":chatbot_result["tokens"],
        "agent_tokens":  agent_result["tokens"],
        "chatbot_err":   chatbot_result["error"],
        "agent_err":     agent_result["error"],
        "note":          case.get("note", ""),
    }


# ── Print comparison table ────────────────────────────────────────────────────
def print_table(results: list):
    print("\n" + "=" * 90)
    print("EVALUATION RESULTS — Chatbot vs ReAct Agent")
    print("=" * 90)
    header = f"{'ID':<5} {'Type':<16} {'Chatbot':^8} {'Agent':^8} {'Winner':<12} {'CB_ms':>6} {'AG_ms':>6}"
    print(header)
    print("-" * 90)
    for r in results:
        cb  = "OK" if r["chatbot_ok"] else ("ERR" if r["chatbot_err"] else "FAIL")
        ag  = "OK" if r["agent_ok"]   else ("ERR" if r["agent_err"]   else "FAIL")
        print(f"{r['id']:<5} {r['type']:<16} {cb:^8} {ag:^8} {r['winner']:<12} {r['chatbot_ms']:>6} {r['agent_ms']:>6}")
    print("=" * 90)


# ── Print aggregate stats ─────────────────────────────────────────────────────
def print_stats(results: list):
    total = len(results)
    agent_wins   = sum(1 for r in results if r["winner"] == "AGENT")
    chatbot_wins = sum(1 for r in results if r["winner"] == "CHATBOT")
    draws        = sum(1 for r in results if r["winner"] == "DRAW")
    both_fail    = sum(1 for r in results if r["winner"] == "BOTH_FAIL")

    print("\nAGGREGATE STATS")
    print("-" * 40)
    print(f"  Total cases    : {total}")
    print(f"  Agent wins     : {agent_wins}  ({agent_wins/total*100:.0f}%)")
    print(f"  Chatbot wins   : {chatbot_wins}  ({chatbot_wins/total*100:.0f}%)")
    print(f"  Draw           : {draws}  ({draws/total*100:.0f}%)")
    print(f"  Both fail      : {both_fail}  ({both_fail/total*100:.0f}%)")

    print("\nBY QUERY TYPE")
    print("-" * 40)
    for qtype in ["simple", "multi", "golden", "edge", "failure_trigger"]:
        sub = [r for r in results if r["type"] == qtype]
        if not sub:
            continue
        a_ok = sum(1 for r in sub if r["agent_ok"])
        c_ok = sum(1 for r in sub if r["chatbot_ok"])
        print(f"  {qtype:<18}: agent {a_ok}/{len(sub)} | chatbot {c_ok}/{len(sub)}")

    cb_ms = [r["chatbot_ms"] for r in results if r["chatbot_ms"] > 0]
    ag_ms = [r["agent_ms"]   for r in results if r["agent_ms"]   > 0]
    if cb_ms:
        print(f"\n  Chatbot avg latency : {sum(cb_ms)//len(cb_ms)} ms")
    if ag_ms:
        print(f"  Agent   avg latency : {sum(ag_ms)//len(ag_ms)} ms")
    print("-" * 40)


# ── Save JSON results ─────────────────────────────────────────────────────────
def save_results(results: list):
    os.makedirs("report/evaluation", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"report/evaluation/eval_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved: {path}")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────
def main(groups=None):
    """
    groups: list of case groups to run. None = run all.
    Example: main(groups=[SIMPLE_CASES, MULTI_CASES])
    """
    print("Building LLM provider...")
    llm = build_provider()
    print(f"Provider: {os.getenv('DEFAULT_PROVIDER','openai')} / {os.getenv('DEFAULT_MODEL','gpt-4o-mini')}")

    cases = []
    if groups is None:
        cases = ALL_TEST_CASES
    else:
        for g in groups:
            cases.extend(g)

    print(f"\nRunning {len(cases)} test cases...\n")
    results = []
    for case in cases:
        r = evaluate_case(case, llm)
        results.append(r)

    print_table(results)
    print_stats(results)
    save_results(results)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate Chatbot vs ReAct Agent")
    parser.add_argument(
        "--group",
        choices=["simple", "multi", "golden", "failure", "edge", "all"],
        default="all",
        help="Which test group to run (default: all)",
    )
    args = parser.parse_args()

    group_map = {
        "simple":  [SIMPLE_CASES],
        "multi":   [MULTI_CASES],
        "golden":  [GOLDEN_CASES],
        "failure": [FAILURE_TRIGGERS],
        "edge":    [EDGE_CASES],
        "all":     None,
    }
    main(groups=group_map[args.group])
