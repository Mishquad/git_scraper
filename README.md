# git_scraper



# git_scraper

A Python tool to extract and enrich **merge commits** and related **GitHub issues** from a list of repositories.

---

## Input

```python
repo_list: List[str]       # список репо для поиска коммитов
start_date: str            # календарная дата, с которой искать коммиты
csv_filename: str          # название для сохраняемого файла
```

## initialize_csv - создание .csv файла с построчной записью 

| Column                   | Type           | Description                      |
|-------------------------|----------------|----------------------------------|
| `repo_name`             | `str`          | Название репо    |
| `base_commit_ids`       | `List[str]`    | ID базовых коммитов             |
| `base_commit_dates`     | `List[str]`    | Даты базовых коммитов            |
| `pr_num`                | `int`          | Номер pull-request             |
| `resolved_commit_id`    | `str`          | ID смердженных коммитов          |
| `changed_file_list`     | `List[List[str]]` | Список измененных файлов для каждого базового коммита |
| `num_changed_files`     | `List[int]`    | Список кол-ва измененных файлов         |
| `pr_close_date`         | `None`         | Placeholder, заполняется потом датой закрытия PR           |
| `pr_open_date`          | `None`         | Placeholder, заполняется потом датой открытия PR              |
| `_pr_description`       | `str`          | Placeholder, заполняется потом описанием PR            |
| `linked_issue_nums`     | `None`         | Placeholder, заполняется потом номерами связанных issue с базовыми коммитами            |
| `_linked_issue_desc`    | `None`         | Placeholder, заполняется потом списком текста из связанных issues              |
| `linked_issue_date_open`  | `None`       | Placeholder, заполняется потом датой открытия issue              |
| `linked_issue_date_closed`| `None`       | Placeholder, заполняется потом датой закрытия issue           |

    
  ## update_dataframe(csv_filename) - обогащение исходника информацией про связанные issue через REST API Git


| Column                    | Type             |
|--------------------------|------------------|
| `repo_name`              | `str`            |
| `base_commit_ids`        | `List[str]`      |
| `base_commit_dates`      | `List[str]`      |
| `pr_num`                 | `int`            |
| `resolved_commit_id`     | `str`            |
| `changed_file_list`      | `List[List[str]]`|
| `num_changed_files`      | `List[int]`      |
| `pr_close_date`          | `str`            |
| `pr_open_date`           | `str`            |
| `_pr_description`        | `str`            |
| `linked_issue_nums`      | `List[int]`      |
| `_linked_issue_desc`     | `List[str]`      |
| `linked_issue_date_open` | `List[str]`      |
| `linked_issue_date_closed`| `List[str]`     |


 ## explode - создаем уникальный ключ base_commit_id + resolving_commit_id
    
| Field                     | Type            |
|---------------------------|-----------------|
| `repo_name`               | `str`           |
| `base_commit`             | `str`           |
| `base_commit_date`        | `str`           |
| `pr_num`                  | `int`           |
| `resolved_commit_id`      | `str`           |
| `changed_file_list`       | `List[str]`     |
| `num_changed_files`       | `int`           |
| `pr_close_date`           | `str`           |
| `pr_open_date`            | `str`           |
| `_pr_description`         | `str`           |
| `linked_issue_nums`       | `List[int]`     |
| `_linked_issue_desc`      | `List[str]`     |
| `linked_issue_date_open`  | `List[str]`     |
| `linked_issue_date_closed`| `List[str]`     |


