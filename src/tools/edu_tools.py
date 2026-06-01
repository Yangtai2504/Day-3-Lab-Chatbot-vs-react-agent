import json
from pathlib import Path
from typing import Dict, Any, List

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load_json(name: str) -> Dict[str, Any]:
    path = DATA_DIR / name
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


STUDENTS = _load_json("students.json")
COURSES = _load_json("courses.json")
SCHOLARSHIPS = _load_json("scholarships.json").get("policies", [])


def _normalize_id(value: str) -> str:
    return str(value).strip().upper()


def _parse_number(value: str) -> float:
    normalized = str(value).replace(",", "").replace("VND", "").replace("%", "").strip()
    return float(normalized)


def get_student_record(student_id: str) -> str:
    student_key = _normalize_id(student_id)
    student = STUDENTS.get(student_key)
    if not student:
        return f"ERROR: Không tìm thấy sinh viên {student_id}"

    passed = student.get("passed", [])
    return (
        f"SV {student_key} ({student['name']}): GPA={student['gpa']}, "
        f"đã học={passed}, tín chỉ đã tích lũy={student['credits_completed']}"
    )


def check_prerequisite(course_id: str) -> str:
    course_key = _normalize_id(course_id)
    course = COURSES.get(course_key)
    if not course:
        return f"ERROR: Không tìm thấy môn {course_id}"
    prereq = course.get("prereq", [])
    return f"Môn {course_key} ({course['name']}) yêu cầu tiên quyết: {prereq}"


def calculate_tuition(course_id: str, credits: str) -> str:
    course_key = _normalize_id(course_id)
    course = COURSES.get(course_key)
    if not course:
        return f"ERROR: Không tìm thấy môn {course_id}"

    try:
        credit_count = int(float(str(credits).strip()))
    except ValueError:
        return f"ERROR: credits phải là số nguyên, nhận được {credits}"

    total = course["fee_per_credit"] * credit_count
    return f"Học phí {course_key} ({credit_count} tín chỉ) = {total:,} VND"


def apply_scholarship(amount: str, percent_or_policy: str) -> str:
    try:
        original_amount = _parse_number(amount)
    except ValueError:
        return f"ERROR: Số tiền không hợp lệ: {amount}"

    policy_code = str(percent_or_policy).strip().upper()
    percent = None
    fixed_amount = 0

    if policy_code:
        for policy in SCHOLARSHIPS:
            if policy["code"] == policy_code:
                percent = policy.get("percent", 0)
                fixed_amount = policy.get("fixed_amount", 0)
                break

    if percent is None:
        try:
            percent = float(str(percent_or_policy).replace("%", "").strip())
        except ValueError:
            return f"ERROR: Học bổng không hợp lệ: {percent_or_policy}"

    final_amount = original_amount - fixed_amount - original_amount * (percent / 100)
    final_amount = max(final_amount, 0)
    return (
        f"Sau học bổng {percent}%" 
        f"{' + ' + str(fixed_amount) + ' VND' if fixed_amount else ''}: "
        f"{final_amount:,.0f} VND"
    )


def get_exam_schedule(course_id: str) -> str:
    course_key = _normalize_id(course_id)
    course = COURSES.get(course_key)
    if not course:
        return f"ERROR: Không tìm thấy môn {course_id}"
    return f"Lịch thi {course_key} ({course['name']}) là {course['exam_date']}"


def check_academic_warning(gpa_or_student_id: str) -> str:
    candidate = str(gpa_or_student_id).strip()
    student_key = _normalize_id(candidate)
    if student_key in STUDENTS:
        gpa = STUDENTS[student_key].get("gpa", 0.0)
    else:
        try:
            gpa = float(candidate)
        except ValueError:
            return f"ERROR: Không xác định được GPA hoặc mã sinh viên: {gpa_or_student_id}"

    if gpa < 2.0:
        return f"GPA {gpa} -> Cảnh báo học vụ."
    return f"GPA {gpa} -> Không bị cảnh báo học vụ."


def get_scholarship_rate(gpa_or_student_id: str) -> str:
    """Tra mức % học bổng merit theo MÃ SINH VIÊN (vd SV001) hoặc theo GPA (vd 3.2)."""
    candidate = str(gpa_or_student_id).strip()
    student_key = _normalize_id(candidate)

    if student_key in STUDENTS:
        gpa = STUDENTS[student_key].get("gpa", 0.0)
        who = f"SV {student_key} (GPA {gpa})"
    else:
        try:
            gpa = float(candidate)
        except ValueError:
            return f"ERROR: Không xác định được GPA hoặc mã sinh viên: {gpa_or_student_id}"
        who = f"GPA {gpa}"

    best = None
    for policy in SCHOLARSHIPS:
        if policy.get("percent", 0) > 0 and gpa >= policy.get("min_gpa", 0):
            if best is None or policy["percent"] > best["percent"]:
                best = policy

    if best is None:
        return f"{who} -> không đủ điều kiện học bổng merit: 0%"
    return f"{who} -> '{best['name']}' ({best['code']}): {best['percent']}%"


def list_available_courses(filter_text: str = "") -> str:
    """Liệt kê các môn học. filter_text rỗng/'all' = tất cả; còn lại lọc theo mã hoặc tên môn."""
    keyword = str(filter_text).strip().lower()
    show_all = keyword in ("", "all", "tất cả", "tat ca")

    items = []
    for course_id, course in COURSES.items():
        if not show_all and keyword not in course_id.lower() and keyword not in course["name"].lower():
            continue
        items.append(f"{course_id} ({course['name']}, {course['credits']} tín chỉ)")

    if not items:
        return f"Không có môn nào khớp với '{filter_text}'."
    return f"Có {len(items)} môn: " + "; ".join(items)


EDU_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_student_record",
        "description": "Tra hồ sơ sinh viên theo mã SV. Trả GPA, môn đã học và tín chỉ tích lũy.",
        "func": get_student_record,
    },
    {
        "name": "check_prerequisite",
        "description": "Kiểm tra danh sách môn tiên quyết của một môn.",
        "func": check_prerequisite,
    },
    {
        "name": "calculate_tuition",
        "description": "Tính học phí dựa trên mã môn và số tín chỉ.",
        "func": calculate_tuition,
    },
    {
        "name": "apply_scholarship",
        "description": "Áp dụng học bổng theo phần trăm hoặc mã học bổng trên một số tiền.",
        "func": apply_scholarship,
    },
    {
        "name": "get_exam_schedule",
        "description": "Tra lịch thi của một môn học.",
        "func": get_exam_schedule,
    },
    {
        "name": "check_academic_warning",
        "description": "Kiểm tra cảnh báo học vụ theo GPA hoặc mã sinh viên.",
        "func": check_academic_warning,
    },
    {
        "name": "get_scholarship_rate",
        "description": "Tra mức % học bổng theo MÃ SINH VIÊN (vd SV001) hoặc theo GPA (vd 3.2).",
        "func": get_scholarship_rate,
    },
    {
        "name": "list_available_courses",
        "description": "Liệt kê các môn học; có thể lọc theo mã hoặc tên môn ('all' = tất cả).",
        "func": list_available_courses,
    },
]
