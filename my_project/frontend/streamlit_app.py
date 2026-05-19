"""Streamlit frontend for the groundwater simulator."""

import time
import json
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st

from my_project.backend.simulation_service import run_simulation
from my_project.groundwater_model import GroundwaterModel


def add_compass_and_invert_yaxis(fig, x_max, y_max, pad):
    """
    Add compass directions (N, S, O, W) and invert y-axis for proper geographic orientation.
    North should be at the top, South at the bottom.
    """
    # Enforce equal scaling for x/y so physical distances are shown
    # with correct aspect ratio. Do NOT reverse the axis here — the
    # model uses row 0 = bottom and row -1 = top, and plotting should
    # reflect that directly.
    fig.update_yaxes(scaleanchor="x", scaleratio=1)

    # Add compass annotations
    compass_props = dict(showarrow=False, font=dict(size=14, color="black"), 
                         bgcolor="rgba(255,255,255,0.7)", borderpad=4)

    # North (top middle)
    fig.add_annotation(x=x_max / 2, y=y_max + pad, text="<b>N</b>", xanchor="center", **compass_props)

    # South (bottom middle)
    fig.add_annotation(x=x_max / 2, y=-pad, text="<b>S</b>", xanchor="center", **compass_props)

    # East (right middle)
    fig.add_annotation(x=x_max + pad, y=y_max / 2, text="<b>E</b>", yanchor="middle", **compass_props)

    # West (left middle)
    fig.add_annotation(x=-pad, y=y_max / 2, text="<b>W</b>", yanchor="middle", **compass_props)
    
    return fig


def enforce_equal_xy_aspect(fig):
    """Ensure 1:1 aspect ratio between x and y axes (equal units per pixel).

    Use this when x and y are in the same physical units so the plot is
    geometrically correct (e.g., a 50x50 grid appears square).
    """
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig


def style_axes(fig, x_max, y_max, cell_size, nticks=6):
    """Style axes for consistent background labels and gridlines.

    - Fix axis ranges to data extents
    - Place a small number of ticks (nticks) evenly
    - Style grid and tick font for dark backgrounds
    """
    # Compute evenly spaced tick positions
    x_tickvals = list(np.linspace(0, x_max, nticks))
    y_tickvals = list(np.linspace(0, y_max, nticks))

    grid_color = "rgba(255,255,255,0.06)"  # subtle grid on dark bg
    tick_font = dict(size=11, color="#dcdcdc")

    fig.update_xaxes(range=[0, x_max], tickmode="array", tickvals=x_tickvals,
                     showgrid=True, gridcolor=grid_color, tickfont=tick_font)
    fig.update_yaxes(range=[0, y_max], tickmode="array", tickvals=y_tickvals,
                     showgrid=True, gridcolor=grid_color, tickfont=tick_font)
    return fig


