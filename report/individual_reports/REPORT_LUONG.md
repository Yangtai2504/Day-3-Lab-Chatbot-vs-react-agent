# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trần Đức Lương
- **Student ID**: 2A202600881
- **Role**: P3 — Chatbot Baseline & Prompt
- **Branch**: luong
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented
| File | Mô tả |
|---|---|
| `chatbot.py` | Baseline chatbot (1 lần gọi LLM, KHÔNG tool) để đối chứng với agent |

### Code Highlights
- `build_provider()`: chọn OpenAI/Gemini theo `.env` (`DEFAULT_PROVIDER`, `DEFAULT_MODEL`).
- `get_system_prompt()`: prompt baseline — *"trả lời trực tiếp, không suy nghĩ theo bước,
  không dùng công cụ"* để làm mốc so sánh đúng tinh thần "chatbot thuần".
- `ask_question()` + vòng CLI (`exit/quit`) cho demo nhanh.

### Vai trò trong so sánh
Chatbot là **đường cơ sở (baseline)**: cùng câu hỏi, cùng model với agent, nhưng **không có
vòng Thought–Action–Observation** → làm nổi bật giá trị của agent ở câu đa bước.

---

## II. Debugging Case Study (10 Points)

### Case: Chatbot bịa/né số liệu ở câu đa bước

**Query**: "SV001 đủ điều kiện ML301 không? Học phí 3 tín chỉ sau học bổng là bao nhiêu?"

**Quan sát thực tế** (Gemini, prompt v1): chatbot trả lời né tránh —
*"Vui lòng kiểm tra đề cương môn học hoặc hệ thống thông tin sinh viên của trường."*

**Chẩn đoán**: chatbot **không có truy cập dữ liệu** (GPA, tiên quyết, học phí). Khi prompt
không cấm chặt, model có 2 kiểu hỏng: (a) **bịa** con số nghe hợp lý, hoặc (b) **né** trả lời.

**Prompt v1 → v2**:
- v1: "Bạn là trợ lý học vụ, trả lời câu hỏi."
- v2: thêm *"Chỉ đưa thông tin chính xác, KHÔNG bịa số liệu; nếu không có dữ liệu, nói rõ là
  không có."*
- **Kết quả**: v2 giảm hẳn việc bịa số — model chuyển sang **thừa nhận giới hạn** thay vì
  phịa GPA/học phí. Đây chính là bằng chứng cho thấy baseline **đụng trần** vì thiếu tool.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: với câu 1 bước (định nghĩa, kiến thức chung) chatbot **ngang ngửa** agent và
   nhanh hơn nhiều (1 call vs 4–5 call). Baseline không hề "vô dụng".
2. **Reliability**: chatbot thua ở **mọi câu cần dữ liệu thật của trường**. Không có ground
   truth → hoặc bịa, hoặc né; cả hai đều không dùng được cho tư vấn đăng ký.
3. **Bài học prompt**: prompt tốt giảm hallucination nhưng **không thay được tool**. Trần của
   chatbot là kiến thức sẵn có; muốn vượt phải có hành động (agent).

---

## IV. Future Improvements (5 Points)

- **Hybrid routing**: câu đơn → chatbot (rẻ, nhanh); câu đa bước → agent. Tận dụng điểm mạnh mỗi bên.
- **RAG cho chatbot**: nhúng `data/*.json` vào context qua retrieval để chatbot có dữ liệu thật
  mà không cần vòng lặp tool.
- **Guardrail xác nhận**: bắt chatbot trả "không chắc/không có dữ liệu" khi câu hỏi cần số liệu cụ thể.
- **Đo lường**: thêm test phân biệt câu "kiến thức chung" vs "cần dữ liệu" để chọn baseline phù hợp.

---

> **Nộp bài**: `report/individual_reports/REPORT_LUONG.md` · **Branch**: `luong` · **Vai trò**: P3
