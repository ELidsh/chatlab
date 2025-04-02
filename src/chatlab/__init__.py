"""ChatDataLab - blablabla"""

__version__ = "0.1.0"

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