def main() -> None:
    st.set_page_config(
        page_title="Groundwater Flow Simulator",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                min-width: 380px;
                max-width: 380px;
                width: 380px;
            }

            section[data-testid="stSidebar"][aria-expanded="false"] {
                min-width: 0 !important;
                max-width: 0 !important;
                width: 0 !important;
                overflow: hidden !important;
            }

            div[data-testid="stSidebarResizer"] {
                display: none;
            }

            section[data-testid="stSidebar"][aria-expanded="false"] ~ div main {
                max-width: 100% !important;
                width: 100% !important;
            }

            button[data-testid="collapsedControl"] {
                position: fixed !important;
                left: 0.25rem !important;
                top: 0.75rem !important;
                right: auto !important;
                z-index: 1000 !important;
            }

            div[data-testid="stMainBlockContainer"] {
                max-width: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
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
        st.session_state.model = GroundwaterModel(nx=50, ny=50)
        st.session_state.solved = False
        st.session_state.previous_result = None
        st.session_state.current_result = None

    model = st.session_state.model
    cell_size = model.cell_size
    x_coords = np.arange(model.nx) * cell_size
    y_coords = np.arange(model.ny) * cell_size
    x_max = x_coords[-1]
    y_max = y_coords[-1]

    st.sidebar.header("Model Parameters")

    with st.sidebar.expander("Domain Size", expanded=False):
        st.caption("Sets the simulation grid’s overall size and resolution. Larger grids reveal finer details but require more computation time.")
        nx = st.slider("Grid width (cells)", min_value=20, max_value=100, value=model.nx)
        ny = st.slider("Grid height (cells)", min_value=20, max_value=100, value=model.ny)

    if nx != model.nx or ny != model.ny:
        for idx in range(1, 7):
            x_key = f"ps{idx}_x"
            y_key = f"ps{idx}_y"
            if x_key in st.session_state:
                st.session_state[x_key] = min(max(int(st.session_state[x_key]), 0), nx)
            if y_key in st.session_state:
                st.session_state[y_key] = min(max(int(st.session_state[y_key]), 0), ny)
        st.session_state.model = GroundwaterModel(nx=nx, ny=ny)
        st.session_state.solved = False
        model = st.session_state.model
        st.rerun()

    with st.sidebar.expander("Hydraulic Head", expanded=False):
        st.caption("Set the hydraulic head values. Point sources inject or extract water at specified locations, while boundary conditions can be applied at the edges of the domain to force inflow or outflow.")
        with st.expander("Point Sources", expanded=False):
            st.caption("Coordinates of the point sources cannot be at the boundaries of the grid.")
            point_source_count = st.slider("Number of point sources", 0, 6, 0)
            point_sources = []
            for idx in range(1, point_source_count + 1):
                default_x = int(round((idx / (point_source_count + 1)) * nx))
                default_y = int(ny * 0.5)
                default_h = 20.0 if idx % 2 else 5.0
                with st.expander(f"Point {idx}", expanded=False):
                    x_val = st.number_input(f"P{idx}: X coord", min_value=0, value=default_x, step=1, key=f"ps{idx}_x")
                    y_val = st.number_input(f"P{idx}: Y coord", min_value=0, value=default_y, step=1, key=f"ps{idx}_y")
                    h_val = st.slider(f"P{idx}: Head (m)", 0.0, 30.0, default_h, step=0.5, key=f"ps{idx}_h")

                x_coord = int(x_val)
                y_coord = int(y_val)
                if x_coord > nx:
                    st.warning(f"Point {idx}: X coordinate exceeds grid width ({nx}). It will be clipped to {nx}.")
                    x_coord = nx
                if y_coord > ny:
                    st.warning(f"Point {idx}: Y coordinate exceeds grid height ({ny}). It will be clipped to {ny}.")
                    y_coord = ny

                # Map UI coordinates [0..nx] / [0..ny] to model cell indices [0..nx-1] / [0..ny-1].
                point_sources.append({"x": min(x_coord, nx - 1), "y": min(y_coord, ny - 1), "h": float(h_val)})

        with st.expander("Boundary Conditions (corners only)", expanded=False):
            st.caption("Define hydraulic head only at the four domain corners. Edges are interpolated linearly from corner values.")

            col1, col2 = st.columns(2)
            with col1:
                corner_tl = st.number_input("Top-left head (m)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
                corner_bl = st.number_input("Bottom-left head (m)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            with col2:
                corner_tr = st.number_input("Top-right head (m)", min_value=0.0, max_value=100.0, value=10.0, step=0.1)
                corner_br = st.number_input("Bottom-right head (m)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

    with st.sidebar.expander("Conductivity", expanded=False):
        st.caption("Define the conductivity distribution across the domain.")
        conductivity_mode = st.radio(
            "Medium type",
            ["Homogeneous medium", "Heterogeneous medium with zone"],
        )

        # Predefined sediment conductivities
        sediment_options = {
            "High conductivity (sand = 10.0 m/day)": 10.0,  # m/day
            "Medium (silt = 0.1 m/day)": 0.1,  # m/day
            "Low conductivity (clay = 0.01 m/day)": 0.01,  # m/day
        }

        # Background conductivity selection (sediment types or custom)
        st.markdown("**Background conductivity**")
        bg_choice = st.radio(
            "Background type",
            [
                "High conductivity (sand = 10.0 m/day)",
                "Medium (silt = 0.1 m/day)",
                "Low conductivity (clay = 0.01 m/day)",
                "Custom",
            ],
            index=1,
        )
        if bg_choice == "Custom":
            background_k = st.slider(
                "Background conductivity K (m/day)", min_value=0.01, max_value=10.0, value=1.0, step=0.01
            )
        else:
            background_k = sediment_options[bg_choice]

        # Color mapping for sediments (used in previews)
        bg_color_map = {
            "High conductivity (sand = 10.0 m/day)": "#fff7b2",  # pale yellow
            "Medium (silt = 0.1 m/day)": "#dcdcdc",  # light gray
            "Low conductivity (clay = 0.01 m/day)": "#4a4a4a",  # dark gray
            "Custom": "#ffffff",  # white
        }
        bg_color = bg_color_map.get(bg_choice, "#ffffff")

        # Prepare defaults for zone
        zone_type = None
        selected_k = None
        zone_x_min = zone_x_max = zone_y_min = zone_y_max = 0

        if conductivity_mode == "Homogeneous medium":
            aspect_ratio = ny / nx
            preview_width = 350
            preview_height = 1200

            bg_grid = np.zeros((ny, nx))
            fig_bg = go.Figure(
                data=go.Heatmap(
                    z=bg_grid,
                    x=np.arange(nx) * cell_size,
                    y=np.arange(ny) * cell_size,
                    colorscale=[[0, bg_color], [1, bg_color]],
                    showscale=False,
                    hovertemplate="Background: x=%{x:.1f} m<br>y=%{y:.1f} m<extra></extra>",
                )
            )
            fig_bg.update_layout(
                title="Background Preview",
                xaxis_title="X (m)",
                yaxis_title="Y (m)",
                height=preview_height,
                margin=dict(l=30, r=30, t=30, b=30),
            )
            st.plotly_chart(fig_bg, use_container_width=True)

        if conductivity_mode == "Heterogeneous medium with zone":
            st.markdown("**Subsurface Zone**")
            st.markdown("Choose sediment type for the zone or set custom K")
            zone_choice = st.radio(
                "Zone type",
                [
                    "High conductivity (sand = 10.0 m/day)",
                    "Medium (silt = 0.1 m/day)",
                    "Low conductivity (clay = 0.01 m/day)",
                    "Custom",
                ],
                index=0,
            )

            if zone_choice == "Custom":
                selected_k = st.slider(
                    "Zone conductivity K (m/day)", min_value=0.1, max_value=5.0, value=2.0, step=0.1
                )
                zone_type = "Custom"
            else:
                selected_k = sediment_options[zone_choice]
                zone_type = zone_choice

            # Position inputs for the zone (same layout as before)
            col1, col2 = st.columns(2)
            with col1:
                zone_x_min = st.number_input("X start", 0, nx, value=int(nx * 0.2))
                zone_y_min = st.number_input("Y start", 0, ny - 1, value=int(ny * 0.3))
            with col2:
                zone_x_max = st.number_input("X end", 1, nx, value=int(nx * 0.8))
                zone_y_max = st.number_input("Y end", 1, ny, value=int(ny * 0.7))

            # Combined preview (background + zone) with correct aspect ratio
            combined_grid = np.zeros((ny, nx))
            combined_grid[zone_y_min:zone_y_max, zone_x_min:zone_x_max] = 1
            aspect_ratio = ny / nx
            preview_width = 350  # Sidebar width
            preview_height = 1200

            zone_color_map = {
                "High conductivity (sand = 10.0 m/day)": "#fff7b2",
                "Medium (silt = 0.1 m/day)": "#dcdcdc",
                "Low conductivity (clay = 0.01 m/day)": "#4a4a4a",
                "Custom": "#ffffff",
            }
            zone_color = zone_color_map.get(zone_type, "#ffffff")

            fig_zone = go.Figure(
                data=go.Heatmap(
                    z=combined_grid,
                    x=np.arange(nx) * cell_size,
                    y=np.arange(ny) * cell_size,
                    colorscale=[[0, bg_color], [1, zone_color]],
                    showscale=False,
                    hovertemplate="X: %{x:.1f} m<br>Y: %{y:.1f} m<br>Zone: %{z}<extra></extra>",
                )
            )
            fig_zone.update_layout(
                title="Domain Preview (background + zone)",
                xaxis_title="X (m)",
                yaxis_title="Y (m)",
                height=preview_height,
                margin=dict(l=30, r=30, t=40, b=30),
            )
            st.plotly_chart(fig_zone, use_container_width=True)

    with st.sidebar.expander("Recharge (Infiltration)", expanded=False):
        st.caption("Define a rectangular recharge zone with a specified rate. The x- and y-values set the coordinates of this zone.")
        aquifer_thickness = st.slider(
            "Aquifer thickness b (m)",
            min_value=1.0,
            max_value=100.0,
            value=float(getattr(model, "aquifer_thickness", 10.0)),
            step=1.0,
        )
        recharge_rate_mm = st.slider("Recharge rate (mm/day)", 0.0, 20.0, 0.0, step=1.0)
        # Convert mm/day to m/day
        recharge_rate = recharge_rate_mm / 1000.0

        col1, col2 = st.columns(2)
        with col1:
            recharge_x_min = st.number_input("X start", 0, nx - 1, value=int(nx * 0.3), key="rechg_x_min")
            recharge_y_min = st.number_input("Y start", 0, ny - 1, value=int(ny * 0.1), key="rechg_y_min")
        with col2:
            recharge_x_max = st.number_input("X end", 1, nx, value=int(nx * 0.7), key="rechg_x_max")
            recharge_y_max = st.number_input("Y end", 1, ny, value=int(ny * 0.3), key="rechg_y_max")
        
        # Recharge zone preview visualization with correct aspect ratio
        recharge_grid = np.zeros((ny, nx))
        recharge_grid[recharge_y_min:recharge_y_max, recharge_x_min:recharge_x_max] = recharge_rate
        aspect_ratio = ny / nx
        preview_width = 350  # Sidebar width
        preview_height = 1200
        
        fig_recharge = go.Figure(
            data=go.Heatmap(
                z=recharge_grid,
                x=np.arange(nx) * cell_size,
                y=np.arange(ny) * cell_size,
                colorscale="Blues",
                showscale=False,
                hovertemplate="X: %{x:.1f} m<br>Y: %{y:.1f} m<br>Rate: %{z:.4f} m/day<extra></extra>",
            )
        )
        fig_recharge.update_layout(
            title="Recharge Zone Preview",
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            height=preview_height,
            margin=dict(l=30, r=30, t=40, b=30),
        )
        st.plotly_chart(fig_recharge, use_container_width=True)

    if st.sidebar.button("Reset Model", type="secondary"):
        st.session_state.model = GroundwaterModel(nx=nx, ny=ny)
        st.session_state.solved = False
        st.rerun()

    with st.sidebar.expander("Solver", expanded=False):
        iterations = st.slider("Max iterations", 10, 5000, 2500, key="solver_iterations")
        tolerance = st.selectbox(
            "Convergence tolerance",
            [1e-2, 1e-3, 1e-4, 1e-5, 1e-6],
            index =3, 
            format_func=lambda x: f"{x:.0e}",
            key="solver_tolerance"
        )

    current_controls = (
        nx,
        ny,
        point_source_count,
        tuple((p["x"], p["y"], p["h"]) for p in point_sources),
        # corners
        float(corner_tl),
        float(corner_tr),
        float(corner_bl),
        float(corner_br),
        conductivity_mode,
        zone_type,
        zone_x_min,
        zone_x_max,
        zone_y_min,
        zone_y_max,
        background_k,
        selected_k,
        aquifer_thickness,
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

    if st.button("Solve Model", width="stretch", type="primary"):
        with st.spinner("Solving..."):
            config = {
                "nx": nx,
                "ny": ny,
                "point_sources": point_sources,
                # corner-only boundary condition values
                "corner_tl": float(corner_tl),
                "corner_tr": float(corner_tr),
                "corner_bl": float(corner_bl),
                "corner_br": float(corner_br),
                "background_k": background_k,
                "conductivity_mode": conductivity_mode,
                "zone_x_min": zone_x_min,
                "zone_x_max": zone_x_max,
                "zone_y_min": zone_y_min,
                "zone_y_max": zone_y_max,
                "selected_k": selected_k,
                "aquifer_thickness": aquifer_thickness,
                "recharge_rate": recharge_rate,
                "recharge_x_min": recharge_x_min,
                "recharge_x_max": recharge_x_max,
                "recharge_y_min": recharge_y_min,
                "recharge_y_max": recharge_y_max,
                "iterations": iterations,
                "tolerance": tolerance,
            }
            st.session_state.previous_result = st.session_state.current_result
            # Timing: measure solver wall time
            t_solve_start = time.perf_counter()
            result = run_simulation(config)
            t_solve_end = time.perf_counter()
            solve_time = t_solve_end - t_solve_start

            # Store timing in session state for later reference
            st.session_state.last_timing = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "solve_time_s": round(solve_time, 3),
                "nx": nx,
                "ny": ny,
                "iterations": iterations,
                "num_point_sources": len(point_sources),
            }

            # Print timing to terminal
            print(f"[TIMING] {st.session_state.last_timing['timestamp']} - Solve time: {solve_time:.3f}s (nx={nx}, ny={ny}, iters={iterations})")

            # Append timing to log file
            try:
                with open("sim_timing.log", "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(st.session_state.last_timing) + "\n")
            except Exception:
                pass

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
        # Start plotting timer
        t_plot_start = time.perf_counter()

        with col_info:
            st.subheader("Results")
            st.metric("Head (min)", f"{summary['head_min']:.2f} m")
            st.metric("Head (max)", f"{summary['head_max']:.2f} m")
            st.metric("Max flow (m/day)", f"{summary['flow_max']:.3f}")

        tabs = st.tabs([
            "Hydraulic Head",
            "Conductivity",
            "Flow Magnitude",
            "Flow Vectors",
            "Recharge Map", 
        ])

        with tabs[0]:
            fig_head = go.Figure(
                data=go.Contour(
                    z=model.head,
                    x=x_coords,
                    y=y_coords,
                    colorscale="viridis",
                    colorbar=dict(title="Head (m)"),
                    contours=dict(coloring="heatmap"),
                )
            )
            fig_head.update_layout(title="Hydraulic Head Distribution", xaxis_title="X (m)", yaxis_title="Y (m)", height=1200)
            fig_head = style_axes(fig_head, x_max, y_max, cell_size)
            fig_head = add_compass_and_invert_yaxis(fig_head, x_max, y_max, cell_size)
            st.plotly_chart(fig_head, width="stretch")

        with tabs[1]:
            fig_cond = go.Figure(
                data=go.Heatmap(
                    z=np.log10(model.hydraulic_conductivity),
                    x=x_coords,
                    y=y_coords,
                    colorscale="RdYlBu_r",
                    colorbar=dict(title="log10(K)"),
                )
            )
            fig_cond.update_layout(title="Hydraulic Conductivity (log scale)", xaxis_title="X (m)", yaxis_title="Y (m)", height=1200)
            fig_cond = style_axes(fig_cond, x_max, y_max, cell_size)
            fig_cond = add_compass_and_invert_yaxis(fig_cond, x_max, y_max, cell_size)
            st.plotly_chart(fig_cond, width="stretch")

        with tabs[2]:
            fig_mag = go.Figure(
                data=go.Contour(
                    z=q_mag,
                    x=x_coords,
                    y=y_coords,
                    colorscale="Plasma",
                    colorbar=dict(title="Flow (m/day)"),
                    contours=dict(coloring="heatmap"),
                )
            )
            fig_mag.update_layout(title="Groundwater Flow Magnitude", xaxis_title="X (m)", yaxis_title="Y (m)", height=1200)
            fig_mag = style_axes(fig_mag, x_max, y_max, cell_size)
            fig_mag = add_compass_and_invert_yaxis(fig_mag, x_max, y_max, cell_size)
            st.plotly_chart(fig_mag, width="stretch")

        with tabs[3]:
            fig, ax = plt.subplots(figsize=(12, 12), constrained_layout=True)
            stream = ax.streamplot(
                x_coords,
                y_coords,
                qx,
                qy,
                color=q_mag,
                cmap="plasma",
                density=1.2,
                linewidth=1.2,
                arrowsize=1.5,
            )
            fig.colorbar(stream.lines, ax=ax, label="Flow (m/day)")
            ax.set_title("Flow Direction and Magnitude")
            ax.set_xlabel("X (m)")
            ax.set_ylabel("Y (m)")
            ax.set_xlim(0, x_max)
            ax.set_ylim(0, y_max)
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True, alpha=0.15)
            st.pyplot(fig, clear_figure=True)

        with tabs[4]:
            recharge_map = np.zeros_like(model.head)
            recharge_map[model.recharge > 0] = model.recharge[model.recharge > 0]
            fig_recharge = go.Figure(data=go.Heatmap(z=recharge_map, x=x_coords, y=y_coords, colorscale="YlGnBu", colorbar=dict(title="Recharge (m/day)")))
            fig_recharge.update_layout(title="Recharge Distribution", xaxis_title="X (m)", yaxis_title="Y (m)", height=1200)
            fig_recharge = style_axes(fig_recharge, x_max, y_max, cell_size)
            st.plotly_chart(fig_recharge, use_container_width=True)    
        # End plotting timer and print to terminal
        t_plot_end = time.perf_counter()
        plot_time = t_plot_end - t_plot_start
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[TIMING] {timestamp} - Plot time: {plot_time:.3f}s")
        try:
            # Append plot timing to same log file
            entry = {
                "timestamp": timestamp,
                "plot_time_s": round(plot_time, 3),
                "nx": model.nx,
                "ny": model.ny,
            }
            with open("sim_timing.log", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        except Exception:
            pass

if __name__ == "__main__":
    main()
