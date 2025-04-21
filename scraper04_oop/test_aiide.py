import os
import pandas as pd
import pytest
from .parser import main_entry_point
# import warnings
# warnings.simplefilter(action='ignore', category=FutureWarning)

@pytest.fixture
def cleanup():
    yield
    for f in ["exploded_df_temp.csv", "df_temp.csv"]:
        if os.path.exists(f):
            os.remove(f)

def test__aiide():
    global row
    expected = {'repo_name': 'Anilturaga/aiide', 
    'resolving_commit_id': 'aaa6e78101f0e96524d4adca094ac32c11218fbb',
     'resolving_commit_date': '2024-05-14 01:22:02 +0530',
     'pr_num': 6,
     'pr_close_date': '2024-05-13T19:52:03Z',
     'pr_open_date': '2024-05-13T19:51:28Z',
     'num_changed_files': 5,
     'changed_files_list': ['README.md',
      'aiide/_aiide.py',
      'docs/figures/aiide_memory_logic.png',
      'docs/figures/aiide_memory_logic_.png',
      'tests/test_aiide.py'],
     'linked_issue_nums': "['2']",
     '_linked_issue_desc': 'Issue #2: Enable using completions with `agent.chat` without using user_query.\r\n\r\nUseful for ReAct',
     '_pr_description': 'Merge pull request #6 from Anilturaga/1-not-using-env\n\nBug fixes',
     'linked_issue_date_open': "['2024-05-07T09:09:17Z']",
     'linked_issue_date_closed': "['2024-05-13T19:52:23Z']",
     'base_commit': '8b78177e9e14ea848c4282ba2485ee9dc0cec9ef',
     'base_commit_date': '2024-05-04 07:03:20 +0530'
    }

    def assert_parsed_row_matches(df: pd.DataFrame, expected: dict, row_index: int = 0) -> None:
        global row
        row = df.iloc[row_index]

        assert row['repo_name'] == expected['repo_name']
        assert row['resolving_commit_id'] == expected['resolving_commit_id']
        assert row['resolving_commit_date'] == expected['resolving_commit_date']
        assert int(row['pr_num']) == expected['pr_num']
        assert row['pr_close_date'] == expected['pr_close_date']
        assert row['pr_open_date'] == expected['pr_open_date']
        assert int(row['num_changed_files']) == expected['num_changed_files']
        assert row['_linked_issue_desc'] == expected['_linked_issue_desc']
        assert row['_pr_description'] == expected['_pr_description']
        assert row['base_commit'] == expected['base_commit']
        assert row['base_commit_date'] == expected['base_commit_date']
        assert eval(row['changed_files_list']) == expected['changed_files_list']
        assert eval(row['linked_issue_nums']) == eval(expected['linked_issue_nums'])
        assert eval(row['linked_issue_date_open']) == eval(expected['linked_issue_date_open'])
        assert eval(row['linked_issue_date_closed']) == eval(expected['linked_issue_date_closed'])

        print("all passed")
        
    
    main_entry_point(repo = "Anilturaga/aiide", 
                     start_date = '2024-01-01', 
                     fn_output = 'df_temp.csv',
                     fn_gredy = "df_temp_gredy.csv"
                    )
    df = pd.read_csv("df_temp.csv")
    os.remove("df_temp.csv")
    os.remove("df_temp_gredy.csv")
    assert_parsed_row_matches(df, expected)