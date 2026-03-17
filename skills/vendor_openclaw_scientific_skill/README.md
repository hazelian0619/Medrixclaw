<div align="center">

# 🔬 OpenClaw Scientific Skill

**A comprehensive AI-powered scientific research toolkit for OpenClaw**

[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-blue?style=for-the-badge)](https://github.com/openclaw/openclaw)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Skills](https://img.shields.io/badge/Skills-8_Domains-purple?style=for-the-badge)](#features)

*Transform your AI assistant into a scientific research powerhouse*

</div>

---

## ✨ Features

### 🧬 Bioinformatics & Genomics
- Sequence analysis with BioPython
- Single-cell RNA-seq with Scanpy
- Variant annotation and interpretation
- Phylogenetic analysis

### 🧪 Cheminformatics & Drug Discovery
- Molecular manipulation with RDKit
- Virtual screening and ADMET prediction
- Molecular docking workflows
- Chemical database access (ChEMBL, PubChem, ZINC)

### 🏥 Clinical Research & Precision Medicine
- ClinicalTrials.gov integration
- Variant interpretation (ClinVar, COSMIC)
- Pharmacogenomics workflows
- Cancer genomics (cBioPortal, DepMap)

### 🤖 Machine Learning & AI
- Deep learning with PyTorch Lightning
- Time series forecasting with TimesFM
- Bayesian methods with PyMC
- Model interpretability with SHAP

### 📚 250+ Scientific Databases
- Literature: PubMed, OpenAlex, bioRxiv
- Proteins: UniProt, PDB, AlphaFold DB
- Chemicals: ChEMBL, PubChem, DrugBank
- Clinical: ClinVar, COSMIC, ClinicalTrials.gov

### 📊 Scientific Visualization & Publishing
- Publication-quality figures
- LaTeX document generation
- Presentation slides
- Citation management

### ⚛️ Physics & Quantum Computing
- Astronomical data analysis (Astropy)
- Quantum computing (Qiskit, PennyLane)
- Symbolic mathematics (SymPy)

### ⚙️ Engineering & Optimization
- Multi-objective optimization (PyMOO)
- Metabolic modeling (COBRApy)
- Materials science (Pymatgen)

---

## 🚀 Quick Start

### Installation

```bash
# The skill is automatically loaded by OpenClaw
# Just copy to your skills directory
cp -r scientific ~/.openclaw/skills/
```

### Example Usage

**Single-cell RNA-seq Analysis:**
```python
import scanpy as sc

# Load and analyze
adata = sc.read_10x_mtx('./data/')
sc.pp.filter_cells(adata, min_genes=200)
sc.tl.pca(adata)
sc.tl.umap(adata)
sc.tl.leiden(adata)
sc.pl.umap(adata, color='leiden')
```

**Query PubMed:**
```python
from Bio import Entrez
Entrez.email = "your@email.com"

handle = Entrez.esearch(db="pubmed", term="EGFR lung cancer", retmax=20)
results = Entrez.read(handle)
```

**Fetch AlphaFold Structure:**
```bash
python scripts/fetch_alphafold.py P00533 --output EGFR.pdb
```

---

## 📁 Structure

```
scientific/
├── SKILL.md                    # Main skill definition
├── references/
│   ├── bioinformatics.md       # Genomics, single-cell, phylogenetics
│   ├── cheminformatics.md      # Drug discovery, molecular modeling
│   ├── clinical.md             # Clinical trials, variant interpretation
│   ├── ml.md                   # Deep learning, time series, Bayesian
│   ├── databases.md            # 250+ database access patterns
│   ├── documents.md            # Visualization, LaTeX, publishing
│   ├── physics.md              # Astronomy, quantum computing
│   └── engineering.md          # Optimization, metabolic modeling
└── scripts/
    ├── install_deps.py         # Install domain-specific dependencies
    ├── query_pubmed.py         # PubMed search utility
    └── fetch_alphafold.py      # AlphaFold structure downloader
```

---

## 🔧 Dependencies

Install dependencies by domain:

```bash
# Core scientific stack
pip install numpy scipy pandas matplotlib seaborn

# Bioinformatics
pip install biopython scanpy pysam

# Cheminformatics
pip install rdkit deepchem

# Machine Learning
pip install torch pytorch-lightning scikit-learn

# Or use the provided script
python scripts/install_deps.py --domain bioinformatics
python scripts/install_deps.py --domain ml
python scripts/install_deps.py --domain all
```

---

## 🗃️ Database Coverage

| Category | Databases |
|----------|-----------|
| **Literature** | PubMed, OpenAlex, bioRxiv, CrossRef |
| **Proteins** | UniProt, PDB, AlphaFold DB, InterPro |
| **Chemicals** | ChEMBL, PubChem, DrugBank, ZINC, BindingDB |
| **Genomics** | Ensembl, NCBI Gene, GEO, GTEx, gnomAD |
| **Clinical** | ClinVar, COSMIC, ClinicalTrials.gov, ClinPGx |
| **Pathways** | KEGG, Reactome, STRING |
| **Cancer** | cBioPortal, DepMap |
| **Economic** | FRED, Alpha Vantage |

---

## 📖 Documentation

- [Bioinformatics Reference](references/bioinformatics.md) - Detailed genomics workflows
- [Cheminformatics Reference](references/cheminformatics.md) - Drug discovery pipelines
- [Clinical Reference](references/clinical.md) - Precision medicine workflows
- [ML Reference](references/ml.md) - Machine learning guides
- [Databases Reference](references/databases.md) - API patterns for 250+ databases

---

## 🤝 Comparison with Claude Scientific Skills

| Feature | Claude Scientific Skills | OpenClaw Scientific Skill |
|---------|-------------------------|---------------------------|
| Format | Agent Skills standard | Agent Skills standard ✅ |
| Domains | 170+ skills | 8 comprehensive domains |
| Code Examples | ✅ | ✅ |
| Scripts | Limited | 3+ executable scripts |
| Database Access | 250+ | 250+ ✅ |
| License | MIT (varies) | MIT |

---

## 📝 Example Workflows

### Find EGFR Inhibitors
```
Query ChEMBL for EGFR inhibitors (IC50 < 50nM),
analyze SAR with RDKit, perform virtual screening
```

### Single-cell Analysis
```
Load 10X data with Scanpy, QC filtering,
PCA/UMAP, Leiden clustering, marker identification
```

### Variant Interpretation
```
Parse VCF, annotate with Ensembl VEP,
query ClinVar for pathogenicity,
check COSMIC for cancer mutations
```

---

## 📜 License

MIT License - Free for academic and commercial use.

---

## 🙏 Acknowledgments

**Inspired by** [Claude Scientific Skills](https://github.com/K-Dense-AI/claude-scientific-skills) by K-Dense.

This is an **independent implementation** with original code examples. See [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) for details.

Built on amazing open-source projects:
- [BioPython](https://biopython.org/)
- [Scanpy](https://scanpy.readthedocs.io/)
- [RDKit](https://www.rdkit.org/)
- [PyTorch](https://pytorch.org/)
- [scikit-learn](https://scikit-learn.org/)

---

<div align="center">

**Made with ❤️ for the scientific community**

[Report Bug](https://github.com/Zhaozilongxa/openclaw-scientific-skill/issues) · [Request Feature](https://github.com/Zhaozilongxa/openclaw-scientific-skill/issues) · [ClawHub](https://clawhub.com)

</div>
