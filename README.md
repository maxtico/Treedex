# Treedex

Treedex is an interactive tool to explore evolutionary and phylogenetic data using a **Dash-based dashboard** and web visualizations.

This README explains **how to install and run Treedex step by step** in development mode.

---

## 📦 Requirements

- Python ≥ 3.12
- Git
- Recommended: a virtual environment (conda or venv)
- Web browser (recommended: **Chrome** or **Firefox**)

---

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/maxtico/Treedex
cd Treedex
```

## Create and activate a virtual environment
conda create -n treedex python=3.12

conda activate treedex

## Install Treedex in editable/development mode
```bash
pip install -e .
```

## Run the tree explorer (ETE)
```bash
ete4 explore -t mammal_tree.nw
```

## Run Treedex
```bash
treedex -d species_information.csv
```
