import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.github_client import fetch_pr

# A small, real, merged public PR — good for testing
TEST_PR_URL = "https://github.com/fastapi/fastapi/pull/15508"

def test_fetch_pr():
    print(f"\nFetching PR: {TEST_PR_URL}\n")
    pr = fetch_pr(TEST_PR_URL)

    print(f"  Title:        {pr.title}")
    print(f"  Author:       {pr.author}")
    print(f"  Repo:         {pr.repo_name}")
    print(f"  Files changed:{pr.total_files_changed}")
    print(f"  Additions:    +{pr.total_additions}")
    print(f"  Deletions:    -{pr.total_deletions}")
    print(f"  Languages:    {', '.join(pr.changed_languages)}")
    print(f"  Commits:      {len(pr.commit_messages)}")
    print(f"\n  Commit messages:")
    for msg in pr.commit_messages:
        print(f"    - {msg}")
    print(f"\n  Files:")
    for f in pr.files:
        marker = "🧪" if f.is_test_file else "⚙️" if f.is_config_file else "📄"
        print(f"    {marker} {f.filename} [{f.language}] +{f.additions}/-{f.deletions}")

    print(f"\n  --- Diff preview (first 600 chars) ---")
    print(pr.get_full_diff_text()[:600])

    # Basic assertions
    assert pr.pr_number > 0
    assert len(pr.files) > 0
    assert pr.author != ""
    print("\n✅  All assertions passed — GitHub tool is working!")

if __name__ == "__main__":
    test_fetch_pr()