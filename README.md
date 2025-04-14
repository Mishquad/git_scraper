# git_scraper



# git_scraper

A Python tool to extract and enrich **merge commits** and related **GitHub issues** from a list of repositories.

---

## Input

```python
repo_list: List[str]       # List of GitHub repositories to scan
start_date: str            # Starting date (YYYY-MM-DD) for collecting merge commits
```

    for repo_name:
      for resolved_base_commit:

Field	Type	Description
repo_name	str	Name of the GitHub repository
base_commit_ids	List[str]	IDs of base commits
base_commit_dates	List[str]	Dates of base commits
pr_num	int	Pull request number
resolved_commit_id	str	Merge commit ID
changed_file_list	List[List[str]]	List of changed files for each commit
num_changed_files	List[int]	Number of files changed
pr_close_date	None	(To be filled later)
pr_open_date	None	(To be filled later)
_pr_description	None	(To be filled later)
linked_issue_nums	None	(To be filled later)
_linked_issue_desc	None	(To be filled later)
linked_issue_date_open	None	(To be filled later)
linked_issue_date_closed	None	(To be filled later)
    
  // обогащение исходника информацией про связанные issue через REST API Git
  
  update_dataframe(csv_filename)
repo_name	str
base_commit_ids	List[str]
base_commit_dates	List[str]
pr_num	int
resolved_commit_id	str
changed_file_list	List[List[str]]
num_changed_files	List[int]
pr_close_date	str
pr_open_date	str
_pr_description	str
linked_issue_nums	List[int]
_linked_issue_desc	List[str]
linked_issue_date_open	List[str]
linked_issue_date_closed	List[str]

    // explode создаем уникальный ключ base_commit_id + resolving_commit_id
    
repo_name: str
base_commit: str
base_commit_date: str
pr_num: int
resolved_commit_id: str
changed_file_list: List[str]
num_changed_files: int
pr_close_date: str
pr_open_date: str
_pr_description: str
linked_issue_nums: List[int]
_linked_issue_desc: List[str]
linked_issue_date_open: List[str]
linked_issue_date_closed: List[str]

