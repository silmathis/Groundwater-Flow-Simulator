"""Streamlit frontend for the groundwater simulator."""

import time
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st

from Simulator.backend.simulation_service import build_model_from_config, run_simulation
from Simulator.groundwater_model import GroundwaterModel


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


def create_head_figure(head, x_coords, y_coords, x_max, y_max, cell_size, title, zmax=None):
    """Build a consistent hydraulic head figure for previews and live updates.

    If `zmax` is not provided, compute zmin/zmax from the data with a small
    padding so the color scale adapts to transient peaks (e.g., recharge zones).
    """
    z = np.asarray(head)
    # Compute robust min/max and add 5% padding to improve readability.
    data_min = float(np.nanmin(z))
    data_max = float(np.nanmax(z))
    if zmax is None:
        span = max(1e-6, data_max - data_min)
        zmin = data_min - 0.05 * span
        zmax_auto = data_max + 0.05 * span
    else:
        # Keep a lower bound at zero unless data_min is negative.
        zmin = min(0.0, data_min)
        zmax_auto = max(float(zmax), data_max)

    fig = go.Figure(
        data=go.Contour(
            z=z,
            x=x_coords,
            y=y_coords,
            colorscale="viridis",
            zmin=zmin,
            zmax=zmax_auto,
            colorbar=dict(title="Head (m)"),
            contours=dict(coloring="heatmap"),
        )
    )
    fig.update_layout(title=title, xaxis_title="X (m)", yaxis_title="Y (m)", height=700)
    fig = style_axes(fig, x_max, y_max, cell_size)
    fig = add_compass_and_invert_yaxis(fig, x_max, y_max, cell_size)
    return fig


def render_plotly_component(fig, height=700):
    """Render a Plotly figure using Streamlit's native Plotly chart renderer.

    This keeps styling consistent with the other `st.plotly_chart` usages
    in the app and matches the design used in the lower tabs.
    """
    config = {"displayModeBar": False, "responsive": True}
    st.plotly_chart(fig, use_container_width=True, height=height, config=config)


