# Cheminformatics & Drug Discovery Reference

Comprehensive guide for molecular manipulation, virtual screening, ADMET prediction, and drug discovery workflows.

## Table of Contents

1. [Molecular Manipulation](#molecular-manipulation)
2. [Molecular Descriptors](#molecular-descriptors)
3. [Virtual Screening](#virtual-screening)
4. [ADMET Prediction](#admet-prediction)
5. [Molecular Docking](#molecular-docking)
6. [Database Access](#database-access)

---

## Molecular Manipulation

### RDKit Basics

```python
# uv pip install rdkit

from rdkit import Chem
from rdkit.Chem import AllChem, Draw, Descriptors
from rdkit.Chem import rdMolDescriptors

# Create molecule from SMILES
mol = Chem.MolFromSmiles('CC(=O)Oc1ccccc1C(=O)O')  # Aspirin

# Get SMILES
smiles = Chem.MolToSmiles(mol)

# Generate 3D conformation
mol_3d = Chem.AddHs(mol)
AllChem.EmbedMolecule(mol_3d, AllChem.ETKDG())
AllChem.MMFFOptimizeMolecule(mol_3d)

# Draw molecule
Draw.MolToImage(mol, size=(300, 300))

# Substructure search
pattern = Chem.MolFromSmarts('c1ccccc1')  # Benzene
matches = mol.GetSubstructMatches(pattern)
```

### Molecular Transformations

```python
from rdkit.Chem import rdChemReactions

# Define reaction
rxn = rdChemReactions.ReactionFromSmarts('[C:1](=[O:2])-[OH:3].[NH2:4]>>[C:1](=[O:2])-[NH:4]')
products = rxn.RunReactants((acid, amine))

# Generate tautomers
from rdkit.Chem import rdTautomerQuery
tautomer_enumerator = rdTautomerQuery.TautomerEnumerator()
tautomers = tautomer_enumerator.Enumerate(mol)
```

### datamol

```python
# uv pip install datamol

import datamol as dm

# Convert formats
mol = dm.to_mol('CCO')
smiles = dm.to_smiles(mol)
selfies = dm.to_selfies(mol)

# Generate conformers
mols_with_conformers = dm.conformers.generate(mol)

# Fingerprints
fp = dm.to_fp(mol, fp_type='ecfp')

# Cluster molecules
clusters = dm.cluster_mols(mols, cutoff=0.7)
```

---

## Molecular Descriptors

### RDKit Descriptors

```python
from rdkit.Chem import Descriptors, rdMolDescriptors

mol = Chem.MolFromSmiles('CCO')

# Physicochemical properties
mw = Descriptors.MolWt(mol)
logp = Descriptors.MolLogP(mol)
tpsa = Descriptors.TPSA(mol)
hbd = Descriptors.NumHDonors(mol)
hba = Descriptors.NumHAcceptors(mol)
rotatable = Descriptors.NumRotatableBonds(mol)

# Lipinski Rule of 5
def passes_lipinski(mol):
    return (
        Descriptors.MolWt(mol) <= 500 and
        Descriptors.MolLogP(mol) <= 5 and
        Descriptors.NumHDonors(mol) <= 5 and
        Descriptors.NumHAcceptors(mol) <= 10
    )

# All descriptors
desc_names = [d[0] for d in Descriptors._descList]
from rdkit.ML.Descriptors import MoleculeDescriptors
calculator = MoleculeDescriptors.MolecularDescriptorCalculator(desc_names)
descriptors = calculator.CalcDescriptors(mol)
```

### Fingerprints

```python
from rdkit.Chem import AllChem, rdMolDescriptors

mol = Chem.MolFromSmiles('CCO')

# Morgan (ECFP) fingerprint
fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)

# MACCS keys
maccs = rdMolDescriptors.GetMACCSKeysFingerprint(mol)

# RDKit fingerprint
rdk_fp = Chem.RDKFingerprint(mol)

# Similarity
from rdkit import DataStructs
similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
```

---

## Virtual Screening

### Similarity Search

```python
from rdkit import DataStructs
from rdkit.Chem import AllChem

def similarity_search(query_smiles, library_smiles_list, cutoff=0.7):
    query_mol = Chem.MolFromSmiles(query_smiles)
    query_fp = AllChem.GetMorganFingerprintAsBitVect(query_mol, 2, 2048)
    
    results = []
    for smi in library_smiles_list:
        mol = Chem.MolFromSmiles(smi)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, 2048)
        sim = DataStructs.TanimotoSimilarity(query_fp, fp)
        if sim >= cutoff:
            results.append((smi, sim))
    
    return sorted(results, key=lambda x: -x[1])
```

### Pharmacophore Search

```python
from rdkit.Chem import rdShapeAlign

# Shape-based alignment
probe_mol = Chem.MolFromSmiles('CCO')
ref_mol = Chem.MolFromSmiles('CCC')

# Generate 3D
AllChem.EmbedMolecule(probe_mol)
AllChem.EmbedMolecule(ref_mol)

# Align
align_score = rdShapeAlign.AlignMol(probe_mol, ref_mol)
```

---

## ADMET Prediction

### DeepChem

```python
# uv pip install deepchem

import deepchem as dc

# Solubility prediction
tasks, datasets, transformers = dc.molnet.load_delaney()
train, valid, test = datasets
model = dc.models.GraphConvModel(len(tasks), mode='regression')
model.fit(train)
predictions = model.predict(test)

# Toxicity prediction
tox21_tasks, tox21_datasets, transformers = dc.molnet.load_tox21()
model = dc.models.GraphConvModel(len(tox21_tasks), mode='classification')
model.fit(tox21_datasets[0])

# ADMET models
from deepchem.models import ADMETModel
```

### molfeat

```python
# uv pip install molfeat

from molfeat.trans import MoleculeTransformer
from molfeat.trans.fp import FPVecTransformer

# Molecular embeddings
transformer = FPVecTransformer(kind='ecfp', length=2048)
features = transformer(['CCO', 'CCN'])

# Pretrained models
from molfeat.calc import FPCalculator
calc = FPCalculator('ecfp')
fp = calc('CCO')
```

---

## Molecular Docking

### DiffDock

```python
# uv pip install diffdock

# Note: DiffDock requires specific setup
# See: https://github.com/gcorso/DiffDock

# Prepare protein
# Prepare ligand
# Run docking
```

### AutoDock Vina (via Python)

```python
# uv pip install vina

from vina import Vina

v = Vina(sf_name='vina')

# Set receptor
v.set_receptor('protein.pdbqt')

# Set ligand
v.set_ligand_from_file('ligand.pdbqt')

# Dock
v.dock()
v.write_poses('output.pdbqt', n_poses=10, energy_range=3)
```

---

## Database Access

### ChEMBL

```python
import requests

def query_chembl(target, ic50_threshold=50):
    """Query ChEMBL for active compounds"""
    url = "https://www.ebi.ac.uk/chembl/api/data/activity.json"
    params = {
        "target_chembl_id": target,
        "standard_type": "IC50",
        "standard_units": "nM",
        "standard_value__lte": ic50_threshold
    }
    response = requests.get(url, params=params)
    return response.json()

# Get compound info
def get_compound(chembl_id):
    url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/{chembl_id}.json"
    response = requests.get(url)
    return response.json()
```

### PubChem

```python
import requests

def search_pubchem(smiles, similarity_threshold=90):
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastsimilarity_2d/smiles/JSON"
    params = {"SMILES": smiles, "Threshold": similarity_threshold}
    response = requests.post(url, data=params)
    return response.json()

def get_pubchem_properties(cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/MolecularWeight,XLogP,TPSA/JSON"
    response = requests.get(url)
    return response.json()
```

### ZINC

```python
import requests

def search_zinc(query, max_price=100):
    url = "https://zinc.docking.org/substances/search/"
    params = {"q": query}
    response = requests.get(url, params=params)
    return response.json()

# ZINC20 API
def get_zinc_tranches(properties):
    """
    Filter compounds by:
    - Molecular weight
    - LogP
    - Reactivity
    - Purchasability
    """
    pass
```

### DrugBank

```python
# Requires license for full access

import xml.etree.ElementTree as ET

def parse_drugbank(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    drugs = []
    for drug in root.findall('{http://drugbank.ca}drug'):
        name = drug.find('{http://drugbank.ca}name').text
        indication = drug.find('{http://drugbank.ca}indication').text
        drugs.append({'name': name, 'indication': indication})
    
    return drugs
```

### BindingDB

```python
import requests

def query_bindingdb(target_name):
    url = "https://www.bindingdb.org/bind/chemsearch/marvin/BindingDB-Search.jsp"
    # Use REST API for binding affinities (Ki, Kd, IC50, EC50)
    params = {"target": target_name}
    # Note: BindingDB has specific API requirements
```

---

## Drug Discovery Workflow

### Lead Optimization

```python
# 1. Start with hit compound
hit_smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin

# 2. Calculate properties
mol = Chem.MolFromSmiles(hit_smiles)
mw = Descriptors.MolWt(mol)
logp = Descriptors.MolLogP(mol)

# 3. Generate analogs
from rdkit.Chem import rdFMCS

# 4. Filter by drug-likeness
from rdkit.Chem import FilterCatalog

def filter_drug_like(mols):
    params = FilterCatalog.FilterCatalogParams()
    params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS)
    catalog = FilterCatalog.FilterCatalog(params)
    
    return [m for m in mols if not catalog.HasMatch(m)]

# 5. Score by predicted activity
# Use trained model or docking

# 6. Check availability
# Query ZINC/PubChem for suppliers
```

---

## Key Packages Summary

| Package | Install | Use Case |
|---------|---------|----------|
| rdkit | `uv pip install rdkit` | Molecular manipulation, descriptors |
| deepchem | `uv pip install deepchem` | ML for chemistry |
| datamol | `uv pip install datamol` | High-level molecular operations |
| molfeat | `uv pip install molfeat` | Molecular embeddings |
| vina | `uv pip install vina` | Molecular docking |
