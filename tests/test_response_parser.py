"""ResponseParser 테스트"""

import pytest

from ai_code_review.models import Severity
from ai_code_review.response_parser import ResponseParser


@pytest.fixture
def parser():
    """파서 fixture"""
    return ResponseParser()


class TestJSONParsing:
    """JSON 형식 파싱 테스트"""

    def test_parse_json_format(self, parser):
        """JSON 형식 파싱"""
        response = """
        ```json
        {
          "issues": [
            {
              "severity": "high",
              "category": "보안",
              "line": 10,
              "description": "SQL 인젝션 취약점",
              "code": "query = f'SELECT * FROM users WHERE id={user_id}'",
              "suggestion": "parameterized query 사용"
            }
          ]
        }
        ```
        """

        issues = parser.parse_review_response(response, "claude", "test.py")

        assert len(issues) == 1
        assert issues[0].severity == Severity.CRITICAL.value
        assert issues[0].title == "보안"
        assert issues[0].location == "test.py:10"
        assert "SQL 인젝션" in issues[0].description

    def test_parse_multiple_issues(self, parser):
        """여러 이슈 파싱"""
        response = """
        ```json
        {
          "issues": [
            {
              "severity": "high",
              "category": "보안",
              "line": 10,
              "description": "이슈1",
              "code": "code1",
              "suggestion": "제안1"
            },
            {
              "severity": "medium",
              "category": "성능",
              "line": 20,
              "description": "이슈2",
              "code": "code2",
              "suggestion": "제안2"
            }
          ]
        }
        ```
        """

        issues = parser.parse_review_response(response, "gemini", "app.py")

        assert len(issues) == 2
        assert issues[0].severity == Severity.CRITICAL.value
        assert issues[1].severity == Severity.MAJOR.value


class TestMarkdownParsing:
    """마크다운 형식 파싱 테스트"""

    def test_parse_markdown_format(self, parser):
        """마크다운 형식 파싱"""
        response = """
        ### [CRITICAL] SQL Injection
        - 위치: database.py:45
        - 설명: SQL 인젝션 취약점 발견
        - 코드: ```python
query = f"SELECT * FROM users WHERE id={user_id}"
```
        - 제안: parameterized query 사용
        """

        issues = parser.parse_review_response(response, "claude", "database.py")

        assert len(issues) >= 1
        assert issues[0].severity == Severity.CRITICAL.value
        assert "SQL Injection" in issues[0].title


class TestTextParsing:
    """텍스트 형식 파싱 테스트"""

    def test_parse_text_format(self, parser):
        """일반 텍스트 형식 파싱"""
        response = """
        CRITICAL: SQL injection vulnerability found at line 10
        The code uses string formatting which is vulnerable to SQL injection.
        ```python
        query = f"SELECT * FROM users WHERE id={user_id}"
        ```

        MAJOR: Missing error handling at line 25
        """

        issues = parser.parse_review_response(response, "grok", "app.py")

        assert len(issues) >= 1
        assert any(i.severity == Severity.CRITICAL.value for i in issues)


class TestSeverityNormalization:
    """심각도 정규화 테스트"""

    def test_severity_mapping(self, parser):
        """심각도 키워드 매핑"""
        test_cases = [
            ("critical", Severity.CRITICAL.value),
            ("high", Severity.CRITICAL.value),
            ("major", Severity.MAJOR.value),
            ("medium", Severity.MAJOR.value),
            ("minor", Severity.MINOR.value),
            ("low", Severity.MINOR.value),
            ("suggestion", Severity.SUGGESTION.value),
        ]

        for keyword, expected in test_cases:
            assert parser.severity_keywords[keyword] == expected


class TestVerificationParsing:
    """검증 응답 파싱 테스트"""

    def test_parse_verification_response(self, parser):
        """검증 응답 파싱"""
        response = """
        ```json
        {
          "validated_issues": [1, 2, 3],
          "new_issues": [],
          "false_positives": [4],
          "confidence_score": 9
        }
        ```
        """

        result = parser.parse_verification_response(response, "claude")

        assert result["confidence_score"] == 9
        assert len(result["validated_issues"]) == 3
        assert len(result["false_positives"]) == 1


class TestConsensusParsing:
    """합의 응답 파싱 테스트"""

    def test_parse_consensus_response(self, parser):
        """합의 응답 파싱"""
        response = """
        ```json
        {
          "consensus_summary": "전체 코드 품질은 양호함",
          "critical_issues": [
            {
              "severity": "high",
              "category": "보안",
              "line": 10,
              "description": "SQL 인젝션",
              "code": "query",
              "suggestion": "수정 필요"
            }
          ],
          "action_items": [
            {"description": "SQL 쿼리 수정", "priority": "immediate"}
          ]
        }
        ```
        """

        result = parser.parse_consensus_response(response, "app.py")

        assert "양호" in result["summary"]
        assert len(result["critical_issues"]) == 1
        assert len(result["action_items"]) == 1


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_response(self, parser):
        """빈 응답 처리"""
        issues = parser.parse_review_response("", "claude", "test.py")
        assert len(issues) == 0

    def test_invalid_json(self, parser):
        """잘못된 JSON 처리"""
        response = """
        ```json
        { "issues": [ invalid json }
        ```
        """
        issues = parser.parse_review_response(response, "claude", "test.py")
        # 파싱 실패 시 빈 리스트 또는 다른 형식으로 파싱 시도
        assert isinstance(issues, list)

    def test_no_file_path(self, parser):
        """파일 경로 없이 파싱"""
        response = """
        ```json
        {
          "issues": [
            {
              "severity": "high",
              "category": "테스트",
              "line": 5,
              "description": "설명",
              "code": "코드",
              "suggestion": "제안"
            }
          ]
        }
        ```
        """

        issues = parser.parse_review_response(response, "claude")

        assert len(issues) == 1
        assert "line 5" in issues[0].location
