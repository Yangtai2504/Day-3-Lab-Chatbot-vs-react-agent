# 📂 Data Layer — Kịch bản A: Trợ lý Đăng ký môn học

Toàn bộ dữ liệu nghiệp vụ được tách khỏi code (`src/tools/`) và lưu dạng **JSON UTF-8**.
Lý do tách file: dễ mở rộng test case, dễ sinh failure trace, và ghi điểm **Code Quality** (modularity)
trong [SCORING.md](../SCORING.md).

> Tool trong `src/tools/edu_tools.py` chỉ cần `json.load()` 3 file dưới đây thay cho dict hard-code.

**Quy mô hiện tại:** 100 sinh viên · 30 môn · 5 chính sách học bổng · 16 test case.

## 🔁 Sinh dữ liệu — `generate_data.py`

```bash
python data/generate_data.py
```

- Tổ hợp họ/đệm/tên phổ biến → tên SV; gen ngẫu nhiên mã SV (`B22DCCN137`) và mã môn (`SE261`).
- **Idempotent** (seed cố định): chạy lại ra y hệt, không phình to dần.
- **Giữ nguyên lõi curated**: `SV001..SV012` + 15 môn neo (`CS101..MLOPS403`) để `test_cases.json` luôn hợp lệ.
- Bảo toàn ràng buộc: prereq là **DAG không vòng**; `passed` chỉ chứa môn đã qua đủ tiên quyết; `credits_completed` = tổng tín chỉ.
- Chỉnh `N_EXTRA_STUDENTS` / `N_EXTRA_COURSES` đầu file để tăng/giảm số lượng.

---

## 1. `students.json` — Hồ sơ sinh viên

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `name` | str | Họ tên |
| `gpa` | float | Điểm trung bình tích lũy (thang 4) |
| `credits_completed` | int | Tổng tín chỉ đã tích lũy (= tổng `credits` các môn trong `passed`) |
| `passed` | list[str] | Mã môn đã qua → dùng để đối chiếu tiên quyết |
| `enrolled` | list[str] | Môn đang học (cho bonus tool) |

## 2. `courses.json` — Danh mục môn học

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `name` | str | Tên môn |
| `credits` | int | Số tín chỉ |
| `prereq` | list[str] | Môn tiên quyết (có chuỗi nhiều tầng: `AI401 → ML301 → MATH201 → CS101`) |
| `fee_per_credit` | int | Học phí / tín chỉ (VND) |
| `exam_date` | str (YYYY-MM-DD) | Lịch thi (cho bonus tool `get_exam_schedule`) |

## 3. `scholarships.json` — Chính sách học bổng

Mỗi policy: `code`, `name`, `min_gpa` (ngưỡng GPA), `percent` (% giảm), `fixed_amount` (giảm cố định VND).
`apply_scholarship` có thể nhận trực tiếp `percent`, hoặc tra policy theo GPA sinh viên.

## 4. `test_cases.json` — Bộ kiểm thử Chatbot vs Agent

Mỗi case có `type`:
- **simple** (1 tool) — cả chatbot lẫn agent đều nên đúng.
- **multi** (≥2 tool) — chatbot dễ bịa số / bỏ bước → minh chứng giá trị của Agent.
- **edge** — data biên (SV/môn không tồn tại, GPA cảnh báo) → **nguyên liệu sinh failure trace**.

---

## 🎯 Data này được thiết kế để "đẻ" ra điểm trong SCORING.md

| Mục cần ghi điểm | Data hỗ trợ thế nào |
|---|---|
| **Trace Quality (9đ)** — cần cả trace ✅ và ❌ | `TC03/TC05` cho trace thành công đa bước; `TC06/TC07` ép tool trả `ERROR` (parse/hallucination); `SV999`/`XYZ123` ép timeout/self-correct |
| **Evaluation & Analysis (7đ)** — so sánh chatbot vs agent | 8 case trải đều simple → multi → edge để chấm tỉ lệ đúng của 2 hệ |
| **Agent v1/v2 (7+7đ)** | Chuỗi tiên quyết nhiều tầng (AI401) buộc agent lập kế hoạch nhiều bước |
| **Tool Design (4đ)** | 4 tool gốc + dữ liệu cho 2 bonus tool (`check_academic_warning`, `get_exam_schedule`) |
| **Code Quality (4đ)** | Data tách JSON, không hard-code trong logic |

### Các "điểm gài" có chủ đích trong data
- **SV002** (GPA 1.8, chỉ học CS101): thiếu tiên quyết ML301 **và** dưới ngưỡng cảnh báo học vụ (< 2.0).
- **SV005** (GPA 2.05): biên cảnh báo học vụ → test ranh giới.
- **SV004** (GPA 3.8): đủ điều kiện học bổng xuất sắc 50% + tiên quyết AI401 đầy đủ.
- **AI401**: tiên quyết 2 môn, tạo chuỗi suy luận sâu nhất.

### Kiểm chứng số học (golden cases)
- **TC03**: ML301 = 3 × 1.500.000 = **4.500.000** → −20% = **3.600.000 VND** ✅
- **TC05**: AI401 = 4 × 1.800.000 = **7.200.000** → −50% = **3.600.000 VND** ✅
