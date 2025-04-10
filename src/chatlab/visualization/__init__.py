# chatlab/visualization/__init__.py
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os
import random
from typing import Union, List, Optional, Dict, Any
from datetime import datetime # Added

# Import helpers from sibling modules
# --- Make sure get_additional_styles is NOT imported if it stays in html_generator ---
from .html_generator import get_metadata_html, get_full_grid_row_html, generate_full_html
from .resources import get_avatars, load_css, load_js, _load_file_content, PACKAGE_ROOT
from ..colnames import colnames

# Optional: For displaying in notebooks
try:
    from IPython.display import display as ipython_display, HTML
    _IPYTHON_AVAILABLE = True
except ImportError:
    _IPYTHON_AVAILABLE = False


# --- Helper function to parse timestamp ---
def _parse_timestamp(timestamp_str: Any, col_name: str) -> Optional[datetime]:
    """Safely parses a timestamp string into a datetime object."""
    if pd.isna(timestamp_str):
        return None
    try:
        # Attempt parsing common formats, add more if needed
        # Try ISO format first
        return datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try another common format
            return datetime.strptime(str(timestamp_str), '%Y-%m-%d %H:%M:%S')
        except ValueError:
             try:
                 # Try just time if that's relevant (adjust format)
                 return datetime.strptime(str(timestamp_str), '%H:%M:%S')
             except ValueError:
                # Fallback or more formats...
                print(f"Warning: Could not parse timestamp '{timestamp_str}' for column '{col_name}'.", file=sys.stderr)
                return None
    except Exception as e:
         print(f"Error parsing timestamp '{timestamp_str}': {e}", file=sys.stderr)
         return None



