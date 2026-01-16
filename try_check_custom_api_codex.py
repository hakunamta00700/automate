"""Custom API Codex Provider 체크 스크립트

127.0.0.1:8001에서 실행되는 Custom API의 Codex Provider가
정상적으로 작동하는지 확인합니다.
"""

import argparse
import json
import sys
import time
from typing import Any

import requests

BASE_URL = "http://127.0.0.1:8001"  # 기본값, main()에서 업데이트 가능
TIMEOUT = 60
PROD_API_KEY = "609eb993-0894-4cdd-b2f3-a70e34fa63ff"


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


def get_headers(use_prod_key: bool) -> dict[str, str]:
    """요청 헤더 생성
    
    Args:
        use_prod_key: 프로덕션 키 사용 여부
        
    Returns:
        요청 헤더 딕셔너리
    """
    if use_prod_key:
        return {"X-API-Key": PROD_API_KEY}
    return {}


def test_health_check(use_prod_key: bool = False) -> bool:
    """헬스 체크 테스트"""
    print_section("1. 헬스 체크")
    try:
        headers = get_headers(use_prod_key)
        response = requests.get(f"{BASE_URL}/health", headers=headers, timeout=5)
        response.raise_for_status()
        result = response.json()
        print_result(True, "서버가 정상적으로 응답합니다", result)
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"서버 연결 실패: {e}")
        print("\n⚠️  서버가 실행 중인지 확인하세요: automate custom-api dev")
        return False


def test_codex_in_models_list(use_prod_key: bool = False) -> bool:
    """모델 목록에 codex가 포함되어 있는지 확인"""
    print_section("2. 모델 목록에 Codex 확인")
    try:
        headers = get_headers(use_prod_key)
        response = requests.get(f"{BASE_URL}/v1/models", headers=headers, timeout=5)
        response.raise_for_status()
        result = response.json()
        models = [m["id"] for m in result["data"]]
        
        if "codex" in models:
            print_result(True, f"Codex 모델이 목록에 있습니다. 전체 모델: {', '.join(models)}")
            return True
        else:
            print_result(False, f"Codex 모델이 목록에 없습니다. 전체 모델: {', '.join(models)}")
            return False
    except requests.exceptions.RequestException as e:
        print_result(False, f"모델 목록 조회 실패: {e}")
        return False


def test_default_provider_is_codex(use_prod_key: bool = False) -> bool:
    """기본 Provider가 Codex인지 확인 (model 파라미터 없이 요청)"""
    print_section("3. 기본 Provider가 Codex인지 확인")
    try:
        headers = get_headers(use_prod_key)
        # model 파라미터 없이 요청
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers=headers,
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "간단히 인사해줘",
                    }
                ],
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        
        # 응답의 model 필드가 codex인지 확인
        if result.get("model") == "codex":
            content = result["choices"][0]["message"]["content"]
            print_result(
                True,
                f"기본 Provider가 Codex입니다 (model 파라미터 없이 요청)",
                {
                    "response_model": result.get("model"),
                    "content_preview": content[:200] + "..." if len(content) > 200 else content,
                },
            )
            return True
        else:
            print_result(
                False,
                f"기본 Provider가 Codex가 아닙니다. 응답 model: {result.get('model')}",
                {"response_model": result.get("model")},
            )
            return False
    except requests.exceptions.RequestException as e:
        print_result(False, f"기본 Provider 확인 실패: {e}")
        if hasattr(e, "response") and e.response:
            try:
                error_detail = e.response.json()
                print(f"에러 상세: {error_detail}")
            except:
                print(f"응답: {e.response.text}")
        return False


def test_codex_explicit_model(use_prod_key: bool = False) -> bool:
    """명시적으로 codex 모델 지정하여 테스트"""
    print_section("4. Codex 모델 명시적 지정 테스트")
    try:
        headers = get_headers(use_prod_key)
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers=headers,
            json={
                "model": "codex",
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
        
        if result.get("model") == "codex":
            content = result["choices"][0]["message"]["content"]
            print_result(
                True,
                f"Codex 모델로 정상 응답 받음 ({len(content)}자)",
                {"content": content[:200] + "..." if len(content) > 200 else content},
            )
            return True
        else:
            print_result(
                False,
                f"응답 model이 codex가 아닙니다: {result.get('model')}",
            )
            return False
    except requests.exceptions.RequestException as e:
        print_result(False, f"Codex 명시적 지정 테스트 실패: {e}")
        if hasattr(e, "response") and e.response:
            try:
                error_detail = e.response.json()
                print(f"에러 상세: {error_detail}")
            except:
                print(f"응답: {e.response.text}")
        return False


def test_codex_dedicated_endpoint(use_prod_key: bool = False) -> bool:
    """Codex 전용 엔드포인트 테스트"""
    print_section("5. Codex 전용 엔드포인트 (/v1/codex/completions)")
    try:
        headers = get_headers(use_prod_key)
        response = requests.post(
            f"{BASE_URL}/v1/codex/completions",
            headers=headers,
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Codex 전용 엔드포인트 테스트: 간단히 인사해줘",
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
            f"Codex 전용 엔드포인트 정상 작동 ({len(content)}자)",
            {"content": content[:200] + "..." if len(content) > 200 else content},
        )
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"Codex 전용 엔드포인트 테스트 실패: {e}")
        if hasattr(e, "response") and e.response:
            try:
                error_detail = e.response.json()
                print(f"에러 상세: {error_detail}")
            except:
                print(f"응답: {e.response.text}")
        return False


