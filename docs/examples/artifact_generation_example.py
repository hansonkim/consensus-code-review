"""
Example usage of Phase 2 artifact generation system.

Demonstrates both 'run' and 'audit' review workflows.
"""

import asyncio

from consensus_code_review.mcp.utils import generate_complete_artifacts, load_review_artifacts


async def example_run_review():
    """Example: Generate artifacts for 'run' review type."""
    print("=" * 60)
    print("EXAMPLE 1: RUN REVIEW (CLAUDE-led iterative)")
    print("=" * 60)

    review_data = {
        "review_type": "run",
        "rounds": [
            {
                "ai_name": "claude-3-5-sonnet-20241022",
                "review": """# Code Review - Round 1

## Security Issues
- Critical: SQL injection vulnerability in user authentication
- Major: Unvalidated input in search endpoint

## Performance Issues
- Database queries not optimized (N+1 problem)
- Missing indexes on frequently queried columns

## Code Quality
- Minor: Inconsistent error handling patterns
- Minor: Missing docstrings in public methods
""",
                "timestamp": "2025-11-01T10:00:00",
                "feedback": ["Add input validation middleware", "Implement parameterized queries"],
                "changes": ["Added SQL injection prevention", "Implemented query optimization"],
            },
            {
                "ai_name": "gemini-2-0-flash-exp",
                "review": """# Code Review - Round 2

## Agreement
Confirmed security vulnerabilities from Round 1.

## Additional Findings
- Style: Inconsistent naming conventions
- Documentation: Missing API documentation

## Recommendations
- Add comprehensive unit tests
- Implement rate limiting
""",
                "timestamp": "2025-11-01T10:05:00",
                "feedback": [],
                "changes": ["Added rate limiting middleware", "Improved test coverage to 85%"],
            },
        ],
        "consensus": {
            "reached": True,
            "total_rounds": 2,
            "ais": ["claude-3-5-sonnet-20241022", "gemini-2-0-flash-exp"],
            "final_review": """# Final Review

Code quality is acceptable with critical security improvements needed.

## Must Fix (Critical)
- SQL injection vulnerability in authentication
- Unvalidated input in search endpoint

## Should Fix (Major)
- Database query optimization
- Add missing indexes

## Nice to Have (Minor)
- Consistent error handling
- Add docstrings
- API documentation
""",
            "timestamp": "2025-11-01T10:10:00",
            "metadata": {"max_rounds": 5, "confidence_score": 0.92},
        },
    }

    # Generate artifacts
    paths = await generate_complete_artifacts(
        review_data=review_data, target="feature/user-authentication", base="main"
    )

    print("\n✅ Artifacts generated successfully!")
    print(f"\n📁 Review Directory: {paths['review_dir']}")
    print(f"📄 Summary: {paths['summary']}")
    print(f"📝 Transcript: {paths['transcript']}")
    print(f"📊 Consensus: {paths['consensus']}")
    print(f"📂 Rounds: {paths['rounds_dir']}")

    return paths


async def example_audit_review():
    """Example: Generate artifacts for 'audit' review type."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: AUDIT REVIEW (Multi-AI verification)")
    print("=" * 60)

    review_data = {
        "review_type": "audit",
        "initial_review": """# Initial Code Review (User-Provided)

I've reviewed the authentication module and found several issues:

1. **Security Concerns**
   - Passwords stored in plain text (CRITICAL!)
   - No rate limiting on login endpoint
   - Session tokens predictable

2. **Code Quality**
   - Error messages expose too much information
   - No input validation on email field
   - Missing logging for security events

3. **Recommendations**
   - Use bcrypt for password hashing
   - Implement rate limiting (5 attempts per minute)
   - Add comprehensive security logging
""",
        "rounds": [
            {
                "ai_name": "gpt-4-turbo",
                "review": """# Audit Round 1

## Verification of Initial Review

✅ **Confirmed Issues:**
- Plain text password storage (CRITICAL)
- Lack of rate limiting
- Predictable session tokens

❌ **Additional Critical Issues Found:**
- Missing CSRF protection
- No password complexity requirements
- Vulnerable to timing attacks

## Recommendations
All issues in initial review are valid. Additional security measures required.
""",
                "timestamp": "2025-11-01T11:00:00",
                "feedback": ["Add CSRF tokens to forms", "Implement password complexity rules"],
                "changes": [],
            },
            {
                "ai_name": "claude-3-opus",
                "review": """# Audit Round 2

## Full Agreement

All findings from initial review and Round 1 are accurate.

## Priority Classification
1. **Immediate (P0)**: Plain text passwords, CSRF
2. **Urgent (P1)**: Rate limiting, timing attacks
3. **Important (P2)**: Logging, error messages

## Implementation Roadmap
Week 1: Address P0 issues
Week 2: Address P1 issues
Week 3: Address P2 issues
""",
                "timestamp": "2025-11-01T11:05:00",
                "feedback": [],
                "changes": ["Created security roadmap", "Prioritized fixes"],
            },
        ],
        "consensus": {
            "reached": True,
            "total_rounds": 2,
            "ais": ["gpt-4-turbo", "claude-3-opus"],
            "final_review": """# Final Audit Conclusion

The initial review correctly identified critical security vulnerabilities.
Multiple AI models confirm all findings and identified additional issues.

## Verified Issues (All Confirmed)
- ✅ Plain text password storage (CRITICAL)
- ✅ No rate limiting
- ✅ Predictable session tokens
- ✅ Missing CSRF protection (NEW)
- ✅ No password complexity (NEW)
- ✅ Timing attack vulnerability (NEW)

## Recommendation
**DO NOT MERGE** until all P0 issues are resolved.
""",
            "timestamp": "2025-11-01T11:10:00",
            "metadata": {"audit_confidence": 0.98, "issues_confirmed": 6, "new_issues_found": 3},
        },
    }

    # Generate artifacts
    paths = await generate_complete_artifacts(
        review_data=review_data, target="security/authentication-fix", base="main"
    )

    print("\n✅ Audit artifacts generated successfully!")
    print(f"\n📁 Review Directory: {paths['review_dir']}")
    print(f"📄 Summary: {paths['summary']}")
    print(f"📋 Initial Review: {paths['initial_review']}")  # Audit-specific
    print(f"📝 Transcript: {paths['transcript']}")
    print(f"📊 Consensus: {paths['consensus']}")

    return paths


async def example_load_artifacts(review_dir: str):
    """Example: Load previously saved artifacts."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: LOAD ARTIFACTS")
    print("=" * 60)

    loaded_data = await load_review_artifacts(review_dir)

    print("\n📖 Loaded Review Data:")
    print(f"   Type: {loaded_data.get('review_type', 'Unknown')}")
    print(f"   Rounds: {len(loaded_data.get('rounds', []))}")

    if "consensus" in loaded_data:
        consensus = loaded_data["consensus"]
        print(f"   Consensus: {consensus.get('consensus_reached', False)}")
        print(f"   AIs: {', '.join(consensus.get('participating_ais', []))}")

    if "initial_review" in loaded_data:
        print("   Has Initial Review: Yes (audit type)")

    return loaded_data


async def main():
    """Run all examples."""
    print("\n🚀 Phase 2 Artifact Generation Examples\n")

    # Example 1: Run review
    run_paths = await example_run_review()

    # Example 2: Audit review
    audit_paths = await example_audit_review()

    # Example 3: Load artifacts
    await example_load_artifacts(run_paths["review_dir"])

    print("\n" + "=" * 60)
    print("✅ All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
