from typing import Any, Dict, List, Optional, Tuple
import os
import logging
import time
import requests
import re

try:
    GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
except KeyError as e:
    print("Specify access token by export GITHUB_TOKEN=ghp_..")
    raise e

class GitHubAPI:
    @staticmethod
    def _make_request(url: str) -> Optional[Dict[str, Any]]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {GITHUB_TOKEN}"
        }

        while True:
            response = requests.get(url, headers=headers)
            if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                sleep_seconds = max(reset_time - int(time.time()), 0) + 1
                logging.warning(f"Rate limit exceeded. Sleeping for {sleep_seconds} seconds...")
                time.sleep(sleep_seconds)
                continue
            break

        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"Failed to fetch {url} with status {response.status_code}")
            return None

    @staticmethod
    def get_pr_dates(repo_name: str, pr_number: int) -> Tuple[str, str]:
        url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
        data = GitHubAPI._make_request(url)
        if data:
            return data.get("created_at", ""), data.get("closed_at", "")
        return "", ""

    @staticmethod
    def get_linked_issues(repo_name: str, pr_number: int) -> List[str]:
        url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
        data = GitHubAPI._make_request(url)
        if data:
            pr_body = data.get("body", "")
            issue_numbers = re.findall(r"(?:fixes|closes|resolves)\s+#(\d+)", str(pr_body), re.IGNORECASE)
            issue_numbers = [num for num in issue_numbers if num != "1234"]
            return list(set(issue_numbers))
        return []

    @staticmethod
    def get_issue_details(repo_name: str, issue_number: int) -> Tuple[str, str, str]:
        url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}"
        data = GitHubAPI._make_request(url)
        if data:
            return (
                data.get("created_at", ""),
                data.get("closed_at", ""),
                data.get("body", "No description")
            )
        return "", "", "Fetch failed"
