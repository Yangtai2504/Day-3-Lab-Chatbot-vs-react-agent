# 💡 IDEA — Lab 3: Chatbot vs ReAct Agent (Chủ đề Giáo dục)

> Tài liệu ý tưởng & hướng triển khai cho nhóm **6 người**.
> Provider sử dụng: **OpenAI / Gemini API** (2 provider đã code sẵn trong `src/core/`).
> Kịch bản chính: **A — Trợ lý Tư vấn Đăng ký môn học**.

---

## 1. Bối cảnh & Mục tiêu

Đi từ một **Chatbot LLM thuần** lên một **ReAct Agent** (vòng lặp Thought → Action → Observation) có **telemetry** kiểu công nghiệp. Mục tiêu chứng minh: chatbot giỏi *nói chuyện*, agent giỏi *hành động* và giải bài toán **đa bước**.

**Phần đã có sẵn (không phải làm lại):**
- `src/core/openai_provider.py`, `src/core/gemini_provider.py` — provider hoàn chỉnh.
- `src/core/local_provider.py` — Phi-3 chạy CPU (dự phòng).
- `src/telemetry/logger.py` — log JSON ra `logs/`.
- `src/telemetry/metrics.py` — khung tracker (còn TODO cost).

**Phần nhóm phải làm:**
- `src/agent/agent.py` — vòng lặp ReAct (skeleton).
- `src/tools/edu_tools.py` — tool giáo dục (chưa có).
- `chatbot.py` — baseline để so sánh (chưa có).
- `_calculate_cost()` trong `metrics.py` — giá thật.
- `scripts/parse_logs.py` — bảng số liệu (chưa có).
- `tests/test_cases.py` — bộ test (chưa có).
- Báo cáo nhóm + 6 báo cáo cá nhân + flowchart.

---

## 2. Các kịch bản giáo dục (chọn 1 làm trục chính)

### 🟢 Kịch bản A — Trợ lý Đăng ký môn học *(KHUYẾN NGHỊ)*
Agent giúp sinh viên quyết định đăng ký môn. Đa bước rõ rệt nhất.

| Tool | Chức năng |
|---|---|
| `get_student_record(student_id)` | Trả GPA + môn đã học |
| `check_prerequisite(course_id)` | Trả list môn tiên quyết |
| `calculate_tuition(course_id, credits)` | Học phí theo tín chỉ |
| `apply_scholarship(amount, percent)` | Trừ học bổng |

**Test case vàng:** *"SV001 đủ điều kiện học ML301 không? Tính học phí 3 tín chỉ sau học bổng 20%."* → cần 4 cặp Thought-Action.

### 🟡 Kịch bản B — Gia sư / Trợ giảng AI
| Tool | Chức năng |
|---|---|
| `search_material(topic)` | Tra tài liệu/định nghĩa |
| `generate_quiz(topic, n)` | Sinh n câu hỏi |
| `grade_answer(question, answer)` | Chấm + giải thích |
| `recommend_next(score)` | Gợi ý bài tiếp theo |

**Test case:** *"Giải thích 'overfitting', cho tôi 2 câu quiz và chấm câu trả lời."*

### 🔵 Kịch bản C — Trợ lý Phòng Đào tạo (Admin)
| Tool | Chức năng |
|---|---|
| `lookup_student(student_id)` | Thông tin SV |
| `calc_accumulated_credits(student_id)` | Tổng tín chỉ tích lũy |
| `check_academic_warning(gpa, credits)` | Cảnh báo học vụ |
| `get_exam_schedule(course_id)` | Lịch thi |

**Test case:** *"SV002 có bị cảnh báo học vụ không? Nếu có, liệt kê lịch thi các môn."*

---

## 3. Phân vai 6 người

| # | Người | Vai trò | File phụ trách | Output chính | Điểm group |
|---|---|---|---|---|---|
| **P1** | **Quỳnh** | Agent Core Lead | `src/agent/agent.py` | `run()` (vòng lặp ReAct), `_execute_tool()`, regex parser | Agent v1 (7) |
| **P2** | **Kiên** | Tools Engineer | `src/tools/edu_tools.py` | 4 tool + registry `EDU_TOOLS` | Tool Design (4) |
| **P3** | **Phương** | Chatbot + Prompt | `chatbot.py` + `get_system_prompt()` | Baseline so sánh; prompt v1→v2 | Chatbot (2) + Agent v2 (7) |
| **P4** | **Dũng** | Telemetry & Metrics | `metrics.py` + `scripts/parse_logs.py` | Cost thật; bảng token/latency/cost | Code Quality (4) + Bonus (+3) |
| **P5** | **Dương** | Evaluation & Failure | `tests/test_cases.py` | ≥6 test case; thu trace thành công + thất bại | Trace (9) + Evaluation (7) |
| **P6** | **Huyền** | Report & Flowchart | `report/group_report/` | Flowchart ReAct; tổng hợp report | Flowchart & Insight (5) |

