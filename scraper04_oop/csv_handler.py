import os
import re
import pandas as pd
import csv
from github_api_wrapper import GitHubAPI
import ast
import logging
# import warnings
# warnings.simplefilter(action='ignore', category=FutureWarning)


class CSVHandler:
    @staticmethod
    def initialize_csv(filename: str) -> None:
        if not os.path.exists(filename):
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'repo_name', 'base_commit_ids', 'base_commit_dates',
                    'resolving_commit_id', 'resolving_commit_date',
                    'pr_num', 'pr_close_date', 'pr_open_date',
                    'num_changed_files', 'changed_files_list', 'linked_issue_nums', 
                    '_linked_issue_desc', '_pr_description', 'linked_issue_date_open', 'linked_issue_date_closed',
                    'full_patch', 'test_patch', 'patch'
                ])

    @staticmethod
    def update_dataframe(csv_filename: str) -> None:
        df = pd.read_csv(csv_filename)

        for index, row in df.iterrows():
            pr_number = row["pr_num"]
            repo_name = row["repo_name"]

            if pd.notna(pr_number) and pd.isna(row["pr_open_date"]):
                pr_open_date, pr_close_date = GitHubAPI.get_pr_dates(repo_name, pr_number)
                df.at[index, "pr_open_date"] = pr_open_date
                df.at[index, "pr_close_date"] = pr_close_date

            if pd.notna(pr_number) and pd.isna(row["_linked_issue_desc"]):
                linked_issues = GitHubAPI.get_linked_issues(repo_name, pr_number)

                issue_descriptions = []
                issue_open_dates = []
                issue_close_dates = []

                for issue_number in linked_issues:
                    issue_open, issue_close, issue_desc = GitHubAPI.get_issue_details(repo_name, issue_number)
                    issue_descriptions.append(f"Issue #{issue_number}: {issue_desc}")
                    issue_open_dates.append(issue_open)
                    issue_close_dates.append(issue_close)

                df.at[index, "linked_issue_nums"] = str(linked_issues)
                df.at[index, "_linked_issue_desc"] = " | ".join(issue_descriptions)
                df.at[index, "linked_issue_date_open"] = str(issue_open_dates)
                df.at[index, "linked_issue_date_closed"] = str(issue_close_dates)

        df.to_csv(csv_filename, index=False)
        print(f"Updated issue and PR data saved in {csv_filename}")



    @staticmethod
    def explode_base_commits(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            logging.warning("Input DataFrame is empty. Skipping explosion.")
            return df

        # Columns that need to be deserialized
        list_cols = ['base_commit_ids', 'base_commit_dates', 'num_changed_files', 'changed_files_list']
        
        # Check if all required columns are present
        missing_cols = [col for col in list_cols if col not in df.columns]
        if missing_cols:
            logging.warning(f"Missing columns in input DataFrame: {missing_cols}. Skipping explosion.")
            return df

        # Convert strings to Python lists
        for col in list_cols:
            df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        
        # Explode each row into multiple rows
        rows = []
        for _, row in df.iterrows():
            base_commits = row['base_commit_ids']
            base_dates = row['base_commit_dates']
            num_files = row['num_changed_files']
            files_list = row['changed_files_list']

            for i in range(len(base_commits)):
                new_row = row.copy()
                new_row['base_commit'] = base_commits[i]
                new_row['base_commit_date'] = base_dates[i] if i < len(base_dates) else None
                new_row['num_changed_files'] = num_files[i] if i < len(num_files) else None
                new_row['changed_files_list'] = files_list[i] if i < len(files_list) else None
                rows.append(new_row)

        # Build the exploded DataFrame
        if rows:
            exploded_df = pd.DataFrame(rows)
            exploded_df = exploded_df.drop(columns=['base_commit_ids', 'base_commit_dates'])
            return exploded_df
        else:
            logging.warning("No rows generated after explosion.")
            return pd.DataFrame(columns=df.columns.tolist() + ['base_commit', 'base_commit_date'])
