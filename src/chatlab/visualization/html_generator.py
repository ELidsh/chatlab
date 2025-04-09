# chatlab/visualization/html_generator.py
import html
from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta # Added for timestamp/duration
import re # Import regex library for placeholder handling
try:
    import markdown # Import the markdown library
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("WARNING: 'markdown' library not found. pip install markdown for full formatting. Falling back to basic escaping.")

from .resources import load_css, load_js
from ..colnames import colnames  # Import the colnames dictionary



# --- Existing get_metadata_html function remains the same ---
def get_metadata_html(conv_id: str, df_row: Any) -> str:
    """
    Generate HTML for the metadata section with simplified sequential format.

    Parameters:
    -----------
    conv_id: The conversation ID
    df_row: Row from the DataFrame containing all metadata
    """
    # Check if df_row is a pandas Series or a dictionary
    has_index = hasattr(df_row, 'index')

    # Get column name mappings
    conv_cols = colnames['conv']

    # Helper function to check if a field exists and is not null
    def field_exists(field_name):
        col_name = conv_cols.get(field_name, field_name)  # Use mapped name if available, original otherwise
        exists = False

        if has_index and col_name in df_row.index:
            try:
                # Handle various null types
                if isinstance(df_row[col_name], (list, dict, np.ndarray)) or not pd.isna(df_row[col_name]):
                    exists = True
            except:
                # If we can't check nullness, assume it exists
                exists = True
        elif not has_index and col_name in df_row:
            value = df_row.get(col_name)
            if value is not None and not (isinstance(value, float) and np.isnan(value)):
                exists = True

        return exists, col_name

    # Helper function to get field value
    def get_field_value(field_name):
        _, col_name = field_exists(field_name)
        return df_row[col_name]

    # Start the metadata container
    html_parts = ['<div class="metadata">']

    # Add conversation ID as title
    html_parts.append(f'<h2>{html.escape(conv_id)}</h2>')

    # Add first horizontal rule
    html_parts.append('<hr class="metadata-divider">')

    # --- Add fields in prescribed order, checking for existence ---

    # 1. Source field
    source_exists, source_col = field_exists('source')
    if source_exists:
        source_value = get_field_value('source')
        if source_value == 'sg':
            html_parts.append(
                '<p><strong>Source:</strong> <a href="https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered" target="_blank">ShareGPT</a></p>')
        elif source_value == 'wc':
            html_parts.append(
                '<p><strong>Source:</strong> <a href="https://huggingface.co/datasets/allenai/WildChat-1M" target="_blank">Wildchat-1M</a></p>')
        else:
            html_parts.append(f'<p><strong>Source:</strong> {html.escape(str(source_value))}</p>')

    # 2. Model field
    model_exists, model_col = field_exists('model')
    if model_exists:
        html_parts.append(f'<p><strong>Model:</strong> {html.escape(str(get_field_value("model")))}</p>')

    # Add second horizontal rule before user info
    html_parts.append('<hr class="metadata-divider">')

    # 3. User field with frequency if available
    user_exists, user_col = field_exists('user_id')
    if user_exists:
        user_text = f'{html.escape(str(get_field_value("user_id")))}'

        user_freq_exists, user_freq_col = field_exists('user_freq')
        if user_freq_exists:
            user_freq = get_field_value('user_freq')
            user_text += f' ({html.escape(str(user_freq))} conversation{"s" if user_freq != 1 else ""})'

        html_parts.append(f'<p><strong>User:</strong> {user_text}</p>')

    # 4. Country field
    country_exists, country_col = field_exists('country')
    if country_exists:
        html_parts.append(f'<p><strong>Country:</strong> {html.escape(str(get_field_value("country")))}</p>')

    # 5. State field
    state_exists, state_col = field_exists('state')
    if state_exists:
        html_parts.append(f'<p><strong>State:</strong> {html.escape(str(get_field_value("state")))}</p>')

    # Add third horizontal rule before stats
    html_parts.append('<hr class="metadata-divider">')

    # 6. Turns with optional details
    turns_exists, turns_col = field_exists('turns')
    if turns_exists:
        turns_text = f'{html.escape(str(get_field_value("turns")))}'
        extra_info = []

        n_code_exists, n_code_col = field_exists('n_code')
        n_toxic_exists, n_toxic_col = field_exists('n_toxic')
        n_redacted_exists, n_redacted_col = field_exists('n_redacted')

        if n_code_exists:
            extra_info.append(f'code: {get_field_value("n_code")}')

        if n_toxic_exists:
            extra_info.append(f'toxic: {get_field_value("n_toxic")}')

        if n_redacted_exists:
            extra_info.append(f'redacted: {get_field_value("n_redacted")}')

        if extra_info:
            turns_text += f' ({", ".join(extra_info)})'

        html_parts.append(f'<p><strong>Turns:</strong> {turns_text}</p>')

    # 7. Start timestamp
    start_exists, start_col = field_exists('start')
    if start_exists:
        try:
            timestamp = pd.to_datetime(get_field_value('start'))
            formatted_time = timestamp.strftime('%d.%m.%Y, %H:%M:%S')
            html_parts.append(f'<p><strong>Start:</strong> {formatted_time}</p>')
        except:
            html_parts.append(f'<p><strong>Start:</strong> {html.escape(str(get_field_value("start")))}</p>')

    # 8. End timestamp
    end_exists, end_col = field_exists('end')
    if end_exists:
        try:
            timestamp = pd.to_datetime(get_field_value('end'))
            formatted_time = timestamp.strftime('%d.%m.%Y, %H:%M:%S')
            html_parts.append(f'<p><strong>End:</strong> {formatted_time}</p>')
        except:
            html_parts.append(f'<p><strong>End:</strong> {html.escape(str(get_field_value("end")))}</p>')

    # 9. Duration (if both timestamps exist)
    if start_exists and end_exists:
        try:
            start_time = pd.to_datetime(get_field_value('start'))
            end_time = pd.to_datetime(get_field_value('end'))
            duration = end_time - start_time

            # Format duration as specified
            seconds = duration.total_seconds()
            days, remainder = divmod(seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)

            duration_parts = []
            if days > 0:
                duration_parts.append(f"{int(days)}d")
            if hours > 0 or days > 0:
                duration_parts.append(f"{int(hours)}h")
            if minutes > 0 or hours > 0 or days > 0:
                duration_parts.append(f"{int(minutes)}m")
            duration_parts.append(f"{int(seconds)}s")

            formatted_duration = ", ".join(duration_parts)
            html_parts.append(f'<p><strong>Duration:</strong> {formatted_duration}</p>')
        except:
            pass  # Skip duration if there's an error

    # 10. Word counts
    n_words_exists, n_words_col = field_exists('n_words')
    if n_words_exists:
        words_text = f'{html.escape(str(get_field_value("n_words")))}'

        # Add average word counts if available
        n_words_user_exists, n_words_user_col = field_exists('n_words_user')
        n_words_gpt_exists, n_words_gpt_col = field_exists('n_words_gpt')

        if n_words_user_exists and n_words_gpt_exists and turns_exists:
            try:
                turns = float(get_field_value('turns'))
                if turns > 0:
                    user_avg = round(float(get_field_value('n_words_user')) / (turns * 0.5))
                    gpt_avg = round(float(get_field_value('n_words_gpt')) / (turns * 0.5))
                    words_text += f' (<em>user avg</em>: {user_avg}, <em>gpt avg</em>: {gpt_avg})'
            except:
                pass  # Skip averages if there's an error

        html_parts.append(f'<p><strong>n words:</strong> {words_text}</p>')

    # 11. Language
    language_exists, language_col = field_exists('language')
    if language_exists:
        html_parts.append(f'<p><strong>Language:</strong> {html.escape(str(get_field_value("language")))}</p>')

    # Close the metadata container
    html_parts.append('</div>')

    return '\n'.join(html_parts)