> Mỗi người tự viết 1 **individual report** (40đ cá nhân) dựa trên đúng phần mình làm + ít nhất 1 failure trace tự debug.

---

## 4. Timeline 240 phút

| Mốc | Thời lượng | Nội dung |
|---|---|---|
| 0. Setup | 15' | Clone, `pip install`, điền API key vào `.env`, chốt kịch bản A |
| 1. Thiết kế tool | 30' | P2 viết spec tool; **P1+P2 chốt format `Action: tool(args)`** |
| 2. Chatbot baseline | 30' | P3 viết `chatbot.py`, cố tình để fail bài đa bước (cú hook). P5 soạn test |
| 3. Agent v1 (lõi) | 60' | P1 vòng lặp + parser; P2 dispatch; P4 nối metrics |
| 4. Failure Analysis | 45' | P4 chạy `parse_logs.py`; P5+P3 đọc log tìm lỗi; P3 sửa prompt v1→v2 |
| 5. Đánh giá nhóm | 30' | P5 chạy full suite; P4 xuất bảng; P6 vẽ flowchart |
| 6. Báo cáo & demo | 30' | P6 ráp report; mỗi người viết individual; chuẩn bị live demo |

**Critical path (điểm nghẽn):** P2 chốt format Action → P1 parser khớp → P4 có log để parse → P3 sửa prompt. Họp chốt format ở **phút 30**.

---

## 5. Hướng implement (code mẫu)

### 5.1 Tools — `src/tools/edu_tools.py`
```python
_STUDENTS = {
    "SV001": {"name": "An",   "gpa": 3.2, "passed": ["CS101", "MATH201"]},
    "SV002": {"name": "Binh", "gpa": 1.8, "passed": ["CS101"]},
}
_COURSES = {
    "ML301": {"name": "Machine Learning", "prereq": ["CS101", "MATH201"], "fee_per_credit": 1_500_000},
    "DB201": {"name": "Databases",        "prereq": ["CS101"],            "fee_per_credit": 1_200_000},
}

def get_student_record(student_id: str) -> str:
    s = _STUDENTS.get(student_id.strip())
    if not s:
        return f"ERROR: Không tìm thấy sinh viên {student_id}"
    return f"SV {student_id} ({s['name']}): GPA={s['gpa']}, đã học={s['passed']}"

def check_prerequisite(course_id: str) -> str:
    c = _COURSES.get(course_id.strip().upper())
    if not c:
        return f"ERROR: Không tìm thấy môn {course_id}"
    return f"Môn {course_id} yêu cầu tiên quyết: {c['prereq']}"

def calculate_tuition(course_id: str, credits: str) -> str:
    c = _COURSES.get(course_id.strip().upper())
    if not c:
        return f"ERROR: Không tìm thấy môn {course_id}"
    total = c["fee_per_credit"] * int(credits)
    return f"Học phí {course_id} ({credits} tín chỉ) = {total:,} VND"

def apply_scholarship(amount: str, percent: str) -> str:
    amt = float(str(amount).replace(",", "").replace("VND", "").strip())
    final = amt * (1 - float(percent) / 100)
    return f"Sau học bổng {percent}%: {final:,.0f} VND"

EDU_TOOLS = [
    {"name": "get_student_record", "description": "Tra hồ sơ SV theo student_id. Trả GPA và môn đã học.", "func": get_student_record},
    {"name": "check_prerequisite", "description": "Tra môn tiên quyết của 1 môn. Args: course_id.", "func": check_prerequisite},
    {"name": "calculate_tuition", "description": "Tính học phí. Args: course_id, credits (int).", "func": calculate_tuition},
    {"name": "apply_scholarship", "description": "Trừ học bổng theo %. Args: amount, percent.", "func": apply_scholarship},
]
```

