# Bioinformatics & Genomics Reference

Comprehensive guide for genomic data analysis, single-cell RNA-seq, variant annotation, and phylogenetics.

## Table of Contents

1. [Sequence Analysis](#sequence-analysis)
2. [Single-Cell RNA-seq](#single-cell-rna-seq)
3. [Variant Analysis](#variant-analysis)
4. [Phylogenetics](#phylogenetics)
5. [Database Access](#database-access)

---

## Sequence Analysis

### BioPython Basics

```python
# uv pip install biopython

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import Entrez

# Parse FASTA/FASTQ
for record in SeqIO.parse("sequences.fasta", "fasta"):
    print(record.id, len(record.seq))

# Sequence operations
seq = Seq("ATGCGATCGATCG")
print(seq.complement())      # Complement strand
print(seq.translate())       # Translate to protein
print(seq.reverse_complement())  # Reverse complement

# BLAST search
from Bio.Blast import NCBIWWW
result = NCBIWWW.qblast("blastn", "nt", "ATGCGATCGATCG")
```

### NCBI Entrez (38 databases)

```python
from Bio import Entrez
Entrez.email = "your_email@example.com"

# List databases
handle = Entrez.einfo()
databases = Entrez.read(handle)
print(databases)  # pubmed, gene, protein, nucleotide, sra, gds, etc.

# Search
handle = Entrez.esearch(db="gene", term="EGFR AND Homo sapiens", retmax=10)
results = Entrez.read(handle)

# Fetch records
handle = Entrez.efetch(db="gene", id="1956", rettype="xml")
record = Entrez.read(handle)

# E-utilities workflow
search_handle = Entrez.esearch(db="pubmed", term="cancer", retmax=100)
ids = Entrez.read(search_handle)["IdList"]
fetch_handle = Entrez.efetch(db="pubmed", id=ids, rettype="abstract")
```

---

## Single-Cell RNA-seq

### Scanpy Workflow

```python
# uv pip install scanpy anndata scvi-tools

import scanpy as sc
import anndata as ad

# Load data
adata = sc.read_10x_mtx('./filtered_feature_bc_matrix/')
# Or from h5ad
adata = sc.read_h5ad('data.h5ad')

# Quality control
adata.var['mt'] = adata.var_names.str.startswith('MT-')
sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)

# Filtering
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)
adata = adata[adata.obs.pct_counts_mt < 20, :]  # Remove high MT cells

# Normalization
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# Feature selection
sc.pp.highly_variable_genes(adata, n_top_genes=2000, flavor='seurat_v3')

# Dimensionality reduction
sc.tl.pca(adata, n_comps=50)
sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)
sc.tl.umap(adata)

# Clustering
sc.tl.leiden(adata, resolution=0.5)

# Marker genes
sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')
sc.pl.rank_genes_groups(adata, n_genes=20)

# Visualization
sc.pl.umap(adata, color=['leiden', 'MT-ATP6'])
```

### scVelo (RNA Velocity)

```python
# uv pip install scvelo

import scvelo as scv

# Load loom files
adata = scv.read('data.loom', cache=True)

# Preprocess
scv.pp.filter_and_normalize(adata)
scv.pp.moments(adata)

# Velocity analysis
scv.tl.velocity(adata)
scv.tl.velocity_graph(adata)

# Visualization
scv.pl.velocity_embedding_stream(adata, basis='umap')
```

### Differential Expression

```python
# uv pip install pydeseq2

from pydeseq2 import DESeq2
import pandas as pd

# Create count matrix and metadata
counts = pd.DataFrame(...)  # genes x samples
metadata = pd.DataFrame(...)  # sample info

# Run DESeq2
deseq = DESeq2(counts=counts, metadata=metadata, design_factors='condition')
deseq.run_deseq()
results = deseq.get_results()
```

---

## Variant Analysis

### VCF Processing with pysam

```python
# uv pip install pysam

import pysam

# Open VCF
vcf = pysam.VariantFile("variants.vcf")

# Iterate variants
for record in vcf:
    print(record.chrom, record.pos, record.ref, record.alts)
    print(record.info)  # INFO fields
    print(record.samples)  # Sample genotypes

# Filter variants
filtered = [r for r in vcf if r.info.get('AF', [1])[0] < 0.01]
```

### Variant Annotation

```python
# Use Ensembl VEP API
import requests

def annotate_variant(chrom, pos, ref, alt):
    url = f"https://rest.ensembl.org/vep/human/region/{chrom}:{pos}+{ref}>{alt}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()
```

### ClinVar Query

```python
import requests

def query_clinvar(gene):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "clinvar",
        "term": f"{gene}[gene]",
        "retmax": 100,
        "retmode": "json"
    }
    response = requests.get(url, params=params)
    return response.json()
```

---

## Phylogenetics

### Multiple Sequence Alignment

```python
# uv pip install biopython

from Bio import AlignIO
from Bio.Align import MultipleSeqAlignment

# Parse alignment
alignment = AlignIO.read("aligned.fasta", "fasta")

# Calculate distance matrix
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
calculator = DistanceCalculator('identity')
dm = calculator.get_distance(alignment)

# Build tree
constructor = DistanceTreeConstructor()
tree = constructor.upgma(dm)

# Draw tree
from Bio import Phylo
Phylo.draw(tree)
```

### ETE Toolkit

```python
# uv pip install ete3

from ete3 import Tree

# Load tree
t = Tree("tree.nwk")

# Visualize
t.show()

# Annotate
for node in t.traverse():
    node.add_features(size=10)

# Compare trees
t1 = Tree("tree1.nwk")
t2 = Tree("tree2.nwk")
rf = t1.robinson_foulds(t2)
```

---

## Database Access

### NCBI Gene

```python
from Bio import Entrez
Entrez.email = "your_email@example.com"

def get_gene_info(gene_symbol):
    # Search for gene
    handle = Entrez.esearch(db="gene", term=f"{gene_symbol}[Gene Name] AND Homo sapiens[Organism]")
    ids = Entrez.read(handle)["IdList"]
    
    # Fetch details
    handle = Entrez.efetch(db="gene", id=ids[0], rettype="xml")
    record = Entrez.read(handle)
    return record
```

### Ensembl REST API

```python
import requests

def get_ensembl_gene(ensembl_id):
    url = f"https://rest.ensembl.org/lookup/id/{ensembl_id}?expand=1"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()

def get_sequence(region, species="human"):
    url = f"https://rest.ensembl.org/sequence/region/{species}/{region}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()
```

### GEO (Gene Expression Omnibus)

```python
from Bio import Geo

# Parse GEO SOFT file
handle = open("GSE12345_family.soft")
records = Geo.parse(handle)

# Or use GEOparse
# uv pip install GEOparse
import GEOparse

gsm = GEOparse.get_GEO(geo="GSM12345", destdir="./")
gse = GEOparse.get_GEO(geo="GSE12345", destdir="./")
```

### gget (20+ databases)

```python
# uv pip install gget

import gget

# Search genes
gget.search("EGFR", species="human")

# Get sequence
gget.sequence("ENSG00000146648")

# BLAST
gget.blast("ATGCGATCGATCG")

# Enrichr enrichment
gget.enrichr(["EGFR", "KRAS", "TP53"], database="GO_Biological_Process_2021")
```

---

## Key Packages Summary

| Package | Install | Use Case |
|---------|---------|----------|
| biopython | `uv pip install biopython` | Sequence analysis, NCBI access |
| scanpy | `uv pip install scanpy` | Single-cell RNA-seq |
| pysam | `uv pip install pysam` | VCF/BAM processing |
| gget | `uv pip install gget` | Multi-database access |
| pydeseq2 | `uv pip install pydeseq2` | Differential expression |
| scvelo | `uv pip install scvelo` | RNA velocity |
| ete3 | `uv pip install ete3` | Phylogenetics |
