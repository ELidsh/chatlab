import pandas as pd
import random
from typing import Optional, Union, List, Tuple
from .utils import apply_filters
from .colnames import conv_id


def filter_subset(df: pd.DataFrame,
                  return_all: bool = False,
                  conv_id_colname: str = conv_id,
                  **kwargs) -> Union[str, List[str], None]:
    """
    Return conversation ID(s) from the DataFrame that match the filters.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing conversation data (required positional argument).
    return_all : bool, default=False
        If True, returns all matching conversation IDs as a list.
        If False, returns a single random conversation ID.
    **kwargs : dict
        Keyword arguments for filtering. If a key matches a column name in df,
        filtering is applied based on the value type:
        - String columns:
          - Single value (e.g., source='wc')
          - List of values (e.g., source=['wc', 'other_source'])
        - Numerical columns:
          - Exact value (e.g., code_turns=0)
          - Range tuple:
            - (2, 10) means from 2 up to and including 10
            - (None, 10) means up to and including 10 (no lower bound)
            - (2, None) means 2 or more (no upper bound)

    Returns:
    --------
    str, List[str], or None:
        If return_all=False: A random conversation ID ('conv_id') from the filtered DataFrame.
        If return_all=True: A list of all matching conversation IDs.
        If no matching conversations are found, returns None.

    Example:
    --------
    # Get a random conversation with source 'wc', exactly 0 code turns,
    # and between 1-3 toxic turns
    filter_subset(df,
                  source='wc',
                  code_turns=0,
                  toxic_turns=(1, 3))

    # Get all conversations with at least 5 turns
    filter_subset(df, return_all=True, turns=(5, None))
    """
    # Apply filters from kwargs
    filtered_df = apply_filters(df, **kwargs)

    # Check if we have any matches
    if filtered_df.empty:
        return None

    # Print the number of matching conversations
    print(f'{len(filtered_df)} conversations match filters')

    # Return based on return_all flag
    if return_all:
        return filtered_df[conv_id_colname].unique().tolist()
    else:
        return random.choice(filtered_df[conv_id_colname].unique())