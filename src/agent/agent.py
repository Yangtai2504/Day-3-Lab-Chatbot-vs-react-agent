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
                transcript += f"{content}\nObservation: Tôi không đọc được Action. Vui lòng dùng định dạng Action: tool_name(arg1, arg2).\n"
                steps += 1
                continue

            tool_name, raw_args = action_data
            observation = self._execute_tool(tool_name, raw_args)
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
