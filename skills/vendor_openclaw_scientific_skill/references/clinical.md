# Clinical Research & Precision Medicine Reference

Comprehensive guide for clinical trials, variant interpretation, pharmacogenomics, and precision medicine workflows.

## Table of Contents

1. [Clinical Trials](#clinical-trials)
2. [Variant Interpretation](#variant-interpretation)
3. [Cancer Genomics](#cancer-genomics)
4. [Pharmacogenomics](#pharmacogenomics)
5. [Clinical Documentation](#clinical-documentation)

---

## Clinical Trials

### ClinicalTrials.gov API

```python
import requests

def search_clinical_trials(condition, location=None, status=None):
    """Search ClinicalTrials.gov for trials"""
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": condition,
        "format": "json",
        "pageSize": 100
    }
    
    if location:
        params["query.locn"] = location
    if status:
        params["filter.overallStatus"] = status
    
    response = requests.get(base_url, params=params)
    return response.json()

def get_trial_details(nct_id):
    """Get details for a specific trial"""
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    params = {"format": "json"}
    response = requests.get(url, params=params)
    return response.json()

# Example: Find lung cancer trials
results = search_clinical_trials("lung cancer", status="RECRUITING")

# Parse eligibility criteria
def parse_eligibility(study):
    protocol = study.get("protocolSection", {})
    eligibility = protocol.get("eligibilityModule", {})
    return {
        "inclusion": eligibility.get("eligibilityCriteria", ""),
        "min_age": eligibility.get("minimumAge", ""),
        "max_age": eligibility.get("maximumAge", ""),
        "gender": eligibility.get("gender", ""),
        "healthy_volunteers": eligibility.get("healthyVolunteers", False)
    }
```

### Trial Matching

```python
def match_patient_to_trials(patient_profile, trials):
    """Match patient profile to clinical trials"""
    matches = []
    
    for trial in trials:
        eligibility = parse_eligibility(trial)
        
        # Check age
        patient_age = patient_profile.get("age")
        min_age = parse_age(eligibility["min_age"])
        max_age = parse_age(eligibility["max_age"])
        
        if min_age and patient_age < min_age:
            continue
        if max_age and patient_age > max_age:
            continue
        
        # Check gender
        if eligibility["gender"] not in ["ALL", patient_profile.get("gender")]:
            continue
        
        matches.append(trial)
    
    return matches

def parse_age(age_str):
    """Parse age string to years"""
    if not age_str:
        return None
    # "18 Years" -> 18
    import re
    match = re.search(r'(\d+)', age_str)
    return int(match.group(1)) if match else None
```

---

## Variant Interpretation

### ClinVar Query

```python
import requests

def query_clinvar_variant(gene, variant=None):
    """Query ClinVar for variant pathogenicity"""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "clinvar",
        "term": f"{gene}[gene]",
        "retmode": "json",
        "retmax": 100
    }
    response = requests.get(url, params=params)
    return response.json()

def get_clinvar_assertion(rcv_id):
    """Get clinical assertion details"""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "clinvar",
        "id": rcv_id,
        "rettype": "vcv"
    }
    response = requests.get(url, params=params)
    return response.text

# Pathogenicity interpretation
PATHOGENICITY_SCALE = {
    "pathogenic": 5,
    "likely pathogenic": 4,
    "uncertain significance": 3,
    "likely benign": 2,
    "benign": 1
}

def interpret_variant(clinvar_result):
    """Extract pathogenicity from ClinVar result"""
    # Parse VCV record
    # Return interpretation with evidence level
    pass
```

### ACMG Classification

```python
# ACMG/AMP variant classification criteria

ACMG_CRITERIA = {
    # Pathogenic (very strong)
    "PVS1": "Null variant in gene where LOF is a known mechanism",
    # Pathogenic (strong)
    "PS1": "Same amino acid change as established pathogenic variant",
    "PS2": "De novo in patient with confirmed paternity/maternity",
    "PS3": "Well-established functional studies show deleterious effect",
    "PS4": "Prevalence in affected significantly increased vs controls",
    # Pathogenic (moderate)
    "PM1": "Located in mutational hot spot or functional domain",
    "PM2": "Absent from population databases",
    "PM3": "Detected in trans with pathogenic variant",
    "PM4": "Protein length change in non-repeat region",
    "PM5": "Novel missense change at position of known pathogenic",
    "PM6": "Assumed de novo without confirmation",
    # Pathogenic (supporting)
    "PP1": "Cosegregation with disease in family",
    "PP2": "Missense in gene with low benign missense rate",
    "PP3": "Multiple computational tools predict deleterious",
    "PP4": "Phenotype specific to gene",
    "PP5": "Reputable source reports pathogenic",
    # Benign (stand-alone)
    "BA1": "Allele frequency > 5%",
    # Benign (strong)
    "BS1": "Allele frequency greater than expected",
    "BS2": "Observed in healthy adult for recessive disorder",
    "BS3": "Functional studies show no deleterious effect",
    "BS4": "Lack of segregation in family",
    # Benign (supporting)
    "BP1": "Missense in gene where only truncating causes disease",
    "BP2": "Observed in trans or cis with pathogenic variant",
    "BP3": "In-frame indel in repeat region",
    "BP4": "Multiple computational tools predict benign",
    "BP5": "Variant found with alternate cause",
    "BP6": "Reputable source reports benign",
    "BP7": "Synonymous with no splice impact predicted"
}

def classify_variant_acmg(criteria_met):
    """Apply ACMG rules to classify variant"""
    # Count criteria by strength
    # Apply combining rules
    # Return classification
    pass
```

---

## Cancer Genomics

### cBioPortal API

```python
import requests

def get_cbioportal_studies():
    """List all cBioPortal cancer studies"""
    url = "https://www.cbioportal.org/api/studies"
    response = requests.get(url)
    return response.json()

def get_molecular_profile(study_id, gene_list):
    """Get molecular data for genes in a study"""
    url = f"https://www.cbioportal.org/api/molecular-profiles/{study_id}_mutations/mutations/fetch"
    params = {"geneList": ",".join(gene_list)}
    response = requests.post(url, json={"geneList": gene_list})
    return response.json()

def get_clinical_data(study_id):
    """Get clinical data for a study"""
    url = f"https://www.cbioportal.org/api/studies/{study_id}/clinical-data"
    response = requests.get(url)
    return response.json()

# Example: Get EGFR mutations in lung cancer
study = "nsclc_tcga_broad_2016"
mutations = get_molecular_profile(study, ["EGFR", "KRAS", "TP53"])
```

### COSMIC Query

```python
import requests

def query_cosmic_gene(gene_name, api_key):
    """Query COSMIC for gene mutations"""
    url = f"https://cancer.sanger.ac.uk/api/v1/genes/{gene_name}/mutations"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    return response.json()

def get_cancer_hotspots(protein_id):
    """Get mutation hotspots from cancerhotspots.org"""
    url = f"https://www.cancerhotspots.org/api/hotspots/{protein_id}"
    response = requests.get(url)
    return response.json()
```

### DepMap (Cancer Dependencies)

```python
import pandas as pd

def load_depmap_data():
    """Load DepMap CRISPR and RNAi dependency data"""
    # Download from: https://depmap.org/portal/
    # Achilles gene effect scores
    # CERES scores for CRISPR
    pass

def find_gene_dependencies(gene, threshold=-1):
    """Find cell lines dependent on a gene"""
    # Load DepMap data
    # Filter by threshold
    # Return cell lines
    pass
```

---

## Pharmacogenomics

### ClinPGx

```python
def query_clinpgx(drug=None, gene=None):
    """Query ClinPGx for pharmacogenomic guidelines"""
    # CPIC guidelines
    # DPWG guidelines
    # Drug-gene interactions
    pass

PHARMACOGENOMIC_GENES = [
    "CYP2D6", "CYP2C19", "CYP2C9", "CYP3A5",
    "SLCO1B1", "TPMT", "DPYD", "UGT1A1",
    "G6PD", "HLA-B", "NUDT15", "IFNL3"
]

def get_cpic_guidelines(drug_name):
    """Get CPIC guidelines for a drug"""
    url = f"https://api.cpicpgx.org/v1/drug/{drug_name}"
    response = requests.get(url)
    return response.json()

def interpret_genotype(gene, genotype):
    """Interpret genotype for drug response"""
    # Map genotype to phenotype
    # Get dosing recommendations
    pass
```

### FDA Drug Labels

```python
def get_fda_pharmacogenomic_labels(drug_name):
    """Get FDA pharmacogenomic biomarker information"""
    # Table of Pharmacogenomic Biomarkers in Drug Labels
    # https://www.fda.gov/drugs/science-and-research-drugs/table-pharmacogenomic-biomarkers-drug-labels
    pass
```

---

## Clinical Documentation

### Clinical Report Structure

```markdown
# Clinical Variant Report

## Patient Information
- Patient ID: [ID]
- Indication: [Reason for testing]
- Sample Type: [Blood/Saliva/Tissue]

## Variants Identified

### Variant 1: [GENE] c.[DNA] p.[Protein]
- **Classification**: Pathogenic/Likely Pathogenic/VUS/Likely Benign/Benign
- **Evidence**:
  - ClinVar: [RCV ID]
  - Literature: [PMID]
  - ACMG Criteria: [PVS1, PS3, etc.]
- **Clinical Significance**: [Disease association]

### Variant 2: ...

## Recommendations
- [Clinical recommendations based on findings]

## Limitations
- [Test limitations]

## References
1. [Reference list]
```

### Treatment Plan Template

```python
def generate_treatment_plan(patient_data, variant_results):
    """Generate personalized treatment plan"""
    plan = {
        "diagnosis": patient_data.get("diagnosis"),
        "molecular_findings": [],
        "treatment_recommendations": [],
        "clinical_trials": [],
        "surveillance": []
    }
    
    # Process variants
    for variant in variant_results:
        if variant["classification"] in ["pathogenic", "likely pathogenic"]:
            plan["molecular_findings"].append({
                "gene": variant["gene"],
                "variant": variant["hgvs"],
                "significance": variant["significance"]
            })
            
            # Add treatment recommendations
            # Check for targeted therapies
            # Search clinical trials
    
    return plan
```

---

## Key Databases Summary

| Database | Content | Access |
|----------|---------|--------|
| ClinicalTrials.gov | Clinical trials | REST API |
| ClinVar | Variant pathogenicity | NCBI E-utilities |
| COSMIC | Cancer mutations | REST API (key required) |
| cBioPortal | Cancer genomics | REST API |
| DepMap | Cancer dependencies | Download |
| ClinPGx | Pharmacogenomics | API |
| CPIC | Drug guidelines | API |
| FDA | Drug labels | Web |
