import math
from typing import List, Optional


def process_repos_in_batches(repo_list: List[str], final_csv_filename: str, batch_size: int = 100, start_date: Optional[str] = None) -> None:
    """
    Processes repositories in batches and appends the results to a final CSV file.

    Args:
        repo_list (List[str]): List of GitHub repositories.
        final_csv_filename (str): The final CSV file to store combined results.
        batch_size (int, optional): Number of repos to process per batch. Defaults to 100.
        start_date (Optional[str], optional): Optional start date for filtering merge commits.
    """
    import pandas as pd
    import os
    import logging

    from datetime import datetime

    initialize_csv(final_csv_filename)

    total_batches = math.ceil(len(repo_list) / batch_size)

    for i in range(total_batches):
        batch = repo_list[i * batch_size:(i + 1) * batch_size]
        temp_csv = f"temp_batch_{i+1}.csv"

        logging.info(f"Starting batch {i+1}/{total_batches} with {len(batch)} repos")

        # Process repos in current batch
        for repo in batch:
            process_repo(repo_name=repo, issues_data={}, csv_filename=temp_csv, start_date=start_date)

        logging.info(f"Batch {i+1} collected. Updating PR and issue data...")
        update_dataframe(temp_csv)
        temp_df_expl = explode_base_commits(pd.read_csv(temp_csv))
        temp_df_expl.to_csv(temp_csv, index = False)

        # Append temp.csv to final.csv
        if os.path.exists(temp_csv):
            temp_df = pd.read_csv(temp_csv)
            final_df = pd.read_csv(final_csv_filename)
            final_df = pd.concat([final_df, temp_df], ignore_index=True)
            final_df.to_csv(final_csv_filename, index=False)
            os.remove(temp_csv)
            logging.info(f"Appended and cleaned up batch {i+1}")

    logging.info(f"All batches processed. Final CSV at {final_csv_filename}")