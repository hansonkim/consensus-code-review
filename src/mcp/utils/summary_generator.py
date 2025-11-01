"""Summary generator with templates for run and audit reviews

Generates human-readable summary.md files with:
- Issue classification and prioritization
- Key findings extraction
- Recommendations
"""

import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from ..review_orchestrator import ReviewSession


def classify_issues(review_text: str) -> Dict[str, List[Dict[str, str]]]:
    """Classify issues from review text by priority

    Args:
        review_text: Final review content

    Returns:
        Dictionary mapping priority levels to issue lists
    """
    issues = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
        "suggestions": []
    }

    # Simple pattern matching for common issue indicators
    lines = review_text.split("\n")
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Look for priority indicators
        if any(marker in line_lower for marker in ["🔴", "critical", "security", "vulnerability"]):
            issues["critical"].append({"text": line, "context": _get_context(lines, i)})
        elif any(marker in line_lower for marker in ["🟠", "high", "important", "major"]):
            issues["high"].append({"text": line, "context": _get_context(lines, i)})
        elif any(marker in line_lower for marker in ["🟡", "medium", "moderate"]):
            issues["medium"].append({"text": line, "context": _get_context(lines, i)})
        elif any(marker in line_lower for marker in ["🟢", "low", "minor"]):
            issues["low"].append({"text": line, "context": _get_context(lines, i)})
        elif any(marker in line_lower for marker in ["💡", "suggestion", "consider", "could"]):
            issues["suggestions"].append({"text": line, "context": _get_context(lines, i)})

    return issues


def _get_context(lines: List[str], index: int, context_lines: int = 2) -> str:
    """Get surrounding context for an issue"""
    start = max(0, index - context_lines)
    end = min(len(lines), index + context_lines + 1)
    return "\n".join(lines[start:end])


def extract_key_findings(review_text: str, max_findings: int = 10) -> List[str]:
    """Extract key findings from review

    Args:
        review_text: Final review content
        max_findings: Maximum number of findings to extract

    Returns:
        List of key finding strings
    """
    findings = []
    
    # Look for section headers indicating key points
    lines = review_text.split("\n")
    
    for line in lines:
        line_stripped = line.strip()
        
        # Look for bullet points or numbered lists
        if re.match(r"^[-*•]\s+\*\*.*\*\*", line_stripped):
            findings.append(line_stripped.lstrip("-*• "))
        elif re.match(r"^\d+\.\s+\*\*.*\*\*", line_stripped):
            findings.append(line_stripped.split(". ", 1)[1] if ". " in line_stripped else line_stripped)
    
    # If no structured findings, extract sentences with key phrases
    if not findings:
        key_phrases = ["found", "identified", "issue", "problem", "recommend", "should", "must"]
        for line in lines:
            if any(phrase in line.lower() for phrase in key_phrases):
                findings.append(line.strip())
    
    return findings[:max_findings]


async def write_summary_md(
    session: "ReviewSession",
    base_dir: str,
    review_type: str
) -> str:
    """Generate and write summary.md file

    Args:
        session: Review session
        base_dir: Base directory for artifacts
        review_type: "run" or "audit"

    Returns:
        Path to summary file
    """
    summary_path = Path(base_dir) / "summary.md"

    if review_type == "run":
        content = _generate_run_summary(session)
    else:
        content = _generate_audit_summary(session)

    summary_path.write_text(content)
    return str(summary_path)


def _generate_run_summary(session: "ReviewSession") -> str:
    """Generate summary for run_code_review"""
    final_review = session.final_review or _get_latest_reviews(session)
    issues = classify_issues(final_review)
    key_findings = extract_key_findings(final_review)

    timestamp = datetime.fromtimestamp(session.created_at).strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# Code Review Summary: {session.target_branch}",
        "",
        f"**Branch**: `{session.base_branch}...{session.target_branch}`",
        f"**Date**: {timestamp}",
        f"**Review Type**: Initial review by Claude Code",
        f"**Consensus**: {'APPROVED' if session.consensus_reached else 'IN PROGRESS'}",
        f"**Reviewed by**: {', '.join(session.reviews.keys())}",
        "",
        "---",
        ""
    ]

    # Critical Issues
    if issues["critical"]:
        lines.append(f"## Critical Issues ({len(issues['critical'])})")
        lines.append("")
        for idx, issue in enumerate(issues["critical"][:5], 1):
            lines.append(f"### 🔴 Issue {idx}")
            lines.append("")
            lines.append(issue["text"])
            lines.append("")

    # High Priority
    if issues["high"]:
        lines.append(f"## High Priority ({len(issues['high'])})")
        lines.append("")
        for idx, issue in enumerate(issues["high"][:10], 1):
            lines.append(f"### 🟠 {idx}. {issue['text'][:100]}...")
            lines.append("")

    # Key Findings
    lines.append("## Key Findings")
    lines.append("")
    for finding in key_findings:
        lines.append(f"- {finding}")
    lines.append("")

    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    lines.append("Based on the review findings, the following actions are recommended:")
    lines.append("")
    for idx, issue in enumerate(issues["critical"] + issues["high"], 1):
        if idx <= 5:
            lines.append(f"{idx}. [ ] {issue['text'][:100]}")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Full transcript available at: `full-transcript.md`*")

    return "\n".join(lines)


def _generate_audit_summary(session: "ReviewSession") -> str:
    """Generate summary for audit_code_review"""
    final_review = session.final_review or _get_latest_reviews(session)
    issues = classify_issues(final_review)
    key_findings = extract_key_findings(final_review)

    timestamp = datetime.fromtimestamp(session.created_at).strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# Code Review Audit Summary: {session.target_branch}",
        "",
        f"**Branch**: `{session.base_branch}...{session.target_branch}`",
        f"**Date**: {timestamp}",
        f"**Review Type**: User review audit",
        f"**Initial Review**: Provided by user",
        f"**Consensus**: {'APPROVED' if session.consensus_reached else 'IN PROGRESS'}",
        f"**Audited by**: {', '.join([k for k in session.reviews.keys() if k != 'USER'])}",
        "",
        "---",
        ""
    ]

    # Initial Review Assessment
    lines.append("## Initial Review Assessment")
    lines.append("")
    lines.append("The user-provided review was evaluated by multiple AI reviewers.")
    lines.append("")

    # Issues found by auditors
    if issues["critical"]:
        lines.append(f"## Critical Issues Found by Auditors ({len(issues['critical'])})")
        lines.append("")
        for idx, issue in enumerate(issues["critical"][:5], 1):
            lines.append(f"### 🔴 Issue {idx}")
            lines.append("")
            lines.append(issue["text"])
            lines.append("")

    # Audit Findings
    lines.append("## Audit Findings")
    lines.append("")
    lines.append("### Issues Added by Auditors")
    for finding in key_findings[:5]:
        lines.append(f"- {finding}")
    lines.append("")

    # Original Review Strengths
    lines.append("### Original Review Strengths")
    lines.append("- Comprehensive coverage of code changes")
    lines.append("- Clear structure and organization")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Original review available at: `initial-review.md`*")
    lines.append(f"*Full audit transcript at: `full-transcript.md`*")

    return "\n".join(lines)


def _get_latest_reviews(session: "ReviewSession") -> str:
    """Get concatenated latest reviews if no final review"""
    reviews = []
    for ai_name, rounds in session.reviews.items():
        if session.current_round in rounds:
            review_data = rounds[session.current_round]
            reviews.append(f"## {ai_name}\n\n{review_data['content']}")
    
    return "\n\n".join(reviews)
