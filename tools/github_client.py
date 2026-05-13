import os
import re
from github import Github, GithubException
from dotenv import load_dotenv
from tools.diff_parser import ParsedPR, parse_file_diff

load_dotenv()


class GitHubClient:
    """Fetches and structures PR data from GitHub."""

    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN not set in .env")
        self.client = Github(token)

    def fetch_pr(self, pr_url: str) -> ParsedPR:
        """
        Main entry point. Pass any GitHub PR URL, get back a ParsedPR.

        Example URL:
          https://github.com/owner/repo/pull/123
        """
        owner, repo_name, pr_number = self._parse_pr_url(pr_url)

        try:
            repo = self.client.get_repo(f"{owner}/{repo_name}")
            pr   = repo.get_pull(pr_number)
        except GithubException as e:
            raise ValueError(f"Could not fetch PR: {e.data.get('message', str(e))}")

        # Collect commit messages
        commits = list(pr.get_commits())
        commit_messages = [
            c.commit.message.split("\n")[0]   # first line only
            for c in commits
        ]

        # Parse every changed file
        files = [parse_file_diff(f) for f in pr.get_files()]

        # Collect unique languages touched
        languages = sorted({f.language for f in files if f.language != "Unknown"})

        return ParsedPR(
            pr_number=pr.number,
            title=pr.title,
            description=pr.body or "(no description provided)",
            author=pr.user.login,
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
            repo_name=f"{owner}/{repo_name}",
            commit_messages=commit_messages,
            files=files,
            total_additions=pr.additions,
            total_deletions=pr.deletions,
            changed_languages=languages,
        )

    def _parse_pr_url(self, url: str) -> tuple[str, str, int]:
        """Extract owner, repo, and PR number from a GitHub PR URL."""
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, url)
        if not match:
            raise ValueError(
                f"Invalid GitHub PR URL: {url}\n"
                "Expected format: https://github.com/owner/repo/pull/123"
            )
        owner    = match.group(1)
        repo     = match.group(2)
        pr_number = int(match.group(3))
        return owner, repo, pr_number


def fetch_pr(pr_url: str) -> ParsedPR:
    """Convenience function — use this in agents."""
    return GitHubClient().fetch_pr(pr_url)