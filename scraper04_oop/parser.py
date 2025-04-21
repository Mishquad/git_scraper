import logging
from csv_handler import CSVHandler
from repository_processor import RepositoryProcessor
import pandas as pd
from fire import Fire
from tempfile import TemporaryDirectory

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

logging.basicConfig(level=logging.INFO)

def parse_git_issue(repo: str = "patrick-kidger/wadler_lindig", 
                    start_date: str = '2024-01-01'
                   ) -> pd.DataFrame:
    with TemporaryDirectory() as temp_dir:
        fn_output = f"{temp_dir}/df_temp.csv"
        fn_gredy  = f"{temp_dir}/df_gredy.csv"
        logging.info(f"Processing to {fn_output}")
        parse_git_issue_to_file(repo, start_date, fn_output, fn_gredy = fn_gredy)
        df_res = pd.read_csv(fn_output)
    return df_res

def parse_git_issue_to_file(repo: str = "patrick-kidger/wadler_lindig", 
         start_date: str = '2024-01-01', 
         fn_output: str = 'df.csv',
         fn_gredy: str = "df_gredy.csv"
        ) -> None:
    """
    Main function to parse and extract data from a GitHub repository.

    Parameters:
    - repo (str): GitHub repository URL.
    - start_date (str): Start date for issue filtering. Default is '2024-01-01'.
    - fn_output (str): Output CSV file name. Default is 'df_temp.csv'.
    """
    issues_data = {}
    
    CSVHandler.initialize_csv(fn_gredy)

    processor = RepositoryProcessor(repo)
    processor.process_repo(issues_data, fn_gredy, start_date=start_date)

    logging.info(f"Processing complete! Data saved in {fn_gredy}, now will try to get issues description")
    CSVHandler.update_dataframe(fn_gredy)
    logging.info(f"Finished collecting issue description")
    logging.info(f"Exploding dataframe")
    CSVHandler.explode_base_commits(pd.read_csv(fn_gredy)).to_csv(fn_output, index=False)
    del processor

def main_entry_point():
    Fire(parse_git_issue_to_file)

if __name__ == "__main__":
    main_entry_point()
