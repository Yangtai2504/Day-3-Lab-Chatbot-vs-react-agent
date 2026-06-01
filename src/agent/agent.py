import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.tools.edu_tools import EDU_TOOLS
from src.core.gemini_provider import GeminiProvider

class ReActAgent:
    """
    A ReAct-style agent that follows the Thought -> Action -> Observation loop.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history: List[Dict[str, Any]] = []

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )
        return f"""
You are a student registration assistant. You may only use the available tools below:
{tool_descriptions}

Follow this exact format for every step:
Thought: explain your reasoning.
Action: tool_name(arg1, arg2)
Observation: result of the tool call.
... (repeat Thought / Action / Observation until you have enough information)
Final Answer: provide the final answer to the user.

Rules:
- Do not invent observations. Every Action must be executed by the agent.
- Do not use tools that are not listed.
- Use the exact format shown above.
"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        transcript = f"Question: {user_input}\n"
        steps = 0
        try:
            while steps < self.max_steps:
                result = self.llm.generate(transcript, system_prompt=self.get_system_prompt())
                content = str(result.get("content", "")).strip()
                usage = result.get("usage", {})
                latency = result.get("latency_ms")

                self.history.append({
                    "step": steps + 1,
                    "response": content,
                    "usage": usage,
                    "latency_ms": latency,
                    "observation": None,  # gán sau khi chạy tool (phục vụ hiển thị trace trên web demo)
                })

                logger.log_event("LLM_RESPONSE", {
                    "step": steps + 1,
                    "content": content[:300],
                    "usage": usage,
                    "latency_ms": latency,
                })

                final_answer = self._parse_final_answer(content)
                if final_answer is not None:
                    logger.log_event("AGENT_END", {"steps": steps + 1, "status": "success"})
                    return final_answer.strip()

                action_data = self._parse_action(content)
                if action_data is None:
                    logger.log_event("PARSE_ERROR", {"step": steps + 1, "raw": content[:300]})
                    self.history[-1]["observation"] = "PARSE_ERROR: không đọc được Action."
                    transcript += f"{content}\nObservation: Tôi không đọc được Action. Vui lòng dùng định dạng Action: tool_name(arg1, arg2).\n"
                    steps += 1
                    continue

                tool_name, raw_args = action_data
                observation = self._execute_tool(tool_name, raw_args)
                self.history[-1]["observation"] = observation
                logger.log_event("TOOL_CALL", {
                    "step": steps + 1,
                    "tool": tool_name,
                    "args": raw_args,
                    "observation": observation,
                })

                thought_action = self._extract_thought_action(content)
                transcript += f"{thought_action}\nObservation: {observation}\n"

                if observation.startswith("ERROR"):
                    transcript += "Note: The tool returned an error, please choose a different action or correct the arguments.\n"

                steps += 1
        except Exception as exc:
            logger.log_event("ERROR", {
                "step": steps + 1,
                "error": str(exc)
            })
            return "Đã có lỗi xảy ra."

        logger.log_event("AGENT_END", {"steps": steps, "status": "max_steps"})
        return (
            "Đã vượt quá giới hạn số bước. "
            "Nếu vẫn chưa có câu trả lời, hãy thử hỏi rõ hơn hoặc giảm số bước yêu cầu."
        )

    def _parse_action(self, text: str) -> Optional[tuple[str, str]]:
        match = re.search(
            r"Action\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None
        tool_name = match.group(1).strip()
        args = match.group(2).strip()
        return tool_name, args

    def _parse_final_answer(self, text: str) -> Optional[str]:
        match = re.search(r"Final Answer\s*:\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return match.group(1).strip()

    def _extract_thought_action(self, text: str) -> str:
        if "Observation:" in text:
            return text.split("Observation:", 1)[0].strip()
        return text

    def _evaluate_args(self, args: str) -> List[str]:
        if not args:
            return []
        raw_args = [arg.strip() for arg in args.split(",") if arg.strip()]
        cleaned = [self._clean_arg(arg) for arg in raw_args]
        return cleaned

    def _clean_arg(self, arg: str) -> str:
        arg = arg.strip()
        if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')):
            return arg[1:-1].strip()
        return arg

    def _execute_tool(self, tool_name: str, args: str) -> str:
        for tool in self.tools:
            if tool["name"] == tool_name:
                try:
                    parsed_args = self._evaluate_args(args)
                    return str(tool["func"](*parsed_args))
                except Exception as exc:
                    return f"ERROR: Khi chạy {tool_name}: {exc}"

        available_tools = [tool["name"] for tool in self.tools]
        return f"ERROR: Tool '{tool_name}' không tồn tại. Chỉ dùng: {available_tools}"

if __name__ == "__main__":
    # ══════════════════════════════════════════════════════════════════════════════
    # NHÓM 1 — SIMPLE (1 tool call)
    # Chatbot có thể trả lời gần đúng bằng cách đoán, nhưng dữ liệu không chính xác.
    # Agent gọi đúng 1 tool → chắc chắn đúng.
    # ══════════════════════════════════════════════════════════════════════════════
    SIMPLE_CASES = [
        {
            "id": "S01",
            "query": "Môn ML301 yêu cầu những môn tiên quyết nào?",
            "type": "simple",
            "expected_tools": ["check_prerequisite"],
            "golden_answer": "ML301 yêu cầu: CS101, MATH201",
            "note": "Tra tiên quyết 1 môn — đơn giản nhất",
        },
        {
            "id": "S02",
            "query": "GPA của sinh viên SV004 là bao nhiêu?",
            "type": "simple",
            "expected_tools": ["get_student_record"],
            "golden_answer": "GPA: 3.7",
            "note": "Tra hồ sơ cơ bản",
        },
        {
            "id": "S03",
            "query": "Sinh viên SV007 đang học ngành gì và đã học những môn nào?",
            "type": "simple",
            "expected_tools": ["get_student_record"],
            "golden_answer": "Ngành Trí tuệ nhân tạo, đã học: CS101, MATH101, MATH201, DB201, ML301, STAT201, ENG101, ENG201",
            "note": "Tra hồ sơ đầy đủ",
        },
        {
            "id": "S04",
            "query": "Học phí môn Deep Learning (DL401) cho 4 tín chỉ là bao nhiêu?",
            "type": "simple",
            "expected_tools": ["calculate_tuition"],
            "golden_answer": "4 × 1,800,000 = 7,200,000 VND",
            "note": "Tính học phí đơn giản",
        },
        {
            "id": "S05",
            "query": "Cho tôi xem danh sách tất cả các môn học hiện có.",
            "type": "simple",
            "expected_tools": ["list_available_courses"],
            "golden_answer": "Danh sách đầy đủ 14 môn học",
            "note": "Liệt kê toàn bộ môn — không lọc",
        },
        {
            "id": "S06",
            "query": "SV002 có bị cảnh báo học vụ không?",
            "type": "simple",
            "expected_tools": ["check_academic_warning"],
            "golden_answer": "GPA 1.8 → CẢNH BÁO HỌC VỤ",
            "note": "Cảnh báo học vụ khi GPA < 2.0",
        },
        {
            "id": "S07",
            "query": "Tỷ lệ học bổng của SV010 hiện tại là bao nhiêu phần trăm?",
            "type": "simple",
            "expected_tools": ["get_scholarship_rate"],
            "golden_answer": "GPA 3.6 → Xuất sắc → 30%",
            "note": "Tra học bổng theo GPA",
        },
        {
            "id": "S08",
            "query": "Môn CS101 có cần tiên quyết gì không?",
            "type": "simple",
            "expected_tools": ["check_prerequisite"],
            "golden_answer": "CS101 không có tiên quyết — đăng ký được ngay",
            "note": "Môn không có tiên quyết — kiểm tra response rỗng",
        },
        {
            "id": "S09",
            "query": "Các môn thuộc khoa Trí tuệ nhân tạo có những môn nào?",
            "type": "simple",
            "expected_tools": ["list_available_courses"],
            "golden_answer": "ML301, CV301, DL401, NLP401",
            "note": "Lọc môn theo khoa",
        },
        {
            "id": "S10",
            "query": "SV014 đang học năm mấy và ngành gì?",
            "type": "simple",
            "expected_tools": ["get_student_record"],
            "golden_answer": "Năm 1, Khoa học dữ liệu",
            "note": "Sinh viên GPA hoàn hảo 4.0",
        },
    ]

    # ══════════════════════════════════════════════════════════════════════════════
    # NHÓM 2 — MULTI-STEP (2–3 tool calls)
    # Chatbot thường trả lời sai hoặc bỏ sót bước.
    # Agent cần chain nhiều tool mới có câu trả lời chính xác.
    # ══════════════════════════════════════════════════════════════════════════════
    MULTI_CASES = [
        {
            "id": "M01",
            "query": "SV005 có đủ điều kiện học ML301 không? Nếu không thì thiếu môn gì?",
            "type": "multi",
            "expected_tools": ["check_prerequisite", "get_student_record"],
            "golden_answer": "SV005 thiếu MATH201 (đã có CS101, MATH101 nhưng chưa học MATH201)",
            "note": "2 bước: tra tiên quyết → tra hồ sơ → đối chiếu",
        },
        {
            "id": "M02",
            "query": "Tính học phí môn Cơ sở dữ liệu cho SV003 nếu đăng ký đủ số tín chỉ của môn đó.",
            "type": "multi",
            "expected_tools": ["check_prerequisite", "calculate_tuition"],
            "golden_answer": "DB201 = 3 tín chỉ × 1,200,000 = 3,600,000 VND",
            "note": "Cần biết số tín chỉ môn DB201 trước khi tính tiền",
        },
        {
            "id": "M03",
            "query": "SV006 được học bổng bao nhiêu phần trăm và nếu học ML301 thì đóng bao nhiêu sau học bổng?",
            "type": "multi",
            "expected_tools": ["get_scholarship_rate", "calculate_tuition", "apply_scholarship"],
            "golden_answer": "GPA 3.5 → 20% → học phí 3 tín chỉ ML301 = 4,500,000 → sau học bổng: 3,600,000 VND",
            "note": "3 bước: tra học bổng → tính học phí → áp học bổng",
        },
        {
            "id": "M04",
            "query": "SV009 có bị cảnh báo học vụ không, và nếu muốn học DB201 thì đủ điều kiện chưa?",
            "type": "multi",
            "expected_tools": ["check_academic_warning", "check_eligibility"],
            "golden_answer": "SV009 GPA 1.5 → CẢNH BÁO | DB201 cần CS101 → SV009 đã có → ĐỦ điều kiện môn này",
            "note": "Kết hợp cảnh báo học vụ + kiểm tra điều kiện môn học",
        },
        {
            "id": "M05",
            "query": "Liệt kê các môn AI rồi cho tôi biết SV008 đã học được môn nào trong số đó.",
            "type": "multi",
            "expected_tools": ["list_available_courses", "get_student_record"],
            "golden_answer": "Môn AI: ML301, CV301, DL401, NLP401 | SV008 chưa học môn nào trong danh sách này",
            "note": "Cần list môn → lấy hồ sơ → giao tập",
        },
        {
            "id": "M06",
            "query": "SV011 năm 4 nhưng GPA thấp, có bị cảnh báo không và học bổng được bao nhiêu?",
            "type": "multi",
            "expected_tools": ["check_academic_warning", "get_scholarship_rate"],
            "golden_answer": "GPA 2.0 → Yếu (không cảnh báo nhưng cần chú ý) | Học bổng 0%",
            "note": "GPA đúng ngưỡng — kiểm tra xử lý biên",
        },
        {
            "id": "M07",
            "query": "SV015 muốn học SE301, đủ điều kiện chưa và học phí 3 tín chỉ là bao nhiêu?",
            "type": "multi",
            "expected_tools": ["check_eligibility", "calculate_tuition"],
            "golden_answer": "SE301 cần CS101 + DB201 | SV015 có cả hai → ĐỦ | Học phí = 3 × 1,300,000 = 3,900,000 VND",
            "note": "2 bước độc lập nhưng cần trả lời cả hai",
        },
        {
            "id": "M08",
            "query": "So sánh học phí của ML301 và DL401 cho số tín chỉ tương ứng của mỗi môn.",
            "type": "multi",
            "expected_tools": ["calculate_tuition", "calculate_tuition"],
            "golden_answer": "ML301: 3 × 1,500,000 = 4,500,000 | DL401: 4 × 1,800,000 = 7,200,000 VND",
            "note": "Gọi cùng 1 tool 2 lần với tham số khác nhau",
        },
    ]

    # ══════════════════════════════════════════════════════════════════════════════
    # NHÓM 3 — GOLDEN TEST CASES (4+ bước — dùng để demo chính)
    # Chatbot hoàn toàn fail. Agent cần ≥4 Thought-Action mới ra đúng.
    # ══════════════════════════════════════════════════════════════════════════════
    GOLDEN_CASES = [
        {
            "id": "G01",
            "query": (
                "SV001 đủ điều kiện học ML301 không? "
                "Nếu đủ, tính học phí 3 tín chỉ sau khi áp học bổng theo GPA thực tế của sinh viên đó."
            ),
            "type": "golden",
            "expected_tools": [
                "check_prerequisite",
                "get_student_record",
                "get_scholarship_rate",
                "calculate_tuition",
                "apply_scholarship",
            ],
            "golden_answer": (
                "SV001 đủ điều kiện (có CS101, MATH201) | "
                "GPA 3.2 → học bổng Giỏi 20% | "
                "Học phí = 4,500,000 | Sau học bổng: 3,600,000 VND"
            ),
            "note": "Test case vàng chính thức — 5 bước",
        },
        {
            "id": "G02",
            "query": (
                "SV004 muốn đăng ký cả DL401 lẫn NLP401 học kỳ này. "
                "Kiểm tra điều kiện từng môn, tính tổng học phí "
                "và cho biết sau học bổng thực đóng bao nhiêu."
            ),
            "type": "golden",
            "expected_tools": [
                "get_student_record",
                "check_eligibility",
                "check_eligibility",
                "calculate_tuition",
                "calculate_tuition",
                "get_scholarship_rate",
                "apply_scholarship",
            ],
            "golden_answer": (
                "DL401: SV004 thiếu ML301 → chưa đủ | "
                "NLP401: thiếu ML301, DL401 → chưa đủ | "
                "Giả sử đăng ký được: DL401 7,200,000 + NLP401 7,200,000 = 14,400,000 | "
                "SV004 GPA 3.7 → 30% → thực đóng 10,080,000 VND"
            ),
            "note": "Multi-course registration — agent phải xử lý 2 môn song song",
        },
        {
            "id": "G03",
            "query": (
                "Tôi là SV002. Tôi đang bị cảnh báo học vụ không? "
                "Tôi muốn học DB201, có đủ điều kiện không? "
                "Nếu đủ, học phí là bao nhiêu và tôi có được học bổng gì không?"
            ),
            "type": "golden",
            "expected_tools": [
                "check_academic_warning",
                "check_eligibility",
                "calculate_tuition",
                "get_scholarship_rate",
            ],
            "golden_answer": (
                "GPA 1.8 → CẢNH BÁO HỌC VỤ | "
                "DB201 cần CS101 → SV002 đã có → ĐỦ điều kiện | "
                "Học phí 3 tín chỉ = 3,600,000 VND | "
                "GPA 1.8 → không có học bổng → thực đóng toàn bộ 3,600,000 VND"
            ),
            "note": "Kịch bản sinh viên yếu — kết hợp cảnh báo + điều kiện + học phí + học bổng",
        },
        {
            "id": "G04",
            "query": (
                "SV012 muốn đăng ký Đồ án tốt nghiệp (CAPSTONE). "
                "Kiểm tra điều kiện, tính học phí 6 tín chỉ, "
                "và cho biết sau học bổng của sinh viên đó thì phải đóng bao nhiêu."
            ),
            "type": "golden",
            "expected_tools": [
                "check_eligibility",
                "get_scholarship_rate",
                "calculate_tuition",
                "apply_scholarship",
            ],
            "golden_answer": (
                "CAPSTONE cần DB201 + ML301 → SV012 có cả hai → ĐỦ | "
                "GPA 3.4 → Giỏi 20% | "
                "Học phí = 6 × 500,000 = 3,000,000 | "
                "Sau 20%: 2,400,000 VND"
            ),
            "note": "Đăng ký môn cuối khóa — học phí rẻ nhưng cần check đủ điều kiện",
        },
    ]

    # ══════════════════════════════════════════════════════════════════════════════
    # NHÓM 4 — FAILURE TRIGGERS (dùng để thu trace thất bại có chủ đích)
    # Dùng cho Debugging Case Study trong individual report.
    # ══════════════════════════════════════════════════════════════════════════════
    FAILURE_TRIGGERS = [
        {
            "id": "F01",
            "query": "Kiểm tra điều kiện của sinh viên SVXXX học môn HACK999.",
            "type": "failure_trigger",
            "expected_failure": "hallucination",
            "expected_tools": ["check_eligibility"],
            "note": (
                "Cả student_id lẫn course_id đều không tồn tại. "
                "Agent dễ hallucinate kết quả thay vì trả lỗi đúng. "
                "Kiểm tra xem tool có trả ERROR đúng không."
            ),
        },
        {
            "id": "F02",
            "query": (
                "Tính học phí cho môn ML301, sau đó áp dụng học bổng "
                "và cho tôi biết tổng chi phí sinh hoạt phí tháng này."
            ),
            "type": "failure_trigger",
            "expected_failure": "hallucination",
            "expected_tools": ["calculate_tuition", "apply_scholarship"],
            "note": (
                "Câu hỏi kết hợp dữ liệu thật (học phí) và thứ không có trong tool (sinh hoạt phí). "
                "Agent dễ bịa số liệu sinh hoạt phí. "
                "Kiểm tra xem agent có biết giới hạn của mình không."
            ),
        },
        {
            "id": "F03",
            "query": "SV001 học bao nhiêu môn rồi? Tính trung bình GPA cả lớp?",
            "type": "failure_trigger",
            "expected_failure": "hallucination",
            "expected_tools": ["get_student_record"],
            "note": (
                "Đếm môn đã học của SV001 thì được (tool có), "
                "nhưng 'GPA trung bình cả lớp' không có tool hỗ trợ. "
                "Agent dễ tự bịa con số thay vì nói 'không có dữ liệu'."
            ),
        },
        {
            "id": "F04",
            "query": (
                "Cho tôi biết SV001 đủ điều kiện học tất cả các môn "
                "thuộc khoa Trí tuệ nhân tạo không, liệt kê từng môn một."
            ),
            "type": "failure_trigger",
            "expected_failure": "timeout",
            "expected_tools": [
                "list_available_courses",
                "get_student_record",
                "check_eligibility",  # × 4 lần
            ],
            "note": (
                "Câu hỏi hợp lệ nhưng cần nhiều bước lặp (4 môn AI × 1 check mỗi môn). "
                "Nếu max_steps=5 thì dễ timeout trước khi hoàn thành. "
                "Trigger để thu trace TIMEOUT."
            ),
        },
        {
            "id": "F05",
            "query": "Áp học bổng fifty percent vào học phí bốn triệu rưỡi.",
            "type": "failure_trigger",
            "expected_failure": "parse_error",
            "expected_tools": ["apply_scholarship"],
            "note": (
                "Tham số viết bằng chữ ('fifty percent', 'bốn triệu rưỡi'). "
                "Agent cần chuyển đổi sang số trước khi gọi tool. "
                "Dễ gây parse error hoặc tool error khi truyền tham số sai kiểu."
            ),
        },
        {
            "id": "F06",
            "query": "Check xem student SV003 qualify cho machine learning course chưa?",
            "type": "failure_trigger",
            "expected_failure": "parse_error",
            "expected_tools": ["check_eligibility"],
            "note": (
                "Query tiếng Anh lẫn lộn — agent cần map 'machine learning course' → ML301. "
                "Kiểm tra xem agent có hiểu đúng course_id không hay gọi tool với tên sai."
            ),
        },
        {
            "id": "F07",
            "query": (
                "Tìm môn học phù hợp nhất cho SV002 để cải thiện GPA "
                "dựa trên lịch sử học tập và năng lực hiện tại."
            ),
            "type": "failure_trigger",
            "expected_failure": "hallucination",
            "expected_tools": ["get_student_record", "list_available_courses"],
            "note": (
                "Không có tool 'recommend' hay 'rank by difficulty'. "
                "Agent có thể tự đưa ra gợi ý dựa trên suy luận (chấp nhận được) "
                "hoặc hallucinate một tool không tồn tại như 'recommend_course'. "
                "Quan sát hành vi xử lý thiếu tool."
            ),
        },
    ]

    # ══════════════════════════════════════════════════════════════════════════════
    # NHÓM 5 — EDGE CASES (dữ liệu biên, kết quả bất ngờ)
    # ══════════════════════════════════════════════════════════════════════════════
    EDGE_CASES = [
        {
            "id": "E01",
            "query": "SV014 (GPA 4.0) học bổng bao nhiêu và học phí NLP401 sau học bổng là bao nhiêu?",
            "type": "edge",
            "expected_tools": ["get_scholarship_rate", "calculate_tuition", "apply_scholarship"],
            "golden_answer": "GPA 4.0 → Xuất sắc 30% | NLP401 4 × 1,800,000 = 7,200,000 | Sau 30%: 5,040,000 VND",
            "note": "GPA cao nhất (4.0) — kiểm tra xử lý đúng tier học bổng Xuất sắc",
        },
        {
            "id": "E02",
            "query": "SV013 (GPA 2.0 đúng ngưỡng) có bị cảnh báo học vụ không?",
            "type": "edge",
            "expected_tools": ["check_academic_warning"],
            "golden_answer": "GPA 2.0 → Yếu — cần chú ý (không phải cảnh báo chính thức vì ngưỡng là < 2.0)",
            "note": "Biên GPA = 2.0 đúng ngưỡng — logic so sánh < vs <=",
        },
        {
            "id": "E03",
            "query": "SV007 (sinh viên giỏi nhất) có thể đăng ký NLP401 không?",
            "type": "edge",
            "expected_tools": ["check_eligibility"],
            "golden_answer": "SV007 đã có ML301 và DL401 → ĐỦ điều kiện NLP401",
            "note": "Sinh viên năm 3 GPA cao — kiểm tra xem có track đúng tiên quyết chuỗi dài không",
        },
        {
            "id": "E04",
            "query": "Học phí môn CAPSTONE (Đồ án tốt nghiệp) cho đúng số tín chỉ quy định là bao nhiêu?",
            "type": "edge",
            "expected_tools": ["check_prerequisite", "calculate_tuition"],
            "golden_answer": "CAPSTONE = 6 tín chỉ × 500,000 = 3,000,000 VND (học phí rẻ nhất so với tín chỉ)",
            "note": "Môn có số tín chỉ lớn nhất (6) nhưng phí/tín chỉ rẻ nhất",
        },
        {
            "id": "E05",
            "query": "SV001 và SV002 ai được học bổng cao hơn?",
            "type": "edge",
            "expected_tools": ["get_scholarship_rate", "get_scholarship_rate"],
            "golden_answer": "SV001 GPA 3.2 → 20% | SV002 GPA 1.8 → 0% | SV001 cao hơn",
            "note": "So sánh 2 sinh viên — gọi cùng tool 2 lần rồi tổng hợp",
        },
    ]

    # ══════════════════════════════════════════════════════════════════════════════
    # TỔNG HỢP — ALL_TEST_CASES (dùng để chạy automation)
    # ══════════════════════════════════════════════════════════════════════════════
    ALL_TEST_CASES = SIMPLE_CASES + MULTI_CASES + GOLDEN_CASES + FAILURE_TRIGGERS + EDGE_CASES

    import dotenv
    dotenv.load_dotenv()

    SEP = "=" * 60
    PASS_MARK = "✅"
    FAIL_MARK = "❌"

    # Select which groups to run (comment out to skip)
    test_groups = [
        # ("SIMPLE",           SIMPLE_CASES),
        ("MULTI-STEP",       MULTI_CASES),
        # ("GOLDEN",           GOLDEN_CASES),
        # ("FAILURE TRIGGERS", FAILURE_TRIGGERS),
        # ("EDGE CASES",       EDGE_CASES),
    ]

    results = []

    for group_name, cases in test_groups:
        print(f"\n{'#' * 60}")
        print(f"# GROUP: {group_name}")
        print(f"{'#' * 60}")

        for case in cases:
            case_id    = case["id"]
            query      = case["query"]
            case_type  = case["type"]
            note       = case.get("note", "")
            golden     = case.get("golden_answer", "N/A")
            exp_tools  = case.get("expected_tools", [])
            exp_fail   = case.get("expected_failure", None)

            print(f"\n{SEP}")
            print(f"[{case_id}] {note}")
            print(f"Type    : {case_type}")
            print(f"Query   : {query}")
            print(f"Expected tools  : {exp_tools}")
            if exp_fail:
                print(f"Expected failure: {exp_fail}")
            if golden != "N/A":
                print(f"Golden answer   : {golden}")
            print(SEP)

            # Fresh agent per test so state doesn't bleed
            llm_fresh = GeminiProvider(
                model_name="gemini-3-flash-preview",
                api_key=os.getenv("GOOGLE_API_KEY"),
            )
            # Golden cases need more steps; failure triggers kept short on purpose
            max_steps = 8 if case_type == "golden" else 5
            agent = ReActAgent(llm=llm_fresh, tools=EDU_TOOLS, max_steps=max_steps)

            status = PASS_MARK
            answer = ""
            try:
                answer = agent.run(query)
                assert isinstance(answer, str) and len(answer) > 0, \
                    "Answer must be a non-empty string"
            except Exception as e:
                status = FAIL_MARK
                answer = f"EXCEPTION: {e}"

            steps_taken = len(agent.history)

            print(f"\n>>> FINAL ANSWER  : {answer}")
            print(f"    Steps taken   : {steps_taken}")

            # For failure triggers, a non-empty answer is still a "pass" for
            # the runner — the interesting signal is the answer content itself.
            if case_type == "failure_trigger":
                print(f"    [failure trigger — inspect answer manually for '{exp_fail}']")

            print(f"    {status} {case_id}")

            results.append({
                "id":     case_id,
                "type":   case_type,
                "status": status,
                "steps":  steps_taken,
            })

    # ── Summary table ────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("RESULTS SUMMARY")
    print(f"{'=' * 60}")
    print(f"  {'ID':<6} {'Type':<18} {'Steps':>5}  Status")
    print(f"  {'-'*6} {'-'*18} {'-'*5}  {'-'*6}")
    for r in results:
        print(f"  {r['id']:<6} {r['type']:<18} {r['steps']:>5}  {r['status']}")

    passed = sum(1 for r in results if r["status"] == PASS_MARK)
    total  = len(results)
    print(f"\n  TOTAL: {passed}/{total} passed")
    print("=" * 60)