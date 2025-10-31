"""Consensus Calculator - Python이 자동으로 합의 수준 계산

AI에게 "3개 중 3개 동의"를 세게 하지 말고, Python이 객관적으로 계산합니다.
"""

import re
from typing import Dict, List, Set, Tuple


class Issue:
    """코드 리뷰 이슈"""

    def __init__(
        self,
        title: str,
        location: str,
        severity: str,
        description: str,
        found_by: str
    ):
        self.title = title
        self.location = location  # "file.py:42"
        self.severity = severity  # CRITICAL, MAJOR, MINOR
        self.description = description
        self.found_by = found_by  # AI 이름
        self.agreed_by: Set[str] = {found_by}
        self.disagreed_by: Set[str] = set()

    def __repr__(self):
        return f"Issue({self.title} at {self.location})"

    def get_key(self) -> str:
        """이슈를 unique하게 식별하는 키"""
        # 제목과 위치를 정규화하여 키 생성
        normalized_title = self.title.lower().strip()
        normalized_location = self.location.lower().strip()
        return f"{normalized_title}@{normalized_location}"


class ConsensusCalculator:
    """Consensus 계산기"""

    def __init__(self):
        self.issues: Dict[str, Issue] = {}  # {issue_key: Issue}

    def extract_issues_from_review(self, review: str, ai_name: str) -> List[Issue]:
        """리뷰 텍스트에서 이슈 추출

        Expected format:
        ### [CRITICAL] SQL Injection
        **Location**: `database.py:42`
        **Problem**: ...
        """
        issues = []

        # Pattern: ### [SEVERITY] Title
        pattern = r'###\s*\[([A-Z]+)\]\s*(.+?)(?=\n|$)'
        matches = re.finditer(pattern, review)

        for match in matches:
            severity = match.group(1)  # CRITICAL, MAJOR, MINOR
            title = match.group(2).strip()

            # Extract location
            start_pos = match.end()
            next_section = review.find('###', start_pos)
            if next_section == -1:
                section = review[start_pos:]
            else:
                section = review[start_pos:next_section]

            # Find **Location**: `file.py:42`
            location_match = re.search(r'\*\*Location\*\*:\s*`([^`]+)`', section)
            if location_match:
                location = location_match.group(1)
            else:
                # Try alternative formats
                location_match = re.search(r'Location:\s*([^\n]+)', section)
                location = location_match.group(1).strip() if location_match else "unknown"

            # Extract description (first paragraph after location)
            description_match = re.search(
                r'\*\*(?:Problem|Description)\*\*:\s*(.+?)(?=\n\*\*|\n###|$)',
                section,
                re.DOTALL
            )
            description = description_match.group(1).strip() if description_match else ""

            issue = Issue(
                title=title,
                location=location,
                severity=severity,
                description=description,
                found_by=ai_name
            )
            issues.append(issue)

        return issues

    def normalize_location(self, location: str) -> str:
        """위치 정규화

        Examples:
        - "src/database.py:42" -> "database.py:42"
        - "`database.py:42`" -> "database.py:42"
        - "database.py line 42" -> "database.py:42"
        """
        # Remove backticks
        location = location.replace('`', '').strip()

        # Extract filename and line number
        # Pattern: path/to/file.py:42
        match = re.search(r'([^/\\]+\.[a-z]+):?(\d+)?', location, re.IGNORECASE)
        if match:
            filename = match.group(1)
            line = match.group(2) if match.group(2) else ""
            return f"{filename}:{line}" if line else filename

        return location

    def is_same_issue(self, issue1: Issue, issue2: Issue) -> bool:
        """두 이슈가 같은 이슈인지 판단

        같은 이슈 조건:
        1. 위치가 같거나 매우 유사 (같은 파일, 가까운 줄)
        2. 제목에 공통 키워드가 많음 (예: "SQL injection" 공통)
        """
        # 1. 위치 비교
        loc1 = self.normalize_location(issue1.location)
        loc2 = self.normalize_location(issue2.location)

        # 정확히 같은 위치
        if loc1 == loc2:
            return True

        # 같은 파일, 가까운 줄 (±5 줄)
        match1 = re.match(r'([^:]+):(\d+)', loc1)
        match2 = re.match(r'([^:]+):(\d+)', loc2)
        if match1 and match2:
            file1, line1 = match1.group(1), int(match1.group(2))
            file2, line2 = match2.group(1), int(match2.group(2))
            if file1 == file2 and abs(line1 - line2) <= 5:
                return True

        # 2. 제목 유사도 (간단한 키워드 매칭)
        title1_words = set(issue1.title.lower().split())
        title2_words = set(issue2.title.lower().split())

        # Remove common words
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        title1_words -= stop_words
        title2_words -= stop_words

        if not title1_words or not title2_words:
            return False

        # Jaccard similarity
        intersection = len(title1_words & title2_words)
        union = len(title1_words | title2_words)
        similarity = intersection / union if union > 0 else 0

        return similarity > 0.5  # 50% 이상 유사하면 같은 이슈

    def add_issue(self, issue: Issue):
        """이슈 추가 (중복 체크)"""
        # 기존 이슈와 비교
        for existing_key, existing_issue in self.issues.items():
            if self.is_same_issue(issue, existing_issue):
                # 같은 이슈 발견 - 동의자에 추가
                existing_issue.agreed_by.add(issue.found_by)
                return

        # 새로운 이슈 추가
        key = issue.get_key()
        self.issues[key] = issue

    def parse_critique_agreements(self, critique: str, ai_name: str) -> Tuple[Set[str], Set[str]]:
        """Round 2 비판에서 동의/반대 파악

        Expected format:
        ## Issues I Agree With
        - [AI name]'s finding about [issue]: ✅ Correct

        ## Issues I Disagree With
        - [AI name]'s finding about [issue]: ❌ Incorrect
        """
        agreements = set()
        disagreements = set()

        # Find agreement section
        agree_section = re.search(
            r'##\s*Issues I Agree With(.+?)(?=##|$)',
            critique,
            re.DOTALL
        )
        if agree_section:
            agree_text = agree_section.group(1)
            # Extract issue titles/locations
            for line in agree_text.split('\n'):
                if '✅' in line or 'agree' in line.lower():
                    # Try to extract issue reference
                    # Pattern: "SQL injection" or "database.py:42"
                    issue_refs = re.findall(r'["\']([^"\']+)["\']', line)
                    agreements.update(issue_refs)

        # Find disagreement section
        disagree_section = re.search(
            r'##\s*Issues I Disagree With(.+?)(?=##|$)',
            critique,
            re.DOTALL
        )
        if disagree_section:
            disagree_text = disagree_section.group(1)
            for line in disagree_text.split('\n'):
                if '❌' in line or 'disagree' in line.lower():
                    issue_refs = re.findall(r'["\']([^"\']+)["\']', line)
                    disagreements.update(issue_refs)

        return agreements, disagreements

    def apply_critique(self, critique: str, ai_name: str):
        """Round 2 비판 적용"""
        agreements, disagreements = self.parse_critique_agreements(critique, ai_name)

        # Apply agreements
        for issue_key, issue in self.issues.items():
            # Check if this AI agrees with this issue
            for agreement_ref in agreements:
                if (agreement_ref.lower() in issue.title.lower() or
                    agreement_ref in issue.location):
                    issue.agreed_by.add(ai_name)

            # Check if this AI disagrees
            for disagreement_ref in disagreements:
                if (disagreement_ref.lower() in issue.title.lower() or
                    disagreement_ref in issue.location):
                    issue.disagreed_by.add(ai_name)

    def calculate_consensus(self, total_ais: int) -> Dict[str, List[Issue]]:
        """Consensus 수준 계산

        Returns:
            {
                'critical': [...],  # 모든 AI 동의 (100%)
                'major': [...],     # 대부분 동의 (≥66%)
                'minor': [...],     # 일부 동의 (≥33%)
                'disputed': [...]   # 논쟁 중
            }
        """
        result = {
            'critical': [],
            'major': [],
            'minor': [],
            'disputed': []
        }

        for issue in self.issues.values():
            agreed_count = len(issue.agreed_by)
            disagreed_count = len(issue.disagreed_by)

            # Consensus percentage
            consensus_pct = agreed_count / total_ais if total_ais > 0 else 0

            # Has disagreement?
            is_disputed = disagreed_count > 0

            # Classify
            if consensus_pct == 1.0 and not is_disputed:
                result['critical'].append(issue)
            elif consensus_pct >= 0.66 and not is_disputed:
                result['major'].append(issue)
            elif consensus_pct >= 0.33:
                result['minor'].append(issue)

            if is_disputed:
                result['disputed'].append(issue)

        # Sort by severity and agreed count
        severity_order = {'CRITICAL': 0, 'MAJOR': 1, 'MINOR': 2}
        for category in result:
            result[category].sort(
                key=lambda x: (
                    severity_order.get(x.severity, 3),
                    -len(x.agreed_by)
                )
            )

        return result

    def format_issue(self, issue: Issue, total_ais: int) -> str:
        """이슈를 텍스트로 포맷"""
        agreed_count = len(issue.agreed_by)
        disagreed_count = len(issue.disagreed_by)
        consensus_pct = (agreed_count / total_ais * 100) if total_ais > 0 else 0

        result = f"""### [{issue.severity}] {issue.title}
**Location**: `{issue.location}`
**Consensus**: {agreed_count}/{total_ais} AIs agree ({consensus_pct:.0f}%)
**Found by**: {', '.join(sorted(issue.agreed_by))}"""

        if disagreed_count > 0:
            result += f"\n**Disagreed by**: {', '.join(sorted(issue.disagreed_by))}"

        result += f"\n**Problem**: {issue.description[:200]}{'...' if len(issue.description) > 200 else ''}"

        return result

    def format_consensus(self, consensus: Dict[str, List[Issue]], total_ais: int) -> str:
        """Consensus 결과를 텍스트로 포맷"""
        output = []

        output.append(f"# Consensus Analysis ({total_ais} AIs)\n")

        # Summary
        output.append("## Summary")
        output.append(f"- **Critical Issues** (all AIs agree): {len(consensus['critical'])}")
        output.append(f"- **Major Issues** (≥66% agree): {len(consensus['major'])}")
        output.append(f"- **Minor Issues** (≥33% agree): {len(consensus['minor'])}")
        output.append(f"- **Disputed Issues**: {len(consensus['disputed'])}")
        output.append("")

        # Critical issues
        if consensus['critical']:
            output.append("## Critical Issues (Must Fix - 100% Agreement)")
            output.append("")
            for issue in consensus['critical']:
                output.append(self.format_issue(issue, total_ais))
                output.append("")

        # Major issues
        if consensus['major']:
            output.append("## Major Issues (Should Fix - ≥66% Agreement)")
            output.append("")
            for issue in consensus['major']:
                output.append(self.format_issue(issue, total_ais))
                output.append("")

        # Minor issues
        if consensus['minor']:
            output.append("## Minor Issues (Consider Fixing - ≥33% Agreement)")
            output.append("")
            for issue in consensus['minor']:
                output.append(self.format_issue(issue, total_ais))
                output.append("")

        # Disputed
        if consensus['disputed']:
            output.append("## Disputed Issues (No Consensus)")
            output.append("")
            for issue in consensus['disputed']:
                output.append(self.format_issue(issue, total_ais))
                output.append("")

        return "\n".join(output)


def calculate_consensus_from_session(session_info: Dict) -> Dict[str, List[Issue]]:
    """세션 정보에서 consensus 계산

    Args:
        session_info: MCP의 get_session_info() 결과

    Returns:
        {
            'critical': [...],
            'major': [...],
            'minor': [...],
            'disputed': [...]
        }
    """
    calculator = ConsensusCalculator()

    participating_ais = session_info.get('participating_ais', [])
    reviews = session_info.get('reviews', {})

    # Round 1: 이슈 추출
    for ai_name in participating_ais:
        if ai_name in reviews:
            rounds = reviews[ai_name]
            if 1 in rounds:  # Round 1 리뷰
                review_content = rounds[1].get('content', '')
                issues = calculator.extract_issues_from_review(review_content, ai_name)
                for issue in issues:
                    calculator.add_issue(issue)

    # Round 2: 비판 적용
    for ai_name in participating_ais:
        if ai_name in reviews:
            rounds = reviews[ai_name]
            if 2 in rounds:  # Round 2 비판
                critique_content = rounds[2].get('content', '')
                calculator.apply_critique(critique_content, ai_name)

    # Consensus 계산
    total_ais = len(participating_ais)
    consensus = calculator.calculate_consensus(total_ais)

    return consensus, calculator
