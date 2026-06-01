# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Khánh Huyền 
- **Student ID**: 2A202600650
- **Role**: P6 — Integrator / Merge & Telemetry
- **Branch**: main
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

Vai trò P6 không sở hữu một feature đơn lẻ mà chịu trách nhiệm **ráp 5 nhánh thành một
`main` chạy được**, vá các điểm gãy khi tích hợp, và lo telemetry + flowchart.

### Đóng góp chính

| Hạng mục | File | Mô tả |
|---|---|---|
| Tích hợp & merge | `main` | Merge `Duong` (P5 eval), `luong` (P3 chatbot), data của P2 theo đúng thứ tự dependency; xử lý xung đột |
| Sửa bug ReAct loop | `src/agent/agent.py` | Đảo logic ưu tiên Action (xem mục II) + siết system prompt tiếng Việt |
| Thêm tool còn thiếu | `src/tools/edu_tools.py` | `get_scholarship_rate` (GPA→% học bổng) + `list_available_courses` |
| Telemetry P4 | `src/telemetry/metrics.py` | `_calculate_cost` bằng **bảng giá thật** (input/output theo model) thay cho dummy |
| Parse logs | `scripts/parse_logs.py` | Đọc log JSON → bảng token/latency/cost/error, tách theo từng run |
| Robustness | `src/core/gemini_provider.py` | Retry/backoff khi gặp 429 (free tier Gemini 5 req/phút) |
| Web demo (bonus) | `app.py` | Streamlit so sánh Chatbot vs Agent, hiện trace Thought→Action→Observation |
| Flowchart | `report/group_report/flowchart_react.md` | Sơ đồ vòng lặp ReAct (Mermaid + ASCII) |

### Điểm gãy tích hợp đã xử lý

- **Interface mismatch P5 ↔ P2:** bộ test của P5 import 8 hàm, nhưng `edu_tools.py` của P2
  chỉ có 6 → `ImportError`. Đã căn chỉnh: bổ sung 2 tool còn thiếu vào `edu_tools.py` và
  để agent tự chain `check_prerequisite` + `get_student_record` cho phần "đủ điều kiện".
- **Dependency order:** P5 eval phụ thuộc P1+P2 nên được merge sau cùng; tool của Dương
  (trùng `edu_tools.py` với P2) bị loại khỏi merge để tránh xung đột chủ quyền file.

---

## II. Debugging Case Study (10 Points)

### Case: Agent dừng ở bước 1 với số liệu bịa (Gemini)

**Triệu chứng:** Hỏi *"SV001 đủ điều kiện học ML301 không? Nếu đủ, tính học phí 3 tín chỉ
sau khi áp học bổng theo GPA thực tế."* — agent **dừng ngay sau bước 1**, trả lời *"giả định
học bổng 20% cho GPA 3.8"*. Khung trace **không có dòng Observation**.

**Bằng chứng:** GPA thật của SV001 là **3.2** (từ tool `get_student_record`), nhưng câu trả lời
ghi **3.8** → số liệu bị **bịa**, tool chưa hề chạy.

**Chẩn đoán:** Gemini xuất **cả `Action` lẫn `Final Answer`** (kèm `Observation` tự bịa) trong
**một lượt**. Vòng lặp `run()` cũ kiểm tra `Final Answer` **trước** khi chạy tool:

```python
final_answer = self._parse_final_answer(content)
if final_answer is not None:
    return final_answer.strip()   # ← thoát ngay, tool KHÔNG bao giờ chạy
action_data = self._parse_action(content)
```

Đây là lỗi kinh điển của ReAct khi LLM "nói trước cả bài" vì không bị chặn lại sau Action.

**Giải pháp:**
1. **Đảo logic** trong `agent.py`: ưu tiên **thực thi Action**; chỉ chấp nhận `Final Answer`
   khi không còn Action.
2. **Siết system prompt:** *"Mỗi lượt chỉ MỘT Thought + MỘT Action rồi DỪNG; KHÔNG tự viết
   Observation; KHÔNG xuất Final Answer cùng lượt với Action."*

**Đo lường tác động:** sau fix, đúng câu hỏi đó chạy **đủ 5 bước** với **GPA thật 3.2**:

