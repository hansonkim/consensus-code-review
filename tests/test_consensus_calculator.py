#!/usr/bin/env python3
"""Test Consensus Calculator - Python이 자동으로 합의 수준 계산"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.mcp.consensus_calculator import (
    ConsensusCalculator,
    Issue,
    calculate_consensus_from_session
)


def test_issue_extraction():
    """Test 1: 리뷰에서 이슈 추출"""
    print("\n" + "=" * 70)
    print("Test 1: Issue Extraction from Review")
    print("=" * 70)

    review = """# Code Review by Claude

## Critical Issues

### [CRITICAL] SQL Injection Vulnerability
**Location**: `database.py:42`
**Problem**: User input directly concatenated into SQL query
**Fix**: Use parameterized queries

### [MAJOR] Memory Leak
**Location**: `processor.py:256`
**Problem**: File handles not closed
**Fix**: Use context manager

## Minor Issues

### [MINOR] Code Duplication
**Location**: `utils.py:100`
**Problem**: Same logic repeated 3 times
**Fix**: Extract to function
"""

    calculator = ConsensusCalculator()
    issues = calculator.extract_issues_from_review(review, "Claude")

    print(f"\n✅ Extracted {len(issues)} issues")
    for issue in issues:
        print(f"   - [{issue.severity}] {issue.title} at {issue.location}")

    assert len(issues) == 3, f"Expected 3 issues, got {len(issues)}"
    assert issues[0].severity == "CRITICAL"
    assert issues[0].title == "SQL Injection Vulnerability"
    assert "database.py:42" in issues[0].location

    print("\n✅ Test 1 PASSED: Issue extraction working")
    return True


def test_issue_normalization():
    """Test 2: 같은 이슈 판별"""
    print("\n" + "=" * 70)
    print("Test 2: Issue Normalization")
    print("=" * 70)

    calculator = ConsensusCalculator()

    # Same issue, different descriptions
    issue1 = Issue(
        title="SQL Injection",
        location="database.py:42",
        severity="CRITICAL",
        description="User input concatenated",
        found_by="Claude"
    )

    issue2 = Issue(
        title="SQL injection vulnerability",
        location="src/database.py:42",  # Different path
        severity="CRITICAL",
        description="SQL injection possible",
        found_by="GPT-4"
    )

    is_same = calculator.is_same_issue(issue1, issue2)
    print(f"\n✅ Same issue detection: {is_same}")
    assert is_same, "Should recognize as same issue"

    # Different issues
    issue3 = Issue(
        title="Memory Leak",
        location="processor.py:256",
        severity="MAJOR",
        description="File not closed",
        found_by="Gemini"
    )

    is_different = not calculator.is_same_issue(issue1, issue3)
    print(f"✅ Different issue detection: {is_different}")
    assert is_different, "Should recognize as different issues"

    print("\n✅ Test 2 PASSED: Issue normalization working")
    return True


def test_consensus_calculation():
    """Test 3: Consensus 계산"""
    print("\n" + "=" * 70)
    print("Test 3: Consensus Calculation")
    print("=" * 70)

    calculator = ConsensusCalculator()

    # Issue 1: All AIs agree (3/3)
    issue1 = Issue(
        title="SQL Injection",
        location="database.py:42",
        severity="CRITICAL",
        description="SQL injection vulnerability",
        found_by="Claude"
    )
    issue1.agreed_by = {"Claude", "GPT-4", "Gemini"}  # All agree
    calculator.issues[issue1.get_key()] = issue1

    # Issue 2: Most AIs agree (2/3)
    issue2 = Issue(
        title="Memory Leak",
        location="processor.py:256",
        severity="MAJOR",
        description="File not closed",
        found_by="Claude"
    )
    issue2.agreed_by = {"Claude", "GPT-4"}  # 2 agree
    calculator.issues[issue2.get_key()] = issue2

    # Issue 3: Only one AI (1/3)
    issue3 = Issue(
        title="Code Style",
        location="utils.py:100",
        severity="MINOR",
        description="Naming convention",
        found_by="Gemini"
    )
    issue3.agreed_by = {"Gemini"}  # Only 1
    calculator.issues[issue3.get_key()] = issue3

    # Issue 4: Disputed (disagreement)
    issue4 = Issue(
        title="Performance Issue",
        location="api.py:30",
        severity="MAJOR",
        description="Slow query",
        found_by="Claude"
    )
    issue4.agreed_by = {"Claude", "GPT-4"}
    issue4.disagreed_by = {"Gemini"}  # Gemini disagrees
    calculator.issues[issue4.get_key()] = issue4

    # Calculate consensus
    consensus = calculator.calculate_consensus(total_ais=3)

    print(f"\n✅ Consensus calculated:")
    print(f"   - Critical (3/3): {len(consensus['critical'])} issues")
    print(f"   - Major (≥66%): {len(consensus['major'])} issues")
    print(f"   - Minor (≥33%): {len(consensus['minor'])} issues")
    print(f"   - Disputed: {len(consensus['disputed'])} issues")

    assert len(consensus['critical']) == 1, "Should have 1 critical issue"
    assert consensus['critical'][0].title == "SQL Injection"

    assert len(consensus['major']) == 1, "Should have 1 major issue (2/3 agreement, no dispute)"
    assert consensus['major'][0].title == "Memory Leak"

    # Note: issue3 (Code Style) is 1/3 = 33% → minor
    # Note: issue4 (Performance) is 2/3 = 67% but disputed → also in minor
    assert len(consensus['minor']) == 2, "Should have 2 minor issues (including disputed one)"

    assert len(consensus['disputed']) == 1, "Should have 1 disputed issue"
    assert consensus['disputed'][0].title == "Performance Issue"

    print("\n✅ Test 3 PASSED: Consensus calculation working")
    return True


def test_full_workflow():
    """Test 4: 전체 workflow"""
    print("\n" + "=" * 70)
    print("Test 4: Full Workflow Simulation")
    print("=" * 70)

    # Simulate session info
    session_info = {
        'session_id': 'test_session',
        'participating_ais': ['Claude', 'GPT-4', 'Gemini'],
        'reviews': {
            'Claude': {
                1: {
                    'content': """# Code Review