def _process_single_conversation(
        df: pd.DataFrame,
        conv_id: str,
        theme: str = 'light',
        custom_css_path: Optional[Union[str, Path]] = None,
        save_mode: str = "base_html", # save_mode is used below now
        user_avatar_svg: Optional[str] = None,
        assistant_avatar_svg: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """
    Process a single conversation and return HTML content for both base and annotation modes.
    Corrected timestamp/duration logic AND function calls.
    """
    # --- 1. Data Retrieval & Validation ---
    #print(f"\n[DEBUG] Processing conv_id: {conv_id}") # Keep DEBUG prints for now
    conv_id_col = colnames['conv']['conv_id']
    timestamp_col = colnames['turn']['timestamp']
    role_col = colnames['turn']['role']
    message_col = colnames['turn']['message']
    toxic_col = colnames['turn']['toxic']
    redacted_col = colnames['turn']['redacted']
    code_block_col = colnames['turn']['code_block']

    try:
        matching_rows = df.loc[df[conv_id_col] == conv_id]
        if len(matching_rows) == 0:
       #     print(f"[DEBUG] Error: Conv ID '{conv_id}' not found in DataFrame.", file=sys.stderr) # Added debug context
            return None
        row = matching_rows.iloc[0]
    except KeyError:
     #   print(f"[DEBUG] Error: '{conv_id_col}' column missing in DataFrame.", file=sys.stderr) # Added debug context
        return None
    except Exception as e:
      #  print(f"[DEBUG] Error accessing row for '{conv_id}': {e}", file=sys.stderr) # Added debug context
        return None

    # --- 2. Load and Prepare Conversation Turns ---
    conversation_col = colnames['conv']['conversation']
    if conversation_col not in row.index:
     #   print(f"[DEBUG] Error: '{conversation_col}' column missing in row for '{conv_id}'.", file=sys.stderr)
        return None

    conversation_data = row[conversation_col]
   # print(f"[DEBUG] Raw conversation_data type for '{conv_id}': {type(conversation_data)}")

    try:
        # ... (existing null check logic) ...
        if pd.isna(conversation_data).any() if hasattr(conversation_data, 'any') else pd.isna(conversation_data):
      #       print(f"[DEBUG] Error: '{conversation_col}' is null or empty for '{conv_id}'.", file=sys.stderr)
             return None
    except Exception as e:
        print(f"[DEBUG] Warning: Could not reliably check for null/missing data in '{conversation_col}' for '{conv_id}': {e}", file=sys.stderr)
        # Continue processing cautiously

    turns = None
    try:
        # --- Existing parsing logic ---
      #  print(f"[DEBUG] Attempting to parse/convert conversation data...")
        if isinstance(conversation_data, str):
            print("[DEBUG] Data is string, trying json.loads...")
            try:
                turns = json.loads(conversation_data)
            except json.JSONDecodeError:
                print("[DEBUG] json.loads failed, trying ast.literal_eval...")
                import ast
                try:
                    turns = ast.literal_eval(conversation_data)
                except (SyntaxError, ValueError) as e_ast:
                    print(f"[DEBUG] ast.literal_eval failed: {e_ast}", file=sys.stderr)
                    raise TypeError("Could not parse conversation string format.") from e_ast
        elif isinstance(conversation_data, list):
          #  print("[DEBUG] Data is already a list.")
            turns = conversation_data
        elif hasattr(conversation_data, 'tolist'):
          #  print("[DEBUG] Data has 'tolist' method, calling it...")
            turns = conversation_data.tolist()
        elif isinstance(conversation_data, np.ndarray):
           #  print("[DEBUG] Data is numpy array, calling tolist()...")
             turns = conversation_data.tolist()
        else:
           # print(f"[DEBUG] Data type {type(conversation_data)} not explicitly handled, trying fallback...")
            try:
                turns_str = str(conversation_data)
                turns = json.loads(turns_str)
            except Exception as e_fallback:
                 print(f"[DEBUG] Fallback str/json conversion failed: {e_fallback}", file=sys.stderr)
                 raise TypeError(f"Unsupported conversation format: {type(conversation_data)}") from e_fallback


        # --- Validation after attempting parse/conversion ---
        if turns is None or not isinstance(turns, list) or not all(isinstance(t, dict) for t in turns):
           print(f"[DEBUG] Failed to get valid list of dicts for turns in {conv_id}.", file=sys.stderr)
           return None
     #   print(f"[DEBUG] Successfully parsed/converted conversation data into list of {len(turns)} turns.")

    except Exception as e:
        print(f"[DEBUG] Error during conversation parsing/conversion for '{conv_id}': {e}", file=sys.stderr)
        # import traceback; traceback.print_exc() # Uncomment for full traceback if needed
        return None

    # --- Pre-process to find relevant timestamps ---
    assistant_timestamps = {}
    for i, turn in enumerate(turns):
        if turn.get(role_col) == 'assistant':
            ts_str = turn.get(timestamp_col)
            parsed_ts = _parse_timestamp(ts_str, timestamp_col) if ts_str is not None else None
            if parsed_ts:
                 assistant_timestamps[i] = parsed_ts

    # --- 3. Prepare Metadata (Conversation Level) ---
    metadata_html = get_metadata_html(conv_id, row)

    # --- 4. Prepare Avatars ---
    avatars = get_avatars(user_avatar_svg, assistant_avatar_svg)

    # --- 5. Generate HTML for Grid Rows ---
    turn_col_names = {
        'role': role_col, 'message': message_col,
        'toxic': toxic_col, 'redacted': redacted_col,
        'code_block': code_block_col, 'timestamp': timestamp_col
    }
    base_grid_rows_html_parts = []
    annotation_grid_rows_html_parts = []
    include_annotations_flag = (save_mode == "annotation")

    first_user_turn_index = -1
    for i, turn in enumerate(turns):
         if turn.get(role_col) == 'user':
              first_user_turn_index = i
              break

    for i, turn in enumerate(turns):
        if not isinstance(turn, dict):
            continue

        turn_number = i + 1
        current_role = turn.get(role_col)

        timestamp_to_display_val = None
        timestamp_for_duration_start_val = None
        show_duration_flag = False

        if current_role == 'user':
            next_assistant_idx = -1
            for k in sorted(assistant_timestamps.keys()):
                if k > i:
                    next_assistant_idx = k
                    break
            if next_assistant_idx != -1:
                timestamp_to_display_val = assistant_timestamps[next_assistant_idx]

            if i > first_user_turn_index:
                prev_assistant_idx = -1
                for k in sorted(assistant_timestamps.keys(), reverse=True):
                    if k < i:
                         prev_assistant_idx = k
                         break
                if prev_assistant_idx != -1 and timestamp_to_display_val:
                    timestamp_for_duration_start_val = assistant_timestamps[prev_assistant_idx]
                    show_duration_flag = True

        try:
            base_html_part = get_full_grid_row_html(
                turn=turn,
                turn_number=turn_number,
                avatars=avatars,
                col_names=turn_col_names,
                timestamp_to_display=timestamp_to_display_val,
                timestamp_for_duration_start=timestamp_for_duration_start_val,
                show_duration=show_duration_flag,
                include_annotations=False
            )
            base_grid_rows_html_parts.append(base_html_part)
        except Exception as e_html_base:
             print(f"[DEBUG] Error generating base HTML for turn {turn_number} of '{conv_id}': {e_html_base}", file=sys.stderr)

        if include_annotations_flag:
             try:
                  anno_html_part = get_full_grid_row_html(
                      turn=turn,
                      turn_number=turn_number,
                      avatars=avatars,
                      col_names=turn_col_names,
                      timestamp_to_display=timestamp_to_display_val,
                      timestamp_for_duration_start=timestamp_for_duration_start_val,
                      show_duration=show_duration_flag,
                      include_annotations=True
                  )
                  annotation_grid_rows_html_parts.append(anno_html_part)
             except Exception as e_html_anno:
                  print(f"[DEBUG] Error generating annotation HTML for turn {turn_number} of '{conv_id}': {e_html_anno}", file=sys.stderr)


    base_chat_rows_html = "\n".join(base_grid_rows_html_parts)
    annotation_chat_rows_html = "\n".join(annotation_grid_rows_html_parts) if include_annotations_flag else base_chat_rows_html


    # --- 6. Load Custom CSS ---
    custom_css_content = None
    if custom_css_path:
        custom_css_content = _load_file_content(Path(custom_css_path), fallback_content="")
        if not custom_css_content:
            print(f"Warning: Could not load custom CSS from '{custom_css_path}'. Using theme '{theme}'.", file=sys.stderr)
            custom_css_content = None

    # --- 7. Generate Full HTML (Using correct signature) ---
    base_html = generate_full_html(
        metadata_html=metadata_html,
        chat_rows_html=base_chat_rows_html,
        theme=theme,
        custom_css_content=custom_css_content,
        include_js=False,
        include_annotations=False
    )

    annotation_html = generate_full_html(
        metadata_html=metadata_html,
        chat_rows_html=annotation_chat_rows_html, # Use annotation HTML here
        theme=theme,
        custom_css_content=custom_css_content,
        include_js=True,
        include_annotations=True
    )


  #  print(f"[DEBUG] Successfully processed and generated HTML for conv_id: {conv_id}")
    return {
        'base_html': base_html,
        'annotation_html': annotation_html
    }

# ... (keep _parse_timestamp helper and visualize_conversation function) ...


# --- Existing visualize_conversation function remains largely the same ---
# It should now correctly call the updated _process_single_conversation
def visualize_conversation(
        df: pd.DataFrame,
        conv_id: Union[str, List[str], pd.DataFrame, pd.Series],
        theme: str = 'light',
        custom_css_path: Optional[Union[str, Path]] = None,
        save: Union[bool, str] = False,
        save_dir: Optional[Union[str, Path]] = None,
        save_mode: str = "base_html",
        display: bool = True,
        user_avatar_svg: Optional[str] = None,
        assistant_avatar_svg: Optional[str] = None,
        tag: Optional[str] = None
) -> None:  # Return type is None
    """
    Generates HTML visualization for conversations with options for display and saving.
    Includes turn-level metadata display.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing conversation data
    conv_id : str, list[str], DataFrame, or Series
        - If str: A single conversation ID to visualize
        - If list[str]: Multiple conversation IDs to process
        - If DataFrame: Will extract conversation IDs from it (expects 'conv_id' column)
        - If Series: Will extract conversation ID(s) from it
    theme : str
        'light' or 'dark' theme for the visualization
    custom_css_path : str or Path or None
        Path to a custom CSS file to use instead of the built-in themes
    save : bool or str
        If True: Save file(s) as {conv_id}.html
        If str: Save file(s) as {conv_id}_{save}.html
    save_dir : str or Path or None
        Directory to save files to. If None, saves to current working directory
    save_mode : str
        'base_html': Basic HTML/CSS only (no JavaScript, no annotations)
        'annotation': Full interactive version with annotation support
    display : bool
        Whether to display the visualization in the console/notebook
    user_avatar_svg : str or None
        Custom SVG content for user avatar
    assistant_avatar_svg : str or None
        Custom SVG content for assistant avatar
    tag : str or None
        Optional tag to add to the end of the filename

    Returns:
    --------
    None
    """
    # Normalize save_mode to lowercase
    save_mode = save_mode.lower()
    if save_mode not in ["base_html", "annotation"]:
        print(f"Warning: Invalid save_mode '{save_mode}'. Using 'base_html'.", file=sys.stderr)
        save_mode = "base_html"

    # Normalize theme to lowercase
    theme = theme.lower()
    if theme not in ["light", "dark"]:
        print(f"Warning: Invalid theme '{theme}'. Using 'light'.", file=sys.stderr)
        theme = "light"

    # Handle save_dir
    if save_dir is not None:
        save_dir_path = Path(save_dir)
        try:
            save_dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory '{save_dir}': {e}", file=sys.stderr)
            print("Files will be saved to current working directory.", file=sys.stderr)
            save_dir_path = Path.cwd()
    else:
        save_dir_path = Path.cwd()

    # --- Start: Define conv_ids based on input type ---
    conv_ids = []
    display_id = None
    conv_id_col = colnames['conv']['conv_id']  # Get the standard column name

    if isinstance(conv_id, str):
        conv_ids = [conv_id]
        display_id = conv_id
    elif isinstance(conv_id, list):
        conv_ids = conv_id
        if conv_ids:
            display_id = random.choice(conv_ids)
    elif isinstance(conv_id, pd.DataFrame):
        if conv_id_col in conv_id.columns:
            conv_ids = conv_id[conv_id_col].unique().tolist()
            if conv_ids:
                display_id = random.choice(conv_ids)
        else:
            print(f"Error: '{conv_id_col}' column not found in provided DataFrame.", file=sys.stderr)
            return None
    elif isinstance(conv_id, pd.Series):
        # Check if the series contains conv_ids (e.g., result of df[conv_id_col])
        # Or if it's a single value series intended as the ID
        if conv_id.name == conv_id_col or conv_id.dtype == 'object' or pd.api.types.is_string_dtype(conv_id.dtype):
            conv_ids = conv_id.astype(str).unique().tolist()
        elif len(conv_id) == 1:
            conv_ids = [str(conv_id.iloc[0])]
        else:
            # Fallback or error if series content is ambiguous
            print(f"Error: Could not reliably extract conversation ID(s) from the provided Series.", file=sys.stderr)
            return None

        if conv_ids:
            display_id = random.choice(conv_ids)
    else:
        print(f"Error: conv_id must be str, list[str], DataFrame, or Series. Got {type(conv_id)}", file=sys.stderr)
        return None
    # --- End: Define conv_ids based on input type ---

    # Now check if conv_ids was successfully populated
    if not conv_ids:
        print("Error: No valid conversation IDs found or extracted.", file=sys.stderr)
        return None  # Keep return None

    # Process all conversations
    processed_results = {}
    # Use the pre-selected display_id if needed later
    actual_display_id = display_id  # Store the randomly chosen ID if we need it for display

    for cid in conv_ids:
        # Call the updated processing function
        result = _process_single_conversation(
            df=df,
            conv_id=str(cid),  # Ensure cid is string for processing function
            theme=theme,
            custom_css_path=custom_css_path,
            save_mode=save_mode,  # Pass save_mode down if needed by _process
            user_avatar_svg=user_avatar_svg,
            assistant_avatar_svg=assistant_avatar_svg
        )

        if result:
            processed_results[str(cid)] = result  # Ensure dictionary keys are strings

    # Handle display
    if display and actual_display_id and str(actual_display_id) in processed_results:
        # Display the version corresponding to the save_mode? Or always base? Stick to base.
        html_content_to_display = processed_results[str(actual_display_id)]['base_html']

        if _IPYTHON_AVAILABLE:
            ipython_display(HTML(html_content_to_display))
            # Add note about interactive features if saving annotation version
            if save_mode == "annotation" and save:
                print("NOTE: Interactive features (like annotations) will be available in the saved HTML file.")
        else:
            print("Warning: IPython is not installed. Cannot display HTML inline.", file=sys.stderr)
            print("You can save the HTML to a file using save=True or providing a save path.", file=sys.stderr)
    elif display:
        print(
            f"Warning: Could not display conversation. Display ID '{actual_display_id}' not found in processed results.",
            file=sys.stderr)

    # Handle saving
    if save:
        # Get theme and save mode tags for filename
        theme_tag = "dark" if theme == "dark" else "light"
        save_mode_tag = "annot" if save_mode == "annotation" else "static"

        saved_files = []
        for cid_str, result in processed_results.items():
            # Determine which HTML version to save
            html_to_save = result['annotation_html'] if save_mode == "annotation" else result['base_html']

            # Build filename with theme and save mode tags
            filename_parts = [cid_str, theme_tag, save_mode_tag]

            # Add user tag if provided
            if tag is not None:
                # Basic sanitization for tag
                safe_tag = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in tag)
                filename_parts.append(safe_tag)

            # Combine parts with underscores
            filename = "_".join(filename_parts) + ".html"

            # If save is a string, use it as a filename part after sanitizing
            if isinstance(save, str):
                # Basic sanitization for save string
                safe_save = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in save)
                # Insert save after cid but before theme/mode tags
                filename_parts = [cid_str, safe_save, theme_tag, save_mode_tag]
                if tag is not None:
                    filename_parts.append(safe_tag)
                filename = "_".join(filename_parts) + ".html"

            # Basic sanitization for filename part from cid_str
            safe_cid_str = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in cid_str)
            filename = filename.replace(cid_str, safe_cid_str)  # Replace original cid with sanitized one

            save_filepath = save_dir_path / filename

            try:
                with open(save_filepath, 'w', encoding='utf-8') as f:
                    f.write(html_to_save)
                saved_files.append(str(save_filepath.resolve()))
            except Exception as e:
                print(f"Error saving to '{save_filepath}': {e}", file=sys.stderr)

        if saved_files:
            if len(saved_files) == 1:
                print(f"Saved to: {saved_files[0]}")
            else:
                print(f"Saved {len(saved_files)} files to {save_dir_path}")
            if save_mode == "annotation":
                print("Note: Files saved with full annotation features.")
        elif processed_results:  # Only print error if we expected to save something
            print("No files were saved due to errors. See above for details.")

    # Return None as per the function's design
    return None