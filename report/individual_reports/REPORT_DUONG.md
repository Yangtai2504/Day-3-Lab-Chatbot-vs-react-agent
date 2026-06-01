# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thái Dương
- **Student ID**: 2A202600823
- **Role**: P5 — Evaluation & Failure Analysis
- **Branch**: Duong
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| File | Dòng code | Mô tả |
|---|---|---|
| `src/tools/edu_tools.py` | ~310 | Dataset 15 SV, 14 môn, 8 tool functions + EDU_TOOLS registry |
| `tests/test_cases.py` | ~350 | 34 test cases chia 5 nhóm + smoke test runner |
| `tests/run_evaluation.py` | ~170 | Runner so sánh chatbot vs agent, xuất bảng + JSON |
| `report/traces/*.md` | 4 files | 1 success trace + 3 failure traces có phân tích |

### Dataset Design

**15 sinh viên** với độ phủ phong phú:
- GPA: 1.5 (SV009) → 4.0 (SV014), phủ tất cả tier học bổng
- Năm học: 1-4, đa dạng kiến thức nền
- Edge cases: GPA 2.0 đúng ngưỡng cảnh báo (SV013), GPA 4.0 (SV014)

**14 môn học** tạo thành đồ thị tiên quyết 4 tầng:
```
Tầng 0 (không có tiên quyết): CS101, MATH101, ENG101
Tầng 1 (cần tầng 0):          MATH201, DB201, STAT201, ENG201, NET301
Tầng 2 (cần tầng 1):          ML301, SE301, CV301
Tầng 3 (cần tầng 2):          DL401
Tầng 4 (cần tầng 3):          NLP401, CAPSTONE
```
Chuỗi tiên quyết dài nhất: CS101 → MATH201 → ML301 → DL401 → NLP401 (4 cấp).

### Test Case Design (34 cases)

```
Simple  (10): 1 tool call  — kiểm tra từng tool độc lập
Multi    (8): 2-3 tools    — chatbot hay sai, agent cần chain
Golden   (4): 4-5 tools    — demo chính thức
Failure  (7): failure trigger — thu trace lỗi có chủ đích
Edge     (5): biên dữ liệu — GPA ngưỡng, multi-call, tool 2 lần
```

### Evaluation Runner

`run_evaluation.py` hỗ trợ:
- Chạy theo nhóm: `--group simple | multi | golden | failure | edge | all`
- Heuristic judge: kiểm tra keyword từ golden_answer xuất hiện trong output
- Xuất bảng so sánh + thống kê theo loại query
- Lưu kết quả JSON vào `report/evaluation/eval_TIMESTAMP.json`

---

## II. Debugging Case Study (10 Points)

### Case: Hallucinated Tool — F07

**Query**: "Tìm môn học phù hợp nhất cho SV002 để cải thiện GPA..."

**Vấn đề phát hiện**: Agent gọi `recommend_course(SV002, improve_gpa)` — tool không tồn tại.

**Log evidence** (từ `logs/`):
```json
{
  "event": "TOOL_CALL",
  "data": {
    "tool": "recommend_course",
    "args": "SV002, improve_gpa",
    "obs": "ERROR: Tool 'recommend_course' không tồn tại. Chỉ dùng: [...]"
  }
}
```

**Chẩn đoán**:
- Query dùng từ "tìm môn phù hợp nhất" → LLM ngầm định phải có tool "recommend".
- System prompt v1 chỉ liệt kê tên tool, không cấm rõ "không được đặt tên tool mới".
- LLM suy luận theo nhu cầu → hallucinate tool name theo pattern thông thường.

**Điểm thú vị**: Agent *tự sửa* được sau lỗi — ở bước 3 chọn `check_prerequisite` + suy luận từ → Final Answer hợp lý. Đây là hành vi self-correction tốt.

**Fix — Prompt v2**:
```
TUYỆT ĐỐI chỉ gọi đúng tên tool trong danh sách.
Nếu không có tool phù hợp, giải thích bằng suy luận,
KHÔNG tự đặt tên tool mới.
```

**Đo lường tác động**: Sau khi thêm dòng này vào prompt, chạy lại F07 → bước 2 không còn ERROR, agent đi thẳng vào `list_available_courses`, số bước giảm từ 4 xuống 3.

**Tổng kết 3 loại lỗi đã phân tích**:

| Loại | Test ID | Nguồn gốc | Fix |
|---|---|---|---|
| Parse Error | F05 | Tham số kiểu chữ thay vì số | Thêm chỉ dẫn "đổi số khi có đơn vị" vào prompt |
| Hallucination | F07 | LLM tự bịa tên tool | Thêm cấm "không đặt tên tool mới" vào prompt |
| Timeout | F04 | max_steps < bước cần thiết | Tăng max_steps hoặc thêm guardrail báo cáo trung gian |

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — Vai trò của Thought block

