# Physics & Astronomy Reference

Guide for astronomical data analysis, quantum computing, and physics simulations.

## Table of Contents

1. [Astronomy](#astronomy)
2. [Quantum Computing](#quantum-computing)
3. [Symbolic Mathematics](#symbolic-mathematics)
4. [Simulations](#simulations)

---

## Astronomy

### Astropy

```python
# uv pip install astropy

from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
from astropy.io import fits
import numpy as np

# Units
distance = 10 * u.lightyear
speed = 299792458 * u.meter / u.second
print(distance.to(u.parsec))
print(speed.to(u.km / u.s))

# Coordinates
coord = SkyCoord(ra='14h29m42.95s', dec='-62d40m46.1s', frame='icrs')
print(coord.ra.degree, coord.dec.degree)

# Time
t = Time('2024-01-01 00:00:00', scale='utc')
print(t.jd)  # Julian Date

# FITS files
hdul = fits.open('image.fits')
data = hdul[0].data
header = hdul[0].header
```

### Coordinate Transformations

```python
from astropy.coordinates import SkyCoord, FK5, ICRS

# Convert between frames
coord_icrs = SkyCoord(ra=150 * u.degree, dec=30 * u.degree, frame='icrs')
coord_fk5 = coord_icrs.transform_to(FK5)

# Alt-Az from Ra-Dec
location = EarthLocation(lat=52 * u.deg, lon=0 * u.deg)
time = Time('2024-01-01 00:00:00')
coord = SkyCoord(ra=180 * u.deg, dec=45 * u.deg)
altaz = coord.transform_to(AltAz(obstime=time, location=location))
print(altaz.alt, altaz.az)
```

---

## Quantum Computing

### Qiskit

```python
# uv pip install qiskit

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Create quantum circuit
qc = QuantumCircuit(2, 2)

# Add gates
qc.h(0)  # Hadamard
qc.cx(0, 1)  # CNOT
qc.measure([0, 1], [0, 1])

# Simulate
simulator = AerSimulator()
compiled = transpile(qc, simulator)
result = simulator.run(compiled, shots=1000).result()
counts = result.get_counts()
print(counts)  # {'00': 500, '11': 500}
```

### PennyLane

```python
# uv pip install pennylane

import pennylane as qml
from pennylane import numpy as np

# Create device
dev = qml.device("default.qubit", wires=2)

# Define quantum function
@qml.qnode(dev)
def circuit(params):
    qml.RX(params[0], wires=0)
    qml.RY(params[1], wires=1)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

# Optimize
params = np.array([0.1, 0.2], requires_grad=True)
opt = qml.GradientDescentOptimizer(stepsize=0.1)

for i in range(100):
    params = opt.step(circuit, params)
```

### Cirq

```python
# uv pip install cirq

import cirq

# Create qubits
q0, q1 = cirq.LineQubit.range(2)

# Create circuit
circuit = cirq.Circuit(
    cirq.H(q0),
    cirq.CNOT(q0, q1),
    cirq.measure(q0, q1, key='result')
)

# Simulate
simulator = cirq.Simulator()
result = simulator.run(circuit, repetitions=100)
print(result.histogram(key='result'))
```

---

## Symbolic Mathematics

### SymPy

```python
# uv pip install sympy

from sympy import symbols, diff, integrate, limit, solve, simplify
from sympy import sin, cos, exp, log, sqrt, pi, E
from sympy import Matrix, eigenvals, eigenvects

# Define symbols
x, y, z = symbols('x y z')

# Calculus
expr = x**3 + 2*x**2 + x + 1
print(diff(expr, x))  # Derivative
print(integrate(expr, x))  # Integral
print(limit(sin(x)/x, x, 0))  # Limit

# Equation solving
eq = x**2 - 4
print(solve(eq, x))  # [−2, 2]

# Simplification
expr = (x**2 - 1) / (x - 1)
print(simplify(expr))  # x + 1

# Matrices
M = Matrix([[1, 2], [3, 4]])
print(M.eigenvals())
print(M.eigenvects())
```

### Physics with SymPy

```python
from sympy.physics.mechanics import LagrangesMethod, Lagrangian
from sympy.physics.mechanics import Particle, Point, ReferenceFrame
from sympy.physics.units import meter, second, kilogram

# Lagrangian mechanics
# Define generalized coordinates, kinetic/potential energy
# Use LagrangesMethod for equations of motion
```

---

## Simulations

### FluidSim (CFD)

```python
# uv pip install fluidsim

from fluidsim import load_sim_for_exec

# Create simulation
# params = ...
# sim = load_sim_for_exec(params)
# sim.time_stepping.start()
```

### SimPy (Discrete Event)

```python
# uv pip install simpy

import simpy

def car(env, name, charging_time, driving_time):
    while True:
        print(f'{name} arriving at {env.now}')
        with charging_station.request() as request:
            yield request
            print(f'{name} starting charging at {env.now}')
            yield env.timeout(charging_time)
            print(f'{name} done charging at {env.now}')
        
        print(f'{name} driving at {env.now}')
        yield env.timeout(driving_time)

env = simpy.Environment()
charging_station = simpy.Resource(env, capacity=2)
env.process(car(env, 'Car 1', 5, 10))
env.process(car(env, 'Car 2', 3, 8))
env.run(until=30)
```

---

## Key Packages Summary

| Package | Install | Use Case |
|---------|---------|----------|
| astropy | `uv pip install astropy` | Astronomy |
| qiskit | `uv pip install qiskit` | Quantum computing |
| pennylane | `uv pip install pennylane` | Quantum ML |
| cirq | `uv pip install cirq` | Quantum computing |
| sympy | `uv pip install sympy` | Symbolic math |
| simpy | `uv pip install simpy` | Discrete simulation |
