# Scientific Documents Reference

Guide for scientific writing, document processing, figures, and publishing.

## Table of Contents

1. [Document Processing](#document-processing)
2. [Scientific Visualization](#scientific-visualization)
3. [LaTeX](#latex)
4. [Presentations](#presentations)
5. [Citation Management](#citation-management)

---

## Document Processing

### PDF Processing

```python
# uv pip install pdfplumber PyPDF2

import pdfplumber

def extract_text(pdf_path):
    """Extract text from PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_tables(pdf_path):
    """Extract tables from PDF."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            tables.extend(page_tables)
    return tables
```

### DOCX Processing

```python
# uv pip install python-docx

from docx import Document

def read_docx(path):
    """Read DOCX file."""
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    tables = [[cell.text for cell in row.cells] for table in doc.tables for row in table.rows]
    return {"paragraphs": paragraphs, "tables": tables}

def create_docx(title, content, output_path):
    """Create DOCX document."""
    doc = Document()
    doc.add_heading(title, level=0)
    doc.add_paragraph(content)
    doc.save(output_path)
```

### Markdown Processing

```python
# uv pip install markdown

import markdown

def md_to_html(md_content):
    """Convert Markdown to HTML."""
    return markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

def extract_sections(md_content):
    """Extract sections from Markdown."""
    sections = []
    current_section = None
    current_content = []
    
    for line in md_content.split('\n'):
        if line.startswith('# '):
            if current_section:
                sections.append({'title': current_section, 'content': '\n'.join(current_content)})
            current_section = line[2:].strip()
            current_content = []
        else:
            current_content.append(line)
    
    if current_section:
        sections.append({'title': current_section, 'content': '\n'.join(current_content)})
    
    return sections
```

---

## Scientific Visualization

### Matplotlib

```python
# uv pip install matplotlib numpy

import matplotlib.pyplot as plt
import numpy as np

# Set publication style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['figure.figsize'] = (8, 6)
plt.rcParams['figure.dpi'] = 300

# Create figure
fig, ax = plt.subplots()
x = np.linspace(0, 10, 100)
ax.plot(x, np.sin(x), label='sin(x)')
ax.plot(x, np.cos(x), label='cos(x)')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_title('Trigonometric Functions')
ax.legend()
plt.savefig('figure.pdf', bbox_inches='tight')
```

### Seaborn

```python
# uv pip install seaborn

import seaborn as sns
import matplotlib.pyplot as plt

# Set style
sns.set_style("whitegrid")
sns.set_palette("deep")

# Heatmap
data = correlation_matrix
sns.heatmap(data, annot=True, cmap='coolwarm', center=0)
plt.savefig('heatmap.pdf')

# Boxplot
sns.boxplot(data=df, x='category', y='value')
plt.savefig('boxplot.pdf')

# Violin plot
sns.violinplot(data=df, x='category', y='value')
plt.savefig('violin.pdf')

# Pairplot
sns.pairplot(df, hue='category')
plt.savefig('pairplot.pdf')
```

### Plotly (Interactive)

```python
# uv pip install plotly

import plotly.express as px
import plotly.graph_objects as go

# Scatter plot
fig = px.scatter(df, x='x', y='y', color='category', hover_data=['label'])
fig.write_html('scatter.html')

# 3D plot
fig = px.scatter_3d(df, x='x', y='y', z='z', color='category')
fig.write_html('3d_scatter.html')

# Heatmap
fig = go.Figure(data=go.Heatmap(z=data, colorscale='Viridis'))
fig.write_html('heatmap.html')
```

### Network Visualization

```python
# uv pip install networkx matplotlib

import networkx as nx
import matplotlib.pyplot as plt

# Create network
G = nx.Graph()
G.add_edges_from([(1, 2), (1, 3), (2, 4), (3, 4), (4, 5)])

# Layout
pos = nx.spring_layout(G)

# Draw
plt.figure(figsize=(10, 8))
nx.draw(G, pos, with_labels=True, node_color='lightblue', 
        node_size=500, font_size=12, font_weight='bold')
plt.savefig('network.pdf')
```

---

## LaTeX

### Python to LaTeX

```python
# uv pip install pylatex

from pylatex import Document, Section, Subsection, Math, Figure, Table, Tabular

def create_latex_document():
    doc = Document('report')
    
    with doc.create(Section('Introduction')):
        doc.append('This is the introduction.')
        
        with doc.create(Subsection('Methods')):
            doc.append('Description of methods.')
            
            # Math
            doc.append(Math(data=['E = mc^2']))
            
            # Table
            with doc.create(Table(position='htbp')) as table:
                with table.create(Tabular('ccc')) as tabular:
                    tabular.add_hline()
                    tabular.add_row(['A', 'B', 'C'])
                    tabular.add_hline()
    
    doc.generate_pdf()
    doc.generate_tex()

create_latex_document()
```

### LaTeX Templates

```latex
% Article template
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{hyperref}

\title{Title}
\author{Author Name}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
Abstract text here.
\end{abstract}

\section{Introduction}
Introduction text.

\section{Methods}
Methods text.

\section{Results}
Results text with figure:
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\textwidth]{figure.pdf}
    \caption{Figure caption}
    \label{fig:example}
\end{figure}

\section{Discussion}
Discussion text.

\bibliographystyle{plain}
\bibliography{references}

\end{document}
```

---

## Presentations

### Beamer (LaTeX)

```latex
\documentclass{beamer}
\usetheme{Madrid}
\usecolortheme{default}

\title{Presentation Title}
\author{Author}
\date{\today}

\begin{document}

\begin{frame}
\titlepage
\end{frame}

\begin{frame}{Slide Title}
\begin{itemize}
    \item Point 1
    \item Point 2
    \item Point 3
\end{itemize}
\end{frame}

\begin{frame}{Figure}
\begin{center}
\includegraphics[width=0.8\textwidth]{figure.pdf}
\end{center}
\end{frame}

\end{document}
```

### PPTX (python-pptx)

```python
# uv pip install python-pptx

from pptx import Presentation
from pptx.util import Inches

def create_presentation():
    prs = Presentation()
    
    # Title slide
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Presentation Title"
    subtitle.text = "Subtitle"
    
    # Content slide
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    title.text = "Slide Title"
    
    # Add bullet points
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.text = "First point"
    p = tf.add_paragraph()
    p.text = "Second point"
    
    # Add image
    slide.shapes.add_picture('figure.png', Inches(1), Inches(2), width=Inches(5))
    
    prs.save('presentation.pptx')
```

---

## Citation Management

### BibTeX Processing

```python
# uv pip install bibtexparser

import bibtexparser

def parse_bibtex(bib_file):
    """Parse BibTeX file."""
    with open(bib_file) as f:
        bib_database = bibtexparser.load(f)
    return bib_database.entries

def search_citations(entries, query):
    """Search citations."""
    results = []
    for entry in entries:
        text = f"{entry.get('title', '')} {entry.get('author', '')} {entry.get('abstract', '')}"
        if query.lower() in text.lower():
            results.append(entry)
    return results

def format_citation(entry, style='apa'):
    """Format citation."""
    authors = entry.get('author', 'Unknown')
    year = entry.get('year', 'n.d.')
    title = entry.get('title', 'Untitled')
    journal = entry.get('journal', '')
    
    if style == 'apa':
        return f"{authors} ({year}). {title}. {journal}."
    elif style == 'mla':
        return f"{authors}. \"{title}.\" {journal}, {year}."
```

### CrossRef API

```python
import requests

def search_crossref(query, max_results=20):
    """Search CrossRef for works."""
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": max_results}
    response = requests.get(url, params=params)
    return response.json()

def get_doi_info(doi):
    """Get info for DOI."""
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    return response.json()

def format_bibtex(doi):
    """Get BibTeX for DOI."""
    url = f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"
    response = requests.get(url)
    return response.text
```

---

## Key Packages Summary

| Package | Install | Use Case |
|---------|---------|----------|
| matplotlib | `uv pip install matplotlib` | Publication figures |
| seaborn | `uv pip install seaborn` | Statistical visualization |
| plotly | `uv pip install plotly` | Interactive plots |
| pdfplumber | `uv pip install pdfplumber` | PDF text extraction |
| python-docx | `uv pip install python-docx` | DOCX processing |
| pylatex | `uv pip install pylatex` | LaTeX generation |
| python-pptx | `uv pip install python-pptx` | PPTX processing |
| bibtexparser | `uv pip install bibtexparser` | Citation management |
