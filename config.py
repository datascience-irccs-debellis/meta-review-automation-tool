# config.py
import os

# --- PATHS ---
DATA_DIR = "data"
RAW_REVIEW_DATABASE_PATH = os.path.join(DATA_DIR, "raw_review_database.csv")
ANNOTATED_REVIEW_DATABASE_PATH = os.path.join(DATA_DIR, "annotated_review_database.csv")
ANALYSIS_JSON_DIR = os.path.join(DATA_DIR, "papers_analysis_db")

OUTPUT_DIR = "outputs"
REVIEW_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "step1_review_plots")
ANALYSIS_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "step2_analysis_plots")

LOGS_DIR = "logs"

# --- META-REVIEW SETTINGS ---
ANNOTATION_TARGETS = {
    "Approach": [
        'Pathology Incidence Analysis',
        'Genomic Analysis',
        'Modifiable Risk Factor Analysis'
    ],
    "Focus": [
        'Specific',
        'Generic',
        'Half'
    ],
    "UkBiobank usage": [
        'Main Study',
        'Validation Study',
        'Support Study'
    ]
}

RESULT_CATS = {
    'Positive Incidence':['pICC', 'pBDC'],
    'Inverse Incidence': ['nICC', 'nBDC'],
    'No Significance':['nsICC', 'nsBDC']
}

META_REVIEW_PLOT_CONFIG = [
    {'type': 'pubxyear', 'column': 'Year', 'title': 'Publications per Year'},
    {'type': 'topkeyword', 'column': 'Keyword', 'title': 'Top Keywords'},
    {'type': 'piechart', 'column': 'UkBiobank usage', 'title': 'UK Biobank Usage'},
    {'type': 'approachdist', 'column': 'Approach', 'title': 'Approaches Distribution'},
    {'type': 'resultsmacro', 'column': 'Results', 'title': 'Macro-level Results'},
    {'type': 'resultsmicro', 'column': 'Results', 'title': 'Micro-level Results'},
    {'type': 'appxyear', 'column': 'Approach', 'title': 'Approaches Over Time'},
    {'type': 'resxyear', 'column': 'Results', 'title': 'Results Macro Over Time'},
    {'type': 'microxyear', 'column': 'Results', 'title': 'Results Micro Over Time'},
    {'type': 'focusxsource', 'column': 'Focus', 'title': 'Focus of Research by Database'},
    {'type': 'focusxcit', 'column': 'Focus', 'title': 'Citations by Focus'},
    {'type': 'rolexyear', 'column': 'UkBiobank usage', 'title': 'UK Biobank Usage Over Time'},
    {'type': 'focxcitxyear', 'column': 'Focus', 'title': 'Citations vs Year Focus'},
    {'type': 'appxres', 'column': 'Results', 'title': 'Approach vs Macro Results'},
    {'type': 'appxmicro', 'column': 'Results', 'title': 'Approach vs Macro Results'},
]

# --- META-ANALYSIS SETTINGS ---
TARGET_TUMORS = ["C22.1", "C24.1"]
TARGET_PAPERS =["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]
MIN_POINTS_FUNNEL = 3
MIN_POINTS_REGRESSION = 2