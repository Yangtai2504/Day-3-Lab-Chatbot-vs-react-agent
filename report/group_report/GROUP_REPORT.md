# Group Report: Lab 3 — Chatbot vs ReAct Agent

- **Team Name**: [điền tên nhóm]
- **Team Members**:
  | Vai trò | Họ tên | MSSV | Branch |
  | :--- | :--- | :--- | :--- |
  | P1 — Agent Core | Trần Văn Huỳnh | 2A202600805 | huynh |
  | P2 — Tools & Data | Đỗ Trung Kiên | 2A202600711 | kien |
  | P3 — Chatbot Baseline | Trần Đức Lương | 2A202600881 | luong |
  | P4 — Telemetry & Cost | Nguyễn Ngọc Dũng | 2A202600906 | dung |
  | P5 — Evaluation | Nguyễn Thái Dương | 2A202600823 | Duong |
  | P6 — Integrator | Nguyễn Khánh Huyền | 2A202600650 | main |
- **Deployment Date**: 2026-06-01
- **Chủ đề**: Trợ lý Tư vấn Đăng ký môn học (giáo dục)

---

## 1. Executive Summary

Nhóm xây dựng một **ReAct Agent** tư vấn đăng ký môn học và so sánh với **Chatbot baseline**
trên cùng bộ câu hỏi. Khác biệt rõ nhất ở các câu **đa bước** (đủ điều kiện → học phí → học bổng):
chatbot trả lời chung chung/né số liệu, còn agent **chain nhiều tool** để lấy dữ liệu thật rồi
mới kết luận.

- **Kết quả chính**: Trên câu golden "SV001 đủ điều kiện ML301 + học phí + học bổng", chatbot
  **không đưa được số liệu** ("vui lòng kiểm tra hệ thống"), agent giải **đủ 5 bước** với GPA
  thật **3.2** → ra học phí **4,500,000 VND** chính xác.
- **Provider**: Gemini `gemini-2.5-flash` (chính), OpenAI (dự phòng).

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop
Vòng lặp `Thought → Action → Observation` lặp đến khi có `Final Answer` hoặc chạm `max_steps`.
Sơ đồ chi tiết: [flowchart_react.md](./flowchart_react.md).

### 2.2 Tool Inventory (`src/tools/edu_tools.py` — 8 tool, đọc từ `data/*.json`)
| Tool | Input | Use case |
| :--- | :--- | :--- |
| `get_student_record` | `student_id` | GPA, môn đã học, tín chỉ |
| `check_prerequisite` | `course_id` | Danh sách môn tiên quyết |
| `calculate_tuition` | `course_id, credits` | Học phí = phí/tín × số tín |
| `apply_scholarship` | `amount, percent_or_policy` | Áp học bổng theo % hoặc mã |
| `get_exam_schedule` | `course_id` | Lịch thi |
| `check_academic_warning` | `gpa | student_id` | Cảnh báo học vụ (GPA < 2.0) |
| `get_scholarship_rate` | `student_id` | Suy GPA → % học bổng merit |
| `list_available_courses` | `filter` | Liệt kê / lọc môn |

### 2.3 LLM Providers
- **Chính**: Gemini `gemini-2.5-flash` (có retry/backoff cho rate limit 429).
- **Dự phòng**: OpenAI (`gpt-4o-mini`), provider local Phi-3 (offline).

---

## 3. Telemetry & Performance Dashboard

Số liệu **thật** từ `scripts/parse_logs.py` trên log một phiên chạy Gemini (token/latency/cost
tính theo bảng giá thật trong `metrics._calculate_cost`):

| Chỉ số | Giá trị |
| :--- | :--- |
| LLM calls | 7 |
| Tool calls | 5 (lỗi tool: 2) |
| Tổng tokens | 6,288 (prompt 4,107 / completion 1,040) |
| Latency trung bình | **2,658 ms/call** |
| Chi phí ước tính | **$0.0038** |

> Lưu ý: eval đầy đủ 34 case không chạy trọn vẹn do **giới hạn quota/ngày của Gemini free tier**
> (5 req/phút). Số liệu trên từ subset thật đã chạy + các lần test agent.

---

## 4. Root Cause Analysis — Failure Traces

### Case 1: Agent dừng ở bước 1 với số liệu bịa *(đã sửa)*
- **Input**: "SV001 đủ điều kiện ML301 không? ... áp học bổng theo GPA thực tế."
- **Triệu chứng**: agent trả lời ngay với GPA **3.8** (thật là **3.2**), không có Observation.
- **Root cause**: Gemini xuất cả `Action` + `Final Answer` trong 1 lượt; vòng lặp cũ ưu tiên
  `Final Answer` → return trước khi chạy tool.
- **Fix**: ưu tiên thực thi Action + siết prompt. Sau fix chạy đủ 5 bước. (Chi tiết:
  [REPORT_HUYEN.md](../individual_reports/REPORT_HUYEN.md) mục II.)

### Case 2: Thiếu tool `get_scholarship_rate` *(đã bổ sung)*
- Agent thử `apply_scholarship(4500000, gpa=3.2)` → ERROR (tool nhận %/mã, không nhận GPA).
- Agent xử lý **trung thực** (báo không tính được) thay vì bịa → P6 bổ sung tool suy GPA→%.

### Case 3 (P5): 3 loại lỗi thu trace — parse / hallucination / timeout
Xem `report/traces/` (do P5 chuẩn bị): trace thành công + 3 loại thất bại có chủ đích.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 → v2 (ưu tiên Action + cấm Final Answer sớm)
| | Prompt v1 | Prompt v2 |
| :--- | :--- | :--- |
| Câu golden SV001 | dừng **1 bước**, GPA bịa 3.8 | chạy **5 bước**, GPA thật 3.2 |
| Tool thực thi | 0 | 4 |
→ Bằng chứng trực tiếp trong log (run #5 vs run #6).

### Experiment 2 (Bonus): Chatbot vs Agent
| Loại câu | Chatbot | Agent | Winner |
| :--- | :--- | :--- | :--- |
| Đơn (1 tool, vd tiên quyết ML301) | thường đúng | đúng | Draw |
| Đa bước (đủ ĐK + học phí + học bổng) | né số liệu / sai | chain tool → đúng | **Agent** |

---

## 6. Production Readiness Review

- **Guardrails**: `max_steps` chặn lặp vô hạn (tránh cháy token); retry/backoff cho 429.
- **Security**: validate `student_id`/`course_id` trước khi vào tool; tool trả `ERROR` rõ ràng
  thay vì throw.
- **Cost control**: cost thật theo model; đề xuất model routing (flash-lite cho câu đơn).
- **Scaling**: chuyển data `*.json` → CSDL; thêm RAG cho tra cứu ngữ nghĩa; cân nhắc multi-agent.
- **Reliability**: free tier rate limit là nút thắt thật → production cần bật billing hoặc đa key.

---

> **Nộp bài**: `report/group_report/GROUP_REPORT.md` · **Branch**: `main`
