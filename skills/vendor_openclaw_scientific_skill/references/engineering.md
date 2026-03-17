# Engineering & Simulation Reference

Guide for optimization, systems modeling, metabolic engineering, and process simulation.

## Table of Contents

1. [Optimization](#optimization)
2. [Systems Modeling](#systems-modeling)
3. [Metabolic Engineering](#metabolic-engineering)
4. [Materials Science](#materials-science)

---

## Optimization

### PyMOO (Multi-Objective)

```python
# uv pip install pymoo

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.problems import get_problem
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter

# Define problem
problem = get_problem("zdt1")

# Setup algorithm
algorithm = NSGA2(pop_size=100)

# Optimize
res = minimize(problem,
               algorithm,
               ('n_gen', 200),
               seed=1,
               verbose=True)

# Visualize
Scatter().add(res.F).show()
```

### Custom Optimization Problem

```python
from pymoo.core.problem import Problem
import numpy as np

class MyProblem(Problem):
    def __init__(self):
        super().__init__(n_var=2, 
                         n_obj=2,
                         n_ieq_constr=2,
                         xl=np.array([-2, -2]),
                         xu=np.array([2, 2]))
    
    def _evaluate(self, X, out, *args, **kwargs):
        f1 = X[:, 0]**2 + X[:, 1]**2
        f2 = (X[:, 0] - 1)**2 + (X[:, 1] - 1)**2
        
        g1 = 2 - (X[:, 0]**2 + X[:, 1]**2)
        g2 = -3 + (X[:, 0]**2 + X[:, 1]**2)
        
        out["F"] = np.column_stack([f1, f2])
        out["G"] = np.column_stack([g1, g2])

problem = MyProblem()
```

### SciPy Optimization

```python
# uv pip install scipy

from scipy.optimize import minimize, differential_evolution, basinhopping

# Single-objective
def objective(x):
    return x[0]**2 + x[1]**2

result = minimize(objective, x0=[1, 1], method='BFGS')
print(result.x)

# Global optimization
result = differential_evolution(objective, bounds=[(-5, 5), (-5, 5)])
```

---

## Systems Modeling

### COBRApy (Metabolic Networks)

```python
# uv pip install cobra

from cobra import Model, Reaction, Metabolite

# Create model
model = Model('example')

# Add metabolites
A = Metabolite('A', compartment='c')
B = Metabolite('B', compartment='c')
C = Metabolite('C', compartment='c')

# Add reactions
R1 = Reaction('R1')
R1.add_metabolites({A: -1, B: 1})
R1.lower_bound = -10  # Reversible

R2 = Reaction('R2')
R2.add_metabolites({B: -1, C: 1})
R2.lower_bound = 0

model.add_reactions([R1, R2])

# Set objective
model.objective = 'R2'

# Optimize
solution = model.optimize()
print(solution.fluxes)
```

### FBA Analysis

```python
from cobra.io import load_model

# Load model
model = load_model("textbook")

# Flux Balance Analysis
solution = model.optimize()
print(f"Growth rate: {solution.objective_value}")

# Flux Variability Analysis
from cobra.flux_analysis import flux_variability_analysis
fva = flux_variability_analysis(model, model.reactions[:10])

# Gene knockout
from cobra.flux_analysis import single_gene_deletion
deletions = single_gene_deletion(model)
```

---

## Metabolic Engineering

### Strain Design

```python
from cobra import Reaction

def add_heterologous_pathway(model, reactions):
    """Add heterologous pathway to model."""
    for rxn in reactions:
        model.add_reaction(rxn)
    return model

def find_production_envelope(model, reaction_id, carbon_source):
    """Calculate production envelope."""
    results = []
    uptake_rates = np.linspace(0, 20, 50)
    
    for rate in uptake_rates:
        model.reactions.get_by_id(carbon_source).lower_bound = -rate
        solution = model.optimize()
        if solution.status == 'optimal':
            results.append({
                'uptake': rate,
                'growth': solution.objective_value,
                'production': solution.fluxes[reaction_id]
            })
    
    return results
```

### OptKnock (in silico strain design)

```python
# Requires cameo or similar package
# uv pip install cameo

from cameo import models
from cameo.strain_design import OptKnock

model = models.bigg.e_coli_core

# Setup OptKnock
optknock = OptKnock(model, 
                    objective=model.reactions.BIOMASS_Ecoli_core_w_GAM,
                    max_knockouts=3)

# Run
solutions = optknock.run(target=model.reactions.EX_succ_e)
```

---

## Materials Science

### Pymatgen

```python
# uv pip install pymatgen

from pymatgen.core import Structure, Lattice

# Create crystal structure
lattice = Lattice.cubic(4.2)
structure = Structure(lattice, ["Na", "Cl"], [[0, 0, 0], [0.5, 0.5, 0.5]])

# Properties
print(structure.density)
print(structure.volume)

# Read CIF
structure = Structure.from_file("structure.cif")

# Write POSCAR
structure.to(filename="POSCAR")
```

### Phase Diagrams

```python
from pymatgen.analysis.phase_diagram import PhaseDiagram, PDPlotter
from pymatgen.entries.computed_entries import ComputedEntry

# Create entries
entries = [
    ComputedEntry("Li", -1.9),
    ComputedEntry("Fe", -6.5),
    ComputedEntry("LiFePO4", -55.3)
]

# Build phase diagram
pd = PhaseDiagram(entries)

# Plot
plotter = PDPlotter(pd)
plotter.show()
```

---

## Key Packages Summary

| Package | Install | Use Case |
|---------|---------|----------|
| pymoo | `uv pip install pymoo` | Multi-objective optimization |
| scipy | `uv pip install scipy` | Scientific computing |
| cobra | `uv pip install cobra` | Metabolic modeling |
| cameo | `uv pip install cameo` | Strain design |
| pymatgen | `uv pip install pymatgen` | Materials science |
