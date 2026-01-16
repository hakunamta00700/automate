"""Custom API 테스트 스크립트

127.0.0.1:8001에서 실행되는 Custom API를 테스트합니다.
"""

import json
import sys
import time
from typing import Any

import requests

BASE_URL = "http://127.0.0.1:8001"
TIMEOUT = 60


def print_section(title: str) -> None:
    """섹션 제목 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(success: bool, message: str, data: Any = None) -> None:
    """결과 출력"""
    status = "✅ 성공" if success else "❌ 실패"
    print(f"{status}: {message}")
    if data:
        if isinstance(data, dict):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(data)


def test_health_check() -> bool:
    """헬스 체크 테스트"""
    print_section("1. 헬스 체크")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        result = response.json()
        print_result(True, "서버가 정상적으로 응답합니다", result)
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"서버 연결 실패: {e}")
        print("\n⚠️  서버가 실행 중인지 확인하세요: automate custom-api dev")
        return False


def test_list_models() -> bool:
    """모델 목록 조회 테스트"""
    print_section("2. 모델 목록 조회")
    try:
        response = requests.get(f"{BASE_URL}/v1/models", timeout=5)
        response.raise_for_status()
        result = response.json()
        models = [m["id"] for m in result["data"]]
        print_result(True, f"사용 가능한 모델: {', '.join(models)}", result)
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"모델 목록 조회 실패: {e}")
        return False


def test_basic_chat_completion(model: str = "codex") -> bool:
    """기본 Chat Completion 테스트"""
    print_section(f"3. 기본 Chat Completion ({model})")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Python으로 'Hello, World!'를 출력하는 코드를 작성해줘",
                    }
                ],
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print_result(
            True,
            f"응답 받음 ({len(content)}자)",
            {"content": content[:200] + "..." if len(content) > 200 else content},
        )
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"Chat completion 실패: {e}")
        if hasattr(e, "response") and e.response:
            try:
                error_detail = e.response.json()
                print(f"에러 상세: {error_detail}")
            except:
                print(f"응답: {e.response.text}")
        return False


def test_system_prompt() -> bool:
    """시스템 프롬프트 테스트"""
    print_section("4. 시스템 프롬프트 사용")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "codex",
                "messages": [
                    {
                        "role": "system",
                        "content": "당신은 전문 Python 개발자입니다. 간결하고 명확한 코드를 작성합니다.",
                    },
                    {"role": "user", "content": "리스트에서 중복을 제거하는 함수를 작성해줘"},
                ],
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print_result(
            True,
            "시스템 프롬프트 적용됨",
            {"content": content[:200] + "..." if len(content) > 200 else content},
        )
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"시스템 프롬프트 테스트 실패: {e}")
        return False


def test_multi_turn_conversation() -> bool:
    """대화형 대화 테스트"""
    print_section("5. 대화형 대화 (Multi-turn)")
    try:
        # 첫 번째 메시지
        conversation = [{"role": "user", "content": "Python에서 리스트와 튜플의 차이점은?"}]

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={"model": "codex", "messages": conversation},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        assistant_reply = result["choices"][0]["message"]["content"]
        print(f"User: {conversation[0]['content']}")
        print(f"Assistant: {assistant_reply[:150]}...")

        # 두 번째 메시지 (대화 이력 포함)
        conversation.append({"role": "assistant", "content": assistant_reply})
        conversation.append(
            {"role": "user", "content": "그럼 언제 리스트를 사용하고 언제 튜플을 사용하나요?"}
        )

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={"model": "codex", "messages": conversation},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        second_reply = result["choices"][0]["message"]["content"]
        print(f"User: {conversation[-1]['content']}")
        print(f"Assistant: {second_reply[:150]}...")

        print_result(True, "대화형 대화 성공")
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"대화형 대화 테스트 실패: {e}")
        return False


def test_model_specific_endpoints() -> bool:
    """모델별 전용 엔드포인트 테스트"""
    print_section("6. 모델별 전용 엔드포인트")

    models = ["codex", "opencode", "gemini", "cursor"]
    success_count = 0

    for model in models:
        try:
            print(f"\n테스트 중: {model}")
            response = requests.post(
                f"{BASE_URL}/v1/{model}/completions",
                json={
                    "messages": [{"role": "user", "content": f"{model} 테스트: 간단히 인사해줘"}],
                },
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"✅ {model}: 성공 ({len(content)}자)")
            success_count += 1
        except requests.exceptions.RequestException as e:
            print(f"❌ {model}: 실패 - {e}")

    print_result(success_count > 0, f"{success_count}/{len(models)} 모델 성공")
    return success_count > 0


def test_parameters() -> bool:
    """파라미터 튜닝 테스트"""
    print_section("7. 파라미터 튜닝 (temperature, max_tokens)")
    try:
        # temperature 테스트
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "codex",
                "messages": [{"role": "user", "content": "창의적인 아이디어 하나 제시해줘"}],
                "temperature": 1.5,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        print(f"Temperature 1.5: {len(result['choices'][0]['message']['content'])}자 응답")

        # max_tokens 테스트
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "codex",
                "messages": [{"role": "user", "content": "Python에 대해 설명해줘"}],
                "max_tokens": 50,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"Max tokens 50: {len(content)}자 응답")
        print(f"응답 내용: {content[:100]}...")

        print_result(True, "파라미터 튜닝 성공")
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"파라미터 튜닝 테스트 실패: {e}")
        return False


def test_streaming() -> bool:
    """스트리밍 테스트"""
    print_section("8. 스트리밍 (Server-Sent Events)")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions/stream",
            json={
                "model": "codex",
                "messages": [{"role": "user", "content": "Python의 장점 3가지를 간단히 나열해줘"}],
                "stream": True,
            },
            stream=True,
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        print("스트리밍 응답 수신 중...")
        chunks_received = 0
        full_content = ""

        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # "data: " 제거
                    if data_str == "[DONE]":
                        print("\n스트리밍 완료")
                        break
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                full_content += content
                                chunks_received += 1
                    except json.JSONDecodeError:
                        pass

        print(f"\n\n총 {chunks_received}개 청크 수신, {len(full_content)}자")
        print_result(True, "스트리밍 성공")
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"스트리밍 테스트 실패: {e}")
        return False


def test_error_handling() -> bool:
    """에러 처리 테스트"""
    print_section("9. 에러 처리")

    # 잘못된 모델 테스트
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "invalid-model",
                "messages": [{"role": "user", "content": "Hello"}],
            },
            timeout=5,
        )
        if response.status_code == 400:
            error_detail = response.json()
            print_result(True, "잘못된 모델 에러 처리 성공", error_detail)
        else:
            print_result(False, f"예상한 400 에러가 아닙니다: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_result(False, f"에러 처리 테스트 실패: {e}")
        return False

    return True


def test_performance() -> bool:
    """성능 테스트"""
    print_section("10. 성능 테스트 (3개 요청 동시 처리)")
    try:
        import concurrent.futures

        def make_request(i: int) -> tuple[int, float, bool]:
            start_time = time.time()
            try:
                response = requests.post(
                    f"{BASE_URL}/v1/chat/completions",
                    json={
                        "model": "codex",
                        "messages": [
                            {"role": "user", "content": f"테스트 요청 {i}: 간단히 인사해줘"}
                        ],
                    },
                    timeout=TIMEOUT,
                )
                response.raise_for_status()
                elapsed = time.time() - start_time
                return (i, elapsed, True)
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"요청 {i} 실패: {e}")
                return (i, elapsed, False)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(1, 4)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = sum(1 for _, _, success in results if success)
        avg_time = sum(elapsed for _, elapsed, _ in results) / len(results)

        print(f"성공: {success_count}/3")
        print(f"평균 응답 시간: {avg_time:.2f}초")
        for req_id, elapsed, success in sorted(results):
            status = "✅" if success else "❌"
            print(f"  요청 {req_id}: {elapsed:.2f}초 {status}")

        print_result(success_count > 0, f"성능 테스트 완료 ({success_count}/3 성공)")
        return success_count > 0
    except Exception as e:
        print_result(False, f"성능 테스트 실패: {e}")
        return False


def main() -> None:
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("  Custom API 테스트 시작")
    print("=" * 60)
    print(f"서버 주소: {BASE_URL}")
    print(f"타임아웃: {TIMEOUT}초")

    # 헬스 체크 먼저 수행
    if not test_health_check():
        print("\n⚠️  서버가 실행 중이지 않습니다. 먼저 서버를 시작하세요:")
        print("   automate custom-api dev")
        sys.exit(1)

    # 테스트 실행
    tests = [
        ("모델 목록 조회", test_list_models),
        ("기본 Chat Completion", lambda: test_basic_chat_completion("codex")),
        ("시스템 프롬프트", test_system_prompt),
        ("대화형 대화", test_multi_turn_conversation),
        ("모델별 전용 엔드포인트", test_model_specific_endpoints),
        ("파라미터 튜닝", test_parameters),
        ("스트리밍", test_streaming),
        ("에러 처리", test_error_handling),
        ("성능 테스트", test_performance),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))

    # 결과 요약
    print_section("테스트 결과 요약")
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)

    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")

    print(f"\n총 {success_count}/{total_count} 테스트 성공")

    if success_count == total_count:
        print("\n🎉 모든 테스트 통과!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_count - success_count}개 테스트 실패")
        sys.exit(1)


if __name__ == "__main__":
    main()
