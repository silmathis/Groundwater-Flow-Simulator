# Groundwater Simulator

An educational web-based tool for exploring 2D groundwater flow patterns using a simplified model based on Darcy's law.

## Overview

The Groundwater Simulator allows students and educators to interactively explore how hydraulic conductivity, recharge, and subsurface structure influence groundwater flow. It is designed for **learning and exploration**, not for engineering predictions.

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

`requirements.txt` contains both runtime and development dependencies.
Install everything from one file after activating your virtual environment.

#### Recommended setup (macOS / Linux / Windows)

Open a terminal in the **repository root** and create a virtual environment, then install the project's Python dependencies.

macOS / Linux (bash, zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Windows (Command Prompt):

```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Windows (Git Bash / MSYS2):

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

Notes:
- Use `python3` on systems where `python` maps to Python 2 or is not available.
- If `pip install -r requirements.txt` fails, use the `python -m pip install -r requirements.txt` form shown above.
- If activation fails, verify you are in the repository root and that the `.venv` directory was created. On macOS you may need to allow script execution or use a different shell (e.g., `zsh`).
- **Remember:** Activate the virtual environment for every new terminal session using the appropriate command for your shell.

### Running the App

After activating the virtual environment:

```bash
streamlit run app.py
```

Or using Python directly from the activated environment:

```bash
python -m streamlit run app.py
```

**Without activation** (directly in the repository root):

Windows (Git Bash):
```bash
./.venv/Scripts/python.exe -m streamlit run app.py
```

macOS / Linux:
```bash
./.venv/bin/python -m streamlit run app.py
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

The Groundwater Simulator solves a steady-state 2D groundwater flow equation based on **Darcy's Law**:

```
q = -K ∇h
```

where:
- **q** = specific discharge (m/day)
- **K** = hydraulic conductivity (m/day)
- **∇h** = hydraulic head gradient

The general groundwater flow equation solved by the model is (steady-state form):

```
∇ · (K ∇h) + R = 0
```

where **h** is hydraulic head, **K** is hydraulic conductivity (which may vary in space), and **R** is recharge (source/sink term). For the special case of spatially constant `K` this reduces to `K ∇²h + R = 0`.

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

** NOT suitable for:**
- Engineering site assessments
- Real-world predictions
- Design calculations
- Regulatory submissions

** SUITABLE for:**
- Hydrogeology education
- Intuition building
- Exploring parameter sensitivity
- Demonstrating fundamental flow principles


## Dependencies

- **NumPy:** Numerical computations
- **SciPy:** Scientific computing utilities
- **Streamlit:** Web application framework
- **Plotly:** Interactive visualizations
- **Matplotlib:** (optional) Static plotting

Install all dependencies with `pip install -r requirements.txt` after activating your virtual environment.


## Future Enhancements (Stretch Goals)

- **Unsaturated Flow:** Extension to vadose zone using Richards equation
- **Transient Simulation:** Time-stepping for non-equilibrium conditions
- **Advanced Visualization:** Particle pathlines, animation
- **Data Import:** Load real geological data
- **Sensitivity Analysis:** Systematic parameter exploration

## License

This project is provided as-is for educational purposes.

## Contact & Support

Für Fragen oder Support schreiben Sie bitte eine E-Mail an silmathis@ethz.ch.

---

**Version:** 0.1.0  
**Last Updated:** 2026-05-28  
**Status:** Active Development
