#!/usr/bin/env python3
"""
PubMed search and fetch utility.

Usage:
    python query_pubmed.py "EGFR lung cancer" --max 20 --output results.json
"""

import argparse
import json
from Bio import Entrez

def search_pubmed(query, max_results=100, email=None):
    """Search PubMed for articles."""
    # NCBI requires email for API access
    if email:
        Entrez.email = email
    else:
        Entrez.email = "your_email@example.com"
        print("⚠️  Warning: Using placeholder email. Set --email for production use.")
    
    handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=max_results,
        usehistory="y"
    )
    results = Entrez.read(handle)
    handle.close()
    
    return results

def fetch_details(pmids):
    """Fetch details for PMIDs."""
    handle = Entrez.efetch(
        db="pubmed",
        id=pmids,
        rettype="medline",
        retmode="xml"
    )
    results = Entrez.read(handle)
    handle.close()
    
    return results

def parse_articles(records):
    """Parse article records."""
    articles = []
    
    for record in records["PubmedArticle"]:
        article = {
            "pmid": record["MedlineCitation"]["PMID"],
            "title": record["MedlineCitation"]["Article"]["ArticleTitle"],
            "authors": [],
            "journal": record["MedlineCitation"]["Article"]["Journal"]["Title"],
            "year": None,
            "abstract": None,
            "keywords": []
        }
        
        # Authors
        if "AuthorList" in record["MedlineCitation"]["Article"]:
            for author in record["MedlineCitation"]["Article"]["AuthorList"]:
                if "LastName" in author and "ForeName" in author:
                    article["authors"].append(f"{author['LastName']} {author['ForeName']}")
        
        # Year
        if "PubDate" in record["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]:
            pub_date = record["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["PubDate"]
            if "Year" in pub_date:
                article["year"] = pub_date["Year"]
        
        # Abstract
        if "Abstract" in record["MedlineCitation"]["Article"]:
            article["abstract"] = record["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][0]
        
        # Keywords
        if "KeywordList" in record["MedlineCitation"]:
            for kw_list in record["MedlineCitation"]["KeywordList"]:
                article["keywords"].extend(kw_list)
        
        articles.append(article)
    
    return articles

def main():
    parser = argparse.ArgumentParser(description="Search PubMed")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max", type=int, default=50, help="Max results")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--email", help="Email for NCBI")
    args = parser.parse_args()
    
    print(f"Searching PubMed for: {args.query}")
    
    # Search
    search_results = search_pubmed(args.query, args.max, args.email)
    pmids = search_results["IdList"]
    print(f"Found {search_results['Count']} results, fetching {len(pmids)}")
    
    # Fetch details
    records = fetch_details(pmids)
    articles = parse_articles(records)
    
    # Output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(articles, f, indent=2)
        print(f"Saved to {args.output}")
    else:
        for article in articles[:5]:
            print(f"\n{article['pmid']}: {article['title']}")
            print(f"  Authors: {', '.join(article['authors'][:3])}")
            print(f"  Journal: {article['journal']} ({article['year']})")

if __name__ == "__main__":
    main()
