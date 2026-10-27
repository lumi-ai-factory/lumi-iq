# LUMI-IQ docs preview

This repository contains a draft of the **LUMI-IQ** (quantum computing) documentation page for
the LUMI AI Factory docs (<https://docs.lumi-supercomputer.eu/laif/software/>), and a minimal
[MkDocs](https://www.mkdocs.org/) setup to preview it locally. The LUMI docs are built with
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

## Repository layout

```
.
├── README.md
├── mkdocs.yml
├── requirements.txt
└── docs/
    ├── index.md
    └── README.md
    └── requirement.txt
```

## Prerequisites

- Python 3.10 or newer

## Setup

From the root directory:

```bash
uv venv .venv
source venv/bin/activate 
uv pip install -r WP2/docs/requirement.txt
```


## Serve the docs locally

From the WP2 root (the folder that contains `mkdocs.yml`):

```bash
mkdocs serve
```

Open <http://127.0.0.1:8000>. The page reloads automatically when you save a file in `docs/`.