def test_codex_with_system_prompt(use_prod_key: bool = False) -> bool:
    """Codex 시스템 프롬프트 테스트"""
    print_section("6. Codex 시스템 프롬프트 사용")
    try:
        headers = get_headers(use_prod_key)
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers=headers,
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
            "Codex 시스템 프롬프트 적용됨",
            {"content": content[:200] + "..." if len(content) > 200 else content},
        )
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"Codex 시스템 프롬프트 테스트 실패: {e}")
        return False


def test_codex_streaming(use_prod_key: bool = False) -> bool:
    """Codex 스트리밍 테스트"""
    print_section("7. Codex 스트리밍 (Server-Sent Events)")
    try:
        headers = get_headers(use_prod_key)
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions/stream",
            headers=headers,
            json={
                "model": "codex",
                "messages": [
                    {"role": "user", "content": "Python의 장점 3가지를 간단히 나열해줘"}
                ],
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
        print_result(True, "Codex 스트리밍 성공")
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"Codex 스트리밍 테스트 실패: {e}")
        return False


def test_codex_parameters(use_prod_key: bool = False) -> bool:
    """Codex 파라미터 튜닝 테스트"""
    print_section("8. Codex 파라미터 튜닝 (temperature, max_tokens)")
    try:
        headers = get_headers(use_prod_key)
        # temperature 테스트
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers=headers,
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
            headers=headers,
            json={
                "model": "codex",
                "messages": [{"role": "user", "content": "Python에 대해 간단히 설명해줘"}],
                "max_tokens": 50,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"Max tokens 50: {len(content)}자 응답")
        print(f"응답 내용: {content[:100]}...")

        print_result(True, "Codex 파라미터 튜닝 성공")
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"Codex 파라미터 튜닝 테스트 실패: {e}")
        return False


def test_codex_multi_turn(use_prod_key: bool = False) -> bool:
    """Codex 대화형 대화 테스트"""
    print_section("9. Codex 대화형 대화 (Multi-turn)")
    try:
        headers = get_headers(use_prod_key)
        # 첫 번째 메시지
        conversation = [{"role": "user", "content": "Python에서 리스트와 튜플의 차이점은?"}]

        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers=headers,
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
            headers=headers,
            json={"model": "codex", "messages": conversation},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        second_reply = result["choices"][0]["message"]["content"]
        print(f"User: {conversation[-1]['content']}")
        print(f"Assistant: {second_reply[:150]}...")

        print_result(True, "Codex 대화형 대화 성공")
        return True
    except requests.exceptions.RequestException as e:
        print_result(False, f"Codex 대화형 대화 테스트 실패: {e}")
        return False


def test_codex_error_handling(use_prod_key: bool = False) -> bool:
    """Codex 에러 처리 테스트"""
    print_section("10. Codex 에러 처리")
    
    # 잘못된 파라미터 테스트 (model은 codex이지만 잘못된 temperature)
    try:
        headers = get_headers(use_prod_key)
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers=headers,
            json={
                "model": "codex",
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 3.0,  # 범위를 벗어난 값
            },
            timeout=5,
        )
        # Pydantic이 검증하므로 422 에러가 나올 수 있음
        if response.status_code in [400, 422]:
            print_result(True, "잘못된 파라미터 에러 처리 성공")
            return True
        else:
            print_result(False, f"예상한 에러 코드가 아닙니다: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_result(False, f"에러 처리 테스트 실패: {e}")
        return False


def main() -> None:
    """메인 테스트 함수"""
    global BASE_URL
    
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description="Custom API Codex Provider 체크 스크립트")
    parser.add_argument(
        "--prod",
        action="store_true",
        help="프로덕션 API 키를 사용하여 테스트합니다",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="http://127.0.0.1:8001",
        help="테스트할 서버 호스트 주소 (기본값: http://127.0.0.1:8001)",
    )
    args = parser.parse_args()
    
    # BASE_URL 업데이트
    BASE_URL = args.host
    use_prod_key = args.prod
    
    print("\n" + "=" * 60)
    print("  Custom API Codex Provider 체크 시작")
    print("=" * 60)
    print(f"서버 주소: {BASE_URL}")
    print(f"타임아웃: {TIMEOUT}초")
    if use_prod_key:
        print(f"🔑 프로덕션 API 키 사용: {PROD_API_KEY[:8]}...")
    else:
        print("🔓 API 키 없이 테스트 (기본 모드)")
    print("\n이 스크립트는 Codex Provider가 정상적으로 작동하는지 확인합니다.")

    # 헬스 체크 먼저 수행
    if not test_health_check(use_prod_key):
        print("\n⚠️  서버가 실행 중이지 않습니다. 먼저 서버를 시작하세요:")
        print("   automate custom-api dev")
        sys.exit(1)

    # 테스트 실행
    tests = [
        ("모델 목록에 Codex 확인", test_codex_in_models_list),
        ("기본 Provider가 Codex인지 확인", test_default_provider_is_codex),
        ("Codex 모델 명시적 지정", test_codex_explicit_model),
        ("Codex 전용 엔드포인트", test_codex_dedicated_endpoint),
        ("Codex 시스템 프롬프트", test_codex_with_system_prompt),
        ("Codex 스트리밍", test_codex_streaming),
        ("Codex 파라미터 튜닝", test_codex_parameters),
        ("Codex 대화형 대화", test_codex_multi_turn),
        ("Codex 에러 처리", test_codex_error_handling),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func(use_prod_key)
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
        print("\n🎉 모든 Codex 테스트 통과!")
        print("✅ Custom API가 Codex 기반으로 정상 작동하고 있습니다.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_count - success_count}개 테스트 실패")
        print("❌ Codex Provider에 문제가 있을 수 있습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
