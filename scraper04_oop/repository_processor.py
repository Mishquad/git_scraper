import os
from git_helper import GitHelper
from typing import Optional
import logging
import re
import csv
import shutil
import stat
from functools import lru_cache
import ast
import json

class RepositoryProcessor:
    def __init__(self, repo_name):
        self.repo_name = repo_name
    
    def handle_remove_readonly(self, func, exc):
        os.chmod(self.repo_path, stat.S_IWRITE)
        func(self.repo_path)
    
    @lru_cache(maxsize=128)
    def fetch_git_diff(self, base_commit_before, base_commit_after):
        return GitHelper.fetch_git_diff(folder=self.repo_path,
                                        base_commit_before=base_commit_before, 
                                        base_commit_after=base_commit_after
                                        )
    
    @staticmethod
    def _get_test_patch(git_diff: str) -> str:
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

    @staticmethod
    def _get_patch(git_diff: str) -> str:
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


    def process_repo(self, issues_data: dict, csv_filename: str, base_path: str = "repos", start_date: Optional[str] = None) -> None:
        self.repo_path = GitHelper.clone_repo(self.repo_name, base_path)
        if not self.repo_path:
            return
        
        merge_commits = GitHelper.get_merge_commits(self.repo_path, start_date)
        
        with open(csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            
            for i, (merge_commit, merge_date) in enumerate(merge_commits, 1):
                logging.info(f"Processing {self.repo_name} {i}/{len(merge_commits)}: {merge_commit}")
                
                parent_commits = GitHelper.get_parent_commits(self.repo_path, merge_commit)
                if not parent_commits:
                    continue
                
                base_commit_dates = [GitHelper.get_commit_date(self.repo_path, commit) for commit in parent_commits]
                resolving_commit_date = GitHelper.get_commit_date(self.repo_path, merge_commit)
                issue_number = GitHelper.get_issues_from_pr(self.repo_path, merge_commit)
                
                if issue_number is None:
                    logging.warning(f"No issue number found for {self.repo_name} merge commit {merge_commit}")
                    continue
                
                changed_files = [GitHelper.get_changed_files(self.repo_path, commit, merge_commit) for commit in parent_commits]
                num_changed_files = list(map(len, changed_files))
                pr_description = GitHelper.get_pr_description(self.repo_path, merge_commit)
                
                full_patch_list = []
                test_patch_list = []
                patch_list = []

                for base_commit_before in parent_commits:
                    full_patch = self.fetch_git_diff(base_commit_before, base_commit_after=merge_commit)
                    full_patch_list.append(full_patch)
                    test_patch_list.append(RepositoryProcessor._get_test_patch(full_patch))
                    patch_list.append(RepositoryProcessor._get_patch(full_patch))
                row = [
                    self.repo_name, parent_commits, base_commit_dates,
                    merge_commit, resolving_commit_date,
                    issue_number, None, None,
                    num_changed_files, 
                    changed_files,
                    None, None, pr_description, None, None,
                    json.dumps(full_patch_list), json.dumps(test_patch_list), json.dumps(patch_list)
                ]
                
                writer.writerow(row)  
                logging.info(f"Saved row: {row}")
    
    def __del__(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, onerror=self.handle_remove_readonly)
            logging.info(f"Deleted cloned repo at {self.repo_path} to save space")