# --- Helper function for duration ---
def _format_duration(start_time: Optional[datetime], end_time: Optional[datetime]) -> str:
    """Formats the duration between two timestamps."""
    if not start_time or not end_time or end_time <= start_time:
        return ""

    duration = end_time - start_time
    seconds = duration.total_seconds()
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    duration_parts = []
    if days > 0:
        duration_parts.append(f"{int(days):02d}d")
    if hours > 0 or days > 0:
        duration_parts.append(f"{int(hours):02d}h")
    if minutes > 0 or hours > 0 or days > 0:
        duration_parts.append(f"{int(minutes):02d}m")
    duration_parts.append(f"{int(seconds):02d}s")

    return f' ({", ".join(duration_parts)})' # Added space before parenthesis


# Fix for the get_full_grid_row_html function in html_generator.py

def get_full_grid_row_html(
    turn: Dict[str, Any],
    turn_number: int,
    avatars: Dict[str, str],
    col_names: Dict[str, str],
    timestamp_to_display: Optional[datetime] = None,
    timestamp_for_duration_start: Optional[datetime] = None,
    show_duration: bool = False,
    include_annotations: bool = True
) -> str:
    """
    Generate HTML for a single conversation turn grid row.
    Applies Markdown formatting to assistant turns using a robust
    placeholder strategy (with non-Markdown characters) for code blocks.
    """
    # --- Get data for the current turn ---
    # Use .get with defaults for safety
    role_col = col_names.get('role', 'role')
    message_col = col_names.get('message', 'content')
    toxic_col = col_names.get('toxic', 'toxic')
    redacted_col = col_names.get('redacted', 'redacted')

    role = turn.get(role_col, '')
    raw_content = str(turn.get(message_col, '')) # Ensure it's a string
    is_toxic = turn.get(toxic_col, False)
    is_redacted = turn.get(redacted_col, False)
    has_code_block_flag = '```' in raw_content

    # --- Metadata Row Content Generation ---
    metadata_left_content = ""
    if role == 'user' and timestamp_to_display:
        timestamp_str = timestamp_to_display.strftime('%H:%M:%S')
        duration_str = ""
        if show_duration and timestamp_for_duration_start:
             duration_str = _format_duration(timestamp_for_duration_start, timestamp_to_display)
        metadata_left_content = f'{html.escape(timestamp_str)}{html.escape(duration_str)}'

    indicators = []
    if role == 'assistant' and has_code_block_flag:
        indicators.append('<span class="indicator indicator-code">Code Block</span>')
    if is_toxic:
        indicators.append('<span class="indicator indicator-toxic">Toxic</span>')
    if is_redacted:
        indicators.append('<span class="indicator indicator-pii">PII</span>')
    metadata_right_content = " | ".join(filter(None, indicators))

    # Always generate metadata row structure
    metadata_row_html = f'''
    <div class="turn-metadata-row">
        <div class="metadata-left">{metadata_left_content}</div>
        <div class="metadata-right">{metadata_right_content}</div>
    </div>
    '''

    # --- Content Formatting (Placeholder Strategy for Assistant) ---
    final_content = ""
    if role == 'assistant' and MARKDOWN_AVAILABLE:
        code_blocks = {}
        # === NEW PLACEHOLDER FORMAT ===
        placeholder_template = "@@CODEBLOCK_{}@@"
        # ============================

        def extract_code_block(match):
            block_index = len(code_blocks)
            placeholder = placeholder_template.format(block_index)
            code_blocks[placeholder] = match.group(1)
            return placeholder

        text_with_placeholders = re.sub(r"(?s)```(.*?)```", extract_code_block, raw_content)

        html_output = ""
        try:
             html_output = markdown.markdown(text_with_placeholders, extensions=['fenced_code', 'tables'])
        except Exception as md_error:
             print(f"Warning: Markdown processing failed for assistant turn {turn_number}: {md_error}. Falling back to basic escaping.")
             # Fallback logic (same as user turn logic below)
             escaped_full_content = html.escape(raw_content)
             processed_parts = []
             split_by_ticks = escaped_full_content.split('```')
             is_code_segment = False
             for i, segment in enumerate(split_by_ticks):
                 if is_code_segment:
                     clean_segment = segment.strip()
                     processed_parts.append(f'<pre><code>{clean_segment}</code></pre>')
                 else:
                     processed_parts.append(segment.replace('\n', '<br />'))
                 if i < len(split_by_ticks) - 1: is_code_segment = not is_code_segment
             html_output = "".join(processed_parts)

        # Reinsert the escaped code blocks using the NEW placeholder
        final_content = html_output
        if code_blocks:
             for placeholder, code_content in code_blocks.items():
                  formatted_code_block = f'<pre><code>{html.escape(code_content.strip())}</code></pre>'
                  # Check for raw placeholder OR placeholder possibly wrapped in <p> tags
                  placeholder_in_p = f"<p>{placeholder}</p>" # Check for markdown adding <p>

                  if placeholder_in_p in final_content:
                       final_content = final_content.replace(placeholder_in_p, formatted_code_block)
                  elif placeholder in final_content:
                       final_content = final_content.replace(placeholder, formatted_code_block)
                  else:
                       print(f"Warning: Placeholder '{placeholder}' not found in html_output for replacement.")

    else:
        # User turn or Markdown library not available: Use basic escaping
        escaped_full_content = html.escape(raw_content)
        processed_parts = []
        split_by_ticks = escaped_full_content.split('```')
        is_code_segment = False
        for i, segment in enumerate(split_by_ticks):
            if is_code_segment:
                clean_segment = segment.strip()
                processed_parts.append(f'<pre><code>{clean_segment}</code></pre>')
            else:
                processed_parts.append(segment.replace('\n', '<br />'))
            if i < len(split_by_ticks) - 1:
                is_code_segment = not is_code_segment
        final_content = "".join(processed_parts)

    # --- Avatar Source ---
    # Use .get for safer dictionary access
    avatar_src = avatars.get(role, avatars.get('fallback_user')) # Use fallback if role unknown

    # --- Generate HTML Structure ---
    turn_content_html = f'''
        <div class="turn {role}">
            <div class="turn-prefix">
                 <div class="turn-number">{turn_number}</div>
                 <div class="avatar"><img src="{avatar_src}" alt="{role} avatar"></div>
            </div>
            <div class="turn-main-content">
                 {metadata_row_html}
                 <div class="message-bubble"><div class="message">{final_content}</div></div>
            </div>
        </div>
    '''

    # --- Annotation Column / Final HTML structure ---
    if include_annotations:
        return f'''
            <div class="grid-col-message">
                {turn_content_html}
            </div>
            <div class="grid-col-resizer"></div>
            <div class="grid-col-annotation">
                <div class="annotation-container">
                    <button class="add-annotation-btn" title="Add annotation">+</button>
                </div>
            </div>
            '''
    else:
        # Return only the message column content if annotations are off
        return f'<div class="grid-col-message">{turn_content_html}</div>'


