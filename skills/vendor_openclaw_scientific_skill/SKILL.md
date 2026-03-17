---
name: scientific
description: |
  Comprehensive scientific research skills for bioinformatics, cheminformatics, clinical research, 
  machine learning, physics, engineering, and scientific communication. Use when: (1) analyzing 
  genomic/proteomic data, (2) molecular modeling and drug discovery, (3) clinical trials and 
  variant interpretation, (4) machine learning and data analysis, (5) scientific writing and 
  literature review, (6) working with scientific databases (PubMed, ChEMBL, UniProt, etc.), 
  (7) creating publication-quality figures and reports.
license: MIT
metadata:
  version: "1.0.0"
  author: "Zhaozilongxa"
  domains: "bioinformatics,cheminformatics,clinical,ml,physics,engineering,visualization"
---

# Scientific Research Skills

A comprehensive toolkit for AI-powered scientific research. This skill provides structured workflows,
database access patterns, and best practices across multiple scientific domains.

## Smoke Test

Note: this is a vendored, documentation-heavy skill library. It does not provide a single `run.py`
entrypoint under ScienceClaw's artifact bundle contract.

Minimal check:

```bash
python3 - <<'PY'
from pathlib import Path
p=Path('references')
print('ok' if p.exists() and p.is_dir() else 'missing')
PY
```

## Quick Start

```python
# Always use uv for package management
import subprocess
subprocess.run(["uv", "pip", "install", "package-name"])
```

## Core Domains

### 1. Bioinformatics & Genomics

**Sequence analysis, single-cell RNA-seq, variant annotation, phylogenetics**

- **BioPython**: `uv pip install biopython` — NCBI Entrez, sequence parsing, BLAST
- **Scanpy**: `uv pip install scanpy` — Single-cell RNA-seq analysis
- **pysam**: `uv pip install pysam` — VCF/BAM file processing
- **gget**: `uv pip install gget` — 20+ genomics databases

See [references/bioinformatics.md](references/bioinformatics.md) for detailed workflows.

### 2. Cheminformatics & Drug Discovery

**Molecular manipulation, virtual screening, ADMET prediction, docking**

- **RDKit**: `uv pip install rdkit` — Molecular fingerprints, descriptors, reactions
- **DeepChem**: `uv pip install deepchem` — Molecular ML models
- **DiffDock**: `uv pip install diffdock` — Molecular docking

See [references/cheminformatics.md](references/cheminformatics.md) for detailed workflows.

### 3. Clinical Research & Precision Medicine

**Clinical trials, variant interpretation, pharmacogenomics**

- **Key databases**: ClinVar, COSMIC, ClinicalTrials.gov, ClinPGx
- **cBioPortal**: Cancer genomics (400+ studies)
- **DepMap**: Cancer cell line dependencies

See [references/clinical.md](references/clinical.md) for detailed workflows.

### 4. Machine Learning & AI

**Deep learning, time series, Bayesian methods, optimization**

- **PyTorch Lightning**: `uv pip install pytorch-lightning`
- **scikit-learn**: `uv pip install scikit-learn`
- **TimesFM**: Zero-shot time series forecasting
- **SHAP**: Model interpretability

See [references/ml.md](references/ml.md) for detailed workflows.

### 5. Scientific Databases

Direct access to 250+ scientific databases:

| Database | Content | Access |
|----------|---------|--------|
| PubMed | Literature | BioPython Entrez |
| ChEMBL | Bioactivity | REST API |
| UniProt | Proteins | REST API |
| PDB | 3D structures | BioPython PDB |
| AlphaFold DB | Predicted structures | REST API |
| ClinicalTrials.gov | Trials | REST API |
| GEO | Expression data | BioPython GEO |

See [references/databases.md](references/databases.md) for API patterns.

### 6. Scientific Communication

**Writing, visualization, publishing**

- **Publication figures**: matplotlib, seaborn, plotly
- **LaTeX documents**: `uv pip install pylatex`
- **Document processing**: See [references/documents.md](references/documents.md)

## Common Workflows

### Gene Expression Analysis

```python
# Install dependencies
# uv pip install scanpy pydeseq2

import scanpy as sc

# Load and process
adata = sc.read_10x_mtx('./data/')
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, n_top_genes=2000)

# Dimensionality reduction
sc.tl.pca(adata, n_comps=50)
sc.pp.neighbors(adata)
sc.tl.umap(adata)
sc.tl.leiden(adata)

# Visualization
sc.pl.umap(adata, color=['leiden', 'gene_of_interest'])
```

### Molecular Property Prediction

```python
# uv pip install rdkit deepchem

from rdkit import Chem
from rdkit.Chem import Descriptors
import deepchem as dc

# Calculate molecular descriptors
mol = Chem.MolFromSmiles('CCO')
mw = Descriptors.MolWt(mol)
logp = Descriptors.MolLogP(mol)

# DeepChem for ML
featurizer = dc.feat.MolecularFeaturizer()
features = featurizer.featurize(['CCO', 'CCN'])
```

### Literature Search

```python
# uv pip install biopython

from Bio import Entrez
Entrez.email = "your_email@example.com"

# Search PubMed
handle = Entrez.esearch(db="pubmed", term="EGFR lung cancer", retmax=20)
results = Entrez.read(handle)
handle.close()

# Fetch abstracts
ids = results["IdList"]
handle = Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="text")
abstracts = handle.read()
```

### Protein Structure Analysis

```python
# uv pip install biopython requests

import requests
from Bio import PDB

# Fetch AlphaFold structure
uniprot_id = "P00533"  # EGFR
url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
response = requests.get(url)
# Download PDB file from returned URL

# Parse structure
parser = PDB.PDBParser()
structure = parser.get_structure("EGFR", "EGFR.pdb")
```

## Scripts

- `scripts/install_deps.py` — Install domain-specific dependencies
- `scripts/query_pubmed.py` — PubMed search utility
- `scripts/fetch_alphafold.py` — AlphaFold structure downloader
- `scripts/vcf_annotate.py` — VCF annotation workflow
- `scripts/sync_upstream.py` — Sync with upstream Claude Scientific Skills
- `scripts/trigger_sync.sh` — Trigger sync via OpenClaw subagent
- `scripts/daily_check.sh` — Daily automated update check (Beijing 08:00)

## Best Practices

1. **Use uv for dependencies**: Always prefer `uv pip install` over `pip install`
2. **Cache API responses**: Many databases have rate limits
3. **Batch operations**: Process data in batches for efficiency
4. **Document provenance**: Track data sources and transformations
5. **Reproducibility**: Use versioned dependencies, random seeds

## Environment Setup

```bash
# Core scientific stack
uv pip install numpy scipy pandas matplotlib seaborn

# Bioinformatics
uv pip install biopython scanpy pysam gget

# Cheminformatics
uv pip install rdkit deepchem

# ML/AI
uv pip install torch pytorch-lightning scikit-learn

# Visualization
uv pip install plotly networkx
```

## References

- [Bioinformatics](references/bioinformatics.md) — Genomics, single-cell, phylogenetics
- [Cheminformatics](references/cheminformatics.md) — Molecular modeling, drug discovery
- [Clinical](references/clinical.md) — Clinical trials, variant interpretation
- [Machine Learning](references/ml.md) — DL, time series, Bayesian methods
- [Databases](references/databases.md) — API patterns for 250+ databases
- [Documents](references/documents.md) — Scientific writing, figures, publishing
- [Physics](references/physics.md) — Astronomy, quantum computing, simulation
- [Engineering](references/engineering.md) — Optimization, systems modeling