```
[1] get_student_record("SV001")   → GPA=3.2, đã học CS101, MATH201
[2] check_prerequisite("ML301")   → cần CS101, MATH201  → ĐỦ điều kiện
[3] calculate_tuition("ML301", 3) → 4,500,000 VND
[4] apply_scholarship(...)        → (lộ ra thiếu tool get_scholarship_rate — đã bổ sung sau)
[5] Final Answer                  → tổng hợp từ Observation THẬT
```

**Lỗi phụ phát hiện được nhờ fix:** bước 4 báo ERROR vì chưa có tool suy GPA→% học bổng.
Agent xử lý **trung thực** (không bịa) — sau đó P6 bổ sung `get_scholarship_rate` để hoàn thiện.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — Thought block buộc agent "biết mình chưa biết"

Quan sát thực tế trên cùng một câu hỏi:
- **Chatbot** trả lời né tránh: *"Vui lòng kiểm tra đề cương môn học hoặc hệ thống của trường"* —
  vì không có dữ liệu thật, nó không dám đưa con số.
- **Agent** đi 5 bước, mỗi bước `Thought` xác định **thiếu dữ liệu gì** rồi gọi tool lấy đúng
  dữ liệu (GPA 3.2, tiên quyết, học phí) trước khi kết luận.

Khác biệt cốt lõi không phải "có tool", mà là **vòng kiểm chứng**: agent ráp câu trả lời từ
Observation thật, chatbot đoán trong 1 bước.

### 2. Reliability — Khi nào agent KHÔNG hơn?

- **Câu 1 bước, kiến thức chung:** agent tốn ~4-5× latency để gọi tool nhưng kết quả tương đương.
- **Latency & rate limit:** agent gọi LLM nhiều lần → trên free tier Gemini (5 req/phút) **một
  câu golden có thể dính 429**. Đây là cái giá thực của "suy luận nhiều bước" mà chatbot không có.
- **Phụ thuộc chất lượng tool:** nếu thiếu tool (như `get_scholarship_rate` ban đầu), agent
  buộc phải báo "không làm được" — đúng nhưng không trọn vẹn. **Agent chỉ mạnh bằng bộ tool của nó.**

### 3. Góc nhìn Integrator — Hợp đồng interface quan trọng hơn code

Bài học lớn nhất khi ráp 5 nhánh: **lỗi không nằm trong từng phần mà ở chỗ ghép**. P5 viết test
gọi 8 tool, P2 chỉ làm 6 → `ImportError` dù cả hai phần "chạy đúng" riêng lẻ. Nếu nhóm **chốt
danh sách tool (tên + chữ ký) ngay đầu giờ** thì đã tránh được. Observation feedback giúp agent
tự sửa trong runtime; nhưng giữa các thành viên thì cần "feedback" sớm qua interface contract.

---

## IV. Future Improvements (5 Points)

### 1. Stop-sequence thay cho vá logic
Bug "Final Answer sớm" được vá ở tầng parse. Cách bền hơn: truyền `stop_sequences=["Observation:"]`
xuống provider để LLM **không thể** tự viết Observation/Final Answer — chặn tận gốc thay vì lọc sau.

### 2. RAG cho tool tra cứu
Hiện `list_available_courses` lọc theo chuỗi. Production nên có `semantic_search_courses(mô tả)`
dùng vector DB → hỏi "môn về học máy" tìm được ML301/DL401 mà không cần biết mã chính xác.

### 3. Multi-agent + hàng đợi
Tách Retrieval Agent (gọi tool) và Reasoning Agent (tổng hợp); dùng async queue cho các lời gọi
tool độc lập (vd kiểm tra 2 môn song song) để giảm latency và né rate limit theo lô.

### 4. Telemetry & cost guardrail
`parse_logs.py` đã có cost thật. Bước tiếp: đặt **ngân sách token/lượt**, cảnh báo khi vượt, và
**model routing** (flash-lite cho câu đơn, flash/pro cho câu golden) để tối ưu chi phí.

---

> **Nộp bài:** `report/individual_reports/REPORT_HUYEN.md`
> **Branch:** `main` · **Vai trò:** P6 — Integrator
