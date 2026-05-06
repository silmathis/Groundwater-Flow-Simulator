# Revised Project Concept

## 1\. Mission

We will build an interactive web-based 2D groundwater flow simulation tool with a graphical user interface that allows users to explore how different parameters such as hydraulic conductivity, recharge, and rock type influence groundwater flow in a simplified and intuitive way. The tool is intended as an educational and exploratory application, not as a predictive engineering model, and should guide users clearly in how to use and interpret the simulation.

\---

## 2\. Scope

### In Scope

* Development of a Python-based interactive 2D groundwater flow simulator.
* Use of a simplified conceptual groundwater flow model based on Darcy’s law.
* Graphical user interface with sliders, buttons, and simple parameter controls.
* User-defined spatial parameter zones, for example different rock types or permeability regions.
* Clear visualisation of hydraulic head and groundwater flow patterns.
* Explanatory guidance inside the program so users understand how to operate it and what the outputs mean.

### Out of Scope / Non-Goals

* Full 3D groundwater modelling.
* Use of real site-specific input data or calibration to real aquifers.
* Detailed treatment of complex hydrogeological processes such as pumping wells, rivers, fractures, or fine-scale heterogeneity.
* Full solution of advanced unsaturated flow models such as the Richards equation in the main project scope.

### Stretch Goal / Advanced Extension

* Extension toward a more advanced formulation including unsaturated flow effects using the Richards equation, if time permits.

\---

## 3\. Objectives

### 3.1 Scientific Validity Objectives

* Reproduce qualitatively correct groundwater flow behaviour, including flow from high hydraulic head to low hydraulic head.
* Show the effect of changing hydraulic conductivity, recharge, and subsurface structure on flow behaviour.
* Ensure that model assumptions and simplifications are clearly documented.
* Maintain physically plausible behaviour within the simplified conceptual framework.

### 3.2 Operational Performance Objectives

* The tool should run interactively on a standard student laptop on the web.
* The graphical user interface should be simple and intuitive for non-experts.
* The program should provide clear instructions or guidance so that a first-time user can understand how to use it.
* Visual outputs should be easy to read and interpret.
* Parameter changes should update the simulation quickly enough to support exploratory use.

\---

## 4\. Inputs / Outputs

### 4.1 Inputs

Inputs will mainly be controlled through the GUI rather than through real datasets. These may include:

* Hydraulic conductivity / permeability
* Recharge or infiltration rate
* Initial or boundary hydraulic head
* Rock type or subsurface zone type
* Porosity or simplified storage-related parameters
* Boundary condition settings
* Grid or domain size

### 4.2 Outputs

* 2D hydraulic head field
* Groundwater flow direction and relative flow magnitude
* Animation of the flow field

\---

## 5\. Core Model Idea

The main model will be a simplified 2D groundwater flow formulation based on Darcy’s law.

The simulation domain will be represented on a 2D grid. Users will be able to adjust parameters interactively and observe how groundwater flow patterns respond. The model is intended to remain conceptual and educational rather than fully hydrogeologically complete.

\---

## 6\. User Guidance and Usability

A key goal of the project is that users should not only be able to run the simulation, but also understand how to use it. Therefore, the program should include:

* short and clear instructions directly in the GUI,
* labels explaining the meaning of parameters,
* warnings that the model is simplified and intended for exploration and learning.

This is important so that the tool is not only technically functional, but also accessible and educational.

\---

## 7\. Constraints

* The model must remain understandable and implementable within the course timeframe.
* The numerical approach must stay simple enough for an interactive GUI application.
* The project should prioritise clarity, usability, and robustness.
* The simulation should run on standard laptops on the web without specialised hardware.

\---

## 8\. Risks \& Mitigation Strategies

|Risk|Mitigation|
|-|-|
|The model becomes too mathematically or numerically complex|Keep the main scope at the level of a simplified Darcy-based 2D model|
|The GUI becomes cluttered or confusing|Start with a minimal interface and only add controls that are clearly useful|
|Users misunderstand the model as realistic prediction|Clearly label the tool as educational and exploratory|
|Simulation is too slow for interactive use|Use a coarse grid and simple numerical updates|
|Team relies too heavily on AI|We're trying to understand the code rather than vibe-coding|
|Users do not know how to use the program|Include built-in instructions, labels, and help text in the interface|

\---

## 9\. Suggested Positioning

This project is best framed as an:

**interactive educational groundwater flow sandbox**

This makes our goal very clear:

* not a professional prediction tool,
* but a visually intuitive environment for exploring groundwater flow processes.

