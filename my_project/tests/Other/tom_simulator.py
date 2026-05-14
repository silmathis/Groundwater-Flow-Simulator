import numpy as np
import matplotlib.pyplot as plt

plt.close("all")

# Independent physical
Kf = 1.0      # Fluid bulk modulus [Pa]
k = 1.0       # Permeability [m²]
mu = 1.0      # Fluid viscosity [Pa s]

# Dependent physical
k_mu = k / mu
c = k_mu * Kf

# Numerical parameters
nx = 50
ny = 50
nt = 500
CFL = 1 / 4
nout = 10

# Geometry
Lx = 6.0
Ly = 6.0

dx = Lx / (nx - 1)
dy = Ly / (ny - 1)

x_vec = np.linspace(-Lx / 2, Lx / 2, nx)
y_vec = np.linspace(-Ly / 2, Ly / 2, ny)

x, y = np.meshgrid(x_vec, y_vec, indexing="ij")

# Characteristic times
tch_diff = min(dx**2, dy**2) / c
dt = tch_diff * CFL / 2

# Initialize pressure field
Source = np.zeros((nx, ny))
qx = np.zeros((nx + 1, ny))
qy = np.zeros((nx, ny + 1))

# Initial condition
Pf = x + y + 6 * np.sin(y * x) - x**2 * y**2

t = 0.0

fig = plt.figure(figsize=(9, 7))
ax = fig.add_subplot(111, projection="3d")

for it in range(1, nt + 1):

    # Boundary conditions
    Pf[0, :] = -Lx / 2 + y[0, :]
    Pf[-1, :] = Lx / 2 + y[-1, :]

    Pf[:, 0] = -Ly / 2 + x[:, 0]
    Pf[:, -1] = Ly / 2 + x[:, -1]

    # Fluid flux
    qx[1:-1, :] = -k_mu * np.diff(Pf, axis=0) / dx
    qy[:, 1:-1] = -k_mu * np.diff(Pf, axis=1) / dy

    # Divergence of flux
    divQ = np.diff(qx, axis=0) / dx + np.diff(qy, axis=1) / dy

    # Pressure update
    dPfdt = -Kf * divQ + Source
    Pf = Pf + dPfdt * dt

    t = t + dt

    # Surf plot
    if it % nout == 0:
        ax.clear()

        surf = ax.plot_surface(x, y, Pf, cmap="viridis")

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_zlabel("Pf")
        ax.set_title(f"Pressure field, timestep = {it}, t = {t:.3f}")

        ax.set_zlim(np.min(Pf), np.max(Pf))

        plt.pause(0.01)

plt.show()