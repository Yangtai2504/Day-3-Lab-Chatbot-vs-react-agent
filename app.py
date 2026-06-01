"""
Web demo (bonus) — Chatbot vs ReAct Agent
Lab 3: Trợ lý Tư vấn Đăng ký môn học.

Chạy:
    streamlit run app.py

Tái dùng trực tiếp code có sẵn: src/agent/agent.py, src/tools/edu_tools.py, src/core/*.
Cần API key trong .env (OPENAI_API_KEY hoặc GEMINI_API_KEY).
"""

import os
import re
import time

import streamlit as st
from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.tools.edu_tools import EDU_TOOLS
from src.telemetry.logger import logger

load_dotenv()

# Mỗi phiên trình duyệt = 1 session log riêng. Tạo id một lần rồi tái dùng.
if "session_id" not in st.session_state:
    st.session_state["session_id"] = logger.new_session()

# ── Cấu hình trang ────────────────────────────────────────────────────────────
st.set_page_config(page_title="Chatbot vs ReAct Agent", page_icon="🎓", layout="wide")

CHATBOT_SYSTEM_PROMPT = (
    "Bạn là trợ lý học vụ của trường đại học. "
    "Hãy trả lời trực tiếp câu hỏi của sinh viên. "
    "Chỉ đưa ra thông tin chính xác, không bịa số liệu."
)

SAMPLE_QUERIES = [
    "GPA của sinh viên SV004 là bao nhiêu?",
    "Môn ML301 yêu cầu những môn tiên quyết nào?",
    "SV001 đủ điều kiện học ML301 không? Nếu đủ, tính học phí 3 tín chỉ "
    "sau khi áp học bổng theo GPA thực tế của sinh viên đó.",
    "Tính học phí môn Cơ sở dữ liệu (DB201) cho 3 tín chỉ rồi áp học bổng 20%.",
]


# ── Provider builder (cache theo provider+model) ──────────────────────────────
@st.cache_resource(show_spinner=False)
def build_provider(provider_name: str, model: str):
    if provider_name == "google":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider(model, os.getenv("GEMINI_API_KEY"))
    if provider_name == "local":
        from src.core.local_provider import LocalProvider
        return LocalProvider(model_path=os.getenv("LOCAL_MODEL_PATH"))
    from src.core.openai_provider import OpenAIProvider
    return OpenAIProvider(model, os.getenv("OPENAI_API_KEY"))


def has_api_key(provider_name: str) -> bool:
    if provider_name == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    if provider_name == "google":
        return bool(os.getenv("GEMINI_API_KEY"))
    if provider_name == "local":
        return bool(os.getenv("LOCAL_MODEL_PATH"))
    return False


# ── Tách Thought / Action để hiển thị đẹp ─────────────────────────────────────
def split_thought_action(text: str):
    thought = re.search(r"Thought\s*:\s*(.+?)(?=\n\s*Action\s*:|\Z)", text, re.IGNORECASE | re.DOTALL)
    action = re.search(r"Action\s*:\s*(.+?)(?=\n\s*Observation\s*:|\Z)", text, re.IGNORECASE | re.DOTALL)
    return (
        thought.group(1).strip() if thought else None,
        action.group(1).strip() if action else None,
    )


# ── Runner ────────────────────────────────────────────────────────────────────
def run_chatbot(llm, query: str) -> dict:
    t0 = time.time()
    result = llm.generate(query, system_prompt=CHATBOT_SYSTEM_PROMPT)
    return {
        "answer": result.get("content", ""),
        "latency_ms": int((time.time() - t0) * 1000),
        "tokens": result.get("usage", {}).get("total_tokens", 0),
    }


