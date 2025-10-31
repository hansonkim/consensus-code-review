"""AI 응답 파싱 모듈

AI로부터 받은 리뷰 응답을 ReviewIssue 객체로 파싱합니다.
"""

import json
import re
from typing import Any, Dict, List, Optional

from ai_code_review.models import ReviewIssue, Severity


class ResponseParser:
    """AI 응답 파서"""

    def __init__(self):
        """초기화"""
        self.severity_keywords = {
            "critical": Severity.CRITICAL.value,
            "high": Severity.CRITICAL.value,
            "major": Severity.MAJOR.value,
            "medium": Severity.MAJOR.value,
            "minor": Severity.MINOR.value,
            "low": Severity.MINOR.value,
            "suggestion": Severity.SUGGESTION.value,
            "info": Severity.SUGGESTION.value,
        }

    def parse_review_response(
        self, response: str, reviewer: str, file_path: str = ""
    ) -> List[ReviewIssue]:
        """AI 리뷰 응답을 ReviewIssue 리스트로 파싱

        Args:
            response: AI 응답 텍스트
            reviewer: 리뷰어 이름 (AI 이름)
            file_path: 리뷰 대상 파일 경로

        Returns:
            ReviewIssue 객체 리스트
        """
        # JSON 형식 파싱 시도
        issues = self._try_parse_json(response, reviewer, file_path)
        if issues:
            return issues

        # 마크다운 형식 파싱 시도
        issues = self._try_parse_markdown(response, reviewer, file_path)
        if issues:
            return issues

        # 텍스트 형식 파싱 시도
        return self._try_parse_text(response, reviewer, file_path)

    def _try_parse_json(
        self, response: str, reviewer: str, file_path: str
    ) -> List[ReviewIssue]:
        """JSON 형식 응답 파싱"""
        try:
            # JSON 블록 추출
            json_match = re.search(r"```json\s*\n(.*?)\n```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # JSON 객체 직접 추출
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if not json_match:
                    return []
                json_str = json_match.group(0)

            data = json.loads(json_str)
            return self._parse_json_data(data, reviewer, file_path)

        except (json.JSONDecodeError, KeyError, ValueError):
            return []

    def _parse_json_data(
        self, data: Dict[str, Any], reviewer: str, file_path: str
    ) -> List[ReviewIssue]:
        """JSON 데이터를 ReviewIssue로 변환"""
        issues = []

        # issues 키에서 이슈 추출
        issues_data = data.get("issues", [])
        if not isinstance(issues_data, list):
            return []

        for issue_data in issues_data:
            try:
                issue = self._create_issue_from_dict(issue_data, reviewer, file_path)
                if issue:
                    issues.append(issue)
            except (ValueError, KeyError):
                continue

        return issues

    def _create_issue_from_dict(
        self, data: Dict[str, Any], reviewer: str, file_path: str
    ) -> Optional[ReviewIssue]:
        """딕셔너리에서 ReviewIssue 생성"""
        # 심각도 정규화
        severity_raw = str(data.get("severity", "minor")).lower()
        severity = self.severity_keywords.get(severity_raw, Severity.MINOR.value)

        # 위치 정보 생성
        line = data.get("line", data.get("line_number", 0))
        location = f"{file_path}:{line}" if file_path else f"line {line}"

        # 이슈 생성
        return ReviewIssue(
            severity=severity,
            title=data.get("category", data.get("title", "Issue")),
            location=location,
            description=data.get("description", ""),
            code_snippet=data.get("code", data.get("code_snippet", "")),
            suggestion=data.get("suggestion", data.get("fix", "")),
            reviewer=reviewer,
        )

    def _try_parse_markdown(
        self, response: str, reviewer: str, file_path: str
    ) -> List[ReviewIssue]:
        """마크다운 형식 응답 파싱

        형식:
        ### [SEVERITY] 이슈 제목
        - 위치: file.py:10
        - 설명: ...
        - 코드: ...
        - 제안: ...
        """
        issues = []

        # 이슈 블록 패턴
        issue_pattern = r"###?\s*\[([^\]]+)\]\s*(.+?)(?=###|$)"
        matches = re.finditer(issue_pattern, response, re.DOTALL)

        for match in matches:
            severity_raw = match.group(1).strip().lower()
            content = match.group(2).strip()

            # 심각도 정규화
            severity = self.severity_keywords.get(
                severity_raw, Severity.MINOR.value
            )

            # 내용 파싱
            title_match = re.search(r"^(.+?)(?:\n|$)", content)
            title = title_match.group(1).strip() if title_match else "Issue"

            location_match = re.search(r"위치[:：]\s*(.+?)(?:\n|$)", content)
            location = (
                location_match.group(1).strip()
                if location_match
                else f"{file_path}:0"
            )

            desc_match = re.search(r"설명[:：]\s*(.+?)(?:\n-|\n$|$)", content, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""

            code_match = re.search(r"코드[:：]\s*```.*?\n(.*?)```", content, re.DOTALL)
            code_snippet = code_match.group(1).strip() if code_match else ""

            sugg_match = re.search(r"제안[:：]\s*(.+?)(?:\n###|$)", content, re.DOTALL)
            suggestion = sugg_match.group(1).strip() if sugg_match else ""

            try:
                issue = ReviewIssue(
                    severity=severity,
                    title=title,
                    location=location,
                    description=description,
                    code_snippet=code_snippet,
                    suggestion=suggestion,
                    reviewer=reviewer,
                )
                issues.append(issue)
            except ValueError:
                continue

        return issues

    def _try_parse_text(
        self, response: str, reviewer: str, file_path: str
    ) -> List[ReviewIssue]:
        """일반 텍스트 형식 응답 파싱"""
        issues = []

        # 심각도 키워드로 이슈 분리
        severity_pattern = r"\b(CRITICAL|HIGH|MAJOR|MEDIUM|MINOR|LOW|SUGGESTION)\b"
        parts = re.split(severity_pattern, response, flags=re.IGNORECASE)

        for i in range(1, len(parts), 2):
            if i + 1 >= len(parts):
                break

            severity_raw = parts[i].lower()
            content = parts[i + 1].strip()

            # 심각도 정규화
            severity = self.severity_keywords.get(
                severity_raw, Severity.MINOR.value
            )

            # 제목 추출 (첫 줄 또는 첫 문장)
            title_match = re.search(r"^(.+?)(?:\n|[.。])", content)
            title = title_match.group(1).strip() if title_match else "Issue"

            # 라인 번호 추출
            line_match = re.search(r"line\s*(\d+)", content, re.IGNORECASE)
            line = line_match.group(1) if line_match else "0"
            location = f"{file_path}:{line}" if file_path else f"line {line}"

            # 코드 블록 추출
            code_match = re.search(r"```.*?\n(.*?)```", content, re.DOTALL)
            code_snippet = code_match.group(1).strip() if code_match else ""

            try:
                issue = ReviewIssue(
                    severity=severity,
                    title=title[:100],  # 제목 길이 제한
                    location=location,
                    description=content[:500],  # 설명 길이 제한
                    code_snippet=code_snippet,
                    suggestion="",  # 텍스트 파싱에서는 제안 분리 어려움
                    reviewer=reviewer,
                )
                issues.append(issue)
            except ValueError:
                continue

        return issues

    def parse_verification_response(
        self, response: str, reviewer: str
    ) -> Dict[str, Any]:
        """Phase 2 검증 응답 파싱

        Returns:
            {
                "validated_issues": [...],
                "new_issues": [...],
                "false_positives": [...],
                "confidence_score": 1-10
            }
        """
        result = {
            "validated_issues": [],
            "new_issues": [],
            "false_positives": [],
            "confidence_score": 7,
        }

        try:
            # JSON 파싱 시도 - 더 관대한 정규식
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if not json_match:
                # json 블록이 없으면 JSON 객체 직접 찾기
                json_match = re.search(r'\{[\s\S]*?"confidence_score"[\s\S]*?\}', response)

            if json_match:
                json_str = json_match.group(1) if json_match.lastindex else json_match.group(0)
                data = json.loads(json_str.strip())
                # result를 직접 업데이트
                result.update(data)
        except (json.JSONDecodeError, KeyError, AttributeError):
            pass

        return result

    def parse_consensus_response(
        self, response: str, file_path: str = ""
    ) -> Dict[str, Any]:
        """Phase 3 합의 응답 파싱

        Returns:
            {
                "summary": "...",
                "critical_issues": [...],
                "moderate_issues": [...],
                "minor_issues": [...],
                "action_items": [...]
            }
        """
        result = {
            "summary": "",
            "critical_issues": [],
            "moderate_issues": [],
            "minor_issues": [],
            "action_items": [],
        }

        try:
            # JSON 파싱 시도 - 더 관대한 정규식
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if not json_match:
                # json 블록이 없으면 JSON 객체 직접 찾기
                json_match = re.search(r'\{[\s\S]*?"consensus_summary"[\s\S]*?\}', response)

            if json_match:
                json_str = json_match.group(1) if json_match.lastindex else json_match.group(0)
                data = json.loads(json_str.strip())

                # 요약 추출 (여러 키 시도)
                result["summary"] = data.get("consensus_summary", data.get("summary", ""))

                # 이슈 추출 및 변환
                for severity_key in ["critical_issues", "moderate_issues", "minor_issues"]:
                    issues_data = data.get(severity_key, [])
                    issues = []
                    for issue_data in issues_data:
                        issue = self._create_issue_from_dict(
                            issue_data, "consensus", file_path
                        )
                        if issue:
                            issues.append(issue)
                    result[severity_key] = issues

                # 액션 아이템 추출
                result["action_items"] = data.get("action_items", [])

        except (json.JSONDecodeError, KeyError, ValueError, AttributeError):
            # JSON 파싱 실패 시 텍스트에서 요약만 추출
            summary_match = re.search(
                r"(?:요약|summary)[:：]\s*(.+?)(?:\n\n|\n#|$)",
                response,
                re.IGNORECASE | re.DOTALL
            )
            if summary_match:
                result["summary"] = summary_match.group(1).strip()

        return result
