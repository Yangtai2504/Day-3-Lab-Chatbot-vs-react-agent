"""
Generator dữ liệu cho Lab 3 (Kịch bản A — Trợ lý Đăng ký môn học).

- GIỮ NGUYÊN phần curated (12 SV + 15 môn) làm "neo" cho data/test_cases.json.
- Gen thêm môn & sinh viên ngẫu nhiên, tổ hợp họ/đệm/tên phổ biến.
- Bảo toàn ràng buộc: prereq là DAG (không vòng); `passed` tôn trọng tiên quyết;
  `credits_completed` = tổng tín chỉ môn đã qua.

Chạy:  python data/generate_data.py
Idempotent: luôn khởi tạo từ lõi curated rồi gen lại -> chạy nhiều lần ra cùng kết quả (seed cố định).
"""
import json
import random
from pathlib import Path

SEED = 42
N_EXTRA_COURSES = 15      # -> tổng ~30 môn
N_EXTRA_STUDENTS = 88     # -> tổng ~100 SV
DATA = Path(__file__).parent

# ---- Pools tên tiếng Việt (tổ hợp) ----
HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
      "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đinh", "Tô", "Trương"]
DEM = ["Văn", "Thị", "Hữu", "Đức", "Minh", "Quang", "Thanh", "Thu", "Ngọc", "Gia",
       "Hoài", "Khánh", "Bảo", "Nhật", "Tuấn", "Hồng", "Phương", "Hải", "Xuân", "Kim"]
TEN = ["An", "Bình", "Chi", "Dung", "Giang", "Hùng", "Lan", "Minh", "Nga", "Phú",
       "Quỳnh", "Sơn", "Trang", "Uyên", "Việt", "Yến", "Khoa", "Linh", "Mai", "Nam",
       "Oanh", "Phong", "Quân", "Tâm", "Thảo", "Vy", "Đạt", "Hà", "Long", "Tú",
       "Bách", "Diệu", "Hiếu", "Kiên", "Loan", "Ngân", "Phước", "Trâm", "Vinh", "Ý"]

DEPTS = ["SE", "DS", "IS", "CYB", "HCI", "SEC", "CLD", "EMB"]
COURSE_NAMES = [
    "Kỹ thuật Phần mềm", "Khoa học Dữ liệu", "Hệ thống Thông tin", "An toàn Thông tin",
    "Tương tác Người-Máy", "Điện toán Đám mây", "Hệ nhúng", "Phân tích Dữ liệu",
    "Lập trình Web", "Lập trình Di động", "Trí tuệ Nhân tạo", "Đồ họa Máy tính",
    "Kiểm thử Phần mềm", "Quản trị Dự án CNTT", "Khai phá Dữ liệu", "Tối ưu hóa",
    "Mật mã học", "Blockchain", "Internet vạn vật", "Thị giác Robot",
]


def load(name):
    return json.load(open(DATA / name, encoding="utf-8"))


# ---- Lõi curated (neo cho test_cases.json) — whitelist để generator idempotent ----
CORE_COURSE_IDS = {
    "CS101", "CS102", "MATH201", "MATH202", "DB201", "STAT201", "OS301", "NET301",
    "ML301", "NLP302", "CV302", "AI401", "BIGDATA401", "RL402", "MLOPS403",
}
courses = {cid: c for cid, c in load("courses.json").items() if cid in CORE_COURSE_IDS}
# Chỉ giữ 12 SV curated SV001..SV012 làm lõi, phần còn lại gen mới
students = {sid: s for sid, s in load("students.json").items() if sid.startswith("SV0")}

rng = random.Random(SEED)


def course_level(cid, c):
    """Bậc môn = max bậc tiên quyết + 1 (môn không tiên quyết = bậc 1)."""
    if not c["prereq"]:
        return 1
    return 1 + max(course_level(p, courses[p]) for p in c["prereq"] if p in courses)


# ---- Gen thêm môn (prereq chỉ chọn từ môn bậc thấp hơn -> DAG) ----
used_names = set()
for i in range(N_EXTRA_COURSES):
    dept = rng.choice(DEPTS)
    level = rng.choice([1, 2, 2, 3, 3, 4])
    cid = f"{dept}{level}{rng.randint(10, 99)}"
    while cid in courses:
        cid = f"{dept}{level}{rng.randint(10, 99)}"
    # tiên quyết: chọn từ các môn có bậc thấp hơn
    lower = [k for k, v in courses.items() if course_level(k, v) < level]
    n_pre = 0 if level == 1 else rng.choice([0, 1, 1, 2])
    prereq = rng.sample(lower, min(n_pre, len(lower))) if lower else []
    name = rng.choice(COURSE_NAMES)
    while name in used_names:
        name = rng.choice(COURSE_NAMES) + f" {rng.choice(['cơ bản', 'nâng cao', 'ứng dụng'])}"
    used_names.add(name)
    courses[cid] = {
        "name": name,
        "credits": rng.choice([2, 3, 3, 4]),
        "prereq": prereq,
        "fee_per_credit": rng.choice([1000000, 1100000, 1200000, 1400000, 1600000, 1800000, 2000000, 2200000]),
        "exam_date": f"2026-07-{rng.randint(4, 28):02d}",
    }

all_cids = list(courses.keys())


def build_passed(target):
    """Chọn tập môn đã qua tôn trọng tiên quyết (chỉ thêm môn khi đã qua đủ prereq)."""
    passed = []
    for _ in range(target * 3):
        if len(passed) >= target:
            break
        avail = [c for c in all_cids if c not in passed
                 and all(p in passed for p in courses[c]["prereq"])]
        if not avail:
            break
        passed.append(rng.choice(avail))
    return passed


def gen_id(existing):
    """Mã SV ngẫu nhiên kiểu khóa-mã, ví dụ B22DCCN137."""
    while True:
        sid = f"B{rng.randint(20, 25)}DC{rng.choice(['CN', 'PT', 'AT', 'DT'])}{rng.randint(100, 999)}"
        if sid not in existing and sid not in students:
            return sid


seen_names = set()
for _ in range(N_EXTRA_STUDENTS):
    target = rng.choice([0, 1, 2, 3, 4, 5, 6, 6, 8, 8, 10, 12])
    passed = build_passed(target)
    credits = sum(courses[c]["credits"] for c in passed)
    # GPA: lệch về khá-giỏi nhưng vẫn có ca cảnh báo học vụ
    gpa = round(rng.choices(
        [rng.uniform(1.0, 2.0), rng.uniform(2.0, 3.0), rng.uniform(3.0, 4.0)],
        weights=[1, 4, 5])[0], 2) if passed else 0.0
    unlocked = [c for c in all_cids if c not in passed
                and all(p in passed for p in courses[c]["prereq"])]
    enrolled = rng.sample(unlocked, min(rng.choice([0, 1, 1, 2]), len(unlocked)))
    name = f"{rng.choice(HO)} {rng.choice(DEM)} {rng.choice(TEN)}"
    sid = gen_id(seen_names)
    seen_names.add(sid)
    students[sid] = {
        "name": name,
        "gpa": gpa,
        "credits_completed": credits,
        "passed": passed,
        "enrolled": enrolled,
    }

json.dump(courses, open(DATA / "courses.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
json.dump(students, open(DATA / "students.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print(f"Da ghi: {len(students)} sinh vien, {len(courses)} mon.")
print("Loi curated giu nguyen: SV001..SV012 + 15 mon neo (CS101..MLOPS403).")
