#!/usr/bin/env python3
"""
Install scientific dependencies by domain.

Usage:
    python install_deps.py --domain bioinformatics
    python install_deps.py --domain ml
    python install_deps.py --domain all
"""

import argparse
import subprocess
import sys

DOMAINS = {
    "core": [
        "numpy", "scipy", "pandas", "matplotlib", "seaborn"
    ],
    "bioinformatics": [
        "biopython", "scanpy", "pysam", "gget", "pydeseq2", "scvelo"
    ],
    "cheminformatics": [
        "rdkit", "deepchem", "datamol", "molfeat"
    ],
    "ml": [
        "torch", "pytorch-lightning", "scikit-learn", "shap",
        "transformers", "stable-baselines3"
    ],
    "clinical": [
        "lifelines", "scikit-survival"
    ],
    "physics": [
        "astropy", "qiskit", "pennylane", "cirq", "sympy"
    ],
    "engineering": [
        "pymoo", "cobra", "pymatgen"
    ],
    "documents": [
        "pdfplumber", "python-docx", "pylatex", "python-pptx",
        "bibtexparser", "plotly"
    ],
    "visualization": [
        "plotly", "networkx", "umap-learn"
    ]
}

def install_packages(packages, use_uv=True):
    """Install packages using uv or pip."""
    cmd = ["uv", "pip", "install"] if use_uv else ["pip", "install"]
    cmd.extend(packages)
    
    print(f"Installing: {' '.join(packages)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    print(f"✓ Installed {len(packages)} packages")
    return True

def main():
    parser = argparse.ArgumentParser(description="Install scientific dependencies")
    parser.add_argument("--domain", "-d", required=True,
                       choices=list(DOMAINS.keys()) + ["all"],
                       help="Domain to install packages for")
    parser.add_argument("--use-pip", action="store_true",
                       help="Use pip instead of uv")
    args = parser.parse_args()
    
    use_uv = not args.use_pip
    
    if args.domain == "all":
        # Install core first
        all_packages = set()
        for domain, packages in DOMAINS.items():
            all_packages.update(packages)
        
        # Separate into batches
        packages = sorted(all_packages)
        for i in range(0, len(packages), 10):
            batch = packages[i:i+10]
            if not install_packages(batch, use_uv):
                sys.exit(1)
    else:
        packages = DOMAINS[args.domain]
        if not install_packages(packages, use_uv):
            sys.exit(1)
    
    print("\n✓ Installation complete!")

if __name__ == "__main__":
    main()
