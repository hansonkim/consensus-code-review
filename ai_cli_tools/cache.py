"""캐시 관리 서비스"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from ai_cli_tools.exceptions import FileOperationError


class CacheManager:
    """AI 모델 가용성 및 MCP 서버 캐시 관리

    Attributes:
        cache_file: 캐시 파일 경로
    """

    def __init__(self, cache_file: Path = Path(".ai_code_review_cache.json")):
        """
        Args:
            cache_file: 캐시 파일 경로 (기본: .ai_code_review_cache.json)
        """
        self.cache_file = cache_file

    def load_cache(self) -> Optional[Dict[str, Any]]:
        """캐시 파일에서 전체 데이터 로드

        Returns:
            캐시 데이터 딕셔너리 또는 None (캐시 없음)
        """
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            # 캐시 파일 읽기 실패 시 None 반환 (재확인 유도)
            print(f"⚠️  캐시 파일 읽기 실패: {e}")
            return None

    def load_cached_models(self) -> Optional[List[str]]:
        """캐시 파일에서 사용 가능한 모델 목록 로드

        Returns:
            캐시된 모델 키 리스트 또는 None (캐시 없음)
        """
        cache = self.load_cache()
        if cache is None:
            return None
        return cache.get('available_models', [])

    def save_cache(self, data: Dict[str, Any]) -> None:
        """전체 캐시 데이터 저장

        Args:
            data: 저장할 캐시 데이터

        Raises:
            FileOperationError: 캐시 저장 실패 시
        """
        try:
            import time
            data['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise FileOperationError(f"캐시 파일 저장 실패: {e}")

    def save_cached_models(self, available_keys: List[str], mcp_servers: Dict[str, bool] = None) -> None:
        """사용 가능한 모델 목록과 MCP 서버 상태를 캐시 파일에 저장

        Args:
            available_keys: 사용 가능한 모델 키 리스트
            mcp_servers: MCP 서버 가용성 딕셔너리

        Raises:
            FileOperationError: 캐시 저장 실패 시
        """
        data = {
            'available_models': available_keys,
        }
        if mcp_servers is not None:
            data['mcp_servers'] = mcp_servers

        self.save_cache(data)

    def clear_cache(self) -> None:
        """캐시 파일 삭제"""
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
                print("✅ 캐시 파일이 삭제되었습니다.")
            except Exception as e:
                raise FileOperationError(f"캐시 파일 삭제 실패: {e}")