def generate_full_html(
        metadata_html: str,
        chat_rows_html: str,
        theme: str = 'light',
        custom_css_content: Optional[str] = None,
        include_js: bool = True,
        include_annotations: bool = True
) -> str:
    """
    Generate the complete HTML document.
    """
    # Load theme CSS or custom CSS
    css_content = custom_css_content if custom_css_content else load_css(theme)

    # Load JavaScript if needed
    js_content = load_js() if include_js else ""

    # --- CSS for conversation metadata section ---
    # These styles apply only to the top-level metadata section
    conv_metadata_css = """
    /* Styling for top-level conversation metadata box */
    .metadata {
        padding: 15px; margin-bottom: 0; border-radius: 8px;
        font-family: sans-serif; /* Ensure consistent font */
        /* Background/border handled by theme CSS */
    }
    .metadata h2 { font-size: 1.5em; margin-bottom: 15px; font-weight: bold; }
    .metadata p { margin: 8px 0; line-height: 1.4; display: block; }
    .metadata hr.metadata-divider {
        border: 0; height: 1px; margin: 15px 0; display: block; width: 100%;
        /* Color handled by theme CSS */
    }
    .metadata em { font-style: italic; opacity: 0.85; }
    .metadata a { text-decoration: none; /* Color handled by theme CSS */ }
    .metadata a:hover { text-decoration: underline; }
    """

    # --- Additional CSS specific to layout modes ---
    layout_specific_css = ""
    if not include_annotations:
        # Styles for base_html mode (non-grid layout)
        layout_specific_css = """
        /* Override grid layout for base_html mode */
        .conversation-section { display: block !important; border: none !important; margin-top: 0 !important; }
        .grid-col-message { padding-left: 0 !important; padding-right: 0 !important; }
        /* Ensure turns have adequate spacing in block layout */
        .turn { margin-bottom: 15px !important; }
        """
    else:
        # Styles needed for the annotation grid layout
        layout_specific_css = """
         /* Styles specific to when annotation grid is enabled */
         .conversation-section {
             display: grid;
             grid-template-columns: 1fr 5px 400px;
             gap: 0 10px;
             border: 1px solid var(--border-color);
             border-radius: 8px;
             position: relative;
             overflow: visible;
             padding: 10px;
             margin-bottom: 0;
         }

         .chat-section {
             border-top: none;
             border-top-left-radius: 0;
             border-top-right-radius: 0;
         }

         .info-section {
             margin-bottom: 0;
         }

         /* Indentation and alignment */
         .metadata-wrapper {
             display: flex;
             padding-left: 60px; /* Match chat bubble indentation (avatar + turn number + gap) */
         }

         /* Editable general observations */
         .editable-observations {
             height: 100%;
             width: 100%;
             border: 1px solid var(--border-color);
             border-radius: 8px;
             padding: 15px;
             background-color: var(--background-color);
             outline: none;
             min-height: 3.5em;  /* Default height matching a one-line message */
         }

         .editable-observations:empty:before {
             content: 'Click to add general observations...';
             color: var(--placeholder-color);
             font-style: italic;
         }

         .editable-observations:focus {
             border-color: var(--focus-border-color);
             box-shadow: 0 0 0 2px var(--focus-shadow-color);
         }

         /* Ensure consistent padding */
         .grid-col-message {
             padding-right: 15px; /* Fixed distance to slider */
         }

         .grid-col-annotation {
             padding-left: 15px; /* Fixed distance from slider */
         }

         /* Ensure proper vertical spacing */
         .metadata, .general-annotation {
             margin-bottom: 0;
         }
         """

    # Combine main theme CSS with specific overrides/additions
    combined_css = f"""
    {css_content} 
    {conv_metadata_css}
    {layout_specific_css}
    """

    # Create the general annotation box HTML with editable content
    general_annotation_html = ""
    if include_annotations:
        general_annotation_html = """
        <div class="general-annotation">
            <div class="section-header">General Observations</div>
            <div class="editable-observations" id="general-observations" contenteditable="true"></div>
        </div>
        """

    # Determine body class based on theme and annotation mode
    body_class = f"{theme}-theme"
    if include_annotations:
        body_class += " annotation-active"

    # Create HTML structure with two separate but aligned sections
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conversation Visualization</title>
    <style>
    {combined_css}
    </style>
</head>
<body class="{body_class}">
    <div class="{'conversation-section info-section' if include_annotations else 'conversation-block'}">
        <div class="grid-col-message">
            <div class="metadata-wrapper">
                {metadata_html}
            </div>
        </div>

        {f'<div class="grid-col-resizer"></div>' if include_annotations else ''}

        {f'<div class="grid-col-annotation">{general_annotation_html}</div>' if include_annotations else ''}
    </div>

    <div class="{'conversation-section chat-section' if include_annotations else 'conversation-block'}">
        {chat_rows_html}
    </div>

    {f'<div id="dragHandle" class="resizer-handle"></div>' if include_annotations else ''}

    {f'<script>{js_content}</script>' if include_js and include_annotations else ''}
</body>
</html>'''

    return full_html
