import pandas as pd
import glob
import os
from typing import Optional, Dict, Any, Union, List


def concat_files(
        directory: str,
        file_type: str = 'json',
        read_kwargs: Optional[Dict[str, Any]] = None,
        concat_kwargs: Optional[Dict[str, Any]] = None,
        verbose: bool = False,
        error_handling: str = 'warn'
) -> pd.DataFrame:
    """
    Reads all files of specified type in the given directory and concatenates them into a single DataFrame.

    Parameters:
    -----------
    directory : str
        The directory containing the files to concatenate.
    file_type : str, default='json'
        The file extension to look for (without the dot).
    read_kwargs : dict, optional
        Additional keyword arguments to pass to the pandas read function.
        For JSON files, defaults to {'orient': 'records', 'lines': True}.
    concat_kwargs : dict, optional
        Additional keyword arguments to pass to pd.concat().
        Defaults to {'ignore_index': True}.
    verbose : bool, default=False
        If True, prints information about the files being processed.
    error_handling : str, default='warn'
        How to handle errors when reading files:
        - 'warn': Skip problematic files and issue a warning
        - 'raise': Raise an exception if any file cannot be read
        - 'ignore': Silently skip problematic files

    Returns:
    --------
    pd.DataFrame
        A DataFrame containing the concatenated data from all files.
        Returns an empty DataFrame if no valid files are found.

    Raises:
    -------
    ValueError
        If directory doesn't exist or error_handling is invalid.
    FileNotFoundError
        If no matching files are found.
    Various pandas exceptions
        If error_handling='raise' and a file cannot be read.

    Examples:
    ---------
    # Concatenate all JSON files in a directory
    df = concat_files('data/raw_files')

    # Concatenate all CSV files with specific reading options
    df = concat_files('data/logs', file_type='csv', read_kwargs={'sep': '|'})
    """
    # Validate directory
    if not os.path.isdir(directory):
        raise ValueError(f"Directory does not exist: {directory}")

    # Validate error_handling parameter
    valid_error_modes = ['warn', 'raise', 'ignore']
    if error_handling not in valid_error_modes:
        raise ValueError(f"error_handling must be one of {valid_error_modes}")

    # Set default kwargs for reading files based on file_type
    if read_kwargs is None:
        if file_type.lower() == 'json':
            read_kwargs = {'orient': 'records', 'lines': True}
        else:
            read_kwargs = {}

    # Default concat kwargs
    if concat_kwargs is None:
        concat_kwargs = {'ignore_index': True}

    # Find all matching files
    files = glob.glob(os.path.join(directory, f"*.{file_type}"))

    if not files:
        raise FileNotFoundError(f"No .{file_type} files found in {directory}")

    if verbose:
        print(f"Found {len(files)} .{file_type} files in {directory}")

    # Create a list to hold dataframes
    dataframes = []

    # Select the appropriate reader function based on file_type
    if file_type.lower() == 'json':
        reader_func = pd.read_json
    elif file_type.lower() == 'csv':
        reader_func = pd.read_csv
    elif file_type.lower() == 'parquet':
        reader_func = pd.read_parquet
    elif file_type.lower() == 'excel' or file_type.lower() in ['xls', 'xlsx']:
        reader_func = pd.read_excel
    else:
        # Default to csv for unknown types
        reader_func = pd.read_csv

    # Read each file
    for file in files:
        try:
            if verbose:
                print(f"Reading {file}...")

            df = reader_func(file, **read_kwargs)

            if verbose:
                print(f"  Read {len(df)} rows from {file}")

            dataframes.append(df)

        except Exception as e:
            if error_handling == 'raise':
                raise
            elif error_handling == 'warn':
                import warnings
                warnings.warn(f"Error reading file {file}: {str(e)}")
            # If 'ignore', just skip silently

    # Check if we have any valid dataframes
    if not dataframes:
        if verbose:
            print("No valid data found in any files.")
        return pd.DataFrame()

    # Concatenate all dataframes
    concatenated_df = pd.concat(dataframes, **concat_kwargs)

    if verbose:
        print(f"Concatenated DataFrame has {len(concatenated_df)} rows and {len(concatenated_df.columns)} columns.")

    return concatenated_df

def hello():
    print("Hello")