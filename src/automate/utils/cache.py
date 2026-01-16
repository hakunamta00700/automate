"""캐시 유틸리티 모듈"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class FileCache:
    """파일 기반 캐시 클래스"""

    def __init__(self, cache_dir: str = ".cache"):
        """캐시 디렉토리 초기화

        Args:
            cache_dir: 캐시 디렉토리 경로 (기본값: '.cache')
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.youtube_cache_dir = self.cache_dir / "youtube"
        self.youtube_cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """캐시 파일 경로 반환

        Args:
            key: 캐시 키

        Returns:
            캐시 파일 경로
        """
        # 파일명에 사용할 수 없는 문자 제거
        safe_key = "".join(c for c in key if c.isalnum() or c in "._-")
        return self.youtube_cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기

        Args:
            key: 캐시 키

        Returns:
            캐시된 값 또는 None
        """
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"캐시 히트: {key}")
                return data.get("value")
        except Exception as e:
            logger.warning(f"캐시 읽기 실패 ({key}): {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """캐시에 값 저장

        Args:
            key: 캐시 키
            value: 저장할 값
        """
        cache_path = self._get_cache_path(key)
        try:
            data = {"value": value}
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"캐시 저장: {key}")
        except Exception as e:
            logger.warning(f"캐시 저장 실패 ({key}): {e}")

    def _hash_transcript(self, transcript: List[Dict]) -> str:
        """대본 리스트의 해시값 생성

        Args:
            transcript: 대본 리스트

        Returns:
            해시 문자열
        """
        # 대본을 JSON 문자열로 변환하여 해시 생성
        transcript_str = json.dumps(transcript, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(transcript_str.encode("utf-8")).hexdigest()[:16]

    def get_transcript_key(self, video_id: str, language: str) -> str:
        """대본 캐시 키 생성

        Args:
            video_id: YouTube 비디오 ID
            language: 언어 코드

        Returns:
            캐시 키
        """
        return f"transcript_{video_id}_{language}"

    def get_metadata_key(self, video_id: str) -> str:
        """메타데이터 캐시 키 생성

        Args:
            video_id: YouTube 비디오 ID

        Returns:
            캐시 키
        """
        return f"metadata_{video_id}"

    def get_summary_key(self, transcript: List[Dict]) -> str:
        """요약 캐시 키 생성

        Args:
            transcript: 대본 리스트

        Returns:
            캐시 키
        """
        transcript_hash = self._hash_transcript(transcript)
        return f"summary_{transcript_hash}"


# 전역 캐시 인스턴스
_cache: Optional[FileCache] = None


def get_cache() -> FileCache:
    """캐시 인스턴스 반환 (싱글톤 패턴)

    Returns:
        FileCache 인스턴스
    """
    global _cache
    if _cache is None:
        _cache = FileCache()
    return _cache