### 5.2 Agent — `src/agent/agent.py`
```python
import re
from src.telemetry.metrics import tracker

def run(self, user_input: str) -> str:
    logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
    transcript = f"Question: {user_input}\n"
    steps = 0

    while steps < self.max_steps:
        steps += 1
        result = self.llm.generate(transcript, system_prompt=self.get_system_prompt())
        text = result["content"]
        tracker.track_request(result["provider"], self.llm.model_name,
                              result["usage"], result["latency_ms"])

        final = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
        if final:
            logger.log_event("AGENT_END", {"steps": steps, "status": "success"})
            return final.group(1).strip()

        action = re.search(r"Action:\s*(\w+)\((.*?)\)", text, re.DOTALL)
        if not action:
            logger.log_event("PARSE_ERROR", {"step": steps, "raw": text[:200]})
            transcript += text + "\nObservation: Lỗi format. Dùng đúng 'Action: tool(args)'.\n"
            continue

        tool_name, raw_args = action.group(1), action.group(2)
        observation = self._execute_tool(tool_name, raw_args)
        logger.log_event("TOOL_CALL", {"tool": tool_name, "args": raw_args, "obs": observation})
        transcript += text.split("Observation:")[0].strip() + f"\nObservation: {observation}\n"

    logger.log_event("AGENT_END", {"steps": steps, "status": "max_steps"})
    return "Đã đạt giới hạn số bước (timeout)."

def _execute_tool(self, tool_name: str, args: str) -> str:
    for tool in self.tools:
        if tool["name"] == tool_name:
            try:
                parsed = [a.strip().strip("'\"") for a in args.split(",") if a.strip()]
                return str(tool["func"](*parsed))
            except Exception as e:
                return f"ERROR khi chạy {tool_name}: {e}"
    return f"ERROR: Tool '{tool_name}' không tồn tại. Chỉ dùng: {[t['name'] for t in self.tools]}"
```

### 5.3 System prompt — `get_system_prompt()`
```python
def get_system_prompt(self) -> str:
    tools = "\n".join(f"- {t['name']}: {t['description']}" for t in self.tools)
    return f"""Bạn là trợ lý học vụ. Bạn CHỈ được dùng các tool sau:
{tools}

Mỗi bước chỉ xuất 1 Thought + 1 Action rồi DỪNG:
Thought: lý do bạn chọn hành động.
Action: tool_name(arg1, arg2)

Sau khi nhận Observation, lặp lại. Khi đã đủ thông tin:
Final Answer: câu trả lời cuối cùng.

QUY TẮC: Không tự bịa Observation. Không bịa tool. Đối số đặt trong ngoặc ()."""
```

### 5.4 Chatbot baseline — `chatbot.py`
```python
import os
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider

def build_provider():
    load_dotenv()
    p = os.getenv("DEFAULT_PROVIDER", "openai")
    if p == "google":
        return GeminiProvider(os.getenv("DEFAULT_MODEL", "gemini-1.5-flash"), os.getenv("GEMINI_API_KEY"))
    return OpenAIProvider(os.getenv("DEFAULT_MODEL", "gpt-4o"), os.getenv("OPENAI_API_KEY"))

if __name__ == "__main__":
    llm = build_provider()
    while True:
        q = input("\nBạn: ")
        if q.lower() in {"exit", "quit"}:
            break
        res = llm.generate(q, system_prompt="Bạn là trợ lý học vụ. Trả lời trực tiếp.")
        print("Bot:", res["content"])
```

### 5.5 Cost thật — `metrics.py`
```python
_PRICING = {  # USD / 1K tokens (prompt, completion)
    "gpt-4o":           (0.0025, 0.010),
    "gpt-4o-mini":      (0.00015, 0.0006),
    "gemini-1.5-flash": (0.000075, 0.0003),
}
def _calculate_cost(self, model, usage):
    pin, pout = self._PRICING.get(model, (0.0, 0.0))
    return round(usage.get("prompt_tokens", 0) / 1000 * pin
               + usage.get("completion_tokens", 0) / 1000 * pout, 6)
```

### 5.6 Parse log — `scripts/parse_logs.py`
```python
import json, glob, re, statistics
events = []
for f in glob.glob("logs/*.log"):
    for line in open(f, encoding="utf-8"):
        m = re.search(r"\{.*\}", line)
        if m:
            try: events.append(json.loads(m.group()))
            except: pass

metrics = [e["data"] for e in events if e.get("event") == "LLM_METRIC"]
print(f"Số lần gọi LLM : {len(metrics)}")
print(f"Tổng tokens    : {sum(m['total_tokens'] for m in metrics)}")
print(f"Tổng cost (USD): {sum(m['cost_estimate'] for m in metrics):.4f}")
if metrics:
    print(f"Latency p50    : {statistics.median(m['latency_ms'] for m in metrics):.0f} ms")
print(f"Parse errors   : {sum(1 for e in events if e.get('event')=='PARSE_ERROR')}")
print(f"Timeouts       : {sum(1 for e in events if e.get('data',{}).get('status')=='max_steps')}")
```

