"""Root entry point so `streamlit run app.py` works from workspace root."""
# Build 2026-05-05 — package-mode fix applied
# funktioniert wenn man im Terminal `streamlit run app.py` eingibt, da es die Hauptdatei ist, die Streamlit ausführt.
# Es importiert die Hauptfunktion aus der Streamlit-App und führt sie aus.

from Simulator.frontend.streamlit_app import main


if __name__ == "__main__":
    main()
