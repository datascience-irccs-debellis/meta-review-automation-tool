# 📊 Meta-Analysis Toolkit: A Configurable Pipeline for Systematic Reviews

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Academic%20Prototype-orange.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> **Associated Paper**: *An Open-source Tool for Automated Meta-Review: Synthesizing Cholangiocarcinoma Research in the UK Biobank*  
> **Target Journal**: *Journal of Biomedical Informatics (JBI)*  
> **Purpose**: End-to-end framework for interactive literature standardization, automated meta-review visualizations, quantitative meta-analysis, and bipartite evidence mapping.

---

## 📖 Overview

Systematic literature reviews and meta-analyses are foundational in biomedical research, but synthesizing qualitative and quantitative evidence across dozens of heterogeneity-heavy studies can be prone to human error and difficult to reproduce. 

This **Meta-Analysis Toolkit** provides a modular, configurable 3-step pipeline:
1. **Step 0 — Interactive Annotation**: A human-in-the-loop CLI assistant to standardize metadata and categorization across scientific publications.
2. **Step 1 — Systematic Meta-Review**: Automated extraction of high-level trends, research approaches, and temporal discovery dynamics with clear statistical plots.
3. **Step 2 — Quantitative Meta-Analysis**: Advanced statistical aggregation generating multi-model **Forest Plots**, publication bias **Funnel Plots**, **Meta-Regression** models, and **Bipartite Network Evidence Maps**.

---

## 🛠️ Pipeline Architecture

```text
               +----------------------------------+
               |  raw_review_database.csv         |
               +----------------------------------+
                                |
                                v
               +----------------------------------+
               |  STEP 0: Interactive Annotation  |  <-- Standardizes taxonomy
               +----------------------------------+
                                |
                                v
               +----------------------------------+
               | annotated_review_database.csv    |
               +----------------------------------+
                                |
        +-----------------------+-----------------------+
        |                                               |
        v                                               v
+-----------------------------+               +-------------------------------+
|  STEP 1: Meta-Review        |               |  STEP 2: Meta-Analysis        |
|  - Publications per Year    |               |  - JSON Flattening            |
|  - Keyword Frequencies      |               |  - Interactive Harmonization  |
|  - Temporal Trends          |               |  - Forest Plots               |
|  - Approach vs. Results     |               |  - Funnel Plots               |
+-----------------------------+               |  - Meta-Regression            |
        |                                     |  - Bipartite Network Map      |
        v                                     +-------------------------------+
+-----------------------------+                         |
|  outputs/step1_review_plots |                         v
+-----------------------------+               +-------------------------------+
                                              |  outputs/step2_analysis_plots |
                                              +-------------------------------+
```

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.8+**
* `pip` package manager

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/meta-analysis-toolkit.git
   cd meta-analysis-toolkit
   ```

2. **Set up a virtual environment (recommended)**:
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📂 Project Directory Layout

```text
.
├── main.py                          # CLI Entry point
├── config.py                        # Central pipeline configuration
├── requirements.txt                 # Dependencies
│
├── core/
│   ├── data_processor.py            # Data transformations, string matching & JSON flattening
│   └── logger.py                    # Dual console/file logging utility
│
├── pipelines/
│   ├── step0_annotate.py            # Interactive standardization pipeline
│   ├── step1_meta_review.py         # Systematic literature review plot generator
│   └── step2_meta_analysis.py       # Forest, Funnel, Meta-Regression & Network pipeline
│
├── data/
│   ├── raw_review_database.csv      # Initial literature search database
│   ├── annotated_review_database.csv # Standardized review database (post Step 0)
│   └── papers_analysis_db/          # JSON files containing study-level numeric data
│       ├── paper_json_1.json
│       └── ...
│
└── outputs/                         # Output generated figures (auto-created)
    ├── step1_review_plots/
    └── step2_analysis_plots/
