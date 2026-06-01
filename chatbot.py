import os
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider


def build_provider():
    load_dotenv()
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").strip().lower()
    model_name = os.getenv("DEFAULT_MODEL", "gpt-4o").strip()

    if provider_name == "google":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for the Google provider.")
        return GeminiProvider(model_name=model_name, api_key=api_key)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for the OpenAI provider.")
    return OpenAIProvider(model_name=model_name, api_key=api_key)


def get_system_prompt() -> str:
    return (
        "Bạn là trợ lý học vụ. Trả lời trực tiếp và rõ ràng bằng tiếng Việt. "
        "Không cần suy nghĩ theo bước hoặc dùng công cụ."
    )


def ask_question(provider, question: str) -> str:
    result = provider.generate(question, system_prompt=get_system_prompt())
    return str(result.get("content", "")).strip()


if __name__ == "__main__":
    llm = build_provider()
    print("=== Chatbot baseline ===")
    print("Gõ 'exit' hoặc 'quit' để thoát.")

    while True:
        try:
            prompt = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nKết thúc.")
            break

        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit"}:
            print("Kết thúc.")
            break

        try:
            answer = ask_question(llm, prompt)
            print("Bot:", answer)
        except Exception as exc:
            print("Lỗi khi gọi LLM:", exc)
