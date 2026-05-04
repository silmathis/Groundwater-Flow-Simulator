"""Root entry point so `streamlit run app.py` works from workspace root."""
#funktioniert wenn man im Terminal `streamlit run app.py` eingibt, da es die Hauptdatei ist, die Streamlit ausführt. Es importiert die Hauptfunktion aus der Streamlit-App und führt sie aus. Man muss im Hauptordner sein um den command nutzen zu können.

from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parent / "my_project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from my_project.frontend.streamlit_app import main


if __name__ == "__main__":
    main()
