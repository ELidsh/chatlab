# chatlab/sample_data/__init__.py
import pandas as pd
from pathlib import Path


def load_sample_data():
    """
    Load the sample conversation data for demonstration purposes.

    Returns:
    --------
    pd.DataFrame
        DataFrame containing sample conversation data

    Examples:
    ---------
    >>> import chatlab as clb
    >>> df = clb.sample_data.load_sample_data()
    >>> clb.visualize_conversation(df, df['conv_id'].iloc[0])
    """
    # Get the path to the sample data file
    sample_dir = Path(__file__).parent
    sample_file = sample_dir / "samples" / "sample_data.parquet"

    # Load and return the parquet file
    return pd.read_parquet(sample_file)