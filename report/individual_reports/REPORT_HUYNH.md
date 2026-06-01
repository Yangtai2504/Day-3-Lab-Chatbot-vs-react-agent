# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trần Văn Huỳnh
- **Student ID**: 2A202600805
- **Role**: P1 — Agent Core (ReAct loop)
- **Branch**: huynh
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented
| File | Mô tả |
|---|---|
| `src/agent/agent.py` | Vòng lặp ReAct `run()`, parser regex, `_execute_tool`, quản lý `history` |

### Code Highlights
- **Vòng lặp Thought–Action–Observation**: lặp tối đa `max_steps` lần; mỗi vòng gọi LLM →
  parse Action → chạy tool → ghép Observation thật vào transcript → lặp tới khi `Final Answer`.
- **Parser bằng regex** (không phụ thuộc model trả JSON):
  - `_parse_action`: `Action\s*:\s*([A-Za-z_]\w*)\s*\((.*?)\)`
  - `_parse_final_answer`: bắt phần sau `Final Answer:`
- **`_execute_tool` + `_evaluate_args`/`_clean_arg`**: tách tham số theo dấu phẩy, bỏ dấu nháy,
  gọi `tool["func"](*args)`; trả `ERROR: ...` nếu tool không tồn tại hoặc ném exception.
- **Guardrail**: chạm `max_steps` → trả thông báo dừng, tránh lặp vô hạn / cháy token.

### Tương tác với ReAct loop
`run()` truyền `get_system_prompt()` (mô tả tool + định dạng) cho LLM; mọi Observation đưa lại
là **kết quả tool thật**, không để model tự bịa.

---

## II. Debugging Case Study (10 Points)

### Case: Keyword-argument làm tool báo ERROR

**Query**: câu golden cần áp học bổng → agent sinh `Action: apply_scholarship(4500000, gpa=3.2)`.

**Log evidence**:
```json
{"event": "TOOL_CALL", "data": {"tool": "apply_scholarship",
 "args": "4500000, gpa=3.2", "observation": "ERROR: Học bổng không hợp lệ: gpa=3.2"}}
```

**Chẩn đoán**: `_evaluate_args` tách tham số theo dấu phẩy thành `["4500000", "gpa=3.2"]` rồi
truyền **vị trí** vào `apply_scholarship(amount, percent_or_policy)`. Tham số thứ 2 trở thành
chuỗi `"gpa=3.2"` → tool không hiểu. LLM dùng cú pháp **keyword arg** kiểu Python mà parser
hiện chỉ hỗ trợ **positional**.

**Giải pháp** (2 hướng):
1. Prompt: yêu cầu gọi tool theo **positional**, đúng thứ tự tham số (giảm kwarg).
2. Code (đề xuất): trong `_clean_arg`, phát hiện `key=value` → cắt lấy `value`, hoặc map theo
   tên tham số của hàm.

**Insight**: parser regex đơn giản là điểm dễ vỡ nhất của ReAct — phải khớp **đúng** cách LLM
xuất Action; cần phòng thủ cho cả positional lẫn keyword.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: `Thought` ép model nói ra "đang thiếu dữ liệu gì" trước khi hành động →
   agent đi từng bước `get_student_record → check_prerequisite → calculate_tuition` thay vì
   đoán cả gói như chatbot.
2. **Reliability**: agent **kém hơn** khi câu chỉ 1 bước (tốn nhiều vòng LLM, latency cao) hoặc
   khi LLM xuất Action sai định dạng → parser fail → tốn 1 bước nhắc lại.
3. **Observation**: feedback từ tool (kể cả `ERROR`) chính là thứ giúp agent **tự sửa**: thấy
   ERROR ở một bước, model đổi chiến lược ở bước sau — cơ chế chatbot hoàn toàn không có.

---

## IV. Future Improvements (5 Points)

- **Stop-sequence**: truyền `stop=["Observation:"]` để LLM dừng ngay sau Action, không tự bịa
  Observation/Final Answer (chặn lỗi tận gốc thay vì lọc sau).
- **Parser mạnh hơn**: hỗ trợ keyword arg, nhiều Action/lượt, JSON mode khi model hỗ trợ.
- **Bộ nhớ**: nén transcript khi dài (tránh vượt context ở câu nhiều bước).
- **Tách tool-router**: với nhiều tool, dùng embedding chọn tool thay vì liệt kê hết trong prompt.

---

> **Nộp bài**: `report/individual_reports/REPORT_HUYNH.md` · **Branch**: `huynh` · **Vai trò**: P1
