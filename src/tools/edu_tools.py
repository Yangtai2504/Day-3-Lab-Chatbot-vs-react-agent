# Mock dataset — Trợ lý Tư vấn Đăng ký môn học
# P2 owns this file. P5 uses the data for test_cases.py.

# ── STUDENTS ──────────────────────────────────────────────────────────────────
_STUDENTS = {
    # ---- Năm 1 ----
    "SV001": {
        "name": "Nguyễn Văn An",
        "year": 2,
        "major": "Công nghệ thông tin",
        "gpa": 3.2,
        "passed": ["CS101", "MATH101", "MATH201"],
        "scholarship_percent": 0,
        "email": "an.sv001@university.edu.vn",
    },
    "SV002": {
        "name": "Trần Thị Bình",
        "year": 1,
        "major": "Khoa học dữ liệu",
        "gpa": 1.8,
        "passed": ["CS101"],
        "scholarship_percent": 0,
        "email": "binh.sv002@university.edu.vn",
    },
    "SV003": {
        "name": "Lê Minh Cường",
        "year": 1,
        "major": "Công nghệ thông tin",
        "gpa": 2.5,
        "passed": ["CS101", "MATH101", "ENG101"],
        "scholarship_percent": 10,
        "email": "cuong.sv003@university.edu.vn",
    },
    # ---- Năm 2 ----
    "SV004": {
        "name": "Phạm Thị Dung",
        "year": 2,
        "major": "Hệ thống thông tin",
        "gpa": 3.7,
        "passed": ["CS101", "MATH101", "MATH201", "DB201", "ENG101"],
        "scholarship_percent": 20,
        "email": "dung.sv004@university.edu.vn",
    },
    "SV005": {
        "name": "Hoàng Văn Em",
        "year": 2,
        "major": "Công nghệ thông tin",
        "gpa": 2.1,
        "passed": ["CS101", "MATH101"],
        "scholarship_percent": 0,
        "email": "em.sv005@university.edu.vn",
    },
    "SV006": {
        "name": "Ngô Thị Phương",
        "year": 2,
        "major": "Khoa học dữ liệu",
        "gpa": 3.5,
        "passed": ["CS101", "MATH101", "MATH201", "STAT201", "ENG101"],
        "scholarship_percent": 15,
        "email": "phuong.sv006@university.edu.vn",
    },
    # ---- Năm 3 ----
    "SV007": {
        "name": "Đinh Quang Giang",
        "year": 3,
        "major": "Trí tuệ nhân tạo",
        "gpa": 3.9,
        "passed": ["CS101", "MATH101", "MATH201", "DB201", "ML301", "STAT201", "ENG101", "ENG201"],
        "scholarship_percent": 30,
        "email": "giang.sv007@university.edu.vn",
    },
    "SV008": {
        "name": "Vũ Thị Hà",
        "year": 3,
        "major": "Công nghệ thông tin",
        "gpa": 2.8,
        "passed": ["CS101", "MATH101", "DB201", "ENG101"],
        "scholarship_percent": 0,
        "email": "ha.sv008@university.edu.vn",
    },
    "SV009": {
        "name": "Bùi Văn Hùng",
        "year": 3,
        "major": "Hệ thống thông tin",
        "gpa": 1.5,
        "passed": ["CS101", "ENG101"],
        "scholarship_percent": 0,
        "email": "hung.sv009@university.edu.vn",
    },
    # ---- Năm 4 ----
    "SV010": {
        "name": "Đỗ Thị Lan",
        "year": 4,
        "major": "Khoa học dữ liệu",
        "gpa": 3.6,
        "passed": ["CS101", "MATH101", "MATH201", "STAT201", "DB201", "ML301", "DL401", "ENG101", "ENG201"],
        "scholarship_percent": 25,
        "email": "lan.sv010@university.edu.vn",
    },
    "SV011": {
        "name": "Trịnh Văn Minh",
        "year": 4,
        "major": "Công nghệ thông tin",
        "gpa": 2.0,
        "passed": ["CS101", "MATH101", "ENG101"],
        "scholarship_percent": 0,
        "email": "minh.sv011@university.edu.vn",
    },
    "SV012": {
        "name": "Lý Thị Ngọc",
        "year": 4,
        "major": "Trí tuệ nhân tạo",
        "gpa": 3.4,
        "passed": ["CS101", "MATH101", "MATH201", "ML301", "STAT201", "DL401", "ENG101", "ENG201", "NLP401"],
        "scholarship_percent": 20,
        "email": "ngoc.sv012@university.edu.vn",
    },
    # ---- Edge cases ----
    "SV013": {
        "name": "Phan Đình Ổn",
        "year": 2,
        "major": "Công nghệ thông tin",
        "gpa": 2.0,      # đúng ngưỡng cảnh báo học vụ
        "passed": ["CS101", "MATH101"],
        "scholarship_percent": 0,
        "email": "on.sv013@university.edu.vn",
    },
    "SV014": {
        "name": "Cao Thị Quỳnh",
        "year": 1,
        "major": "Khoa học dữ liệu",
        "gpa": 4.0,      # GPA hoàn hảo
        "passed": ["CS101", "MATH101", "MATH201", "STAT201"],
        "scholarship_percent": 50,
        "email": "quynh.sv014@university.edu.vn",
    },
    "SV015": {
        "name": "Tống Văn Rồng",
        "year": 3,
        "major": "Hệ thống thông tin",
        "gpa": 3.1,
        "passed": ["CS101", "MATH101", "DB201", "NET301", "ENG101"],
        "scholarship_percent": 10,
        "email": "rong.sv015@university.edu.vn",
    },
}

