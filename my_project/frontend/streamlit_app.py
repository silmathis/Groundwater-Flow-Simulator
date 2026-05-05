"""Streamlit frontend for the groundwater simulator."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from my_project.backend.simulation_service import run_simulation
from my_project.groundwater_model import GroundwaterModel

def add_compass_and_invert_yaxis(fig, ny, nx):
    """
    Add compass directions (N, S, O, W) and invert y-axis for proper geographic orientation.
    North should be at the top, South at the bottom.
    """
    # Invert y-axis so North (index 0) is at top
    fig.update_yaxes(autorange="reversed")
    
    # Add compass annotations
    compass_props = dict(showarrow=False, font=dict(size=14, color="black"), 
                         bgcolor="rgba(255,255,255,0.7)", borderpad=4)
    
    # North (oben mittig)
    fig.add_annotation(x=nx/2, y=-2, text="<b>N</b>", xanchor="center", **compass_props)
    
    # South (unten mittig)
    fig.add_annotation(x=nx/2, y=ny+2, text="<b>S</b>", xanchor="center", **compass_props)
    
    # Ost/East (rechts mittig)
    fig.add_annotation(x=nx+2, y=ny/2, text="<b>O</b>", yanchor="middle", **compass_props)
    
    # West (links mittig)
    fig.add_annotation(x=-2, y=ny/2, text="<b>W</b>", yanchor="middle", **compass_props)
    
    return fig


def main() -> None:
    st.set_page_config(
        page_title="Groundwater Flow Simulator",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Increase sidebar width for better preview visualization
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] > div:first-child {
                width: 450px;
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

    st.sidebar.subheader("Point Sources (Fixed Hydraulic Head)")
    st.sidebar.caption("Coordinates for point sources are linked to the grid size selected above.")
    point_source_count = st.sidebar.slider("Number of point sources", 1, 6, 2)

    point_sources = []
    for idx in range(1, point_source_count + 1):
        default_x = int(round((idx / (point_source_count + 1)) * nx))
        default_y = int(ny * 0.5)
        default_h = 20.0 if idx % 2 else 5.0
        with st.sidebar.expander(f"Point {idx}", expanded=idx <= 2):
            x_val = st.number_input(f"P{idx}: X coord", min_value=0, value=default_x, step=1, key=f"ps{idx}_x")
            y_val = st.number_input(f"P{idx}: Y coord", min_value=0, value=default_y, step=1, key=f"ps{idx}_y")
            h_val = st.slider(f"P{idx}: Head (m)", 0.0, 30.0, default_h, step=0.5, key=f"ps{idx}_h")

        x_coord = int(x_val)
        y_coord = int(y_val)
        if x_coord > nx:
            st.sidebar.warning(f"Point {idx}: X coordinate exceeds grid width ({nx}). It will be clipped to {nx}.")
            x_coord = nx
        if y_coord > ny:
            st.sidebar.warning(f"Point {idx}: Y coordinate exceeds grid height ({ny}). It will be clipped to {ny}.")
            y_coord = ny

        # Map UI coordinates [0..nx] / [0..ny] to model cell indices [0..nx-1] / [0..ny-1].
        point_sources.append({"x": min(x_coord, nx - 1), "y": min(y_coord, ny - 1), "h": float(h_val)})


    st.sidebar.subheader("Boundary Conditions (Head in meters)")
    use_boundary_conditions = st.sidebar.checkbox("Use boundary conditions", value=False)

    head_north = 15.0
    head_south = 5.0
    head_west = 10.0
    head_east = 10.0

    if use_boundary_conditions:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            head_north = st.slider("North (top)", 0.0, 30.0, 15.0, step=0.5)
            head_south = st.slider("South (bottom)", 0.0, 30.0, 5.0, step=0.5)
        with col2:
            head_west = st.slider("West (left)", 0.0, 30.0, 10.0, step=0.5)
            head_east = st.slider("East (right)", 0.0, 30.0, 10.0, step=0.5)


    st.sidebar.subheader("Conductivity")
    conductivity_mode = st.sidebar.radio(
        "Medium type",
        ["Homogeneous medium", "Heterogeneous medium with zone"],
    )

    # Predefined sediment conductivities
    sediment_options = {
        "High conductivity (sand)": 5.0,
        "Medium (silt)": 1.0,
        "Low conductivity (clay)": 0.1,
    }

    # Background conductivity selection (sediment types or custom)
    st.sidebar.markdown("**Background conductivity**")
    bg_choice = st.sidebar.radio(
        "Background type",
        ["High conductivity (sand)", "Medium (silt)", "Low conductivity (clay)", "Custom"],
        index=1,
    )
    if bg_choice == "Custom":
        background_k = st.sidebar.slider(
            "Background conductivity K (m/day)", min_value=0.1, max_value=5.0, value=1.0, step=0.1
        )
    else:
        background_k = sediment_options[bg_choice]

    # Color mapping for sediments (used in previews)
    bg_color_map = {
        "High conductivity (sand)": "#fff7b2",  # pale yellow
        "Medium (silt)": "#dcdcdc",            # light gray
        "Low conductivity (clay)": "#4a4a4a",  # dark gray
        "Custom": "#ffffff",                   # white
    }
    bg_color = bg_color_map.get(bg_choice, "#ffffff")

    # If homogeneous medium is selected, show a single background preview
    if conductivity_mode == "Homogeneous medium":
        aspect_ratio = ny / nx
        preview_width = 350
        preview_height = int(preview_width * aspect_ratio)

        bg_grid = np.zeros((ny, nx))
        fig_bg = go.Figure(
            data=go.Heatmap(
                z=bg_grid,
                colorscale=[[0, bg_color], [1, bg_color]],
                showscale=False,
                hovertemplate="Background: %{x}, %{y}<extra></extra>",
            )
        )
        fig_bg.update_layout(
            title="Background Preview",
            xaxis_title="X",
            yaxis_title="Y",
            height=preview_height,
            margin=dict(l=30, r=30, t=30, b=30),
        )
        st.sidebar.plotly_chart(fig_bg, use_container_width=True)

    # Prepare defaults for zone
    zone_type = None
    selected_k = None
    zone_x_min = zone_x_max = zone_y_min = zone_y_max = 0

    if conductivity_mode == "Heterogeneous medium with zone":
        st.sidebar.subheader("Subsurface Zone")
        st.sidebar.markdown("Choose sediment type for the zone or set custom K")
        zone_choice = st.sidebar.radio(
            "Zone type",
            ["High conductivity (sand)", "Medium (silt)", "Low conductivity (clay)", "Custom"],
            index=0,
        )

        if zone_choice == "Custom":
            selected_k = st.sidebar.slider(
                "Zone conductivity K (m/day)", min_value=0.1, max_value=5.0, value=2.0, step=0.1
            )
            zone_type = "Custom"
        else:
            selected_k = sediment_options[zone_choice]
            zone_type = zone_choice

        # Position inputs for the zone (same layout as before)
        col1, col2 = st.sidebar.columns(2)
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
        preview_height = int(preview_width * aspect_ratio)

        zone_color_map = {
            "High conductivity (sand)": "#fff7b2",
            "Medium (silt)": "#dcdcdc",
            "Low conductivity (clay)": "#4a4a4a",
            "Custom": "#ffffff",
        }
        zone_color = zone_color_map.get(zone_type, "#ffffff")

        fig_zone = go.Figure(
            data=go.Heatmap(
                z=combined_grid,
                colorscale=[[0, bg_color], [1, zone_color]],
                showscale=False,
                hovertemplate="X: %{x}<br>Y: %{y}<br>Zone: %{z}<extra></extra>",
            )
        )
        fig_zone.update_layout(
            title=f"Domain Preview (background + zone)",
            xaxis_title="X",
            yaxis_title="Y",
            height=preview_height,
            margin=dict(l=30, r=30, t=40, b=30),
        )
        st.sidebar.plotly_chart(fig_zone, use_container_width=True)

    st.sidebar.subheader("Recharge (Infiltration)")
    recharge_rate = st.sidebar.slider("Recharge rate (m/day)", 0.0, 0.05, 0.01, step=0.001)
    
    col1, col2 = st.sidebar.columns(2)
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
    preview_height = int(preview_width * aspect_ratio)
    
    fig_recharge = go.Figure(
        data=go.Heatmap(
            z=recharge_grid,
            colorscale="Blues",
            showscale=False,
            hovertemplate="X: %{x}<br>Y: %{y}<br>Rate: %{z:.4f} m/day<extra></extra>",
        )
    )
    fig_recharge.update_layout(
        title="Recharge Zone Preview",
        xaxis_title="X",
        yaxis_title="Y",
        height=preview_height,
        margin=dict(l=30, r=30, t=40, b=30),
    )
    st.sidebar.plotly_chart(fig_recharge, use_container_width=True)

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
        point_source_count,
        tuple((p["x"], p["y"], p["h"]) for p in point_sources),
        use_boundary_conditions,
        head_north,
        head_south,
        head_west,
        head_east,
        conductivity_mode,
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

    if st.button("Solve Model", width="stretch", type="primary"):
        with st.spinner("Solving..."):
            config = {
                "nx": nx,
                "ny": ny,
                "point_sources": point_sources,
                "use_boundary_conditions": use_boundary_conditions,
                "head_north": head_north,
                "head_south": head_south,
                "head_west": head_west,
                "head_east": head_east,
                "background_k": background_k,
                "conductivity_mode": conductivity_mode,
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
                    colorscale="jet",
                    colorbar=dict(title="Head (m)"),
                    contours=dict(coloring="heatmap"),
                )
            )
            fig_head.update_layout(title="Hydraulic Head Distribution", xaxis_title="X (cells)", yaxis_title="Y (cells)", height=500)
            fig_head = add_compass_and_invert_yaxis(fig_head, model.ny, model.nx)
            st.plotly_chart(fig_head, width="stretch")

        with tabs[1]:
            fig_cond = go.Figure(
                data=go.Heatmap(
                    z=np.log10(model.hydraulic_conductivity),
                    colorscale="RdYlBu_r",
                    colorbar=dict(title="log10(K)"),
                )
            )
            fig_cond.update_layout(title="Hydraulic Conductivity (log scale)", xaxis_title="X (cells)", yaxis_title="Y (cells)", height=500)
            fig_cond = add_compass_and_invert_yaxis(fig_cond, model.ny, model.nx)
            st.plotly_chart(fig_cond, width="stretch")

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
            fig_mag = add_compass_and_invert_yaxis(fig_mag, model.ny, model.nx)
            st.plotly_chart(fig_mag, width="stretch")

        with tabs[3]:
            # Use logarithmic scale for better gradient visualization
            q_mag_display = np.log10(q_mag + 1e-8)  # Add small value to avoid log(0)
            
            fig_vec = go.Figure(data=go.Heatmap(
                z=q_mag_display, 
                colorscale="RdYlBu_r",
                colorbar=dict(title="Flow log10(m/day)"),
                hovertemplate="X: %{x}<br>Y: %{y}<br>Flow: %{customdata:.3e} m/day<extra></extra>",
                customdata=q_mag
            ))
            
            # Use finer grid for more arrows (every 2-3 cells instead of sparse)
            step = max(1, max(model.nx, model.ny) // 20)
            
            for i in range(0, model.ny, step):
                for j in range(0, model.nx, step):
                    mag = q_mag[i, j]
                    
                    # Scale arrow size based on flow magnitude
                    # Normalize magnitude for arrow sizing
                    q_max = np.max(q_mag)
                    if q_max > 0:
                        normalized_mag = mag / q_max
                    else:
                        normalized_mag = 0
                    
                    # Adaptive scaling: larger for stronger flows
                    scale_factor = 2.5 + 3.5 * normalized_mag  # Range 2.5 to 6.0
                    arrow_width = max(0.5, 3.0 * normalized_mag)  # Range 0.5 to 3.0
                    
                    fig_vec.add_annotation(
                        x=j,
                        y=i,
                        ax=j - qx[i, j] * scale_factor,
                        ay=i - qy[i, j] * scale_factor,
                        arrowhead=2,
                        arrowsize=1.5,
                        arrowwidth=arrow_width,
                        arrowcolor="darkred",
                        xref="x",
                        yref="y",
                        axref="x",
                        ayref="y",
                        showarrow=True,
                        opacity=0.7
                    )
            
            fig_vec.update_layout(
                title="Flow Direction and Magnitude (Arrow size indicates flow strength)",
                xaxis_title="X (cells)",
                yaxis_title="Y (cells)",
                height=550
            )
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
                fig_head_delta = add_compass_and_invert_yaxis(fig_head_delta, model.ny, model.nx)
                st.plotly_chart(fig_head_delta, width="stretch")

                fig_flow_delta = go.Figure(data=go.Heatmap(z=flow_delta, colorscale="RdBu", zmid=0.0, colorbar=dict(title="Delta flow (m/day)")))
                fig_flow_delta.update_layout(title="Flow Change Since Previous Solve", xaxis_title="X (cells)", yaxis_title="Y (cells)", height=450)
                fig_flow_delta = add_compass_and_invert_yaxis(fig_flow_delta, model.ny, model.nx)
                st.plotly_chart(fig_flow_delta, width="stretch")
            else:
                st.info("Solve at least twice with different inputs to see change maps.")


if __name__ == "__main__":
    main()