### 5.7 Test cases — `tests/test_cases.py`
```python
TEST_CASES = [
    ("Môn ML301 yêu cầu tiên quyết gì?", "simple"),
    ("GPA của SV001 là bao nhiêu?", "simple"),
    ("SV001 đủ điều kiện học ML301 không? Tính học phí 3 tín chỉ sau học bổng 20%.", "multi"),
    ("SV002 có học được ML301 không, nếu không thì thiếu môn gì?", "multi"),
]
# Với mỗi case: chạy chatbot.generate() vs agent.run(), ghi kết quả + đọc logs để đếm bước/lỗi.
```

---

## 6. Ví dụ Trace ReAct

### ✅ Trace thành công (test case vàng — 4 bước)
```
Question: SV001 đủ điều kiện học ML301 không? Tính học phí 3 tín chỉ sau học bổng 20%.

BƯỚC 1
Thought: Cần biết ML301 yêu cầu tiên quyết gì trước.
Action: check_prerequisite(ML301)
Observation: Môn ML301 yêu cầu tiên quyết: ['CS101', 'MATH201']

BƯỚC 2
Thought: Xem SV001 đã học môn nào để đối chiếu.
Action: get_student_record(SV001)
Observation: SV SV001 (An): GPA=3.2, đã học=['CS101', 'MATH201']

BƯỚC 3
Thought: An đã học đủ → tính học phí 3 tín chỉ.
Action: calculate_tuition(ML301, 3)
Observation: Học phí ML301 (3 tín chỉ) = 4,500,000 VND

BƯỚC 4
Thought: Áp học bổng 20% lên học phí gốc.
Action: apply_scholarship(4500000, 20)
Observation: Sau học bổng 20%: 3,600,000 VND

Final Answer: SV001 (An) ĐỦ điều kiện học ML301 (đã học CS101 và MATH201).
Học phí 3 tín chỉ là 4,500,000 VND, sau học bổng 20% còn 3,600,000 VND.
```

### ❌ Trace thất bại (nguyên liệu cho Debugging Case Study)

**Lỗi 1 — Parse Error (LLM tự bịa Observation):**
```
Thought: Tôi sẽ kiểm tra tiên quyết.
Action: check_prerequisite(ML301)
Observation: ML301 cần CS101.        ← LLM BỊA, chưa gọi tool thật!
Final Answer: Bạn đủ điều kiện.       ← sai, thiếu MATH201
Fix: parser cắt phần sau "Observation:" → buộc gọi tool thật. Ghi event PARSE_ERROR.
```

**Lỗi 2 — Hallucinated Tool:**
```
Action: check_gpa_requirement(ML301)   ← tool không tồn tại
Observation: ERROR: Tool 'check_gpa_requirement' không tồn tại. Chỉ dùng: [...]
→ Agent tự sửa ở bước sau (self-correct).
```

**Lỗi 3 — Infinite Loop / Timeout:**
```
Bước 1..5: Action: get_student_record(SV001)  ← lặp y hệt → max_steps
Log: AGENT_END {"steps": 5, "status": "max_steps"}
Fix: guardrail — nếu Action trùng bước trước → nhắc "Hãy dùng kết quả đã có".
```

3 loại lỗi này map đúng vào `EVALUATION.md` (JSON Parser / Hallucination / Timeout).

---

## 7. Mapping điểm (mục tiêu 100/100)

- **Group base 45**: đủ nếu 6 vai hoàn thành output.
- **Bonus +15** (cap group 60): P4 cost/token-ratio (+3), P2 tool search/browsing (+2), P1 retry/guardrail chống loop (+3), live demo (+5), P3+P5 ablation prompt v1 vs v2 (+2).
- **Cá nhân 40/người**: technical contribution (15) + debugging case study (10) + insight (10) + future RAG/multi-agent (5).
- **Công thức:** `Total = MIN(60, Group Base + Bonus) + Individual (≤40)`.

---

## 8. Checklist trước khi nộp

- [ ] `chatbot.py` chạy được, fail rõ ở bài đa bước.
- [ ] `agent.py` giải đúng test case vàng (4 bước).
- [ ] Có ≥1 trace thành công + ≥1 trace thất bại mỗi loại (parse/hallucination/timeout).
- [ ] `parse_logs.py` ra bảng token/latency/cost/error.
- [ ] Prompt v1 → v2 có dẫn chứng từ log (không đoán).
- [ ] Flowchart vòng lặp ReAct.
- [ ] Group report + 6 individual report.
- [ ] (Bonus) Live demo + ablation.

---

*"In the world of AI, the trace is the truth." — Đọc log, đừng đoán.*