def run_agent(llm, query: str, max_steps: int) -> dict:
    agent = ReActAgent(llm=llm, tools=EDU_TOOLS, max_steps=max_steps)
    t0 = time.time()
    answer = agent.run(query)
    return {
        "answer": answer,
        "latency_ms": int((time.time() - t0) * 1000),
        "tokens": sum(h.get("usage", {}).get("total_tokens", 0) for h in agent.history),
        "history": agent.history,
    }


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Cấu hình")
    provider_name = st.selectbox(
        "Provider",
        ["openai", "google", "local"],
        index=["openai", "google", "local"].index(os.getenv("DEFAULT_PROVIDER", "openai")),
    )
    default_model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    model = st.text_input("Model", value=default_model)
    max_steps = st.slider("Agent max_steps", min_value=3, max_value=10, value=7)

    if has_api_key(provider_name):
        st.success(f"✅ Đã có cấu hình cho `{provider_name}`")
    else:
        st.error(
            f"❌ Thiếu key cho `{provider_name}`.\n\n"
            "Tạo file `.env` (copy từ `.env.example`) và điền "
            "`OPENAI_API_KEY` hoặc `GEMINI_API_KEY`."
        )

    st.divider()
    st.caption("Câu hỏi mẫu — bấm để điền:")
    for i, q in enumerate(SAMPLE_QUERIES):
        if st.button(q, key=f"sample_{i}", use_container_width=True):
            st.session_state["query"] = q


# ── Main ──────────────────────────────────────────────────────────────────────
st.title("🎓 Chatbot vs ReAct Agent")
st.caption("Trợ lý Tư vấn Đăng ký môn học — Lab 3. Gõ một câu hỏi và so sánh hai cách trả lời.")

query = st.text_area(
    "Câu hỏi của sinh viên",
    value=st.session_state.get("query", SAMPLE_QUERIES[2]),
    height=80,
    key="query",
)

run_clicked = st.button("▶️ Chạy so sánh", type="primary", use_container_width=True)

if run_clicked:
    if not query.strip():
        st.warning("Hãy nhập câu hỏi trước.")
        st.stop()
    if not has_api_key(provider_name):
        st.error("Chưa có API key — xem hướng dẫn ở sidebar.")
        st.stop()

    # Logger là global (dùng chung nhiều phiên trong cùng tiến trình) — gắn lại
    # session_id của phiên này trước khi chạy để log không lẫn sang phiên khác.
    logger.set_session(st.session_state["session_id"])

    try:
        llm = build_provider(provider_name, model)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Không khởi tạo được provider: {exc}")
        st.stop()

    col_cb, col_ag = st.columns(2)

    # ── Chatbot ──
    with col_cb:
        st.subheader("💬 Chatbot (baseline)")
        with st.spinner("Chatbot đang trả lời..."):
            try:
                cb = run_chatbot(llm, query)
                st.info(cb["answer"] or "(rỗng)")
                st.caption(f"⏱️ {cb['latency_ms']} ms · 🔢 {cb['tokens']} tokens · 1 lần gọi LLM")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Lỗi: {exc}")

    # ── Agent ──
    with col_ag:
        st.subheader("🤖 ReAct Agent")
        with st.spinner("Agent đang suy luận từng bước..."):
            try:
                ag = run_agent(llm, query, max_steps)
                st.success(ag["answer"] or "(rỗng)")
                st.caption(
                    f"⏱️ {ag['latency_ms']} ms · 🔢 {ag['tokens']} tokens · "
                    f"🔁 {len(ag['history'])} bước"
                )
                st.markdown("**Trace suy luận:**")
                for h in ag["history"]:
                    thought, action = split_thought_action(h["response"])
                    obs = h.get("observation")
                    title = f"Bước {h['step']}"
                    if action:
                        title += f" · `{action}`"
                    with st.expander(title, expanded=False):
                        if thought:
                            st.markdown(f"🧠 **Thought:** {thought}")
                        if action:
                            st.markdown(f"🛠️ **Action:** `{action}`")
                        if obs is not None:
                            st.markdown(f"👀 **Observation:** {obs}")
                        if not (thought or action or obs):
                            st.code(h["response"])
            except Exception as exc:  # noqa: BLE001
                st.error(f"Lỗi: {exc}")

    st.divider()
    st.caption(
        "💡 Câu đơn (1 bước) hai bên thường ngang nhau. Câu đa bước — đủ điều kiện + "
        "học phí + học bổng — chatbot hay bịa/sai số, còn agent chain nhiều tool nên ra đúng."
    )