Khác biệt lớn nhất không phải là "có tool hay không" mà là **quy trình suy luận có cấu trúc**.

Với Chatbot: LLM đưa ra câu trả lời trong 1 bước duy nhất — không có cơ chế kiểm tra lại. Kết quả là câu trả lời nghe có vẻ hợp lý nhưng thiếu dữ liệu thực tế (ví dụ báo học phí tùy chính sách trường mà không có con số cụ thể).

Với Agent: Mỗi bước Thought → Action → Observation tạo ra một vòng lặp kiểm tra-cập nhật. Agent *biết mình chưa biết gì* và gọi tool để có dữ liệu trước khi kết luận. Đây chính là điểm tạo ra độ chính xác.

Kết quả thực tế từ bài test:
- 10/10 simple cases: cả hai đều trả lời, nhưng chatbot hay sai số liệu (không có ground truth).
- 8/8 multi cases: agent luôn ra đúng, chatbot fail 6/8 do không thể chain thông tin.
- 4/4 golden cases: chatbot fail toàn bộ, agent giải được cả 4.

### 2. Reliability — Khi nào Chatbot thắng?

Chatbot **tốt hơn Agent** trong 2 trường hợp:
1. **Câu hỏi 1 bước, kiến thức chung**: "Giải thích Machine Learning là gì?" — Agent mất ~5x latency để gọi tool nhưng kết quả tương đương chatbot.
2. **Latency-sensitive**: Chatbot ~800ms vs Agent ~4,200ms cho golden case. Nếu ứng dụng yêu cầu response < 1s, agent có thể không phù hợp.

Trích dẫn từ bảng đo: với 10 simple cases, winner là DRAW 7 lần — chatbot không thua kém gì agent về độ chính xác khi bài chỉ 1 bước.

### 3. Observation — Feedback loop làm thay đổi quyết định

Observation có giá trị lớn nhất khi nó **chuẩn chỉnh sai lầm**:
- Trong F05 (parse error): Observation "could not convert string to float" khiến agent tự chuyển đổi chữ→số ở bước 2. Không có observation này, agent sẽ trả lời sai.
- Trong F07 (hallucination): Observation "Tool không tồn tại" khiến agent chọn strategy khác hoàn toàn.

Đây là cơ chế mà chatbot hoàn toàn không có: một chatbot sau khi đưa ra câu trả lời sai không có cách nào tự biết và tự sửa.

---

## IV. Future Improvements (5 Points)

### 1. Mở rộng lên RAG (Retrieval-Augmented Generation)

Hiện tại toàn bộ dữ liệu là mock dict trong Python. Để lên production:
- Chuyển `_STUDENTS` và `_COURSES` vào CSDL (PostgreSQL).
- Thêm tool `semantic_search_courses(description)` dùng vector DB (Qdrant/Weaviate) → tìm môn bằng mô tả tự nhiên thay vì phải biết mã môn chính xác.
- Việc hỏi "Tìm môn về học máy" sẽ tìm được ML301, DL401, NLP401 thay vì báo lỗi.

### 2. Multi-Agent Architecture

Chia thành 2 agent chuyên biệt:
- **Retrieval Agent**: chuyên lấy thông tin (get_student_record, check_prerequisite).
- **Reasoning Agent**: nhận dữ liệu từ Retrieval Agent, tính toán và đưa ra khuyến nghị.

Lợi ích: parallelism (2 môn có thể kiểm tra cùng lúc), scale đơn giản, dễ debug từng agent riêng.

### 3. Guardrails & Safety

- **Input validation**: sanitize student_id (chỉ cho phép SVxxx format) trước khi truyền vào tool.
- **Output validator**: kiểm tra Final Answer có chứa số liệu trước khi trả về (nếu không có → yêu cầu agent tính toán lại).
- **Confidence score**: nếu agent trả lời "không có dữ liệu", log kèm confidence để analyst review.

### 4. Cost Optimization

- **Prompt caching**: system prompt ít thay đổi → cache ở provider level (giảm ~60% prompt token cost).
- **Tool routing**: với simple query (1 từ khóa, 1 entity), bypass ReAct loop, gọi thẳng tool → giảm latency 5x.
- **Model routing**: dùng gpt-4o-mini cho simple, gpt-4o chỉ cho golden/complex cases.

---

> **Nộp bài**: File này được đặt tại `report/individual_reports/REPORT_DUONG.md`
> **Branch**: `Duong`
> **Commit**: feat(P5)
