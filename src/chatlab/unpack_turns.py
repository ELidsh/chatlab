from colnames import conversation
import pandas as pd

def unpack_turns(df,
                 conv_colname: str = conversation):
    # Step 1: Create a subset of df with only the 'conversation' column
    conversation_df = df[[conv_colname]].copy()

    # Step 2: Unpack each conversation dictionary to one row per dict
    # Assuming each entry in the 'conversation' column is a list of dictionaries
    unpacked_df = conversation_df.explode(conv_colname)

    # Convert the dictionaries in the 'conversation' column into separate columns
    unpacked_df = unpacked_df.dropna().reset_index(drop=True)
    unpacked_df = pd.json_normalize(unpacked_df[conv_colname])

    return unpacked_df