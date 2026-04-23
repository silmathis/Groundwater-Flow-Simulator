"""Streamlit frontend for the groundwater simulator."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from my_project.backend import run_simulation
from my_project.groundwater_model import GroundwaterModel


def main() -> None:
    st.set_page_config(
        page_title="Groundwater Flow Simulator",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Interactive Groundwater Flow Simulator")
    st.markdown(
        """
**Educational Tool Only**  
This is a simplified, conceptual model designed for learning and exploration.
It is **not** suitable for engineering predictions or real-world applications.
"""
    )

    if "model" not in st.session_state:
        st.session_state.model = GroundwaterModel(nx=60, ny=40)
        st.session_state.solved = False
        st.session_state.previous_result = None
        st.session_state.current_result = None

    model = st.session_state.model

    st.sidebar.header("Model Parameters")

    st.sidebar.subheader("Domain Size")
    nx = st.sidebar.slider("Grid width (cells)", min_value=20, max_value=100, value=model.nx)
    ny = st.sidebar.slider("Grid height (cells)", min_value=15, max_value=80, value=model.ny)

    if nx != model.nx or ny != model.ny:
        st.session_state.model = GroundwaterModel(nx=nx, ny=ny)
        st.session_state.solved = False
        model = st.session_state.model
        st.rerun()

    st.sidebar.subheader("Boundary Conditions (Head in meters)")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        head_north = st.slider("North (top)", 0.0, 30.0, 15.0, step=0.5)
        head_south = st.slider("South (bottom)", 0.0, 30.0, 5.0, step=0.5)
    with col2:
        head_west = st.slider("West (left)", 0.0, 30.0, 10.0, step=0.5)
        head_east = st.slider("East (right)", 0.0, 30.0, 10.0, step=0.5)

    st.sidebar.subheader("Subsurface Zones")
    zone_type = st.sidebar.radio(
        "Add/modify zone:",
        ["High conductivity (sand)", "Low conductivity (clay)", "Medium (silt)"],
    )

    zone_conductivities = {
        "High conductivity (sand)": 5.0,
        "Low conductivity (clay)": 0.1,
        "Medium (silt)": 1.0,
    }
    selected_k = zone_conductivities[zone_type]

    background_k = st.sidebar.slider(
        "Background conductivity K (m/day)",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1,
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        zone_x_min = st.number_input("X start", 0, nx - 1, value=int(nx * 0.2))
        zone_y_min = st.number_input("Y start", 0, ny - 1, value=int(ny * 0.3))
    with col2:
        zone_x_max = st.number_input("X end", 1, nx, value=int(nx * 0.8))
        zone_y_max = st.number_input("Y end", 1, ny, value=int(ny * 0.7))

    st.sidebar.subheader("Recharge (Infiltration)")
    recharge_rate = st.sidebar.slider("Recharge rate (m/day)", 0.0, 0.05, 0.01, step=0.001)
    recharge_x_min = st.sidebar.number_input("R: X start", 0, nx - 1, value=int(nx * 0.3), key="rechg_x_min")
    recharge_x_max = st.sidebar.number_input("R: X end", 1, nx, value=int(nx * 0.7), key="rechg_x_max")
    recharge_y_min = st.sidebar.number_input("R: Y start", 0, ny - 1, value=int(ny * 0.1), key="rechg_y_min")
    recharge_y_max = st.sidebar.number_input("R: Y end", 1, ny, value=int(ny * 0.3), key="rechg_y_max")

    if st.sidebar.button("Reset Model", type="secondary"):
        st.session_state.model = GroundwaterModel(nx=nx, ny=ny)
        st.session_state.solved = False
        st.rerun()

    st.sidebar.subheader("Solver")
    iterations = st.sidebar.slider("Max iterations", 10, 500, 100)
    tolerance = st.sidebar.selectbox(
        "Convergence tolerance",
        [1e-2, 1e-3, 1e-4, 1e-5],
        format_func=lambda x: f"{x:.0e}",
    )

    current_controls = (
        nx,
        ny,
        head_north,
        head_south,
        head_west,
        head_east,
        zone_type,
        zone_x_min,
        zone_x_max,
        zone_y_min,
        zone_y_max,
        background_k,
        selected_k,
        recharge_rate,
        recharge_x_min,
        recharge_x_max,
        recharge_y_min,
        recharge_y_max,
        iterations,
        tolerance,
    )

    if st.session_state.get("last_controls") != current_controls:
        st.session_state.solved = False
        st.session_state.last_controls = current_controls

    col_main, col_info = st.columns([3, 1])

    if st.button("Solve Model", use_container_width=True, type="primary"):
        with st.spinner("Solving..."):
            config = {
                "nx": nx,
                "ny": ny,
                "head_north": head_north,
                "head_south": head_south,
                "head_west": head_west,
                "head_east": head_east,
                "background_k": background_k,
                "zone_x_min": zone_x_min,
                "zone_x_max": zone_x_max,
                "zone_y_min": zone_y_min,
                "zone_y_max": zone_y_max,
                "selected_k": selected_k,
                "recharge_rate": recharge_rate,
                "recharge_x_min": recharge_x_min,
                "recharge_x_max": recharge_x_max,
                "recharge_y_min": recharge_y_min,
                "recharge_y_max": recharge_y_max,
                "iterations": iterations,
                "tolerance": tolerance,
            }
            st.session_state.previous_result = st.session_state.current_result
            result = run_simulation(config)
            st.session_state.current_result = result
            st.session_state.model = result["model"]
            st.session_state.solved = True
        st.success("Model solved!")

    if st.session_state.solved and st.session_state.current_result is not None:
        model = st.session_state.current_result["model"]
        qx = st.session_state.current_result["qx"]
        qy = st.session_state.current_result["qy"]
        q_mag = st.session_state.current_result["q_mag"]
        summary = st.session_state.current_result["summary"]
        previous_result = st.session_state.get("previous_result")
        has_previous = previous_result is not None and previous_result["model"].head.shape == model.head.shape

        with col_info:
            st.subheader("Results")
            st.metric("Head (min)", f"{summary['head_min']:.2f} m")
            st.metric("Head (max)", f"{summary['head_max']:.2f} m")
            st.metric("Flow (max)", f"{summary['flow_max']:.3f} m/day")

        tabs = st.tabs([
            "Hydraulic Head",
            "Conductivity",
            "Flow Magnitude",
            "Flow Vectors",
            "Change vs Previous Solve",
        ])

        with tabs[0]:
            fig_head = go.Figure(
                data=go.Contour(
                    z=model.head,
                    colorscale="Viridis",
                    colorbar=dict(title="Head (m)"),
                    contours=dict(coloring="heatmap"),
                )
            )
            fig_head.update_layout(title="Hydraulic Head Distribution", xaxis_title="X (cells)", yaxis_title="Y (cells)", height=500)
            st.plotly_chart(fig_head, use_container_width=True)

        with tabs[1]:
            fig_cond = go.Figure(
                data=go.Heatmap(
                    z=np.log10(model.hydraulic_conductivity),
                    colorscale="RdYlBu_r",
                    colorbar=dict(title="log10(K)"),
                )
            )
            fig_cond.update_layout(title="Hydraulic Conductivity (log scale)", xaxis_title="X (cells)", yaxis_title="Y (cells)", height=500)
            st.plotly_chart(fig_cond, use_container_width=True)

        with tabs[2]:
            fig_mag = go.Figure(
                data=go.Contour(
                    z=q_mag,
                    colorscale="Plasma",
                    colorbar=dict(title="Flow (m/day)"),
                    contours=dict(coloring="heatmap"),
                )
            )
            fig_mag.update_layout(title="Groundwater Flow Magnitude", xaxis_title="X (cells)", yaxis_title="Y (cells)", height=500)
            st.plotly_chart(fig_mag, use_container_width=True)

        with tabs[3]:
            fig_vec = go.Figure(data=go.Heatmap(z=q_mag, colorscale="Blues", colorbar=dict(title="Flow (m/day)")))
            step = max(1, max(model.nx, model.ny) // 12)
            for i in range(0, model.ny, step):
                for j in range(0, model.nx, step):
                    if q_mag[i, j] > 1e-6:
                        scale_factor = 3.0
                        fig_vec.add_annotation(
                            x=j,
                            y=i,
                            ax=j - qx[i, j] * scale_factor,
                            ay=i - qy[i, j] * scale_factor,
                            arrowhead=2,
                            arrowsize=1.5,
                            arrowwidth=2,
                            arrowcolor="darkred",
                            xref="x",
                            yref="y",
                            axref="x",
                            ayref="y",
                            showarrow=True,
                        )
            fig_vec.update_layout(title="Flow Direction and Magnitude", xaxis_title="X (cells)", yaxis_title="Y (cells)", height=500)
            st.plotly_chart(fig_vec, use_container_width=True)

        with tabs[4]:
            if has_previous:
                prev_model = previous_result["model"]
                prev_q_mag = previous_result["q_mag"]
                head_delta = model.head - prev_model.head
                flow_delta = q_mag - prev_q_mag

                st.metric("max |Delta head|", f"{np.max(np.abs(head_delta)):.3f} m")
                st.metric("max |Delta flow|", f"{np.max(np.abs(flow_delta)):.3f} m/day")

                fig_head_delta = go.Figure(data=go.Heatmap(z=head_delta, colorscale="RdBu", zmid=0.0, colorbar=dict(title="Delta head (m)")))
                fig_head_delta.update_layout(title="Head Change Since Previous Solve", xaxis_title="X (cells)", yaxis_title="Y (cells)", height=450)
                st.plotly_chart(fig_head_delta, use_container_width=True)

                fig_flow_delta = go.Figure(data=go.Heatmap(z=flow_delta, colorscale="RdBu", zmid=0.0, colorbar=dict(title="Delta flow (m/day)")))
                fig_flow_delta.update_layout(title="Flow Change Since Previous Solve", xaxis_title="X (cells)", yaxis_title="Y (cells)", height=450)
                st.plotly_chart(fig_flow_delta, use_container_width=True)
            else:
                st.info("Solve at least twice with different inputs to see change maps.")


if __name__ == "__main__":
    main()