# In this main function, we build the Streamlit UI which handles user input and displays results.
def main() -> None:
    # Defines the title, layout and sidebar state for the Streamlit app:
    st.set_page_config(
        page_title="Groundwater Simulator",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                min-width: 420px;
                max-width: 420px;
                width: 420px;
        

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

            button[data-testid="stMainMenuItem-theme-System"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Groundwater Simulator")
    # Adding a disclaimer that this is a simplified model for educational purposes:
    st.markdown(
        """
**Conceptual Tool Only!**  
Simulates groundwater flow on a rectangular grid.
Computes hydraulic head at each cell.
Point sources, boundaries, and recharge shape the head.
Solver updates heads iteratively until they converge.
Result is a steady-state head field.
Outputs: maps of head, flow magnitude, and flow vectors.

**IMPORTANT:** Do not confuse the iterations as time steps. This model computes a steady-state solution, not a transient evolution."""
    )

# Tests if model already exists in session state. 
# If not, a new model is initialized.
    if "model" not in st.session_state:
        st.session_state.model = GroundwaterModel(nx=50, ny=50)
        st.session_state.solved = False
        st.session_state.previous_result = None
        st.session_state.current_result = None

    model = st.session_state.model
    cell_size = model.cell_size
    # Use cell centers for display so the outer domain boundary reaches the full extent.
    x_coords = (np.arange(model.nx) + 0.5) * cell_size
    y_coords = (np.arange(model.ny) + 0.5) * cell_size
    x_max = model.nx * cell_size
    y_max = model.ny * cell_size

# Now, we build the sidebar UI for user input of the model parameters.
    st.sidebar.header("Model Parameters")

    # This section allows the user to set the domain size.
    # Grid width and height can be chosen, each between 20 and 100 cells.
    with st.sidebar.expander("Domain Size", expanded=False):
        st.caption("Sets the simulation grid’s overall size and resolution. Larger grids reveal finer details but require more computation time.")
        nx = st.slider("Grid width (cells)", min_value=20, max_value=100, value=model.nx)
        ny = st.slider("Grid height (cells)", min_value=20, max_value=100, value=model.ny)

    # The model restarts whenever the grid size changes.
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

    # Here, the user can set hydraulic head values through point sources and boundary conditions.
    with st.sidebar.expander("Hydraulic Head", expanded=False):
        st.caption("Set the hydraulic head values. Point sources inject or extract water at specified locations, while boundary conditions can be applied at the edges of the domain to force inflow or outflow.")
        
        # This is the Section for the point sources.
        # The user can add up to 6 point sources, each with its own location and head value.
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

        # This is the section for the boundary conditions at the corners of the domain.
        # The user can set the hydraulic head values at the four corners, and the model will interpolate linearly along the edges.
        with st.expander("Boundary Conditions (corners only)", expanded=False):
            st.caption("Define hydraulic head only at the four domain corners. Edges are interpolated linearly from corner values.")

            col1, col2 = st.columns(2)
            with col1:
                corner_tl = st.number_input("Top-left head (m)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
                corner_bl = st.number_input("Bottom-left head (m)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            with col2:
                corner_tr = st.number_input("Top-right head (m)", min_value=0.0, max_value=100.0, value=10.0, step=0.1)
                corner_br = st.number_input("Bottom-right head (m)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

    # In this section, the user can define the conductivity distribution across the domain.
    with st.sidebar.expander("Conductivity", expanded=False):
        st.caption("Define the conductivity distribution across the domain.")
        conductivity_mode = st.radio(
            "Medium type",
            ["Homogeneous medium", "Heterogeneous medium with zone"],
        )

        # These are the different predefined sediment conductivities.
        sediment_options = {
            "High conductivity (sand = 10.0 m/day)": 10.0,  # m/day
            "Medium (silt = 0.1 m/day)": 0.1,  # m/day
            "Low conductivity (clay = 0.01 m/day)": 0.01,  # m/day
        }

        # Here, the user can choose a custom background conductivity or select from the predefined sediment types.
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

        # This maps the colors for the preview based on the user's choices.
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

        # This is the preview for the homogeneous conductivity.
        if conductivity_mode == "Homogeneous medium":
            aspect_ratio = ny / nx
            preview_width = 100
            preview_height = 300

            bg_grid = np.zeros((ny, nx))
            fig_bg = go.Figure(
                data=go.Heatmap(
                    z=bg_grid,
                    x=x_coords,
                    y=y_coords,
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
            st.plotly_chart(fig_bg, use_container_width=True, config={"displayModeBar": False, "responsive": True})

        # This is the preview for the heterogeneous conductivity with a zone.
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
            preview_width = 100  # Sidebar width
            preview_height = 300

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
                    x=x_coords,
                    y=y_coords,
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
            st.plotly_chart(fig_zone, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    # This section allows the user to define a recharge zone where water infiltrates into the aquifer.
    with st.sidebar.expander("Recharge (Infiltration)", expanded=False):
        st.caption("Define a rectangular recharge zone with a specified rate. The x- and y-values set the coordinates of this zone. **Attention** if the conductivity is low and the recharge rate is high, the water can build up and cause very high head values.")
        # Add aquifer thickness which is needed for the calculations of the model.
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
        
        # This shows a preview of the recharge zone based on the user's input.
        recharge_grid = np.zeros((ny, nx))
        recharge_grid[recharge_y_min:recharge_y_max, recharge_x_min:recharge_x_max] = recharge_rate
        aspect_ratio = ny / nx
        preview_width = 100  # Sidebar width
        preview_height = 300
        
        fig_recharge = go.Figure(
            data=go.Heatmap(
                z=recharge_grid,
                x=x_coords,
                y=y_coords,
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
        st.plotly_chart(fig_recharge, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    # Finally, the user can set the solver parameters such as maximum iterations and convergence tolerance.
    with st.sidebar.expander("Solver", expanded=False):
        iterations = st.slider("Max iterations", 10, 5000, 2500, key="solver_iterations")
        tolerance = st.selectbox(
            "Convergence tolerance",
            [1e-2, 1e-3, 1e-4, 1e-5, 1e-6],
            index =3, 
            format_func=lambda x: f"{x:.0e}",
            key="solver_tolerance"
        )

    # This creates a button to reset the model to its initial state.
    col_reset, col_spacer = st.sidebar.columns([1, 1.5])
    with col_reset:
        if st.button("Reset Model", type="secondary", use_container_width=True):
            st.session_state.model = GroundwaterModel(nx=nx, ny=ny)
            st.session_state.solved = False
            st.rerun()

    # The current contrals are stored in the session state.
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

    simulation_config = {
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

    # If the controls have changed since the last run, we mark the model as unsolved to indicate that the results may be outdated.
    if st.session_state.get("last_controls") != current_controls:
        st.session_state.solved = False
        st.session_state.last_controls = current_controls

    col_main, col_info = st.columns([3, 1])

    head_display_candidates = [
        1.0,
        float(corner_tl),
        float(corner_tr),
        float(corner_bl),
        float(corner_br),
    ]
    head_display_candidates.extend(float(p["h"]) for p in point_sources)
    head_display_max = max(head_display_candidates)

# In the main area, we display the hydraulic head distribution. If the model is solved, we show the final head field. If not, we show the initial head field based on the current parameters.
    with col_main:
        st.subheader("Live Hydraulic Head Evolution")
        head_status_slot = st.empty()
        head_plot_slot = st.empty()

        if st.session_state.solved and st.session_state.current_result is not None:
            head_status_slot.caption("Final hydraulic head field")
            with head_plot_slot.container():
                render_plotly_component(
                    create_head_figure(
                        st.session_state.current_result["model"].head,
                        x_coords,
                        y_coords,
                        x_max,
                        y_max,
                        cell_size,
                        "Hydraulic Head Distribution",
                        None,
                    )
                )
        else:
            preview_model = build_model_from_config(simulation_config)
            preview_model.prepare_initial_state()
            head_status_slot.caption("Initial hydraulic head field before solving")
            with head_plot_slot.container():
                render_plotly_component(
                    create_head_figure(
                        preview_model.head,
                        x_coords,
                        y_coords,
                        x_max,
                        y_max,
                        cell_size,
                        "Initial Hydraulic Head Field",
                        None,
                    )
                )

    # This button runs the simulation with the current parameters. 
    # It also shows a spinner while the model is being solved and updates the session state with the results.
    if st.button("Solve Model", width="stretch", type="primary"):
        with st.spinner("Solving..."):
            st.session_state.previous_result = st.session_state.current_result

            def update_head_progress(iteration: int, head_snapshot, is_final: bool) -> None:
                if iteration == 0:
                    status_text = "Initial hydraulic head field"
                elif is_final:
                    status_text = f"Hydraulic head converged after {iteration} iterations"
                else:
                    status_text = f"Hydraulic head after {iteration} iterations"

                head_status_slot.caption(status_text)
                with head_plot_slot.container():
                    render_plotly_component(
                        create_head_figure(
                            head_snapshot,
                            x_coords,
                            y_coords,
                            x_max,
                            y_max,
                            cell_size,
                            status_text,
                            None,
                        )
                    )

            result = run_simulation(
                simulation_config,
                progress_callback=update_head_progress,
                progress_interval=50,
            )

            st.session_state.current_result = result
            st.session_state.model = result["model"]
            st.session_state.solved = True
        st.success("Model solved!")

    # If the model is solved and results are available, we display the results in the main area. 
    if st.session_state.solved and st.session_state.current_result is not None:
        model = st.session_state.current_result["model"]
        qx = np.asarray(st.session_state.current_result["qx"])
        qy = np.asarray(st.session_state.current_result["qy"])
        q_mag = np.asarray(st.session_state.current_result["q_mag"])
        summary = st.session_state.current_result["summary"]
        
        # The results are briefly summarized here.
        with col_info:
            st.subheader("Results")
            st.metric("Head (min)", f"{summary['head_min']:.2f} m")
            st.metric("Head (max)", f"{summary['head_max']:.2f} m")
            st.metric("Max flow", f"{summary['flow_max']:.3f} m/day")

        # To organize the visualizations, the following tabs are used.
        tabs = st.tabs([
            "Hydraulic Head",
            "Flow Magnitude",
            "Flow Vectors",
            "Conductivity",
            "Recharge Map",
        ])

        # This is the first tab: Hydraulic head distribution.
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
            fig_head.update_layout(title="Hydraulic Head Distribution", xaxis_title="X (m)", yaxis_title="Y (m)", height=800)
            fig_head = style_axes(fig_head, x_max, y_max, cell_size)
            fig_head = add_compass_and_invert_yaxis(fig_head, x_max, y_max, cell_size)
            st.plotly_chart(fig_head, use_container_width=True, config={"displayModeBar": False, "responsive": True})

        # This is the second tab: Flow magnitude distribution.
        with tabs[1]:
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
            fig_mag.update_layout(title="Groundwater Flow Magnitude", xaxis_title="X (m)", yaxis_title="Y (m)", height=800)
            fig_mag = style_axes(fig_mag, x_max, y_max, cell_size)
            fig_mag = add_compass_and_invert_yaxis(fig_mag, x_max, y_max, cell_size)
            st.plotly_chart(fig_mag, use_container_width=True, config={"displayModeBar": False, "responsive": True})

        # This is the third tab: Flow vectors showing the direction and magnitude of the flow.
        with tabs[2]:
            # Streamplot visualization using Matplotlib for clear flow lines
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

        # This is the fourth tab: Conductivity distribution (moved after flow vectors).
        with tabs[3]:
            fig_cond = go.Figure(
                data=go.Heatmap(
                    z=np.log10(model.hydraulic_conductivity),
                    x=x_coords,
                    y=y_coords,
                    colorscale="RdYlBu_r",
                    colorbar=dict(title="log10(K)"),
                )
            )
            fig_cond.update_layout(title="Hydraulic Conductivity (log scale)", xaxis_title="X (m)", yaxis_title="Y (m)", height=800)
            fig_cond = style_axes(fig_cond, x_max, y_max, cell_size)
            fig_cond = add_compass_and_invert_yaxis(fig_cond, x_max, y_max, cell_size)
            st.plotly_chart(fig_cond, use_container_width=True, config={"displayModeBar": False, "responsive": True})

        # This is the fifth tab: Recharge distribution.
        with tabs[4]:
            recharge_map = np.zeros_like(model.head)
            recharge_map[model.recharge > 0] = model.recharge[model.recharge > 0]
            fig_recharge = go.Figure(
                data=go.Heatmap(
                    z=recharge_map,
                    x=x_coords,
                    y=y_coords,
                    colorscale="YlGnBu",
                    colorbar=dict(title="Recharge (m/day)"),
                )
            )
            fig_recharge.update_layout(title="Recharge Distribution", xaxis_title="X (m)", yaxis_title="Y (m)", height=800)
            fig_recharge = style_axes(fig_recharge, x_max, y_max, cell_size)
            st.plotly_chart(fig_recharge, use_container_width=True, config={"displayModeBar": False, "responsive": True})

# The main function is called when the script is run, starting the Streamlit app.
if __name__ == "__main__":
    main()
