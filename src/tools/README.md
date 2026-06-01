# 🛠️ Edu Tools — Hướng dẫn sử dụng

Bộ tool giáo dục cho **Kịch bản A — Trợ lý Đăng ký môn học**.
File: [`edu_tools.py`](edu_tools.py). Dữ liệu nạp từ [`data/`](../../data/) (xem [data/README.md](../../data/README.md)).

> **Quan hệ với data:** một chiều, **read-only**. Tool đọc `data/*.json` vào RAM *một lần* lúc import
> rồi chỉ tra cứu/tính toán — KHÔNG ghi đè file. Đổi data thì sửa JSON (hoặc chạy `generate_data.py`) rồi chạy lại.

---

## 1. Danh sách tool

| Tool | Đối số | Trả về (ví dụ) |
|---|---|---|
| `get_student_record` | `student_id` | `SV SV001 (Nguyễn Văn An): GPA=3.2, tín chỉ tích lũy=7, đã học=[...], đang học=[...]` |
| `check_prerequisite` | `course_id` | `Môn ML301 (Học máy) yêu cầu tiên quyết: ['CS101', 'MATH201']` |
| `calculate_tuition` | `course_id, credits` | `Học phí ML301 (3 tín chỉ x 1,500,000) = 4,500,000 VND` |
| `apply_scholarship` | `amount, percent` | `Sau học bổng 20%: 3,600,000 VND (gốc 4,500,000 VND)` |
| `check_academic_warning` | `gpa` | `CẢNH BÁO HỌC VỤ: GPA=1.8 < 2.0...` |
| `get_exam_schedule` | `course_id` | `Lịch thi môn DB201 (Cơ sở dữ liệu): 2026-06-22` |

**Quy ước chung:**
- Mọi đối số nhận vào dạng **chuỗi** (vì agent tách từ `Action: tool(a, b)`); tool tự ép kiểu khi cần.
- Mọi tool luôn trả về **một chuỗi** để đưa thẳng vào dòng `Observation:`.
- Lỗi (SV/môn không tồn tại, đối số sai) trả chuỗi bắt đầu bằng **`ERROR:`** thay vì văng exception → agent có thể tự sửa (self-correct).
- `course_id` không phân biệt hoa/thường (`ml301` = `ML301`); `credits` ở `calculate_tuition` bỏ trống thì lấy số tín chỉ chuẩn của môn.

---

## 2. Dùng trực tiếp trong Python

```python
from src.tools.edu_tools import get_student_record, calculate_tuition, apply_scholarship

print(get_student_record("SV001"))
print(calculate_tuition("ML301", "3"))      # -> ...= 4,500,000 VND
print(apply_scholarship("4500000", "20"))   # -> Sau học bổng 20%: 3,600,000 VND
```

Chạy self-test có sẵn (không cần LLM/model):

```bash
python -m src.tools.edu_tools
```

> Windows: nếu console báo lỗi Unicode, đặt `PYTHONIOENCODING=utf-8` trước khi chạy.

---

## 3. Dùng qua Agent (registry `EDU_TOOLS`)

Agent không gọi hàm trực tiếp — nó nhận **registry** `EDU_TOOLS` (list các dict `name`/`description`/`func`):

```python
from src.agent.agent import ReActAgent
from src.tools.edu_tools import EDU_TOOLS

agent = ReActAgent(llm, EDU_TOOLS, max_steps=6)
agent.run("SV001 đủ điều kiện học ML301 không? Tính học phí 3 tín chỉ sau học bổng 20%.")
```

LLM xuất `Action: tool_name(args)`; agent parse rồi gọi `func(*args)`. Mỗi dict trong registry:

```python
{"name": "calculate_tuition",
 "description": "Tính học phí. Args: course_id, credits (số nguyên).",
 "func": calculate_tuition}
```

`description` chính là phần đưa vào system prompt để LLM biết tool nào tồn tại và đối số gì — **viết mô tả rõ = agent ít gọi sai**.

---

## 4. Thêm tool mới

1. Viết hàm nhận đối số **chuỗi**, trả về **chuỗi** (lỗi → `"ERROR: ..."`).
2. Thêm 1 dict vào list `EDU_TOOLS` với `name` / `description` / `func`.

```python
def get_course_info(course_id: str) -> str:
    c = _COURSES.get(course_id.strip().upper())
    if not c:
        return f"ERROR: Không tìm thấy môn {course_id}"
    return f"{course_id}: {c['name']}, {c['credits']} tín chỉ"

EDU_TOOLS.append(
    {"name": "get_course_info",
     "description": "Tra tên + số tín chỉ của 1 môn. Args: course_id.",
     "func": get_course_info})
```

Không cần sửa agent — agent tự đọc `EDU_TOOLS`.

---

## 5. Ví dụ chuỗi gọi cho test case vàng (TC05)

```
check_prerequisite(ML301)        -> tiên quyết ['CS101', 'MATH201']
get_student_record(SV001)        -> đã học ['CS101', 'MATH201']  => ĐỦ điều kiện
calculate_tuition(ML301, 3)      -> 4,500,000 VND
apply_scholarship(4500000, 20)   -> 3,600,000 VND
```
