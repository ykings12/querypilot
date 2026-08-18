import sys
from pathlib import Path

_UI_DIR = Path(__file__).resolve().parent.parent
if str(_UI_DIR) not in sys.path:
    sys.path.insert(0, str(_UI_DIR))

from components.how_to_use import render_getting_started_page

st.set_page_config(page_title="How to use", page_icon="📖", layout="wide")
render_getting_started_page()