# ── COURSES ───────────────────────────────────────────────────────────────────
_COURSES = {
    # ---- Đại cương ----
    "CS101": {
        "name": "Nhập môn Lập trình",
        "department": "Cơ sở",
        "credits": 3,
        "prereq": [],
        "fee_per_credit": 900_000,
        "description": "Python cơ bản, tư duy thuật toán.",
    },
    "MATH101": {
        "name": "Đại số tuyến tính",
        "department": "Cơ sở",
        "credits": 3,
        "prereq": [],
        "fee_per_credit": 900_000,
        "description": "Ma trận, vector, không gian tuyến tính.",
    },
    "MATH201": {
        "name": "Giải tích & Xác suất",
        "department": "Cơ sở",
        "credits": 3,
        "prereq": ["MATH101"],
        "fee_per_credit": 1_000_000,
        "description": "Giải tích nhiều biến, phân phối xác suất.",
    },
    "ENG101": {
        "name": "Tiếng Anh cơ bản",
        "department": "Ngôn ngữ",
        "credits": 2,
        "prereq": [],
        "fee_per_credit": 800_000,
        "description": "Ngữ pháp và giao tiếp cơ bản.",
    },
    "ENG201": {
        "name": "Tiếng Anh kỹ thuật",
        "department": "Ngôn ngữ",
        "credits": 2,
        "prereq": ["ENG101"],
        "fee_per_credit": 900_000,
        "description": "Đọc tài liệu kỹ thuật và viết báo cáo.",
    },
    # ---- Chuyên ngành năm 2 ----
    "DB201": {
        "name": "Cơ sở dữ liệu",
        "department": "Công nghệ thông tin",
        "credits": 3,
        "prereq": ["CS101"],
        "fee_per_credit": 1_200_000,
        "description": "SQL, thiết kế CSDL quan hệ.",
    },
    "STAT201": {
        "name": "Thống kê ứng dụng",
        "department": "Khoa học dữ liệu",
        "credits": 3,
        "prereq": ["MATH101"],
        "fee_per_credit": 1_100_000,
        "description": "Thống kê mô tả, kiểm định giả thuyết.",
    },
    "NET301": {
        "name": "Mạng máy tính",
        "department": "Công nghệ thông tin",
        "credits": 3,
        "prereq": ["CS101"],
        "fee_per_credit": 1_200_000,
        "description": "TCP/IP, routing, bảo mật mạng cơ bản.",
    },
    # ---- Chuyên sâu năm 3 ----
    "ML301": {
        "name": "Machine Learning",
        "department": "Trí tuệ nhân tạo",
        "credits": 3,
        "prereq": ["CS101", "MATH201"],
        "fee_per_credit": 1_500_000,
        "description": "Supervised/unsupervised learning, scikit-learn.",
    },
    "CV301": {
        "name": "Thị giác máy tính",
        "department": "Trí tuệ nhân tạo",
        "credits": 3,
        "prereq": ["CS101", "MATH201", "ML301"],
        "fee_per_credit": 1_600_000,
        "description": "OpenCV, CNN cơ bản, nhận dạng ảnh.",
    },
    "SE301": {
        "name": "Kỹ thuật phần mềm",
        "department": "Công nghệ thông tin",
        "credits": 3,
        "prereq": ["CS101", "DB201"],
        "fee_per_credit": 1_300_000,
        "description": "Agile, UML, kiểm thử phần mềm.",
    },
    # ---- Nâng cao năm 4 ----
    "DL401": {
        "name": "Deep Learning",
        "department": "Trí tuệ nhân tạo",
        "credits": 4,
        "prereq": ["ML301", "MATH201"],
        "fee_per_credit": 1_800_000,
        "description": "PyTorch, CNN, RNN, Transformer.",
    },
    "NLP401": {
        "name": "Xử lý ngôn ngữ tự nhiên",
        "department": "Trí tuệ nhân tạo",
        "credits": 4,
        "prereq": ["ML301", "DL401"],
        "fee_per_credit": 1_800_000,
        "description": "BERT, fine-tuning LLM, RAG.",
    },
    "CAPSTONE": {
        "name": "Đồ án tốt nghiệp",
        "department": "Tất cả",
        "credits": 6,
        "prereq": ["DB201", "ML301"],
        "fee_per_credit": 500_000,
        "description": "Dự án thực tế cuối khóa.",
    },
}