```

---

## 📑 Input Data Formats

### 1. Literature Database (`.csv`) — *Used by Steps 0 & 1*
Placed in `data/raw_review_database.csv`. Key expected columns:
* `Title`, `Authors`, `Year`, `Keyword`, `Database`, `Citation Number`
* Category targets: `Approach`, `Focus`, `UkBiobank usage`, `Results`

### 2. Quantitative Study Files (`.json`) — *Used by Step 2*
Placed in `data/papers_analysis_db/paper_json_<ID>.json`. Each file encodes structured statistics extracted from a publication:
```json
{
  "tumors": [
    {
      "tumor_subtype": "C22.1",
      "total_participants": "500000",
      "models": [
        {
          "model_type": "Multivariate",
          "subgroups": [
            {
              "subgroup_type": "Overall",
              "subgroup": "Overall",
              "results": [
                {
                  "feature": "Alcohol Consumption",
                  "measure": "HR",
                  "value": 1.45,
                  "ci_lower": 1.12,
                  "ci_upper": 1.88,
                  "p_value": 0.005
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 💻 Usage Instructions

The software is controlled through `main.py`. You can execute steps individually or run the whole pipeline end-to-end.

```bash
# View help and options
python main.py --help
```

### Option A: Run Steps Individually

#### **Step 0 — Interactive Annotation**
Checks unstandardized string values in the CSV against allowed options specified in `config.py`. It presents non-matching entries interactively in the terminal and allows the user to select the correct standard category or skip.
```bash
python main.py --step 0
```

#### **Step 1 — Meta-Review Analysis**
Generates overview visualizations (distribution of studies over time, focus areas, database origins, and heatmaps).
```bash
python main.py --step 1
```

#### **Step 2 — Quantitative Meta-Analysis**
Parses study JSON files, prompts for fuzzy feature name matching/harmonization across studies, and generates quantitative meta-analysis plots.
```bash
python main.py --step 2
```

### Option B: Run Full Pipeline
Executes Step 0, Step 1, and Step 2 sequentially:
```bash
python main.py --all
```

---

## 🔬 Explanation of Generated Outputs (Non-Expert Guide)

### 📈 Step 1 Visualizations (`outputs/step1_review_plots/`)
* **Publications per Year**: Displays literature production rates.
* **Top Keywords**: Identifies dominant terminology in the literature.
* **Approach / Macro / Micro Heatmaps**: Shows how methodological choices correlate with discovered clinical findings.

---

### 📊 Step 2 Visualizations (`outputs/step2_analysis_plots/`)

#### 🌲 1. Forest Plots
* **What it shows**: Summarizes risk estimates across models and clinical subgroups.
* **How to read**: The center point indicates the effect estimate (e.g., Hazard Ratio). Lines represent 95% Confidence Intervals (CI). A dashed line at `1.0` indicates no effect. If an interval line crosses `1.0`, the finding is not statistically significant.

#### 📣 2. Funnel Plots
* **What it shows**: Detects publication bias or small-study effects across literature.
* **How to read**: Effect sizes are plotted against standard errors (SE). In the absence of bias, points form an inverted symmetric funnel centered on the pooled effect size. Asymmetry suggests missing negative or small-sample studies.

#### 🫧 3. Meta-Regression Bubble Plots
* **What it shows**: Evaluates whether sample sizes impact observed effect magnitudes using Weighted Least Squares (WLS).
* **How to read**: Larger bubbles represent studies with greater statistical weight. The fitted line indicates the overall trend, surrounded by a 95% confidence band.

#### 🕸️ 4. Bipartite Evidence Map (`Bipartite_Evidence_Map.png`)
* **What it shows**: A hierarchical network graph linking scientific papers (left) to analyzed clinical features (right).
* **How to read**: Shared features (analyzed by multiple papers) are highlighted in bright green, identifying prime targets for quantitative pooling, while unique features are displayed in light gray.

---

## ⚙️ Configuration (`config.py`)

All global parameters can be customized in `config.py`:
* `ANNOTATION_TARGETS`: Allowed values for interactive standardization in Step 0.
* `RESULT_CATS`: Acronym/keyword mappings for micro/macro evidence levels.
* `TARGET_TUMORS` / `TARGET_PAPERS`: Target ICD codes and study identifiers for statistical filtering.
* `MIN_POINTS_FUNNEL` / `MIN_POINTS_REGRESSION`: Minimum thresholds required to build Funnel and Regression plots.

---

<!-- ## 💡 Academic Reproducibility & Citation

If you use this toolkit in your research or wish to reproduce the findings reported in our *Journal of Biomedical Informatics* submission, please refer to the repository's example dataset and cite:

```bibtex
@article{meta_analysis_toolkit_2026,
  title={Meta-Analysis Toolkit: A configurable pipeline for systematic reviews},
  author={Authors List},
  journal={Journal of Biomedical Informatics},
  year={2026},
  note={Under Review}
}
```
-->
