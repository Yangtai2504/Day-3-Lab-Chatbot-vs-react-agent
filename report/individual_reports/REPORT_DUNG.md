# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Ngọc Dũng
- **Student ID**: 2A202600906
- **Role**: P4 — Telemetry & Cost
- **Branch**: dung
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented
| File | Mô tả |
|---|---|
| `src/telemetry/metrics.py` | `PerformanceTracker.track_request` + `_calculate_cost` (giá thật) |
| `scripts/parse_logs.py` | Đọc log JSON → bảng token / latency / cost / error |
| `src/telemetry/logger.py` | Log sự kiện dạng JSON (AGENT_START, LLM_RESPONSE, TOOL_CALL, ...) |

### Code Highlights
- **`_calculate_cost`**: bảng giá thật theo từng model, tính riêng input/output:
  ```
  cost = prompt_tokens/1e6 × giá_in + completion_tokens/1e6 × giá_out
  ```
  (gemini-2.5-flash 0.30/2.50; flash-lite 0.10/0.40; gpt-4o-mini 0.15/0.60 USD/1M token).
- **`parse_logs.py`**: gom theo từng run (mỗi `AGENT_START` mở 1 run), tổng hợp tokens, latency
  trung bình, cost, đếm `PARSE_ERROR` / lỗi tool / timeout.

### Số liệu thật thu được
Trên một phiên chạy Gemini: 7 LLM calls · 6,288 tokens · latency TB **2,658 ms/call** ·
cost **$0.0038**. Bắt được cả before/after của bug agent (run 1 bước vs 5 bước).

---

## II. Debugging Case Study (10 Points)

### Case: Cost luôn ra sai vì model name không có trong log LLM

**Vấn đề**: bản đầu `_calculate_cost` trả hằng số dummy (`tokens/1000 × 0.01`) → cost vô nghĩa.
Khi viết `parse_logs.py` để tính cost thật thì phát hiện: sự kiện `LLM_RESPONSE` **không kèm tên
model** (chỉ có `usage` + `latency`), nên không biết áp giá nào.

**Log evidence**:
```json
{"event":"LLM_RESPONSE","data":{"step":1,"usage":{...},"latency_ms":2498}}   // thiếu "model"
{"event":"AGENT_START","data":{"model":"gemini-2.5-flash", ...}}              // model ở đây
```

**Chẩn đoán**: agent ghi log trực tiếp qua `logger`, **không đi qua `tracker.track_request`**,
nên cost không được tính tại nguồn; còn `LLM_RESPONSE` lại thiếu trường model.

**Giải pháp**: trong `parse_logs.py`, **bám model từ `AGENT_START` gần nhất** rồi áp cho các
`LLM_RESPONSE` thuộc cùng run. Đồng thời thay `_calculate_cost` bằng bảng giá thật input/output.
→ Cost khớp thực tế ($0.0038 cho phiên test), tách được chi phí theo từng run.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: telemetry cho thấy agent tốn ~**4–5× tokens & latency** so với chatbot cho cùng
   câu hỏi (nhiều vòng LLM) — cái giá để đổi lấy độ chính xác ở câu đa bước.
2. **Reliability**: số liệu đo được làm rõ điểm yếu agent: latency cao + dễ dính rate limit. Không
   có telemetry thì các nhận định "agent tốt hơn" chỉ là cảm tính.
3. **Observation**: việc log đầy đủ TOOL_CALL (kèm observation) giúp truy vết chính xác **bước nào
   gọi tool gì, lỗi ở đâu** — nền tảng cho mọi phân tích thất bại.

---

## IV. Future Improvements (5 Points)

- **Ghi model vào mọi sự kiện LLM** (hoặc bắt buộc đi qua `track_request`) để cost tính tại nguồn.
- **Cost guardrail**: đặt ngân sách token/lượt; cảnh báo & dừng khi vượt (tránh cháy chi phí ở
  câu lặp nhiều bước).
- **Dashboard P50/P99 latency** theo loại câu; export Prometheus/Grafana khi lên production.
- **Model routing theo cost**: flash-lite cho câu đơn, flash/pro cho câu golden.

---

> **Nộp bài**: `report/individual_reports/REPORT_DUNG.md` · **Vai trò**: P4 — Telemetry
