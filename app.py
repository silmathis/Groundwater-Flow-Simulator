"""Root entry point so `streamlit run app.py` works from workspace root."""

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent / "my_project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from my_project.frontend.streamlit_app import main


if __name__ == "__main__":
    main()