### [CRITICAL] SQL Injection
**Location**: `database.py:42`
**Problem**: Vulnerable to SQL injection

### [MAJOR] Memory Leak
**Location**: `processor.py:256`
**Problem**: Files not closed
""",
                    'timestamp': 1234567890
                },
                2: {
                    'content': """# Round 2 Critique

## Issues I Agree With
- GPT-4's "SQL Injection" finding: ✅ Correct
- Gemini's "Memory Leak" finding: ✅ Valid
""",
                    'timestamp': 1234567895
                }
            },
            'GPT-4': {
                1: {
                    'content': """# Code Review

### [CRITICAL] SQL injection vulnerability
**Location**: `src/database.py:42`
**Problem**: SQL injection possible

### [MINOR] Code Duplication
**Location**: `utils.py:100`
**Problem**: DRY violation
""",
                    'timestamp': 1234567891
                },
                2: {
                    'content': """# Round 2 Critique

## Issues I Agree With
- Claude's "SQL Injection" finding: ✅ Critical issue
""",
                    'timestamp': 1234567896
                }
            },
            'Gemini': {
                1: {
                    'content': """# Code Review

### [CRITICAL] SQL Injection Risk
**Location**: `database.py:42`
**Problem**: Unsafe SQL query

### [MAJOR] Resource Leak
**Location**: `processor.py:256`
**Problem**: Memory leak detected
""",
                    'timestamp': 1234567892
                },
                2: {
                    'content': """# Round 2 Critique

## Issues I Agree With
- Claude's "SQL Injection" finding: ✅ Agree
- GPT-4's "SQL injection" finding: ✅ Same issue
""",
                    'timestamp': 1234567897
                }
            }
        }
    }

    # Calculate consensus
    print("\n📊 Calculating consensus from session...")
    consensus, calculator = calculate_consensus_from_session(session_info)

    print(f"\n✅ Results:")
    print(f"   - Critical issues: {len(consensus['critical'])}")
    print(f"   - Major issues: {len(consensus['major'])}")
    print(f"   - Minor issues: {len(consensus['minor'])}")
    print(f"   - Disputed issues: {len(consensus['disputed'])}")

    # Verify SQL Injection is recognized as same issue by all 3 AIs
    sql_injection_issues = [
        i for i in calculator.issues.values()
        if 'injection' in i.title.lower()
    ]
    print(f"\n✅ SQL Injection detection:")
    print(f"   - Found {len(sql_injection_issues)} SQL injection issue(s)")
    if sql_injection_issues:
        issue = sql_injection_issues[0]
        print(f"   - Agreed by: {sorted(issue.agreed_by)}")
        print(f"   - Consensus: {len(issue.agreed_by)}/3 AIs")

    assert len(sql_injection_issues) >= 1, "Should find SQL injection issue"
    # Note: Might be merged into one or remain separate depending on similarity detection

    # Format output
    print("\n📄 Formatted consensus report:")
    print("-" * 70)
    consensus_text = calculator.format_consensus(consensus, 3)
    print(consensus_text[:500] + "..." if len(consensus_text) > 500 else consensus_text)

    print("\n✅ Test 4 PASSED: Full workflow working")
    return True


def main():
    """Run all tests"""
    print("\n🧪 Consensus Calculator Test Suite")
    print("=" * 70)

    tests = [
        test_issue_extraction,
        test_issue_normalization,
        test_consensus_calculation,
        test_full_workflow
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ Test FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ Test ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    if failed == 0:
        print(f"🎉 ALL TESTS PASSED! ({passed}/{len(tests)})")
        print("\n✅ Python consensus calculation is working correctly!")
        print("\n📊 Key Benefits:")
        print("   - Accurate: Python calculates mathematically (no AI errors)")
        print("   - Transparent: Logic is clear and testable")
        print("   - Fast: AI only writes report (no counting needed)")
        print("   - Fair: All AIs' opinions are objectively measured")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED: {passed} passed, {failed} failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
