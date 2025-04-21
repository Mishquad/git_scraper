import subprocess
import logging
import os
from typing import List, Optional, Tuple
import re
from pathlib import Path

class GitHelper:
    @staticmethod
    def run_git_command(repo_path: str, command: List[str]) -> Optional[str]:
        try:
            result = subprocess.run(
                ['git', '-C', repo_path] + command, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Git command failed: {' '.join(command)}: {e}")
            return None

    @staticmethod
    def clone_repo(repo_name: str, base_path: str = "repos") -> Optional[str]:
        repo_path = os.path.join(base_path, repo_name)
        if not os.path.exists(repo_path):
            os.makedirs(base_path, exist_ok=True)
            repo_url = f"https://github.com/{repo_name}.git"
            logging.info(f"Cloning repository: {repo_url}")
            try:
                subprocess.run(["git", "clone", repo_url, repo_path], check=True)
                return repo_path
            except subprocess.CalledProcessError:
                logging.error(f"Failed to clone {repo_name}")
                return None
        return repo_path

    @staticmethod
    def get_merge_commits(repo_path: str, start_date: Optional[str] = None) -> List[Tuple[str, str]]:
        command = ['log', '--merges', '--pretty=%H %ci']
        if start_date:
            command.insert(1, f'--since={start_date}')
        
        output = GitHelper.run_git_command(repo_path, command)
        return [(line.split()[0], ' '.join(line.split()[1:])) for line in output.split('\n') if line] if output else []

    @staticmethod
    def get_parent_commits(repo_path: str, merge_commit: str) -> List[str]:
        output = GitHelper.run_git_command(repo_path, ['rev-list', '--parents', '-n', '1', merge_commit])
        if output:
            parts = output.split()
            return parts[1:] if len(parts) > 2 else []
        return []

    @staticmethod
    def get_commit_date(repo_path: str, commit_hash: str) -> str:
        return GitHelper.run_git_command(repo_path, ['show', '-s', '--format=%ci', commit_hash]) or "Unknown"

    @staticmethod
    def get_issues_from_pr(repo_path: str, merge_commit: str) -> Optional[str]:
        output = GitHelper.run_git_command(repo_path, ['log', '-1', '--pretty=%B', merge_commit])
        match = re.search(r'(?:fixes|closes|resolves)?\s*#(\d+)', output, re.IGNORECASE) if output else None
        return match.group(1) if match else None

    @staticmethod
    def get_changed_files(repo_path: str, parent_commit: str, merge_commit: str) -> List[str]:
        output = GitHelper.run_git_command(repo_path, ['diff', '--name-only', f"{parent_commit}..{merge_commit}"])
        return output.split("\n") if output else []

    @staticmethod
    def get_pr_description(repo_path: str, merge_commit: str) -> str:
        output = GitHelper.run_git_command(repo_path, ['log', '-1', '--pretty=%B', merge_commit])
        return output.strip() if output else "No description"
    
    @staticmethod
    def fetch_git_diff(folder: str, base_commit_before: str, base_commit_after: str) -> str:
        """
        Fetch git diff between two commits in the specified repository folder.
        
        Args:
            folder: Path to the git repository
            base_commit_before: The older commit hash
            base_commit_after: The newer commit hash
        
        Returns:
            The git diff as a string
        """
        # Convert to absolute path and resolve any symlinks
        folder = str(Path(folder).resolve())
        
        # Run git diff command
        result = subprocess.run(
            ["git", "-C", folder, "diff", f"{base_commit_before}..{base_commit_after}"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
