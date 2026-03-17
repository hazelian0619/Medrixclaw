#!/usr/bin/env python3
"""
Fetch AlphaFold structure for a protein.

Usage:
    python fetch_alphafold.py P00533 --output EGFR.pdb
    python fetch_alphafold.py P00533 --info
"""

import argparse
import json
import requests

def get_prediction_info(uniprot_id):
    """Get AlphaFold prediction info."""
    url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def download_pdb(uniprot_id, output_path=None):
    """Download AlphaFold PDB file."""
    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-model_v4.pdb"
    response = requests.get(url)
    response.raise_for_status()
    
    if output_path:
        with open(output_path, "w") as f:
            f.write(response.text)
        return output_path
    return response.text

def download_pae(uniprot_id, output_path=None):
    """Download predicted aligned error (PAE) plot data."""
    url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot_id}-F1-predicted_aligned_error_v4.json"
    response = requests.get(url)
    response.raise_for_status()
    
    if output_path:
        with open(output_path, "w") as f:
            json.dump(response.json(), f)
        return output_path
    return response.json()

def main():
    parser = argparse.ArgumentParser(description="Fetch AlphaFold structure")
    parser.add_argument("uniprot_id", help="UniProt accession (e.g., P00533)")
    parser.add_argument("--output", "-o", help="Output PDB file")
    parser.add_argument("--info", action="store_true", help="Show prediction info")
    parser.add_argument("--pae", help="Output PAE JSON file")
    args = parser.parse_args()
    
    uniprot_id = args.uniprot_id.upper()
    
    # Get info
    try:
        info = get_prediction_info(uniprot_id)
        
        if args.info:
            print(f"UniProt ID: {uniprot_id}")
            print(f"Gene: {info.get('gene', 'N/A')}")
            print(f"Organism: {info.get('organismScientificName', 'N/A')}")
            print(f"UniProt URL: {info.get('uniprotUrl', 'N/A')}")
            print(f"PDB URL: {info.get('pdbUrl', 'N/A')}")
            return
        
        # Download PDB
        output_path = args.output or f"{uniprot_id}.pdb"
        print(f"Downloading AlphaFold structure for {uniprot_id}...")
        download_pdb(uniprot_id, output_path)
        print(f"Saved to {output_path}")
        
        # Download PAE
        if args.pae:
            print(f"Downloading PAE data...")
            download_pae(uniprot_id, args.pae)
            print(f"Saved to {args.pae}")
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"No AlphaFold structure found for {uniprot_id}")
        else:
            raise

if __name__ == "__main__":
    main()
