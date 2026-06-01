import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

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
Bạn là trợ lý tư vấn đăng ký môn học của trường đại học. Bạn CHỈ được dùng các công cụ sau:
{tool_descriptions}

Luôn trả lời bằng tiếng Việt và tuân theo ĐÚNG định dạng sau cho mỗi bước.
Giữ NGUYÊN các từ khóa tiếng Anh: "Thought", "Action", "Observation", "Final Answer".
Thought: trình bày suy luận của bạn (bằng tiếng Việt).
Action: tên_công_cụ(tham_số1, tham_số2)
Observation: kết quả công cụ trả về.
... (lặp lại Thought / Action / Observation đến khi đủ thông tin)
Final Answer: câu trả lời cuối cùng cho người dùng (bằng tiếng Việt).

Quy tắc:
- Mỗi lượt CHỈ xuất ĐÚNG MỘT Thought và MỘT Action, rồi DỪNG.
- KHÔNG tự viết Observation — agent sẽ chạy công cụ và đưa kết quả thật cho bạn.
- KHÔNG xuất "Final Answer" trong cùng lượt với một Action. Chỉ đưa Final Answer ở
  lượt sau, sau khi đã thấy các Observation thật và có đủ thông tin.
- Không dùng công cụ ngoài danh sách trên.
- Dùng đúng định dạng trên; toàn bộ nội dung viết bằng tiếng Việt.
"""

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        transcript = f"Question: {user_input}\n"
        steps = 0

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

            action_data = self._parse_action(content)
            final_answer = self._parse_final_answer(content)

            # Ưu tiên thực thi Action. Model (đặc biệt Gemini) hay xuất cả Action lẫn
            # "Final Answer" (kèm Observation tự bịa) trong cùng một lượt — nếu trả về
            # ngay khi thấy Final Answer thì tool không bao giờ chạy, agent dừng ở bước 1
            # với số liệu bịa. Vì vậy: còn Action thì luôn chạy tool trước.
            if action_data is not None:
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
                continue

            # Không còn Action — nếu có Final Answer thì kết thúc.
            if final_answer is not None:
                logger.log_event("AGENT_END", {"steps": steps + 1, "status": "success"})
                return final_answer.strip()

            # Không có cả Action lẫn Final Answer → parse error, nhắc lại định dạng.
            logger.log_event("PARSE_ERROR", {"step": steps + 1, "raw": content[:300]})
            self.history[-1]["observation"] = "PARSE_ERROR: không đọc được Action."
            transcript += f"{content}\nObservation: Tôi không đọc được Action. Vui lòng dùng định dạng Action: tool_name(arg1, arg2).\n"
            steps += 1

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
        # Hỗ trợ keyword-arg kiểu Python mà LLM hay dùng: tool(course_id='ML301')
        # → bỏ phần "course_id=" chỉ giữ giá trị. Tham số vẫn truyền theo vị trí.
        kw = re.match(r"^[A-Za-z_]\w*\s*=\s*(.+)$", arg)
        if kw:
            arg = kw.group(1).strip()
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
