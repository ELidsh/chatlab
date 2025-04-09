# chatlab/visualization/resources.py
import base64
import sys
from pathlib import Path
import importlib.resources
from ..utils import get_package_root # Import from parent directory utility

# --- Default Assets ---
DEFAULT_USER_SVG_FALLBACK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="40" height="40"><circle cx="50" cy="50" r="45" fill="#4A90E2"/><text x="50" y="65" font-size="40" fill="#FFFFFF" text-anchor="middle">U</text></svg>"""
DEFAULT_ASSISTANT_SVG_FALLBACK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="40" height="40"><circle cx="50" cy="50" r="45" fill="#50E3C2"/><text x="50" y="65" font-size="40" fill="#000000" text-anchor="middle">A</text></svg>"""

PACKAGE_ROOT = get_package_root()
ASSETS_DIR = PACKAGE_ROOT / 'assets'
STATIC_DIR = ASSETS_DIR / 'static'
IMAGES_DIR = ASSETS_DIR / 'images'

def _load_file_content(file_path: Path, fallback_content: str = "", encoding='utf-8') -> str:
    """Loads text content from a file, using fallback if not found/error."""
    try:
        # More robust way using importlib.resources if files are package data
        # Assuming 'assets' is adjacent to the 'chatlab' package directory might be fragile.
        # It's better if assets are INSIDE the chatlab package or handled via setup.py data_files
        # For simplicity here, we use the path relative to package root found earlier.
        if file_path.exists():
             return file_path.read_text(encoding=encoding)
        else:
             print(f"Warning: File not found at '{file_path}'. Using fallback.", file=sys.stderr)
             return fallback_content
    except Exception as e:
        print(f"Warning: Error reading file '{file_path}': {e}. Using fallback.", file=sys.stderr)
        return fallback_content

def load_css(theme: str = 'light') -> str:
    """Loads the CSS content for the specified theme."""
    if theme == 'dark':
        return _load_file_content(STATIC_DIR / 'visualize_dark.css', '')
    else:
        if theme != 'light':
             print(f"Warning: Invalid theme '{theme}'. Using 'light'.", file=sys.stderr)
        return _load_file_content(STATIC_DIR / 'visualize_light.css', '')

def load_js() -> str:
    """Loads the JavaScript content."""
    return _load_file_content(STATIC_DIR / 'visualize.js', '')

def load_svg_content(filename: str, fallback_svg: str) -> str:
    """Loads SVG content from the images directory."""
    svg_path = IMAGES_DIR / filename
    # Use internal _load_file_content which handles fallback
    return _load_file_content(svg_path, fallback_svg)

def svg_to_base64(svg_content: str) -> str:
    """Convert SVG string to a base64 data URI."""
    try:
        encoded = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{encoded}"
    except Exception as e:
        print(f"Error encoding SVG to base64: {e}. Returning empty string.", file=sys.stderr)
        return "data:image/svg+xml;base64,"

def get_avatars(user_svg_override: str | None = None, assistant_svg_override: str | None = None) -> dict[str, str]:
    """Loads or uses override SVG, converts to base64."""
    if user_svg_override:
        user_svg = user_svg_override
    else:
        user_svg = load_svg_content('user_avatar.svg', DEFAULT_USER_SVG_FALLBACK)

    if assistant_svg_override:
        assistant_svg = assistant_svg_override
    else:
        assistant_svg = load_svg_content('gpt_avatar.svg', DEFAULT_ASSISTANT_SVG_FALLBACK)

    return {
        'user': svg_to_base64(user_svg),
        'assistant': svg_to_base64(assistant_svg),
        'fallback_user': svg_to_base64(DEFAULT_USER_SVG_FALLBACK),
        'fallback_assistant': svg_to_base64(DEFAULT_ASSISTANT_SVG_FALLBACK),
    }