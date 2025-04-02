import pandas as pd
from typing import Optional, Union, Tuple, Any


def parse_range(range_input: Any) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse range input and return (min, max) tuple.

    For numeric values:
    - int/float: exact value match
    - (2, 10): from 2 up to and including 10
    - (None, 10): up to and including 10 (no lower bound)
    - (2, None): 2 or more (no upper bound)
    """
    if range_input is None:
        return None, None

    # Handle exact value (int or float)
    if isinstance(range_input, (int, float)):
        return range_input, range_input

    # Handle tuple range
    if isinstance(range_input, tuple):
        if len(range_input) == 0:
            return None, None
        elif len(range_input) == 1:
            return range_input[0], None  # Only lower limit provided
        else:
            return range_input[0], range_input[1]  # Both limits provided

    # Default to exact match for anything else
    return range_input, range_input


def apply_filters(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Apply multiple filters to a DataFrame based on column types.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to filter
    **kwargs : dict
        Keyword arguments for filtering, where keys are column names and
        values are filter criteria

    Returns:
    --------
    pandas.DataFrame
        Filtered DataFrame
    """
    filtered_df = df.copy()

    # Apply filters for each keyword argument
    for key, value in kwargs.items():
        # Skip if the column doesn't exist
        if key not in df.columns:
            continue

        # Get the column data type
        dtype = df[key].dtype

        if pd.api.types.is_numeric_dtype(dtype):
            # Numeric column handling
            min_val, max_val = parse_range(value)

            if min_val is not None and max_val is not None and min_val == max_val:
                # Exact value match
                filtered_df = filtered_df[filtered_df[key] == min_val]
            else:
                # Range filter
                if min_val is not None:
                    filtered_df = filtered_df[filtered_df[key] >= min_val]
                if max_val is not None:
                    filtered_df = filtered_df[filtered_df[key] <= max_val]
        else:
            # String/Object column handling
            if isinstance(value, list):
                # Filter with a list of values
                filtered_df = filtered_df[filtered_df[key].isin(value)]
            else:
                # Single value filter
                filtered_df = filtered_df[filtered_df[key] == value]

    return filtered_df