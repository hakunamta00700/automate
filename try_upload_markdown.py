"""Custom API upload_markdown 기능 테스트 스크립트

127.0.0.1:8001에서 실행되는 Custom API의
`/v1/func/upload_markdown` 엔드포인트가 정상적으로 작동하는지 확인합니다.

기본 파라미터는 `try_check_custom_api_codex.py`와 동일하게 유지합니다:
- --host
- --prod

추가로, 이번 기능 테스트에 필요한 파라미터를 받습니다:
- --row-id (필수)
- --from (기본값: airtable)
"""

import argparse
import json
import sys
import time
from typing import Any

import requests

BASE_URL = "http://127.0.0.1:8001"  # 기본값, main()에서 업데이트 가능
TIMEOUT = 540
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


def test_upload_markdown(
    source: str,
    row_id: str,
    use_prod_key: bool = False,
    *,
    wait: bool = False,
    wait_timeout: int = 600,
    poll_interval: float = 1.0,
) -> bool:
    """upload_markdown POST 엔드포인트 테스트"""
    print_section("2. upload_markdown POST 테스트")
    try:
        headers = get_headers(use_prod_key)
        response = requests.post(
            f"{BASE_URL}/v1/func/upload_markdown",
            params={"from": source},
            headers=headers,
            json={"data": {"row_id": row_id}},
            timeout=TIMEOUT,
        )

        # 4xx/5xx라도 JSON 에러 상세를 보여주기 위해 여기서 분기 처리
        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = {"text": response.text}
            print_result(
                False,
                f"요청 실패 (status={response.status_code})",
                detail,
            )
            return False

        result = response.json()
        ok = bool(result.get("ok"))
        task_id = result.get("task_id")

        print_result(
            ok,
            "upload_markdown enqueue 완료",
            {
                "ok": ok,
                "from": result.get("from"),
                "row_id": result.get("row_id"),
                "task_id": task_id,
                "note": "worker가 실행 중이어야 실제 작업이 처리됩니다. (automate worker)",
            },
        )

        if not ok or not task_id:
            return False

        # wait 모드: task_status를 폴링하여 결과 확인
        if not wait:
            return True

        print_section("3. task_status 폴링")

        deadline = time.time() + wait_timeout
        while time.time() < deadline:
            status_resp = requests.get(
                f"{BASE_URL}/v1/func/task_status",
                params={"task_id": task_id},
                headers=headers,
                timeout=10,
            )

            if status_resp.status_code >= 400:
                try:
                    detail = status_resp.json()
                except Exception:
                    detail = {"text": status_resp.text}
                print_result(
                    False,
                    f"task_status 조회 실패 (status={status_resp.status_code})",
                    detail,
                )
                return False

            status_json = status_resp.json()
            done = bool(status_json.get("done"))
            if not done:
                print(f"⏳ 진행 중... task_id={task_id}")
                time.sleep(poll_interval)
                continue

            task_result = status_json.get("result") or {}
            task_ok = bool(task_result.get("ok"))
            stdout = task_result.get("stdout") or ""
            stderr = task_result.get("stderr") or ""

            print_result(
                task_ok,
                "작업 완료",
                {
                    "task_id": task_id,
                    "ok": task_ok,
                    "returncode": task_result.get("returncode"),
                    "command": task_result.get("command"),
                    "timeout_seconds": task_result.get("timeout_seconds"),
                    "stdout_preview": stdout[:500],
                    "stderr_preview": (stderr[:2000] if not task_ok else stderr[:500]),
                    "error": task_result.get("error"),
                },
            )
            return task_ok

        print_result(False, f"폴링 타임아웃: {wait_timeout}초")
        return False
    except requests.exceptions.Timeout:
        print_result(False, f"요청 타임아웃: {TIMEOUT}초")
        return False
    except requests.exceptions.RequestException as e:
        print_result(False, f"요청 실패: {e}")
        return False


def main() -> None:
    """메인 함수"""
    global BASE_URL

    parser = argparse.ArgumentParser(description="Custom API upload_markdown 기능 체크 스크립트")
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
    parser.add_argument(
        "--row-id",
        type=str,
        required=True,
        help="Airtable row_id (record id). 예: recXXXXXXXXXXXXXXX",
    )
    parser.add_argument(
        "--from",
        dest="source",
        type=str,
        default="airtable",
        choices=["airtable", "googlesp"],
        help="데이터 소스 (기본값: airtable)",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="enqueue 후 task_status를 폴링하여 완료까지 기다립니다",
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=600,
        help="--wait 모드에서 최대 대기 시간(초) (기본값: 600)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="--wait 모드에서 폴링 간격(초) (기본값: 1.0)",
    )
    args = parser.parse_args()

    BASE_URL = args.host.rstrip("/")
    use_prod_key = args.prod

    print("\n" + "=" * 60)
    print("  Custom API upload_markdown 체크 시작")
    print("=" * 60)
    print(f"서버 주소: {BASE_URL}")
    print(f"타임아웃: {TIMEOUT}초")
    print(f"from: {args.source}")
    print(f"row_id: {args.row_id}")
    if args.wait:
        print(f"wait: True (timeout={args.wait_timeout}s, interval={args.poll_interval}s)")
    if use_prod_key:
        print(f"🔑 프로덕션 API 키 사용: {PROD_API_KEY[:8]}...")
    else:
        print("🔓 API 키 없이 테스트 (기본 모드)")

    if not test_health_check(use_prod_key):
        print("\n⚠️  서버가 실행 중이지 않습니다. 먼저 서버를 시작하세요:")
        print("   automate custom-api dev")
        sys.exit(1)

    ok = test_upload_markdown(
        args.source,
        args.row_id,
        use_prod_key,
        wait=bool(args.wait),
        wait_timeout=int(args.wait_timeout),
        poll_interval=float(args.poll_interval),
    )
    if ok:
        print("\n✅ upload_markdown 테스트 통과!")
        sys.exit(0)

    print("\n❌ upload_markdown 테스트 실패")
    sys.exit(1)


if __name__ == "__main__":
    main()
