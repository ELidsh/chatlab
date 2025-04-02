import pandas as pd
import random
import re
import warnings
from typing import Union, List, Tuple
from .utils import apply_filters
from colnames import conv_id, message, turn_number


def search_text_matches(df: pd.DataFrame,
                        text: str,
                        case_sensitive: bool = True,
                        regex: bool = False,
                        return_all: bool = False,
                        conv_id_colname: str = conv_id,
                        message_colname: str = message,
                        turn_num_colname: str = turn_number,
                        verbose=True,
                        **kwargs) -> Union[List[str], Tuple[str, List[int]], None]:
    """
    Search for text matches in a DataFrame's 'message' column and apply additional filters.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing conversation data with at least 'message', 'conv_id', and 'turn_num' columns.
    text : str
        The text to search for in the 'message' column. If regex=True, this is treated as a regular expression pattern.
        To match text at specific positions, use regex=True with:
        - "^text" to match at the beginning of messages
        - "text$" to match at the end of messages
    case_sensitive : bool, default=True
        Whether the text search should be case sensitive.
    regex : bool, default=False
        If True, the 'text' parameter is treated as a regular expression pattern.
        If False, the text is escaped to be treated as a literal string.
    return_all : bool, default=False
        If True, returns a list of all unique 'conv_id' values from matching rows.
        If False, returns a tuple with (random conv_id, list of turn_num values with matches in that conv_id).
    conv_colname : str
        The name of the column containing conversation IDs.
    message_colname : str
        The name of the column containing message text.
    verbose : bool, default=True
        Whether to print information about the number of matching messages and conversations.
    **kwargs : dict
        Additional keyword arguments for filtering. If a key matches a column name in df,
        filtering is applied using the same logic as in filter_subset:
        - String columns (like 'role'): single value or list of values
          e.g., role='user' to filter for user messages only
        - Numerical columns: exact value or range tuple
        A warning will be issued for kwargs that don't match column names.

    Returns:
    --------
    - If return_all=True: List[str] of unique conv_ids matching the search
    - If return_all=False: Tuple[str, List[int]] containing (random conv_id, list of turn_nums with matches)
    - If no matches found: None

    Example:
    --------
    # Find a random conversation with "Python" in messages from the assistant
    search_text_matches(df, "Python", role="assistant")

    # Find all conversations where messages start with "Hello"
    search_text_matches(df, "^Hello", regex=True, return_all=True)

    # Find all conversations with messages ending with a question mark
    search_text_matches(df, r"\?$", regex=True)

    # Find all conversations with "help" in messages and at least 5 turns
    search_text_matches(df, "help", return_all=True, turns=(5, None))
    """
    # Verify required columns exist
    required_columns = [conv_id_colname, message_colname, turn_num_colname]
    if not all(column in df.columns for column in required_columns):
        raise ValueError(f"DataFrame is missing one or more required columns: {required_columns}")

    # Start with a copy of the DataFrame
    filtered_df = df.copy()

    # Prepare the pattern based on regex flag
    pattern = text if regex else re.escape(text)

    # Apply text search to message column
    filtered_df = filtered_df[filtered_df[message_colname].str.contains(
        pattern, case=case_sensitive, regex=True, na=False)]

    # Apply additional filters from kwargs (with warning for non-existent columns)
    filtered_kwargs = {}
    for key, value in kwargs.items():
        if key not in df.columns:
            warnings.warn(f"Column '{key}' not found in DataFrame. This filter will be ignored.")
        else:
            filtered_kwargs[key] = value

    # Apply remaining filters
    if filtered_kwargs:
        filtered_df = apply_filters(filtered_df, **filtered_kwargs)

    # Check if we have any matches
    if filtered_df.empty:
        return None

    # Print the number of matching rows and conversations
    unique_convs = filtered_df[conv_id_colname].unique()

    if verbose:
        print(f'Found {len(filtered_df)} matching messages in {len(unique_convs)} conversations')

    # Return based on return_all flag
    if return_all:
        return unique_convs.tolist()
    else:
        # Select a random conversation
        random_conv = random.choice(unique_convs)

        # Get the turn numbers for the matching messages in this conversation
        turn_nums = filtered_df[filtered_df[conv_id_colname] == random_conv][turn_num_colname].tolist()

        return random_conv, turn_nums