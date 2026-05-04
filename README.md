# 💧 Interactive Groundwater Flow Simulator

An educational web-based tool for exploring 2D groundwater flow patterns using a simplified model based on Darcy's law.

## Overview

This simulator allows students and educators to interactively explore how hydraulic conductivity, recharge, and subsurface structure influence groundwater flow. It is designed for **learning and exploration**, not for engineering predictions.

### Key Features

- **Interactive 2D Simulation:** Adjust parameters in real-time and watch flow patterns respond
- **Zone-based Conductivity:** Define regions with different rock types (sand, silt, clay)
- **Boundary Controls:** Set water table heights at domain edges
- **Rich Visualizations:**
  - Hydraulic head (water table elevation) contours
  - Conductivity/permeability zones
  - Flow magnitude heatmaps
  - Flow direction vectors
- **Built-in Guidance:** Clear explanations of model parameters and output meaning

## Getting Started

### Installation

`pip install -e .` installs this project into the currently active Python environment.
It does **not** create a virtual environment by itself.

#### Recommended setup (macOS / Linux / Windows)

Open a terminal in the **repository root** and follow the platform-specific steps below to create and activate a virtual environment, then install the project.

macOS / Linux (bash, zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Windows (with Git Bash):

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -e .
```

Notes:
- Use `python3` on systems where `python` maps to Python 2 or is not available. For example, `python3 -m venv .venv` and `python3 -m pip install -e .` on macOS.
- If `pip install -e .` fails with `command not found`, prefer the `python -m pip ...` form shown above.
- If activation fails, verify you are in the repository root and that the `.venv` directory was created. On macOS you may need to allow script execution or use a different shell (e.g., `zsh`).

### Running the App

```bash
streamlit run app.py
```

If the app is already running inside the virtual environment, you can also use:

```bash
python -m streamlit run app.py
```

The app will open in your web browser at `http://localhost:8501`.

## Usage

1. **Set Boundary Conditions:** Use sliders to set hydraulic head at domain edges
2. **Define Subsurface Zones:** Draw regions with different conductivity (high = sand, low = clay)
3. **Add Recharge:** Define where water infiltrates from above
4. **Solve:** Click "Solve Model" to calculate the equilibrium head and flow field
5. **Explore:** View multiple visualizations to understand flow behavior

## Model Description

### Physical Basis

The simulator solves a steady-state 2D groundwater flow equation based on **Darcy's Law**:

```
q = -K ∇h
```

where:
- **q** = specific discharge (m/day)
- **K** = hydraulic conductivity (m/day)
- **∇h** = hydraulic head gradient

The flow equation is:
```
∇²h + R/K = 0
```

where **R** is the recharge rate.

### Numerical Approach

- **Discretization:** Finite differences on a regular 2D grid
- **Solver:** Iterative relaxation method (Gauss-Seidel)
- **Boundary Conditions:** Fixed head (Dirichlet) at domain edges

### Assumptions & Limitations

- **Steady-state only:** Equilibrium conditions, no time-dependent dynamics
- **Homogeneous within zones:** Conductivity is constant within each defined zone
- **No wells or springs:** Simplified boundary representation
- **No anisotropy:** Same conductivity in all directions
- **Fully saturated:** No vadose (unsaturated) zone
- **2D only:** Simplified representation (ignores 3D effects)

**⚠️ NOT suitable for:**
- Engineering site assessments
- Real-world predictions
- Design calculations
- Regulatory submissions

**✅ SUITABLE for:**
- Hydrogeology education
- Intuition building
- Exploring parameter sensitivity
- Demonstrating fundamental flow principles

## Project Structure

```
.
├── app.py                           # Root Streamlit entry point
├── requirements.txt                 # Root runtime dependencies
├── START_APP.bat                    # Local launcher
├── Streamlit_Start/                 # Quick-start shortcuts
└── my_project/
    ├── pyproject.toml               # Package metadata
    ├── README.md                    # This file
    └── my_project/
        ├── __init__.py
        ├── groundwater_model.py     # Core physics model
        ├── frontend/
        │   └── streamlit_app.py     # UI layer
        └── backend/
            └── simulation_service.py # Simulation service layer
```

## Dependencies

- **NumPy:** Numerical computations
- **SciPy:** Scientific computing utilities
- **Streamlit:** Web application framework
- **Plotly:** Interactive visualizations
- **Matplotlib:** (optional) Static plotting

Install all dependencies:
```bash
pip install numpy scipy streamlit plotly matplotlib
```

## Examples & Exercises

### Exercise 1: Effect of Conductivity
1. Draw a low-conductivity (clay) zone in the center
2. Solve and observe: Does flow go around or through the clay?
3. Try changing the zone's conductivity and re-solve

### Exercise 2: Recharge vs. Conductivity
1. Add a recharge zone on one side
2. Vary the conductivity of the aquifer
3. How does conductivity affect the shape of the water table?

### Exercise 3: Boundary Condition Effects
1. Set one boundary much higher than others
2. Solve and observe flow direction
3. Try symmetric vs. asymmetric boundary conditions

## Contributing

Contributions are welcome! Areas for potential improvement:

- [ ] Time-dependent (transient) flow simulation
- [ ] Unsaturated flow (Richards equation)
- [ ] Pumping wells as boundary conditions
- [ ] Parameter sensitivity analysis
- [ ] Particle tracking (pathline visualization)
- [ ] Export results to file formats

## Future Enhancements (Stretch Goals)

- **Unsaturated Flow:** Extension to vadose zone using Richards equation
- **Transient Simulation:** Time-stepping for non-equilibrium conditions
- **Advanced Visualization:** Particle pathlines, animation
- **Data Import:** Load real geological data
- **Sensitivity Analysis:** Systematic parameter exploration

## License

This project is provided as-is for educational purposes.

## Contact & Support

For questions or issues, please open an issue in the repository.

---

**Version:** 0.1.0  
**Last Updated:** 2026-04-21  
**Status:** Active Development

