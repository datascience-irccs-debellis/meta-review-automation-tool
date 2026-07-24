# data_processor.py
import pandas as pd


def categorize_item(item, categories, default='Other'):
    """Helper function to map a single descriptive item to a MACRO category."""
    item = str(item).strip().lower()

    if item in ['n.a.', 'n.a', 'na', 'n/a', 'not applicable', 'none', '']:
        return 'N.A.'

    if isinstance(categories, dict):
        for category, keywords in categories.items():
            if any(kw.lower() in item for kw in keywords):
                return category

    elif isinstance(categories, list):
        for category in categories:
            if category.lower() in item:
                return category

    return default


def categorize_multiple(text, categories, default='Other'):
    """Splits comma-separated values, categorizes each to MACRO, and returns a unique list."""
    if pd.isna(text):
        return ['N.A.']

    items = str(text).split(',')
    labels = []
    for item in items:
        cat = categorize_item(item, categories, default)
        if cat not in labels:
            labels.append(cat)

    return labels


def extract_micro_multiple(text, categories):
    """Extracts the exact matching MICRO-values (e.g. pICCA, nBDC) from the text."""
    if pd.isna(text):
        return ['N.A.']

    items = str(text).split(',')
    micros = []

    for item in items:
        item_clean = item.strip().lower()

        # Handle NA
        if item_clean in ['n.a.', 'n.a', 'na', 'n/a', 'not applicable', 'none', '']:
            if 'N.A.' not in micros:
                micros.append('N.A.')
            continue

        found = False
        if isinstance(categories, dict):
            for category, keywords in categories.items():
                for kw in keywords:
                    # If the exact micro acronym/keyword is in the text, extract it
                    if kw.lower() in item_clean:
                        if kw not in micros:
                            micros.append(kw)
                        found = True

        # If it doesn't match any micro value, label as 'Other'
        if not found and 'N.A.' not in micros:
            if 'Other' not in micros:
                micros.append('Other')

    return micros


def json_flatten(data):
    """Flattens JSON objects into a list of dictionaries."""
    records = []

    for tumor in data.get("tumors", []):
        # Handle multiple tumors safely
        t_sub_raw = tumor.get("tumor_subtype", "Unknown_Tumor")
        if isinstance(t_sub_raw, list):
            t_subtypes = [str(t).strip() for t in t_sub_raw]
        else:
            t_subtypes = [t.strip() for t in str(t_sub_raw).split(",")]

        # Handle multiple populations safely
        pop_raw = tumor.get("total_participants", "Unknown_Pop")
        if isinstance(pop_raw, list):
            pops = [str(p).strip() for p in pop_raw]
        else:
            pops = [p.strip() for p in str(pop_raw).split(",")]

        seen_models = {}

        for model in tumor.get("models", []):
            raw_m_type = model.get("model_type", "Unknown_Model").strip()

            # Auto-increment duplicate model names
            if raw_m_type in seen_models:
                seen_models[raw_m_type] += 1
                m_type = f"{raw_m_type} ({seen_models[raw_m_type]})"
            else:
                seen_models[raw_m_type] = 1
                m_type = raw_m_type

            for subgroup in model.get("subgroups", []):
                sg_type = str(subgroup.get("subgroup_type", "")).strip()
                sg_label = str(subgroup.get("subgroup", "")).strip()
                sg_thresh = subgroup.get("threshold", "")

                is_overall = False
                if sg_type.lower() == "overall" or sg_label.lower() == "overall" or (not sg_type and not sg_label):
                    is_overall = True

                for res in subgroup.get("results", []):
                    val = res.get("value")
                    ci_l = res.get("ci_lower")
                    ci_u = res.get("ci_upper")

                    # 1. Skip if core numeric objects are entirely missing
                    if val is None or ci_l is None or ci_u is None:
                        continue

                        # 2. Skip if explicitly set to "NC" (Not Calculable)
                    if str(val).strip().upper() == "NC" or str(ci_l).strip().upper() == "NC" or str(
                            ci_u).strip().upper() == "NC":
                        continue

                    for t_sub in t_subtypes:
                        for pop in pops:
                            records.append({
                                "Tumor": t_sub,
                                "Population": pop,
                                "Model": m_type,
                                "Is_Overall": is_overall,
                                "Subgroup_Type": sg_type,
                                "Threshold": sg_thresh,
                                "Subgroup_Label": sg_label,
                                "Feature": res.get("feature", "Unknown_Feature"),
                                "Measure": res.get("measure", "HR").upper(),
                                "Value": float(val),
                                "CI_Lower": float(ci_l),
                                "CI_Upper": float(ci_u),
                                "P_Value": res.get("p_value", None)
                            })
    return records

def deduplicate_ylabels(df):
    """Ensures no two rows within the exact same horizontal column share the same Y_Label."""
    df = df.copy()
    for col in df['Col_Label'].unique():
        mask = df['Col_Label'] == col
        seen = {}
        for idx, val in df.loc[mask, 'Y_Label'].items():
            if val in seen:
                seen[val] += 1
                df.at[idx, 'Y_Label'] = f"{val} ({seen[val]})"
            else:
                seen[val] = 1
    return df

def format_pval(p):
    """Formats the p-value for clean display."""
    if pd.isna(p) or p is None:
        return None
    try:
        p_flt = float(p)
        if p_flt < 0.001: return "p<0.001"
        if p_flt < 0.01: return f"p={p_flt:.3f}"
        return f"p={p_flt:.2f}"
    except:
        return f"p={p}"