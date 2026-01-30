"""한국 음식 에이전트 CLI"""

import sys
from typing import Optional


def main():
    """메인 CLI 진입점"""
    print("=" * 50)
    print("🍜 한국 음식 AI 어시스턴트")
    print("=" * 50)
    print()

    # 환경 변수 체크
    from .config import settings

    if not settings.openai_api_key and not settings.google_api_key:
        print("❌ API 키가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY 또는 GOOGLE_API_KEY를 설정해주세요.")
        sys.exit(1)

    # 사용할 모델 결정
    provider = settings.model_provider.value
    if provider == "openai" and not settings.openai_api_key:
        provider = "gemini"
    elif provider == "gemini" and not settings.google_api_key:
        provider = "openai"

    print(f"🤖 사용 모델: {provider.upper()}")
    print()

    # 에이전트 생성
    from .agent import KoreanFoodAgent

    try:
        agent = KoreanFoodAgent(provider=provider)
    except Exception as e:
        print(f"❌ 에이전트 생성 실패: {e}")
        sys.exit(1)

    print("💬 무엇이든 물어보세요! (종료: quit 또는 exit)")
    print("-" * 50)
    print()

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "종료", "끝"]:
                print("\n👋 맛있는 하루 되세요!")
                break

            # 모델 전환 명령어
            if user_input.startswith("/model "):
                new_provider = user_input.split()[1].lower()
                if new_provider in ["openai", "gemini"]:
                    agent.switch_model(new_provider)
                else:
                    print("❌ 지원 모델: openai, gemini")
                continue

            if user_input == "/help":
                print_help()
                continue

            # 에이전트 응답
            print("\n🍳 Assistant: ", end="", flush=True)

            response = agent.chat(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\n👋 맛있는 하루 되세요!")
            break
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}\n")


def print_help():
    """도움말 출력"""
    print("""
📖 사용 가이드

💬 질문 예시:
  • "OOO 레시피 알려줘"
  • "냉장고에 있는 재료로 뭐 만들 수 있어?"
  • "OOO 칼로리가 얼마야?"
  • "일주일 식단 짜줘"
  • "OOO 대신 쓸 수 있는 재료 있어?"

🔧 명령어:
  /model openai  - OpenAI 모델로 전환
  /model gemini  - Gemini 모델로 전환
  /help          - 도움말 보기
  quit           - 종료
""")


if __name__ == "__main__":
    main()
