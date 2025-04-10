#chatlab/__init__.py
"""ChatDataLab - blablabla"""

__version__ = "0.1.4"

from .concat_files import concat_files, hello

try:
    from .unpack_turns import unpack_turns
except Exception as e:
    print(f"Error importing unpack_turns: {e}")

try:
    from .filter_subset import filter_subset
except Exception as e:
    print(f"Error importing filter_subset: {e}")

try:
    from .text_search import search_text_matches
except Exception as e:
    print(f"Error importing text_search: {e}")


from .visualization import visualize_conversation

# Alternative approach for main chatlab/__init__.py
from .sample_data import load_sample_data as sample_data