# ── SCHOLARSHIP TIERS ─────────────────────────────────────────────────────────
_SCHOLARSHIP_TIERS = [
    {"min_gpa": 3.6, "label": "Xuất sắc",  "percent": 30},
    {"min_gpa": 3.2, "label": "Giỏi",       "percent": 20},
    {"min_gpa": 2.8, "label": "Khá",        "percent": 10},
    {"min_gpa": 0.0, "label": "Không có",   "percent": 0},
]


# ── TOOL FUNCTIONS ─────────────────────────────────────────────────────────────

def get_student_record(student_id: str) -> str:
    """Tra hồ sơ sinh viên: GPA, năm học, ngành, môn đã qua."""
    s = _STUDENTS.get(student_id.strip().upper())
    if not s:
        return f"ERROR: Không tìm thấy sinh viên '{student_id}'. ID hợp lệ: {list(_STUDENTS.keys())}"
    return (
        f"SV {student_id} — {s['name']} | Năm {s['year']} | Ngành: {s['major']} | "
        f"GPA: {s['gpa']} | Đã học: {s['passed']} | "
        f"Học bổng hiện tại: {s['scholarship_percent']}%"
    )


def check_prerequisite(course_id: str) -> str:
    """Tra môn tiên quyết của 1 môn học."""
    c = _COURSES.get(course_id.strip().upper())
    if not c:
        return f"ERROR: Không tìm thấy môn '{course_id}'. Mã hợp lệ: {list(_COURSES.keys())}"
    if not c["prereq"]:
        return f"Môn {course_id} ({c['name']}) không có tiên quyết — đăng ký được ngay."
    return f"Môn {course_id} ({c['name']}) yêu cầu tiên quyết: {c['prereq']}"


def check_eligibility(student_id: str, course_id: str) -> str:
    """Kiểm tra sinh viên có đủ điều kiện học môn không (so sánh tiên quyết vs môn đã qua)."""
    s = _STUDENTS.get(student_id.strip().upper())
    c = _COURSES.get(course_id.strip().upper())
    if not s:
        return f"ERROR: Không tìm thấy sinh viên '{student_id}'"
    if not c:
        return f"ERROR: Không tìm thấy môn '{course_id}'"
    missing = [p for p in c["prereq"] if p not in s["passed"]]
    if not missing:
        return f"SV {student_id} ({s['name']}) ĐỦ điều kiện học {course_id} ({c['name']})."
    return (
        f"SV {student_id} ({s['name']}) CHƯA đủ điều kiện học {course_id}. "
        f"Thiếu môn tiên quyết: {missing}"
    )


def calculate_tuition(course_id: str, credits: str) -> str:
    """Tính học phí theo số tín chỉ đăng ký."""
    c = _COURSES.get(course_id.strip().upper())
    if not c:
        return f"ERROR: Không tìm thấy môn '{course_id}'"
    try:
        cr = int(str(credits).strip())
    except ValueError:
        return f"ERROR: Số tín chỉ không hợp lệ '{credits}'"
    total = c["fee_per_credit"] * cr
    return f"Học phí {course_id} ({c['name']}) | {cr} tín chỉ × {c['fee_per_credit']:,} = {total:,} VND"


def apply_scholarship(amount: str, percent: str) -> str:
    """Trừ học bổng vào học phí. Args: amount (VND), percent (%)."""
    try:
        amt = float(str(amount).replace(",", "").replace("VND", "").replace(".", "").strip())
        pct = float(str(percent).replace("%", "").strip())
    except ValueError as e:
        return f"ERROR: Tham số không hợp lệ — {e}"
    discount = amt * pct / 100
    final = amt - discount
    return (
        f"Học phí gốc: {amt:,.0f} VND | "
        f"Học bổng {pct}%: -{discount:,.0f} VND | "
        f"Thực đóng: {final:,.0f} VND"
    )


