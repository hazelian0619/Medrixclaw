# Scientific Databases Reference

Comprehensive guide for accessing 250+ scientific databases for genomics, chemistry, clinical research, and more.

## Table of Contents

1. [Literature Databases](#literature-databases)
2. [Protein Databases](#protein-databases)
3. [Chemical Databases](#chemical-databases)
4. [Genomic Databases](#genomic-databases)
5. [Clinical Databases](#clinical-databases)
6. [Pathway Databases](#pathway-databases)
7. [Financial & Economic Databases](#financial--economic-databases)

---

## Literature Databases

### PubMed (via BioPython)

```python
from Bio import Entrez
Entrez.email = "your_email@example.com"

def search_pubmed(query, max_results=100):
    """Search PubMed for articles"""
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    results = Entrez.read(handle)
    handle.close()
    return results["IdList"]

def fetch_abstracts(pmids):
    """Fetch abstracts for PMIDs"""
    handle = Entrez.efetch(db="pubmed", id=pmids, rettype="abstract", retmode="text")
    return handle.read()

def fetch_metadata(pmids):
    """Fetch article metadata"""
    handle = Entrez.efetch(db="pubmed", id=pmids, rettype="medline", retmode="text")
    # Parse MEDLINE format
    return handle.read()

# Example
ids = search_pubmed("EGFR lung cancer treatment", max_results=20)
abstracts = fetch_abstracts(ids)
```

### OpenAlex

```python
import requests

def search_openalex(query, per_page=50):
    """Search OpenAlex for scholarly works"""
    url = "https://api.openalex.org/works"
    params = {"search": query, "per_page": per_page}
    response = requests.get(url, params=params)
    return response.json()

def get_author_works(orcid):
    """Get works by author ORCID"""
    url = f"https://api.openalex.org/authors/orcid:{orcid}"
    response = requests.get(url)
    return response.json()

def get_journal_metrics(issn):
    """Get journal metrics"""
    url = f"https://api.openalex.org/sources/issn:{issn}"
    response = requests.get(url)
    return response.json()
```

### bioRxiv

```python
import requests

def get_biorxiv_doi(doi):
    """Get bioRxiv paper details"""
    url = f"https://api.biorxiv.org/details/biorxiv/{doi}"
    response = requests.get(url)
    return response.json()

def get_biorxiv_by_date(interval):
    """Get papers published in interval"""
    # Format: YYYY-MM-DD/YYYY-MM-DD
    url = f"https://api.biorxiv.org/details/biorxiv/{interval}"
    response = requests.get(url)
    return response.json()
```

---

## Protein Databases

### UniProt

```python
import requests

def get_uniprot_entry(accession):
    """Get UniProt entry by accession"""
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.json"
    response = requests.get(url)
    return response.json()

def search_uniprot(query, size=25):
    """Search UniProt"""
    url = "https://rest.uniprot.org/uniprotkb/search"
    params = {"query": query, "size": size, "format": "json"}
    response = requests.get(url, params=params)
    return response.json()

def get_sequence(accession):
    """Get protein sequence"""
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.fasta"
    response = requests.get(url)
    return response.text

# Example: Get EGFR protein
entry = get_uniprot_entry("P00533")
sequence = get_sequence("P00533")
```

### PDB (Protein Data Bank)

```python
from Bio import PDB
import requests

def fetch_pdb(pdb_id):
    """Fetch PDB file"""
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    response = requests.get(url)
    return response.text

def parse_pdb(pdb_content):
    """Parse PDB structure"""
    parser = PDB.PDBParser()
    import io
    structure = parser.get_structure("protein", io.StringIO(pdb_content))
    return structure

def get_pdb_info(pdb_id):
    """Get PDB metadata"""
    url = f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"
    response = requests.get(url)
    return response.json()

# Example
pdb_content = fetch_pdb("1M17")  # EGFR kinase domain
structure = parse_pdb(pdb_content)
```

### AlphaFold DB

```python
import requests

def get_alphafold_prediction(uniprot_id):
    """Get AlphaFold prediction for UniProt ID"""
    url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
    response = requests.get(url)
    return response.json()

def download_alphafold_pdb(uniprot_id):
    """Download AlphaFold PDB file"""
    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"
    response = requests.get(url)
    return response.text

# Example: Get EGFR AlphaFold structure
prediction = get_alphafold_prediction("P00533")
pdb_content = download_alphafold_pdb("P00533")
```

### InterPro

```python
import requests

def get_interpro_entry(entry_id):
    """Get InterPro entry"""
    url = f"https://www.ebi.ac.uk/interpro/api/entry/interpro/{entry_id}"
    response = requests.get(url)
    return response.json()

def search_interpro(protein_accession):
    """Get InterPro domains for protein"""
    url = f"https://www.ebi.ac.uk/interpro/api/protein/uniprot/{protein_accession}"
    response = requests.get(url)
    return response.json()
```

---

## Chemical Databases

### ChEMBL

```python
import requests

BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

def search_chembl_molecule(query):
    """Search ChEMBL for molecules"""
    url = f"{BASE_URL}/molecule/search"
    params = {"q": query, "format": "json"}
    response = requests.get(url, params=params)
    return response.json()

def get_chembl_molecule(chembl_id):
    """Get molecule details"""
    url = f"{BASE_URL}/molecule/{chembl_id}.json"
    response = requests.get(url)
    return response.json()

def get_target_activities(target_chembl_id, standard_type="IC50"):
    """Get activities for a target"""
    url = f"{BASE_URL}/activity.json"
    params = {
        "target_chembl_id": target_chembl_id,
        "standard_type": standard_type,
        "format": "json"
    }
    response = requests.get(url, params=params)
    return response.json()

# Example: Get EGFR inhibitors
activities = get_target_activities("CHEMBL203", "IC50")
```

### PubChem

```python
import requests

def search_pubchem_by_name(name):
    """Search PubChem by compound name"""
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IUPACName,IsomericSMILES,MolecularWeight/JSON"
    response = requests.get(url)
    return response.json()

def search_pubchem_by_smiles(smiles):
    """Search PubChem by SMILES"""
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastidentity/smiles/property/IsomericSMILES,MolecularFormula/JSON"
    response = requests.post(url, data={"smiles": smiles})
    return response.json()

def get_pubchem_bioassays(cid):
    """Get bioassays for compound"""
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/xrefs/AssayName/JSON"
    response = requests.get(url)
    return response.json()

# Example
compound = search_pubchem_by_name("aspirin")
```

### ZINC

```python
import requests

def search_zinc(smiles=None, properties=None):
    """Search ZINC database"""
    # ZINC20 API
    url = "https://zinc20.docking.org/substances.json"
    params = {}
    if smiles:
        params["smiles"] = smiles
    response = requests.get(url, params=params)
    return response.json()

def get_zinc_catalog():
    """Get purchasable compound catalogs"""
    url = "https://zinc20.docking.org/catalogs.json"
    response = requests.get(url)
    return response.json()
```

### DrugBank

```python
# Requires license

import xml.etree.ElementTree as ET

def parse_drugbank(xml_file):
    """Parse DrugBank XML"""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    ns = {"db": "http://www.drugbank.ca"}
    
    drugs = []
    for drug in root.findall("db:drug", ns):
        name = drug.find("db:name", ns).text
        indication = drug.find("db:indication", ns).text
        drugs.append({"name": name, "indication": indication})
    
    return drugs
```

---

## Genomic Databases

### Ensembl

```python
import requests

BASE_URL = "https://rest.ensembl.org"

def get_ensembl_gene(gene_id):
    """Get Ensembl gene info"""
    url = f"{BASE_URL}/lookup/id/{gene_id}?expand=1"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()

def get_ensembl_sequence(region, species="human"):
    """Get genomic sequence"""
    url = f"{BASE_URL}/sequence/region/{species}/{region}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()

def get_ensembl_variants(gene_id):
    """Get variants in gene"""
    url = f"{BASE_URL}/overlap/id/{gene_id}?feature=variation"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    return response.json()

# Example
gene = get_ensembl_gene("ENSG00000146648")  # EGFR
sequence = get_ensembl_sequence("7:55019021-55211628")
```

### NCBI Gene

```python
from Bio import Entrez
Entrez.email = "your_email@example.com"

def get_gene_info(gene_id):
    """Get NCBI Gene info"""
    handle = Entrez.efetch(db="gene", id=gene_id, rettype="xml")
    record = Entrez.read(handle)
    return record

def search_gene(gene_symbol, organism="Homo sapiens"):
    """Search for gene"""
    query = f"{gene_symbol}[Gene Name] AND {organism}[Organism]"
    handle = Entrez.esearch(db="gene", term=query)
    results = Entrez.read(handle)
    return results["IdList"]

# Example
gene_ids = search_gene("EGFR")
gene_info = get_gene_info(gene_ids[0])
```

### GEO (Gene Expression Omnibus)

```python
from Bio import Geo
import GEOparse

# Using GEOparse
# uv pip install GEOparse

def get_geo_series(gse_id):
    """Get GEO series"""
    gse = GEOparse.get_GEO(geo=gse_id, destdir="./")
    return gse

def get_geo_sample(gsm_id):
    """Get GEO sample"""
    gsm = GEOparse.get_GEO(geo=gsm_id, destdir="./")
    return gsm

# Example
gse = get_geo_series("GSE12345")
print(gse.metadata)
```

### GTEx

```python
import requests

def get_gtex_expression(gene_id):
    """Get GTEx expression data"""
    url = f"https://gtexportal.org/api/v2/expression/gene/{gene_id}"
    response = requests.get(url)
    return response.json()

def get_gtex_eqtls(gene_id):
    """Get eQTLs for gene"""
    url = f"https://gtexportal.org/api/v2/association/gene/{gene_id}"
    response = requests.get(url)
    return response.json()
```

### gnomAD

```python
import requests

def get_gnomad_gene(gene_symbol):
    """Get gnomAD gene constraints"""
    url = f"https://gnomad.broadinstitute.org/api/gene/{gene_symbol}"
    response = requests.get(url)
    return response.json()

def get_gnomad_variant(variant_id):
    """Get gnomAD variant"""
    url = f"https://gnomad.broadinstitute.org/api/variant/{variant_id}"
    response = requests.get(url)
    return response.json()
```

---

## Clinical Databases

### ClinicalTrials.gov

```python
import requests

def search_clinical_trials(query, max_results=100):
    """Search clinical trials"""
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": query,
        "pageSize": max_results,
        "format": "json"
    }
    response = requests.get(url, params=params)
    return response.json()

def get_trial(nct_id):
    """Get trial by NCT ID"""
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    params = {"format": "json"}
    response = requests.get(url, params=params)
    return response.json()
```

### ClinVar

```python
import requests

def search_clinvar(gene):
    """Search ClinVar for gene"""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "clinvar",
        "term": f"{gene}[gene]",
        "retmode": "json"
    }
    response = requests.get(url, params=params)
    return response.json()
```

---

## Pathway Databases

### KEGG

```python
import requests

def get_kegg_pathway(pathway_id):
    """Get KEGG pathway"""
    url = f"https://rest.kegg.jp/get/{pathway_id}"
    response = requests.get(url)
    return response.text

def get_kegg_genes(pathway_id):
    """Get genes in pathway"""
    url = f"https://rest.kegg.jp/link/genes/{pathway_id}"
    response = requests.get(url)
    return response.text

# Example
pathway = get_kegg_pathway("hsa04010")  # MAPK signaling
```

### Reactome

```python
import requests

def get_reactome_pathway(pathway_id):
    """Get Reactome pathway"""
    url = f"https://reactome.org/ContentService/data/query/{pathway_id}"
    response = requests.get(url)
    return response.json()

def get_reactome_participants(pathway_id):
    """Get participants in pathway"""
    url = f"https://reactome.org/ContentService/data/query/{pathway_id}/participants"
    response = requests.get(url)
    return response.json()
```

### STRING

```python
import requests

def get_string_interactions(proteins, species=9606):
    """Get protein interactions from STRING"""
    url = "https://string-db.org/api/json/network"
    params = {
        "identifiers": "\r".join(proteins),
        "species": species
    }
    response = requests.get(url, params=params)
    return response.json()
```

---

## Financial & Economic Databases

### FRED

```python
import requests

def get_fred_series(series_id, api_key):
    """Get FRED economic data"""
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json"
    }
    response = requests.get(url, params=params)
    return response.json()

# Common series: GDP, UNRATE, CPIAUCSL
```

### Alpha Vantage

```python
import requests

def get_stock_data(symbol, api_key):
    """Get stock data from Alpha Vantage"""
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key
    }
    response = requests.get(url, params=params)
    return response.json()
```

---

## Key Multi-Database Packages

| Package | Databases | Install |
|---------|-----------|---------|
| BioPython | NCBI (38 dbs), GEO, PDB | `uv pip install biopython` |
| gget | 20+ genomics dbs | `uv pip install gget` |
| BioServices | 40+ bioinformatics services | `uv pip install bioservices` |
