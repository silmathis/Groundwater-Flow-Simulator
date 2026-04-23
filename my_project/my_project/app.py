"""Legacy entry point that forwards to the separated frontend app."""

from my_project.frontend.streamlit_app import main


if __name__ == "__main__":
    main()

st.sidebar.markdown("---")
st.sidebar.info(
    "**Educational Groundwater Simulator**  \n"
    "Version 0.1.0  \n"
    "Built with Streamlit, NumPy, and SciPy"
)