def get_scholarship_rate(student_id: str) -> str:
    """Tra tỷ lệ học bổng hiện tại của sinh viên theo GPA."""
    s = _STUDENTS.get(student_id.strip().upper())
    if not s:
        return f"ERROR: Không tìm thấy sinh viên '{student_id}'"
    for tier in _SCHOLARSHIP_TIERS:
        if s["gpa"] >= tier["min_gpa"]:
            return (
                f"SV {student_id} ({s['name']}) | GPA {s['gpa']} → "
                f"Học bổng loại {tier['label']}: {tier['percent']}%"
            )
    return f"SV {student_id} không được hưởng học bổng."


def list_available_courses(department: str = "all") -> str:
    """Liệt kê các môn theo khoa/bộ môn. department='all' để xem tất cả."""
    dept = department.strip().lower()
    result = []
    for cid, c in _COURSES.items():
        if dept == "all" or dept in c["department"].lower():
            prereq_str = ", ".join(c["prereq"]) if c["prereq"] else "Không có"
            result.append(
                f"{cid}: {c['name']} | {c['credits']} tín chỉ | "
                f"Tiên quyết: {prereq_str} | Phí/TC: {c['fee_per_credit']:,} VND"
            )
    if not result:
        return f"Không tìm thấy môn nào thuộc khoa '{department}'."
    return "Danh sách môn học:\n" + "\n".join(result)


def check_academic_warning(student_id: str) -> str:
    """Kiểm tra sinh viên có bị cảnh báo học vụ không (GPA < 2.0)."""
    s = _STUDENTS.get(student_id.strip().upper())
    if not s:
        return f"ERROR: Không tìm thấy sinh viên '{student_id}'"
    if s["gpa"] < 2.0:
        status = "CẢNH BÁO HỌC VỤ"
        note = "Sinh viên cần cải thiện GPA trong học kỳ tới hoặc có thể bị buộc thôi học."
    elif s["gpa"] < 2.5:
        status = "Yếu — cần chú ý"
        note = "GPA dưới mức Trung bình khá. Nên tăng cường học tập."
    else:
        status = "Bình thường"
        note = "Không có cảnh báo học vụ."
    return f"SV {student_id} ({s['name']}) | GPA {s['gpa']} | Tình trạng: {status} | {note}"


# ── TOOL REGISTRY ──────────────────────────────────────────────────────────────
EDU_TOOLS = [
    {
        "name": "get_student_record",
        "description": (
            "Tra hồ sơ sinh viên theo student_id (VD: SV001). "
            "Trả về: tên, năm học, ngành, GPA, danh sách môn đã học, % học bổng hiện tại."
        ),
        "func": get_student_record,
    },
    {
        "name": "check_prerequisite",
        "description": (
            "Tra danh sách môn tiên quyết của 1 môn học theo course_id (VD: ML301). "
            "Trả về: tên môn và list tiên quyết (hoặc thông báo không có)."
        ),
        "func": check_prerequisite,
    },
    {
        "name": "check_eligibility",
        "description": (
            "Kiểm tra sinh viên có đủ điều kiện học 1 môn không. "
            "Args: student_id, course_id. "
            "Trả về: ĐỦ hoặc CHƯA ĐỦ + danh sách môn còn thiếu."
        ),
        "func": check_eligibility,
    },
    {
        "name": "calculate_tuition",
        "description": (
            "Tính học phí theo số tín chỉ đăng ký. "
            "Args: course_id, credits (số nguyên). "
            "Trả về: học phí tổng (VND)."
        ),
        "func": calculate_tuition,
    },
    {
        "name": "apply_scholarship",
        "description": (
            "Trừ học bổng vào học phí gốc. "
            "Args: amount (số VND, không có dấu phẩy), percent (% học bổng). "
            "Trả về: học phí gốc, số tiền giảm, học phí thực đóng."
        ),
        "func": apply_scholarship,
    },
    {
        "name": "get_scholarship_rate",
        "description": (
            "Tra tỷ lệ học bổng hiện tại của sinh viên dựa trên GPA. "
            "Args: student_id. "
            "Trả về: loại học bổng và % được hưởng."
        ),
        "func": get_scholarship_rate,
    },
    {
        "name": "list_available_courses",
        "description": (
            "Liệt kê các môn học theo khoa. "
            "Args: department ('all' để xem tất cả, hoặc tên khoa như 'Trí tuệ nhân tạo'). "
            "Trả về: danh sách môn với tín chỉ, tiên quyết và học phí."
        ),
        "func": list_available_courses,
    },
    {
        "name": "check_academic_warning",
        "description": (
            "Kiểm tra tình trạng học vụ của sinh viên (cảnh báo nếu GPA < 2.0). "
            "Args: student_id. "
            "Trả về: tình trạng học vụ và gợi ý cải thiện."
        ),
        "func": check_academic_warning,
    },
]
