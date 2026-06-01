# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Đỗ Trung Kiên 
- **Student ID**: 2A202600711
- **Role**: P2 — Tools & Data
- **Branch**: kien
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented
| File | Mô tả |
|---|---|
| `src/tools/edu_tools.py` | Bộ tool giáo dục + registry `EDU_TOOLS` |
| `data/*.json` | Dataset: students, courses, scholarships, test_cases |

### Tool Design (định dạng `Action: tool(args)`)
8 tool, mọi tool nhận **string** và trả **string** (dễ cho LLM gọi và đọc Observation):

| Tool | Use case |
|---|---|
| `get_student_record` | GPA, môn đã học, tín chỉ tích lũy |
| `check_prerequisite` | Danh sách môn tiên quyết |
| `calculate_tuition` | `fee_per_credit × số tín` |
| `apply_scholarship` | Áp % hoặc mã chính sách lên số tiền |
| `get_exam_schedule` | Lịch thi |
| `check_academic_warning` | Cảnh báo học vụ (GPA < 2.0) |
| `get_scholarship_rate` | Suy GPA → bậc học bổng merit |
| `list_available_courses` | Liệt kê / lọc môn |

### Data
- Đọc từ `data/*.json` (không hardcode), nạp 1 lần khi import.
- Chính sách học bổng theo `min_gpa`: MERIT_50 (≥3.5→50%), MERIT_30 (≥3.2→30%), MERIT_20 (≥3.0→20%).
- Helper `_normalize_id` (chuẩn hóa mã SV/môn) + `_parse_number` (bóc "VND"/"%"/dấu phẩy).

---

## II. Debugging Case Study (10 Points)

### Case: Tham số `credits` dạng chữ làm `calculate_tuition` vỡ

**Query**: "Học phí ML301 ba tín chỉ?" → agent gọi `calculate_tuition("ML301", "ba")`.

**Vấn đề**: `int("ba")` ném `ValueError` → cả tool sập nếu không bắt lỗi.

**Chẩn đoán**: LLM đôi khi truyền số bằng chữ (tiếng Việt/Anh) thay vì chữ số. Tool phải
**phòng thủ kiểu dữ liệu** vì input đến từ model, không kiểm soát được.

**Giải pháp**: bọc ép kiểu trong try/except, trả Observation lỗi rõ ràng thay vì throw:
```python
try:
    credit_count = int(float(str(credits).strip()))
except ValueError:
    return f"ERROR: credits phải là số nguyên, nhận được {credits}"
```
→ Agent đọc được ERROR và sửa ở bước sau (gọi lại với `3`).

**Tool Design Evolution**: thống nhất **mọi tool trả `ERROR: ...`** khi gặp input xấu thay vì
ném exception — giúp ReAct loop tiếp tục thay vì chết giữa chừng.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: chatbot không có nguồn sự thật nên bịa số học phí/học bổng; agent qua tool đọc
   `data/*.json` → con số chính xác (ML301 = 3 × 1,500,000 = 4,500,000 VND).
2. **Reliability**: tool chỉ hữu ích nếu **chữ ký rõ ràng**. Khi P5 kỳ vọng tool mà P2 chưa làm
   (`get_scholarship_rate`, `list_available_courses`), eval gãy → bài học: chốt interface sớm.
3. **Observation**: Observation dạng câu tiếng Việt dễ đọc giúp LLM "hiểu" kết quả và suy luận
   tiếp tốt hơn so với trả JSON thô.

---

## IV. Future Improvements (5 Points)

- **Schema/validation**: dùng pydantic cho tham số tool (chặn input xấu sớm, tự sinh mô tả).
- **CSDL thay JSON**: chuyển `data/*.json` → PostgreSQL khi quy mô lớn.
- **Tool ngữ nghĩa**: `semantic_search_courses(mô tả)` để hỏi "môn về học máy" không cần mã.
- **Thêm field khoa/ngành** vào `courses.json` để `list_available_courses` lọc theo khoa.

---

> **Nộp bài**: `report/individual_reports/REPORT_KIEN.md` · **Branch**: `kien` · **Vai trò**: P2
