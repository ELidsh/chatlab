import pandas as pd
from .colnames import conversation

def unpack_turns(df: pd.DataFrame,
                 conv_colname: str = conversation) -> pd.DataFrame:
    """
    Unpacks conversation turns from a nested structure into separate rows.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing a column with nested conversation data.
    conv_colname : str, default=conversation
        The name of the column containing conversation data (list of dictionaries).

    Returns:
    --------
    pandas.DataFrame
        A new DataFrame with each turn unpacked into a separate row.

    Notes:
    ------
    This function assumes each entry in the conv_colname column is a list of dictionaries,
    where each dictionary represents a turn in the conversation.
    """
    # Check if the conversation column exists
    if conv_colname not in df.columns:
        raise ValueError(f"Column '{conv_colname}' not found in DataFrame")

    # Step 1: Create a subset of df with only the conversation column
    conversation_df = df[[conv_colname]].copy()

    # Step 2: Check if the column contains valid data
    if conversation_df.empty:
        return pd.DataFrame()

    # Step 3: Unpack each conversation dictionary to one row per dict
    # Explode will create one row per list item in the conversation column
    unpacked_df = conversation_df.explode(conv_colname)

    # Step 4: Drop any rows where the conversation is None/NaN
    unpacked_df = unpacked_df.dropna().reset_index(drop=True)

    # Step 5: Convert the dictionaries in the conversation column into separate columns
    # json_normalize will create columns from the dictionary keys
    unpacked_df = pd.json_normalize(unpacked_df[conv_colname])

    return unpacked_df