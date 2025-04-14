import subprocess
import os
import logging
import re
import requests
import pandas as pd
import csv
from typing import List, Tuple, Optional

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", insert you key)

def run_git_command(repo_path: str, command: List[str]) -> Optional[str]:
    """
    Executes a Git command and returns the standard output.

    Args:
        repo_path (str): The path to the Git repository.
        command (List[str]): The Git command to run.

    Returns:
        Optional[str]: The standard output of the Git command, or None if an error occurs.
    """
    try:
        result = subprocess.run(
            ['git', '-C', repo_path] + command, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Git command failed: {' '.join(command)}: {e}")
        return None

def clone_repo_if_needed(repo_name: str, base_path: str = "repos") -> Optional[str]:
    """
    Clones a Git repository if it doesn't already exist at the specified path.

    Args:
        repo_name (str): The name of the Git repository to clone.
        base_path (str, optional): The base path where the repository will be cloned. Defaults to "repos".

    Returns:
        Optional[str]: The path to the cloned repository, or None if cloning fails.
    """
    repo_path = os.path.join(base_path, repo_name)
    if not os.path.exists(repo_path):
        os.makedirs(base_path, exist_ok=True)
        repo_url = f"https://github.com/{repo_name}.git"
        logging.info(f"Cloning repository: {repo_url}")
        try:
            subprocess.run(["git", "clone", repo_url, repo_path], check=True)
        except subprocess.CalledProcessError:
            logging.error(f"Failed to clone {repo_name}")
            return None
    return repo_path

def get_merge_commits(repo_path: str, start_date: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Retrieves a list of merge commits from the Git repository.

    Args:
        repo_path (str): The path to the Git repository.
        start_date (Optional[str], optional): The start date to filter merge commits. Defaults to None.

    Returns:
        List[Tuple[str, str]]: A list of tuples containing the commit hash and the commit date.
    """
    command = ['log', '--merges', '--pretty=%H %ci']
    if start_date:
        command.insert(1, f'--since={start_date}')
    
    output = run_git_command(repo_path, command)
    return [(line.split()[0], ' '.join(line.split()[1:])) for line in output.split('\n') if line] if output else []

def get_parent_commits(repo_path: str, merge_commit: str) -> List[str]:
    """
    Retrieves the parent commits of a merge commit.

    Args:
        repo_path (str): The path to the Git repository.
        merge_commit (str): The hash of the merge commit.

    Returns:
        List[str]: A list of parent commit hashes.
    """
    output = run_git_command(repo_path, ['rev-list', '--parents', '-n', '1', merge_commit])
    if output:
        parts = output.split()
        return parts[1:] if len(parts) > 2 else []
    return []

def get_commit_date(repo_path: str, commit_hash: str) -> str:
    """
    Retrieves the date of a specific commit.

    Args:
        repo_path (str): The path to the Git repository.
        commit_hash (str): The commit hash.

    Returns:
        str: The commit date, or "Unknown" if not found.
    """
    return run_git_command(repo_path, ['show', '-s', '--format=%ci', commit_hash]) or "Unknown"

def get_issues_from_pr(repo_path: str, merge_commit: str) -> Optional[str]:
    """
    Retrieves the issue number linked to a pull request via a merge commit.

    Args:
        repo_path (str): The path to the Git repository.
        merge_commit (str): The merge commit hash.

    Returns:
        Optional[str]: The issue number, or None if no issue is found.
    """
    output = run_git_command(repo_path, ['log', '-1', '--pretty=%B', merge_commit])
    match = re.search(r'(?:fixes|closes|resolves)?\s*#(\d+)', output, re.IGNORECASE) if output else None
    return match.group(1) if match else None

def get_changed_files(repo_path: str, parent_commit: str, merge_commit: str) -> List[str]:
    """
    Retrieves the list of changed files between a parent commit and a merge commit.

    Args:
        repo_path (str): The path to the Git repository.
        parent_commit (str): The parent commit hash.
        merge_commit (str): The merge commit hash.

    Returns:
        List[str]: A list of changed file paths.
    """
    output = run_git_command(repo_path, ['diff', '--name-only', f"{parent_commit}..{merge_commit}"])
    return output.split("\n") if output else []

def get_pr_description(repo_path: str, merge_commit: str) -> str:
    """
    Retrieves the pull request description from the commit message.

    Args:
        repo_path (str): The path to the Git repository.
        merge_commit (str): The merge commit hash.

    Returns:
        str: The PR description, or "No description" if not found.
    """
    output = run_git_command(repo_path, ['log', '-1', '--pretty=%B', merge_commit])
    return output.strip() if output else "No description"

def get_pr_dates(repo_name: str, pr_number: int) -> Tuple[str, str]:
    """
    Fetches the open and close dates of a pull request from the GitHub API.

    Args:
        repo_name (str): The GitHub repository name.
        pr_number (int): The pull request number.

    Returns:
        Tuple[str, str]: A tuple containing the PR open date and close date.
    """
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("created_at", ""), data.get("closed_at", "")
    else:
        logging.warning(f"Failed to fetch PR {pr_number} from {repo_name}")
        return "", ""

def get_linked_issues(repo_name: str, pr_number: int) -> List[str]:
    """
    Retrieves the linked issue numbers from a pull request description using the GitHub API.

    Args:
        repo_name (str): The GitHub repository name.
        pr_number (int): The pull request number.

    Returns:
        List[str]: A list of linked issue numbers.
    """
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        pr_body = data.get("body", "")

        # Find issue references like "fixes #123", "closes #456"
        issue_numbers = re.findall(r"(?:fixes|closes|resolves)\s+#(\d+)", pr_body, re.IGNORECASE)
        
        # Remove incorrect "1234" example
        issue_numbers = [num for num in issue_numbers if num != "1234"]

        return list(set(issue_numbers))  # Remove duplicates
    else:
        logging.warning(f"Failed to fetch PR {pr_number} from {repo_name}")
        return []

def get_issue_details(repo_name: str, issue_number: int) -> Tuple[str, str, str]:
    """
    Fetches details for a GitHub issue including open/close dates and description.

    Args:
        repo_name (str): The GitHub repository name.
        issue_number (int): The issue number.

    Returns:
        Tuple[str, str, str]: A tuple containing the open date, close date, and issue description.
    """
    url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return (
            data.get("created_at", ""),  # Open date
            data.get("closed_at", ""),   # Close date
            data.get("body", "No description")  # Description
        )
    else:
        logging.warning(f"Failed to fetch issue {issue_number} from {repo_name}")
        return "", "", "Fetch failed"

def get_issue_description(repo_name: str, issue_number: int) -> str:
    """
    Fetches the description of a GitHub issue.

    Args:
        repo_name (str): The GitHub repository name.
        issue_number (int): The issue number.

    Returns:
        str: The issue description, or "Fetch failed" if not found.
    """
    url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get("body", "No description")
    else:
        logging.warning(f"Failed to fetch issue {issue_number} from {repo_name}")
        return "Fetch failed"

def update_dataframe(csv_filename: str) -> None:
    """
    Updates the DataFrame with linked issues, PR dates, and issue details.

    Args:
        csv_filename (str): The CSV file containing commit data to update.
    """
    df = pd.read_csv(csv_filename)

    for index, row in df.iterrows():
        pr_number = row["pr_num"]
        repo_name = row["repo_name"]

        # Process PR open/close dates
        if pd.notna(pr_number) and pd.isna(row["pr_open_date"]):
            pr_open_date, pr_close_date = get_pr_dates(repo_name, pr_number)
            df.at[index, "pr_open_date"] = pr_open_date
            df.at[index, "pr_close_date"] = pr_close_date

        # Process linked issues
        if pd.notna(pr_number) and pd.isna(row["_linked_issue_desc"]):
            linked_issues = get_linked_issues(repo_name, pr_number)

            issue_descriptions = []
            issue_open_dates = []
            issue_close_dates = []

            for issue_number in linked_issues:
                issue_open, issue_close, issue_desc = get_issue_details(repo_name, issue_number)
                issue_descriptions.append(f"Issue #{issue_number}: {issue_desc}")
                issue_open_dates.append(issue_open)
                issue_close_dates.append(issue_close)

            # Store extracted data
            df.at[index, "linked_issue_nums"] = str(linked_issues)  # List of issue numbers
            df.at[index, "_linked_issue_desc"] = " | ".join(issue_descriptions)
            df.at[index, "linked_issue_date_open"] = str(issue_open_dates)
            df.at[index, "linked_issue_date_closed"] = str(issue_close_dates)

    df.to_csv(csv_filename, index=False)
    print(f"Updated issue and PR data saved in {csv_filename}")

def process_repo(repo_name: str, issues_data: dict, csv_filename: str, base_path: str = "repos", start_date: Optional[str] = None) -> None:
    """
    Processes the repository by cloning it if needed, retrieving merge commits, and saving data.

    Args:
        repo_name (str): The name of the repository to process.
        issues_data (dict): A dictionary containing issues data.
        csv_filename (str): The name of the CSV file to save the processed data.
        base_path (str, optional): The base path for repositories. Defaults to "repos".
        start_date (Optional[str], optional): The start date for filtering merge commits. Defaults to None.
    """
    repo_path = clone_repo_if_needed(repo_name, base_path)
    if not repo_path:
        return
    
    merge_commits = get_merge_commits(repo_path, start_date)
    
    with open(csv_filename, 'a', newline='') as f:
        writer = csv.writer(f)
        
        for i, (merge_commit, merge_date) in enumerate(merge_commits, 1):
            logging.info(f"Processing {repo_name} {i}/{len(merge_commits)}: {merge_commit}")
            
            parent_commits = get_parent_commits(repo_path, merge_commit)
            if not parent_commits:
                continue
            
            base_commit_dates = [get_commit_date(repo_path, commit) for commit in parent_commits]
            resolving_commit_date = get_commit_date(repo_path, merge_commit)
            issue_number = get_issues_from_pr(repo_path, merge_commit)
            
            if issue_number is None:
                logging.warning(f"No issue number found for {repo_name} merge commit {merge_commit}")
                continue
            
            #issue_open_date, issue_closed_date, issue_description = get_issue_dates_from_api(repo_name, issue_number)
            changed_files = [get_changed_files(repo_path, commit, merge_commit) for commit in parent_commits]
            num_changed_files = list(map(len, changed_files))
            pr_description = get_pr_description(repo_path, merge_commit)
            
            row = [
                repo_name, parent_commits, base_commit_dates,
                merge_commit, resolving_commit_date,
                issue_number, None, None,
                #PR_closed_date, PR_open_date,
                num_changed_files, changed_files,
                None, None, pr_description, None, None
            ]
            
            writer.writerow(row)  
            logging.info(f"Saved row: {row}")

def initialize_csv(filename: str) -> None:
    """
    Ensures the CSV file has headers if it doesn’t exist.

    Args:
        filename (str): The CSV file to check and initialize.
    """
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'repo_name', 'base_commit_ids', 'base_commit_dates',
                'resolving_commit_id', 'resolving_commit_date',
                'pr_num', 'pr_close_date', 'pr_open_date',
                'num_changed_files', 'changed_files_list', 'linked_issue_nums', 
                '_linked_issue_desc', '_pr_description', 'linked_issue_date_open', 'linked_issue_date_closed'
            ])

import subprocess
from pathlib import Path

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

def get_test_patch(git_diff: str) -> str:
    """
    Extract test-related changes from the git diff.
    
    Args:
        git_diff: The full git diff string
        
    Returns:
        A diff string containing only test files (files that match common test patterns)
    """
    test_patches = []
    current_patch = []
    in_patch = False
    is_test_file = False
    
    for line in git_diff.splitlines(keepends=True):
        if line.startswith("diff --git"):
            # Process the previous patch if we were in one
            if in_patch and is_test_file:
                test_patches.extend(current_patch)
            
            # Reset for new patch
            current_patch = [line]
            in_patch = True
            is_test_file = False
            
            # Check if this is a test file
            if "test/" in line or "tests/" in line or "_test.py" in line or "test_" in line:
                is_test_file = True
        elif in_patch:
            current_patch.append(line)
    
    # Add the last patch if it was a test file
    if in_patch and is_test_file:
        test_patches.extend(current_patch)
    
    return "".join(test_patches)

def get_patch(git_diff: str) -> str:
    """
    Extract non-test-related changes from the git diff.
    
    Args:
        git_diff: The full git diff string
        
    Returns:
        A diff string containing only non-test files
    """
    other_patches = []
    current_patch = []
    in_patch = False
    is_test_file = False
    
    for line in git_diff.splitlines(keepends=True):
        if line.startswith("diff --git"):
            # Process the previous patch if we were in one
            if in_patch and not is_test_file:
                other_patches.extend(current_patch)
            
            # Reset for new patch
            current_patch = [line]
            in_patch = True
            is_test_file = False
            
            # Check if this is a test file
            if "test/" in line or "tests/" in line or "_test.py" in line or "test_" in line:
                is_test_file = True
        elif in_patch:
            current_patch.append(line)
    
    # Add the last patch if it wasn't a test file
    if in_patch and not is_test_file:
        other_patches.extend(current_patch)
    
    return "".join(other_patches)

# # Example of ussage
# folder = "/data/adam/build_ecs_gigacode_worker/mtsai/dynamic_bench/repos/sympy"
# base_commit_before = "490c6d0f7df7b02a70e04c0ed4ead899cd430e70"
# base_commit_after  = "9173d613a048493c1a4bfb07e69a419b1c73aa3d"

# # cd /data/adam/build_ecs_gigacode_worker/mtsai/dynamic_bench/repos/sympy git clone 
# full_diff = fetch_git_diff(folder, base_commit_before, base_commit_after)
# test_patch = get_test_patch(full_diff)
# patch = get_patch(full_diff)

# open("dynamic_bench/repos/full_diff.txt", "w+").write(full_diff)
# open("dynamic_bench/repos/test_patch.txt", "w+").write(test_patch)
# open("dynamic_bench/repos/patch.txt", "w+").write(patch)

def main() -> None:
    """
    The main function to process repositories and update issue and PR data in a CSV file.
    """
    logging.basicConfig(level=logging.INFO)
    repo_list = ['sympy/sympy']
    issues_data = {}
    start_date = '2025-01-01'  
    csv_filename = 'sympy_sympy_commits_002.csv'

    initialize_csv(csv_filename)

    for repo_name in repo_list:
        process_repo(repo_name, issues_data, csv_filename, start_date=start_date)

    logging.info(f"Processing complete! Data saved in {csv_filename}, now will try to get issues description")
   
    update_dataframe(csv_filename)
    logging.info(f"Finished collecting issue description")

if __name__ == '__main__':
    main()
