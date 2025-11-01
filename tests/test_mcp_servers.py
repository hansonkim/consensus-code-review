"""MCP 서버 테스트

Pure Task Delegation Architecture:
- Git/Filesystem MCP 서버는 제거됨 (Python이 내부 처리)
- Review Orchestrator만 테스트
"""
import unittest
from src.mcp.manager import MCPManager
from src.mcp.review_orchestrator import ReviewOrchestrator


class TestReviewOrchestrator(unittest.TestCase):
    """Review Orchestrator 테스트 (Pure Task Delegation)"""

    def setUp(self):
        """테스트 설정"""
        self.orchestrator = ReviewOrchestrator()

    def test_create_review_session(self):
        """리뷰 세션 생성 테스트"""
        session_id = self.orchestrator.create_review_session("main", "HEAD")
        self.assertIsInstance(session_id, str)
        self.assertTrue(session_id.startswith("review_"))

    def test_get_available_tools(self):
        """사용 가능한 도구 목록 테스트"""
        tools = self.orchestrator.get_available_tools()
        self.assertIsInstance(tools, list)
        self.assertEqual(len(tools), 11)  # Review 도구 11개 (audit_code_review, run_code_review 포함)

        # 핵심 도구들 확인
        tool_names = [t["name"] for t in tools]
        self.assertIn("audit_code_review", tool_names)
        self.assertIn("run_code_review", tool_names)
        self.assertIn("create_review_session", tool_names)
        self.assertIn("submit_review", tool_names)
        self.assertIn("get_other_reviews", tool_names)
        self.assertIn("report_progress", tool_names)
        self.assertIn("get_progress", tool_names)

        # Git/Filesystem 도구는 없어야 함
        self.assertNotIn("get_diff", tool_names)
        self.assertNotIn("read_file", tool_names)

    def test_submit_and_get_review(self):
        """리뷰 제출 및 조회 테스트"""
        # 세션 생성
        session_id = self.orchestrator.create_review_session("main", "HEAD")

        # 리뷰 제출
        review_text = "# Test Review\n\nThis is a test review."
        self.orchestrator.submit_review(session_id, "TestAI", review_text)

        # 다른 AI가 리뷰 조회 (리스트 반환)
        other_reviews = self.orchestrator.get_other_reviews(session_id, "OtherAI")
        self.assertIsInstance(other_reviews, list)
        self.assertEqual(len(other_reviews), 1)
        self.assertEqual(other_reviews[0]["ai_name"], "TestAI")
        self.assertEqual(other_reviews[0]["review"], review_text)

    def test_progress_reporting(self):
        """실시간 진행 상황 보고 테스트"""
        # 세션 생성
        session_id = self.orchestrator.create_review_session("main", "HEAD")

        # Progress 보고
        result = self.orchestrator.report_progress(
            session_id,
            "TestAI",
            "Analyzing code..."
        )
        self.assertEqual(result["status"], "progress_recorded")

        # Progress 조회
        progress = self.orchestrator.get_progress(session_id)
        self.assertGreater(len(progress["updates"]), 0)
        self.assertEqual(progress["updates"][0]["ai_name"], "TestAI")


class TestMCPManager(unittest.TestCase):
    """MCPManager 테스트 (Pure Task Delegation)"""

    def setUp(self):
        """테스트 설정"""
        self.manager = MCPManager()

    def test_get_all_tools(self):
        """모든 도구 목록 조회 테스트"""
        tools = self.manager.get_all_tools()
        self.assertIsInstance(tools, dict)

        # review 서버만 있어야 함 (Git/Filesystem 제거됨)
        self.assertIn("review", tools)
        self.assertNotIn("filesystem", tools)
        self.assertNotIn("git", tools)

        # Review 도구 11개 확인 (audit_code_review, run_code_review 포함)
        self.assertEqual(len(tools["review"]), 11)

    def test_generate_tool_description(self):
        """도구 설명 문서 생성 테스트"""
        doc = self.manager.generate_tool_description()
        self.assertIsInstance(doc, str)
        self.assertIn("Available MCP Tools", doc)
        self.assertIn("Review", doc)

        # Git/Filesystem는 없어야 함
        self.assertNotIn("Filesystem", doc)
        self.assertNotIn("Git Tools", doc)

    def test_call_tool(self):
        """도구 호출 테스트"""
        # Review 세션 생성 호출
        session_id = self.manager.call_tool("review", "create_review_session", base="main")
        self.assertIsInstance(session_id, str)
        self.assertTrue(session_id.startswith("review_"))

    def test_call_tool_invalid_server(self):
        """존재하지 않는 서버 호출 테스트"""
        with self.assertRaises(ValueError):
            self.manager.call_tool("git", "some_tool")

        with self.assertRaises(ValueError):
            self.manager.call_tool("filesystem", "some_tool")

    def test_call_tool_invalid_tool(self):
        """존재하지 않는 도구 호출 테스트"""
        with self.assertRaises(ValueError):
            self.manager.call_tool("review", "invalid_tool")


if __name__ == "__main__":
    unittest.main()
