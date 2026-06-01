"""
Tool giáo dục cho Kịch bản A — Trợ lý Đăng ký môn học.

Dữ liệu được nạp từ `data/*.json` (xem data/README.md), KHÔNG hard-code trong logic.
Mỗi tool nhận đối số dạng chuỗi (do parser của agent tách từ `Action: tool(a, b)`),
luôn trả về MỘT chuỗi để đưa vào `Observation:`. Lỗi trả chuỗi bắt đầu bằng "ERROR:"
để agent có thể tự sửa (self-correct) thay vì văng exception.
"""
import json
from pathlib import Path

# data/ nằm ở gốc project: src/tools/edu_tools.py -> parents[2] = root
_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_WARNING_GPA = 2.0  # GPA < ngưỡng này -> cảnh báo học vụ


def _load(name: str) -> dict:
    with open(_DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


# Nạp 1 lần khi import (data tĩnh trong phạm vi lab)
_STUDENTS = _load("students.json")
_COURSES = _load("courses.json")
_SCHOLARSHIPS = _load("scholarships.json")


# --------------------------------------------------------------------------- #
# 4 tool gốc
# --------------------------------------------------------------------------- #
def get_student_record(student_id: str) -> str:
    """Tra hồ sơ sinh viên theo student_id. Trả GPA + danh sách môn đã học."""
    sid = student_id.strip().upper()
    s = _STUDENTS.get(sid)
    if not s:
        return f"ERROR: Không tìm thấy sinh viên {student_id}"
    return (f"SV {sid} ({s['name']}): GPA={s['gpa']}, "
            f"tín chỉ tích lũy={s['credits_completed']}, "
            f"đã học={s['passed']}, đang học={s['enrolled']}")


def check_prerequisite(course_id: str) -> str:
    """Tra môn tiên quyết của một môn. Args: course_id."""
    cid = course_id.strip().upper()
    c = _COURSES.get(cid)
    if not c:
        return f"ERROR: Không tìm thấy môn {course_id}"
    if not c["prereq"]:
        return f"Môn {cid} ({c['name']}) KHÔNG yêu cầu tiên quyết."
    return f"Môn {cid} ({c['name']}) yêu cầu tiên quyết: {c['prereq']}"


def calculate_tuition(course_id: str, credits: str = None) -> str:
    """Tính học phí. Args: course_id, [credits]. Bỏ trống credits -> dùng tín chỉ chuẩn của môn."""
    cid = course_id.strip().upper()
    c = _COURSES.get(cid)
    if not c:
        return f"ERROR: Không tìm thấy môn {course_id}"
    try:
        n = int(float(credits)) if credits not in (None, "") else c["credits"]
    except (TypeError, ValueError):
        return f"ERROR: Số tín chỉ không hợp lệ: {credits}"
    total = c["fee_per_credit"] * n
    return f"Học phí {cid} ({n} tín chỉ x {c['fee_per_credit']:,}) = {total:,} VND"


def apply_scholarship(amount: str, percent: str) -> str:
    """Trừ học bổng theo %. Args: amount (VND), percent (0-100)."""
    try:
        amt = float(str(amount).replace(",", "").replace("VND", "").strip())
        pct = float(str(percent).replace("%", "").strip())
    except ValueError:
        return f"ERROR: Đối số không hợp lệ (amount={amount}, percent={percent})"
    final = amt * (1 - pct / 100)
    return f"Sau học bổng {pct:g}%: {final:,.0f} VND (gốc {amt:,.0f} VND)"


# --------------------------------------------------------------------------- #
# 2 bonus tool (Tool Design Evolution / +2 Extra Tools trong SCORING.md)
# --------------------------------------------------------------------------- #
def check_academic_warning(gpa: str) -> str:
    """Kiểm tra cảnh báo học vụ theo GPA. Args: gpa. Ngưỡng cảnh báo: GPA < 2.0."""
    try:
        g = float(str(gpa).strip())
    except ValueError:
        return f"ERROR: GPA không hợp lệ: {gpa}"
    if g < _WARNING_GPA:
        return f"CẢNH BÁO HỌC VỤ: GPA={g} < {_WARNING_GPA}. Sinh viên thuộc diện cảnh báo."
    return f"Bình thường: GPA={g} >= {_WARNING_GPA}, KHÔNG bị cảnh báo học vụ."


def get_exam_schedule(course_id: str) -> str:
    """Tra lịch thi của một môn. Args: course_id."""
    cid = course_id.strip().upper()
    c = _COURSES.get(cid)
    if not c:
        return f"ERROR: Không tìm thấy môn {course_id}"
    return f"Lịch thi môn {cid} ({c['name']}): {c['exam_date']}"


# --------------------------------------------------------------------------- #
# Registry — agent đọc list này (mỗi tool: name / description / func)
# --------------------------------------------------------------------------- #
EDU_TOOLS = [
    {"name": "get_student_record",
     "description": "Tra hồ sơ SV theo student_id. Trả GPA, tín chỉ tích lũy, môn đã học. Args: student_id.",
     "func": get_student_record},
    {"name": "check_prerequisite",
     "description": "Tra môn tiên quyết của 1 môn. Args: course_id.",
     "func": check_prerequisite},
    {"name": "calculate_tuition",
     "description": "Tính học phí. Args: course_id, credits (số nguyên).",
     "func": calculate_tuition},
    {"name": "apply_scholarship",
     "description": "Trừ học bổng theo phần trăm. Args: amount (VND), percent (0-100).",
     "func": apply_scholarship},
    {"name": "check_academic_warning",
     "description": "Kiểm tra cảnh báo học vụ. Args: gpa. Cảnh báo khi GPA < 2.0.",
     "func": check_academic_warning},
    {"name": "get_exam_schedule",
     "description": "Tra lịch thi của 1 môn. Args: course_id.",
     "func": get_exam_schedule},
]


if __name__ == "__main__":
    # Self-test nhanh trên test case vàng (TC05) — không cần LLM.
    print(check_prerequisite("ML301"))
    print(get_student_record("SV001"))
    print(calculate_tuition("ML301", "3"))
    print(apply_scholarship("4500000", "20"))
    print(check_academic_warning("1.8"))
    print(get_exam_schedule("DB201"))
    print(get_student_record("SV999"))  # ERROR path
