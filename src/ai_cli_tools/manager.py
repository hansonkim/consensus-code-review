"""AI 모델 관리 서비스"""

import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

from ai_cli_tools.cache import CacheManager
from ai_cli_tools.constants import ALL_AI_MODELS, MIN_REVIEWERS, MODEL_CHECK_TIMEOUT
from ai_cli_tools.exceptions import NoAvailableModelsError
from ai_cli_tools.models import AIModel


class ModelManager:
    """AI 모델 가용성 확인 및 관리

    Attributes:
        cache_manager: 캐시 관리자
        available_models: 사용 가능한 AI 모델 딕셔너리
    """

    def __init__(self, cache_manager: CacheManager):
        """
        Args:
            cache_manager: 캐시 관리자 인스턴스
        """
        self.cache_manager = cache_manager
        self.available_models: Dict[str, AIModel] = {}

    def check_model_availability(self, model_key: str, model: AIModel) -> bool:
        """특정 AI 모델의 CLI가 사용 가능한지 확인

        Args:
            model_key: 모델 키 (예: "claude")
            model: AI 모델 정보

        Returns:
            사용 가능하면 True, 아니면 False
        """
        # 1단계: CLI 설치 확인 (빠른 체크)
        test_cmd = model.test_command or model.command[:1] + ["--version"]

        try:
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=MODEL_CHECK_TIMEOUT * 2,
                encoding="utf-8",
            )
            # CLI가 없거나 심각한 오류면 즉시 False
            if result.returncode not in [0, 1]:
                return False
        except FileNotFoundError:
            return False
        except subprocess.TimeoutExpired:
            # 타임아웃은 실행은 되지만 응답이 느린 경우
            pass
        except Exception:
            return False

        # 2단계: 실제 API 호출 테스트 (간단한 호출로 크레딧/인증 확인)
        try:
            test_prompt = "ok"
            result = subprocess.run(
                model.command + [test_prompt],
                capture_output=True,
                text=True,
                timeout=10.0,  # AI API 호출은 충분한 시간 필요 (10초)
                encoding="utf-8",
            )

            # stdout과 stderr 모두에서 명확한 에러만 확인
            output = (result.stdout + result.stderr).lower()

            # 크레딧/인증 관련 명확한 에러 키워드
            critical_errors = [
                "doesn't have any credits",
                "purchase credits",
                "no credits",
                "credit balance",
                "billing",
                "payment required",
            ]

            # 명확한 크레딧/결제 에러가 있으면 사용 불가
            if any(error in output for error in critical_errors):
                return False

            # returncode 0이면 성공
            if result.returncode == 0:
                return True

            # 그 외의 경우는 CLI가 설치되어 있으므로 사용 가능으로 간주
            # (API 키 설정 등은 사용자가 실제 사용 시 해결할 문제)
            return True

        except subprocess.TimeoutExpired:
            # 타임아웃 = API가 느리지만 동작함 (사용 가능)
            return True
        except Exception:
            # 기타 에러는 CLI가 설치되어 있으므로 사용 가능으로 간주
            return True

    def initialize_models(self, force_refresh: bool = False) -> None:
        """사용 가능한 AI 모델 확인 및 초기화

        Args:
            force_refresh: True면 캐시 무시하고 강제로 재확인

        Raises:
            NoAvailableModelsError: 최소 리뷰어 수 미달 시
        """
        # 캐시 확인 (force_refresh가 아닐 때만)
        if not force_refresh:
            cached_keys = self.cache_manager.load_cached_models()
            if cached_keys:
                print("✅ 캐시된 AI 모델 정보 사용")
                self.available_models = {
                    key: ALL_AI_MODELS[key] for key in cached_keys if key in ALL_AI_MODELS
                }
                if len(self.available_models) >= MIN_REVIEWERS:
                    model_names = ", ".join(m.display_name for m in self.available_models.values())
                    print(f"🤖 사용 가능한 AI 모델: {model_names}\n")
                    return
                else:
                    print("⚠️  캐시된 모델이 최소 요구사항을 충족하지 못합니다. 재확인합니다...\n")

        # AI 모델 가용성 확인 (병렬 처리)
        print("🔍 AI 모델 가용성 확인 중... (병렬 처리)")
        print("-" * 60)

        # 초기화 (이전 데이터 제거)
        self.available_models.clear()
        available_keys = []

        # 병렬로 모든 모델 확인
        with ThreadPoolExecutor(max_workers=len(ALL_AI_MODELS)) as executor:
            # 모든 모델 확인 작업 제출
            future_to_model = {
                executor.submit(self.check_model_availability, key, model): (key, model)
                for key, model in ALL_AI_MODELS.items()
            }

            # 완료되는 대로 결과 처리
            for future in as_completed(future_to_model):
                model_key, model = future_to_model[future]
                try:
                    is_available = future.result()
                    if is_available:
                        self.available_models[model_key] = model
                        available_keys.append(model_key)
                        print(f"  ✅ {model.display_name} - 사용 가능")
                    else:
                        print(f"  ❌ {model.display_name} - 사용 불가")
                except Exception as e:
                    print(f"  ❌ {model.display_name} - 확인 실패: {e}")

        print("-" * 60)

        # 최소 리뷰어 수 확인
        if len(self.available_models) < MIN_REVIEWERS:
            error_msg = self._get_installation_guide(len(self.available_models))
            raise NoAvailableModelsError(error_msg)

        # 캐시 저장
        self.cache_manager.save_cached_models(available_keys)

        print(f"\n✅ {len(self.available_models)}개의 AI 리뷰어 사용 가능")
        model_names = ", ".join(m.display_name for m in self.available_models.values())
        print(f"🤖 사용 가능한 리뷰어: {model_names}\n")

    def get_available_models(self) -> Dict[str, AIModel]:
        """사용 가능한 모델 반환

        Returns:
            사용 가능한 AI 모델 딕셔너리
        """
        return self.available_models

    @staticmethod
    def _get_installation_guide(current_count: int) -> str:
        """AI CLI 설치 안내 메시지 생성

        Args:
            current_count: 현재 사용 가능한 AI 개수

        Returns:
            설치 안내 메시지
        """
        return f"""
❌ 최소 {MIN_REVIEWERS}개의 AI CLI가 필요하지만 {current_count}개만 사용 가능합니다!

AI 코드 리뷰 시스템은 여러 AI가 서로를 검증하는 방식이므로
최소 {MIN_REVIEWERS}개 이상의 AI CLI가 필요합니다.

다음 AI CLI 중 {MIN_REVIEWERS}개 이상을 설치해주세요:

1. Claude (Anthropic)
   - 설치: npm install -g @anthropic-ai/claude-cli
   - 문서: https://docs.anthropic.com/claude/docs/claude-cli

2. OpenAI GPT (Codex)
   - 설치: npm install -g @openai/codex-cli
   - 문서: https://platform.openai.com/docs/codex

3. Gemini (Google)
   - 설치: pip install google-generativeai
   - 문서: https://ai.google.dev/docs

4. Grok (xAI)
   - 설치: pip install grok-cli
   - 문서: https://x.ai/docs

💡 설치 후 다음을 실행하여 캐시를 갱신하세요:
   python ai_code_review.py --force-refresh

또는 캐시 파일을 직접 삭제:
   rm .ai_code_review_cache.json
"""
