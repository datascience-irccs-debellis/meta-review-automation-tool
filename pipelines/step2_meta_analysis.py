# pipelines/step2_meta_analysis.py
import os
import re
import glob
import json
import textwrap
import difflib
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
import pandas as pd
import networkx as nx
from config import (ANALYSIS_JSON_DIR, ANALYSIS_OUTPUT_DIR, TARGET_TUMORS, TARGET_PAPERS,
                    MIN_POINTS_FUNNEL, MIN_POINTS_REGRESSION, ANNOTATED_REVIEW_DATABASE_PATH)
from core.logger import setup_logger
from core.data_processor import json_flatten, deduplicate_ylabels, format_pval
from matplotlib.lines import Line2D


class MetaAnalysisPipeline:
    def __init__(self):
        self.logger = setup_logger("Step2_MetaAnalysis")
        os.makedirs(ANALYSIS_OUTPUT_DIR, exist_ok=True)

    def run(self):
        self.logger.info("Starting Step 2: Meta-Analysis Pipeline...")

        df_dict = self._load_and_parse_jsons()
        if len(df_dict) == 0:
            self.logger.error("No valid data parsed from JSON files. Aborting.")
            return

        self.logger.info(f"Successfully loaded {len(df_dict)} valid papers.")

        # Execute Analysis Strategies
        self._generate_forest_plots(df_dict)
        self._generate_funnel_plots(df_dict)
        self._generate_meta_regression(df_dict)
        self._generate_network_map(df_dict)

        self.logger.info("Step 2 Complete. Check the outputs and logs.")

    def _load_and_parse_jsons(self):
        """Returns a dictionary paper_id - dataframe processed from json files."""
        json_files = glob.glob(os.path.join(ANALYSIS_JSON_DIR, "paper_json_*.json"))
        if not json_files:
            self.logger.warning(f"No JSON files found in {ANALYSIS_JSON_DIR}")
            return {}

        papers_df_dict = {}
        for file_path in json_files:
            filename = os.path.basename(file_path)
            paper_id = re.search(r'paper_json_(\d+)\.json', filename).group(1)
            self.logger.info(f"Processing {filename}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    flattened_data = json_flatten(data)
                    papers_df_dict[paper_id] = pd.DataFrame(flattened_data)

            except Exception as e:
                self.logger.error(f"Failed to process the json {filename}: {e}")

        return papers_df_dict

    def _get_author_mapping(self):
        """Reads the CSV and maps row index (Paper N) to 'FirstAuthor et al.'"""
        mapping = {}
        if not os.path.exists(ANNOTATED_REVIEW_DATABASE_PATH):
            self.logger.warning(f"Author mapping failed: '{ANNOTATED_REVIEW_DATABASE_PATH}' not found.")
            return mapping

        try:
            df_csv = pd.read_csv(ANNOTATED_REVIEW_DATABASE_PATH)
            if 'Authors' in df_csv.columns:
                for idx, row in df_csv.iterrows():
                    # Assuming Row 0 in CSV corresponds to 'paper_json_1.json'
                    paper_id = str(idx + 1)
                    authors = str(row['Authors'])

                    if pd.notna(row['Authors']) and authors.strip():
                        # Split by comma to grab just the first author
                        first_author = authors.split(',')[0].strip()
                        mapping[paper_id] = f"{first_author}"
                    else:
                        mapping[paper_id] = f"Paper {paper_id}"
        except Exception as e:
            self.logger.error(f"Could not load author mapping: {e}")

        return mapping

    def _generate_forest_plots(self, df_dict):
        self.logger.info("--> Generating Forest Plots...")
        for paper_id, df in df_dict.items():
            if df.empty:
                continue

            group_keys = df[['Tumor', 'Population']].drop_duplicates()

            for _, group_meta in group_keys.iterrows():
                tumor = group_meta['Tumor']
                pop = group_meta['Population']

                safe_tumor = str(tumor).replace(" ", "_").replace("/", "-")
                safe_pop = str(pop).replace(" ", "_")
                df_tp = df[(df['Tumor'] == tumor) & (df['Population'] == pop)].copy()

                # --- PLOT 1: OVERALL ---
                df_overall = df_tp[df_tp['Is_Overall'] == True].copy()
                if not df_overall.empty:
                    df_overall['Y_Label'] = df_overall['Feature'].str.title()

                    # Column label is just the Model for Overall
                    df_overall['Col_Label'] = df_overall['Model'].apply(lambda m: textwrap.fill(m.title(), width=25))
                    df_overall = deduplicate_ylabels(df_overall)

                    paper_dir = os.path.join(ANALYSIS_OUTPUT_DIR, f"paper_{paper_id}")
                    os.makedirs(paper_dir, exist_ok=True)
                    out_path = os.path.join(paper_dir, f"Tumor_{safe_tumor}_Pop_{safe_pop}_Overall.png")
                    title = f"Overall Analysis\nTumor: {tumor} | Population: {pop}"
                    self._draw_horizontal_forest_grid(df_overall, out_path, title)

                # --- PLOT 2: STRATIFIED (Grouped by Subgroup Category) ---
                df_strat = df_tp[df_tp['Is_Overall'] == False].copy()
                if not df_strat.empty:

                    # We separate out DIFFERENT stratification types (e.g., Sex vs Age) into distinct files
                    for sg_type, df_sg in df_strat.groupby('Subgroup_Type'):
                        df_sg = df_sg.copy()

                        # For stratified plots, Y-axis is just the Feature
                        df_sg['Y_Label'] = df_sg['Feature'].str.title()

                        # Column Label combines Model and Class Category (e.g., "Multivariate [Male]")
                        def make_col_label(row):
                            m = textwrap.fill(row['Model'].title(), width=25)
                            c = textwrap.fill(row['Subgroup_Label'].title(), width=25)
                            return f"{m}\n[{c}]"

                        df_sg['Col_Label'] = df_sg.apply(make_col_label, axis=1)
                        df_sg = deduplicate_ylabels(df_sg)

                        # Clean filename for this specific stratification
                        safe_sg_type = str(sg_type).replace(" ", "_").replace("/", "-")
                        if not safe_sg_type: safe_sg_type = "Unknown_Stratification"

                        paper_dir = os.path.join(ANALYSIS_OUTPUT_DIR, f"paper_{paper_id}")
                        os.makedirs(paper_dir, exist_ok=True)
                        out_path = os.path.join(paper_dir,
                                                f"Tumor_{safe_tumor}_Pop_{safe_pop}_Strat_{safe_sg_type}.png")
                        title = f"Stratified Analysis: {sg_type.title()}\nTumor: {tumor} | Population: {pop}"

                        self._draw_horizontal_forest_grid(df_sg, out_path, title)
                else:
                    self.logger.warning(f"Skipping Stratified Forest plot for {tumor}: No stratified models found.")
        # Check logic...
        self.logger.info(f"\n✅ Forest Plots successfully generated in the '{ANALYSIS_OUTPUT_DIR}' directory.")

    def _generate_funnel_plots(self, df_dict):
        self.logger.info("--> Generating Funnel Plots...")
        all_data = []

        author_mapping = self._get_author_mapping()

        for paper_id, df in df_dict.items():
            if paper_id not in TARGET_PAPERS or df.empty:
                continue

            # Filter to keep only the overall population analyses
            if 'Is_Overall' in df.columns:
                df = df[df['Is_Overall'] == True].copy()
            else:
                self.logger.warning(f"Paper {paper_id} missing 'Is_Overall' column. Skipping.")
                continue

            # Skip invalid math values (HRs must be > 0 for logarithms)
            df = df[(df["Value"] > 0) & (df["CI_Lower"] > 0) & (df["CI_Upper"] > 0)].copy()

            if df.empty:
                continue

            # Calculate Meta-Analysis Stats: Log Effect and Standard Error
            df["Log_Effect"] = np.log(df["Value"])
            df["SE"] = (np.log(df["CI_Upper"]) - np.log(df["CI_Lower"])) / 3.92

            df = df[df["SE"] > 0].copy()

            if df.empty:
                continue

            df["Variance"] = df["SE"] ** 2
            df["Weight"] = 1 / df["Variance"]
            df["Paper_ID"] = paper_id
            all_data.append(df)

        if not all_data:
            self.logger.warning("No valid data found to generate Funnel Plots.")
            return

        self.logger.info(f"Processing {len(all_data)} valid dataframes...")
        master_df = pd.concat(all_data, ignore_index=True)

        # ==========================================
        # INTERACTIVE HARMONIZATION (FEATURES ONLY)
        # ==========================================
        # Extract unique features for human-in-the-loop review
        unique_features = master_df["Feature"].unique()

        # Ask user to resolve similarities (default threshold 85%)
        feature_map = self._resolve_similar_strings(unique_features, "Feature", threshold=0.99)

        # Apply the user's decisions to the dataframe.
        # If a feature wasn't mapped, it keeps its original string.
        master_df["Feature_Clean"] = master_df["Feature"].map(feature_map).fillna(master_df["Feature"])

        # ==========================================
        # GROUPING & PLOTTING
        # ==========================================
        MIN_PAPERS_FUNNEL = 2

        # We group by the strict ICD-10 Tumor code and the Cleaned Feature
        for (tumor, feature), group_df in master_df.groupby(['Tumor', 'Feature_Clean']):

            # Verify we have multiple *distinct* papers, not just multiple rows from one paper
            unique_papers_count = group_df['Paper_ID'].nunique()

            if unique_papers_count < MIN_PAPERS_FUNNEL:
                self.logger.warning(
                    f"  -> Skipping Funnel Plot for {tumor} - {feature} "
                    f"(Only {unique_papers_count} distinct paper(s) found; need at least {MIN_PAPERS_FUNNEL})"
                )
                continue

            # (Optional) You can still enforce a strict total point count if needed
            if len(group_df) < MIN_POINTS_FUNNEL:
                self.logger.warning(
                    f"  -> Skipping Funnel Plot for {tumor} - {feature} "
                    f"(Not enough total data points: {len(group_df)} < {MIN_POINTS_FUNNEL})"
                )
                continue

            # Create a directory for each tumor (using the ICD-10 code)
            safe_tumor_dir = str(tumor).replace(".", "_")
            tumor_dir = os.path.join(ANALYSIS_OUTPUT_DIR, safe_tumor_dir)
            os.makedirs(tumor_dir, exist_ok=True)

            # Sanitize feature name for file saving
            safe_feat = str(feature).replace(" ", "_").replace("/", "-")
            out_path = os.path.join(tumor_dir, f"Funnel_{safe_tumor_dir}_{safe_feat}.png")

            # Format the title nicely
            title = f"Funnel Plot (Overall): {feature}\nTumor (ICD-10): {tumor} | Papers included: {unique_papers_count}"

            self._draw_funnel_plot(group_df, out_path, title, author_mapping)
            self.logger.info(f"  -> ✅ Generated Funnel Plot: {tumor} - {feature}")

        self.logger.info(
            f"\nAll eligible Funnel Plots successfully generated in the '{ANALYSIS_OUTPUT_DIR}' directory.")

    def _resolve_similar_strings(self, unique_items: list, entity_name: str, threshold: float = 0.95) -> dict:
        """
        Compares unique strings and asks the user to harmonize them if similarity > threshold.
        """
        mapping = {}
        processed = set()

        # Sort items so comparisons are consistent
        unique_items = sorted([str(x) for x in unique_items if pd.notna(x)])

        print(f"\n--- Starting Interactive Harmonization for {entity_name} ---")

        for i, item_a in enumerate(unique_items):
            if item_a in processed:
                continue

            # The first item we see becomes the "canonical" (standard) name
            canonical_name = item_a
            mapping[item_a] = canonical_name
            processed.add(item_a)

            for item_b in unique_items[i + 1:]:
                if item_b in processed:
                    continue

                # Calculate similarity (converting to lowercase for the check to be case-insensitive)
                similarity = difflib.SequenceMatcher(None, item_a.lower(), item_b.lower()).ratio()

                if similarity >= threshold:
                    print(f"\n[Similarity: {similarity:.2f}]")
                    print(f"  1: '{item_a}'")
                    print(f"  2: '{item_b}'")

                    while True:
                        choice = input(f"Do these {entity_name}s mean the same thing? (y/n): ").strip().lower()
                        if choice in ('y', 'yes'):
                            # Map item_b to use item_a's exact spelling
                            mapping[item_b] = canonical_name
                            processed.add(item_b)
                            print(f"  -> Merged. '{item_b}' will now be treated as '{canonical_name}'.")
                            break
                        elif choice in ('n', 'no'):
                            # They are different, leave them alone for now
                            break
                        else:
                            print("Please type 'y' or 'n'.")

        return mapping

    def _generate_meta_regression(self, df_dict):
        self.logger.info("--> Generating Meta-Regression Plots...")
        all_data = []
        for paper_id, df in df_dict.items():
            if paper_id not in TARGET_PAPERS or df.empty:
                continue

                # Filter to keep only the overall population analyses to ensure independent studies
            if 'Is_Overall' in df.columns:
                df = df[df['Is_Overall'] == True].copy()
            else:
                self.logger.warning(f"Paper {paper_id} missing 'Is_Overall' column. Skipping.")
                continue

            df = df[(df["Value"] > 0) & (df["CI_Lower"] > 0) & (df["CI_Upper"] > 0)]
            df["Log_Effect"] = np.log(df["Value"])
            df["SE"] = (np.log(df["CI_Upper"]) - np.log(df["CI_Lower"])) / 3.92
            df = df[df["SE"] > 0]
            df["Variance"] = df["SE"] ** 2
            df["Weight"] = 1 / df["Variance"]
            def parse_pop(pop_raw):
                if isinstance(pop_raw, list):
                    pop_raw = pop_raw[0]
                cleaned = re.sub(r'[^\d.]', '', str(pop_raw))
                return float(cleaned) if cleaned else np.nan

            df["Total_Participants"] = pd.to_numeric(df["Population"].apply(parse_pop))
            df["Paper_ID"] = paper_id
            all_data.append(df)

        master_df = pd.concat(all_data, ignore_index=True)

        # Group by Tumor and Feature
        for (tumor, feature), group_df in master_df.groupby(['Tumor', 'Feature']):

            # Only run regression if we meet the minimum study threshold
            num_studies = len(group_df['Paper_ID'].unique())
            if num_studies < MIN_POINTS_REGRESSION:
                continue

            tumor_dir = os.path.join(ANALYSIS_OUTPUT_DIR, tumor.replace(".", "_"))
            os.makedirs(tumor_dir, exist_ok=True)

            safe_feat = str(feature).replace(" ", "_").replace("/", "-")
            out_path = os.path.join(tumor_dir, f"MetaReg_{tumor.replace('.', '_')}_{safe_feat}.png")

            title = f"Meta-Regression: Sample Size vs Effect\nTumor: {tumor} | Feature: {feature} (N={num_studies})"

            # Wrap in try-except because statsmodels might fail if X variance is 0 (e.g., all studies have exact same sample size)
            try:
                self._draw_bubble_plot(group_df, out_path, title)
                self.logger.info(f"✅ Generated Meta-Regression Plot: {tumor} - {feature}")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not perform regression for {tumor} - {feature}: {e}")

        self.logger.info(f"\nMeta-Regression finished in '{ANALYSIS_OUTPUT_DIR}'.")

    def _generate_network_map(self, df_dict):
        self.logger.info("--> Generating Bipartite Network Map...")
        all_data = []
        for paper_id, df in df_dict.items():
            df["Paper"] = paper_id
            df = df[df["Tumor"].isin(TARGET_TUMORS)]
            df.drop_duplicates()
            all_data.append(df)

        master_df = pd.concat(all_data, ignore_index=True).drop_duplicates()
        try:
            self._draw_bipartite_graph(master_df)
            self.logger.info(f"✅ Generated Bipartite Network Map.")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not perform Bipartite Network Map.")

        self.logger.info(f"\nBipartite Network Map finished in '{ANALYSIS_OUTPUT_DIR}'.")



    # Supporting functions
    def _draw_horizontal_forest_grid(self, df_subset, output_path, title_prefix):
        """Draws a forest plot where different categories/models are placed horizontally side-by-side."""
        if df_subset.empty:
            return

        # Sort Y labels to keep the rows unified and alphabetical
        df_subset = df_subset.sort_values(by=['Y_Label'])
        y_labels = df_subset['Y_Label'].unique()

        # Extract unique horizontal columns, preserving Model -> Category ordering
        # This ensures Univariate [Female] sits next to Univariate [Male]
        col_order_df = df_subset[['Model', 'Subgroup_Label', 'Col_Label']].drop_duplicates()
        col_order_df = col_order_df.sort_values(by=['Model', 'Subgroup_Label'])
        columns = col_order_df['Col_Label'].tolist()

        num_cols = len(columns)

        # Layout: 1 horizontal grid row, [Text, Plot] for each column
        fig, axes_flat = plt.subplots(
            1, num_cols * 2,
            figsize=(6 * num_cols + 4, max(4, 0.8 * len(y_labels))),
            sharey=True,
            gridspec_kw={'width_ratios': [1, 2.5] * num_cols}
        )

        # Ensure axes iterable
        if num_cols * 2 == 2:
            axes_flat = [axes_flat[0], axes_flat[1]]

        y_pos_map = {label: i for i, label in enumerate(y_labels)}

        for i, col_name in enumerate(columns):
            ax_text = axes_flat[i * 2]
            ax_plot = axes_flat[i * 2 + 1]

            df_col = df_subset[df_subset['Col_Label'] == col_name]

            # 1. GRAPH SETUP
            ax_plot.axvline(1.0, color='gray', linestyle='--', linewidth=1)

            # 2. TEXT SETUP
            ax_text.set_xlim(0, 1)
            ax_text.get_xaxis().set_visible(False)
            for spine in ax_text.spines.values():
                spine.set_visible(False)

            for _, row in df_col.iterrows():
                y_pos = y_pos_map[row['Y_Label']]
                val = row['Value']
                ci_l = row['CI_Lower']
                ci_u = row['CI_Upper']

                # Draw point & error bar
                err_lower = val - ci_l
                err_upper = ci_u - val
                ax_plot.errorbar(x=val, y=y_pos, xerr=[[err_lower], [err_upper]],
                                 fmt='o', color='navy', ecolor='steelblue', capsize=4, markersize=8)

                # Write text stats
                annot_text = f"{val:.2f}[{ci_l:.2f}-{ci_u:.2f}]"
                p_text = format_pval(row['P_Value'])
                if p_text:
                    annot_text += f"\n{p_text}"

                ax_text.text(0.5, y_pos, annot_text, va='center', ha='center', fontsize=10, color='black')

            # Formatting titles and axes
            ax_plot.set_title(col_name, fontsize=11, fontweight='bold', pad=15)
            ax_plot.set_xlabel(f"Effect Size ({df_subset['Measure'].iloc[0]})", fontweight='bold')
            ax_plot.set_xscale('log')
            ax_plot.grid(True, axis='y', linestyle=':', alpha=0.6)

            ax_text.set_title("Statistics", fontsize=11, fontweight='bold', pad=15)

        # Format the shared Y-Axis (Row Names) on the far left only
        ax_first = axes_flat[0]
        ax_first.set_yticks(list(y_pos_map.values()))

        # Wrap long feature names
        wrapped_ylabels = [textwrap.fill(lbl, width=25) for lbl in y_pos_map.keys()]
        ax_first.set_yticklabels(wrapped_ylabels, fontsize=11, fontweight='bold')
        ax_first.tick_params(axis='y', length=0)
        ax_first.invert_yaxis()

        plt.suptitle(title_prefix, fontsize=14, fontweight='bold', y=1.05)
        plt.subplots_adjust(wspace=0.1)
        plt.tight_layout()

        fig.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close(fig)

    def _draw_funnel_plot(self, df_subset, output_path, title_prefix, author_mapping):
        """Draws a standard Meta-Analysis Funnel Plot with 95% pseudo-confidence limits."""
        if len(df_subset) < MIN_POINTS_FUNNEL:
            return

        # Calculate Inverse-Variance Pooled Effect (Center of the Funnel)
        sum_weight = df_subset['Weight'].sum()
        sum_weight_effect = (df_subset['Weight'] * df_subset['Log_Effect']).sum()
        pooled_log_effect = sum_weight_effect / sum_weight

        fig, ax = plt.subplots(figsize=(8, 6))

        # --- Draw the Pseudo-95% Confidence "Funnel" Lines ---
        max_se = df_subset['SE'].max()
        y_line = np.linspace(0, max_se * 1.1, 100)

        # 95% CI is roughly +/- 1.96 * SE
        x_lower = pooled_log_effect - 1.96 * y_line
        x_upper = pooled_log_effect + 1.96 * y_line

        ax.plot(x_lower, y_line, color='gray', linestyle='--', linewidth=1.5, label='95% Pseudo-CI')
        ax.plot(x_upper, y_line, color='gray', linestyle='--', linewidth=1.5)

        # Draw Center Line (Pooled Effect)
        ax.axvline(pooled_log_effect, color='black', linestyle='-', linewidth=1.5,
                   label=f'Pooled Log Effect ({pooled_log_effect:.2f})')
        # Draw Null Line (Log HR = 0 -> HR = 1)
        ax.axvline(0, color='red', linestyle=':', linewidth=1.5, label='Null Effect (HR=1)')

        # --- Plot the Data Points ---
        # We use a scatter plot, optionally coloring by Paper ID if you have multiple papers
        papers = df_subset['Paper_ID'].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(papers)))

        for paper, color in zip(papers, colors):
            df_p = df_subset[df_subset['Paper_ID'] == paper]

            author_label = author_mapping.get(str(paper), f"Paper {paper}")

            ax.scatter(df_p['Log_Effect'], df_p['SE'], color=color, alpha=0.7, s=70, edgecolor='black',
                       label=author_label)

        # --- Formatting ---
        ax.set_ylim(max_se * 1.1, 0)  # INVERT Y-AXIS (Standard for funnel plots)

        # Set X axis label based on the measure
        measure = df_subset['Measure'].iloc[0]
        ax.set_xlabel(f"Log {measure} (Log Effect Size)", fontsize=12, fontweight='bold')
        ax.set_ylabel("Standard Error (SE)", fontsize=12, fontweight='bold')

        ax.set_title(title_prefix, fontsize=14, fontweight='bold', pad=15)
        ax.grid(True, linestyle=':', alpha=0.6)

        # Move legend outside if there are many papers
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

        plt.tight_layout()
        fig.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close(fig)

    def _draw_bubble_plot(self, df_subset, output_path, title_prefix):
        """Draws a Meta-Regression Bubble Plot."""
        # X variable: Sample Size (Log transformed for better visualization of massive registries vs small cohorts)
        X = np.log10(df_subset['Total_Participants'])
        Y = df_subset['Log_Effect']
        W = df_subset['Weight']

        # Fit Weighted Least Squares (WLS) Regression
        X_with_const = sm.add_constant(X)
        model = sm.WLS(Y, X_with_const, weights=W).fit()

        # Generate predictions for the regression line
        x_pred = np.linspace(X.min() * 0.9, X.max() * 1.1, 100)
        x_pred_const = sm.add_constant(x_pred)
        y_pred = model.predict(x_pred_const)

        # Get Confidence Intervals for the regression line
        pred_results = model.get_prediction(x_pred_const)
        pred_ci = pred_results.conf_int(alpha=0.05)

        # --- PLOTTING ---
        fig, ax = plt.subplots(figsize=(9, 6))

        # Plot the bubbles (Size of bubble = Weight of the study)
        # Scale bubble sizes for visual aesthetics
        bubble_sizes = (W / W.max()) * 1000

        scatter = ax.scatter(X, Y, s=bubble_sizes, color='steelblue', alpha=0.6, edgecolors='black',
                             label='Included Studies')

        # Plot Regression Line
        ax.plot(x_pred, y_pred, color='crimson', linewidth=2, label=f'Regression Line (p={model.pvalues.iloc[1]:.3f})')

        # Plot 95% Confidence Band
        ax.fill_between(x_pred, pred_ci[:, 0], pred_ci[:, 1], color='crimson', alpha=0.15, label='95% CI Band')

        # Plot Null Effect Line (HR = 1, Log HR = 0)
        ax.axhline(0, color='gray', linestyle='--', linewidth=1.5, label='Null Effect (HR=1)')

        # --- FORMATTING ---
        measure = df_subset['Measure'].iloc[0]
        ax.set_ylabel(f"Log {measure} (Effect Size)", fontsize=12, fontweight='bold')
        ax.set_xlabel("Log10(Total Participants)", fontsize=12, fontweight='bold')

        ax.set_title(title_prefix, fontsize=14, fontweight='bold', pad=15)
        ax.grid(True, linestyle=':', alpha=0.6)

        # Add R-squared text to graph
        r2_text = f"Adj R-squared: {model.rsquared_adj:.2f}\nBeta: {model.params.iloc[1]:.3f}"
        ax.text(0.05, 0.95, r2_text, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='gray'))

        ax.legend(loc='upper right', fontsize=10)

        plt.tight_layout()
        fig.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close(fig)

    def _draw_bipartite_graph(self, df):
        """Generates and saves a highly optimized bipartite network graph."""
        if df.empty:
            self.logger.warning("No valid data found to draw the network.")
            return

        # --- INITIALIZE GRAPH ---
        B = nx.Graph()
        papers = sorted(df['Paper'].unique().tolist())
        features = df['Feature'].unique().tolist()

        B.add_nodes_from(papers, bipartite=0, type='paper')
        B.add_nodes_from(features, bipartite=1, type='feature')

        for _, row in df.iterrows():
            B.add_edge(row['Paper'], row['Feature'], tumor=row['Tumor'])

        # --- WATERFALL SORTING FOR READABILITY ---
        feature_degrees = dict(B.degree(features))

        shared_features = [f for f in features if feature_degrees[f] > 1]
        unique_features = [f for f in features if feature_degrees[f] == 1]

        # Sort shared features by highest connection count
        shared_features.sort(key=lambda f: feature_degrees[f], reverse=True)

        # Sort unique features grouped by the specific paper they belong to
        unique_feat_info = [(f, list(B.neighbors(f))[0]) for f in unique_features]
        unique_feat_info.sort(key=lambda x: x[1])  # Sort by connected paper name
        sorted_unique_features = [x[0] for x in unique_feat_info]

        # Final optimized vertical order
        sorted_features = shared_features + sorted_unique_features

        # --- CALCULATE POSITIONS MANUALLY ---
        # This prevents the "spaghetti" effect of default bipartite layouts
        pos = {}

        # Distribute features evenly across the vertical axis
        y_feat = np.linspace(len(sorted_features), 0, len(sorted_features)) if len(sorted_features) > 1 else [0]
        for f, y in zip(sorted_features, y_feat):
            pos[f] = [1.0, y]

        # Distribute papers evenly across the vertical axis
        y_pap = np.linspace(len(sorted_features), 0, len(papers)) if len(papers) > 1 else [len(sorted_features) / 2]
        for p, y in zip(papers, y_pap):
            pos[p] = [-1.0, y]

        # --- VISUALIZATION SETUP ---
        # Dynamically scale height: ~0.25 inches per feature node so they never overlap
        fig_height = max(10, len(sorted_features) * 0.25)
        plt.figure(figsize=(16, fig_height))

        # --- DRAW EDGES WITH HIERARCHY ---
        # Shared edges are thick/opaque; Unique edges are thin/transparent
        for u, v, d in B.edges(data=True):
            feat = v if v in features else u
            is_shared = feature_degrees[feat] > 1

            e_color = 'crimson' if d['tumor'] == 'C22.1' else 'royalblue'
            e_alpha = 0.7 if is_shared else 0.25
            e_width = 2.0 if is_shared else 1.0

            nx.draw_networkx_edges(B, pos, edgelist=[(u, v)], edge_color=e_color, width=e_width, alpha=e_alpha)

        # --- DRAW NODES WITH HIERARCHY ---
        # Papers
        nx.draw_networkx_nodes(B, pos, nodelist=papers, node_color='lightblue',
                               node_shape='s', node_size=1000, edgecolors='black')

        # Shared Features (Large, Bright Green)
        shared_sizes = [400 + (feature_degrees[n] * 150) for n in shared_features]
        if shared_features:
            nx.draw_networkx_nodes(B, pos, nodelist=shared_features, node_color='limegreen',
                                   node_shape='o', node_size=shared_sizes, edgecolors='black')

        # Unique Features (Small, Pale)
        if unique_features:
            nx.draw_networkx_nodes(B, pos, nodelist=sorted_unique_features, node_color='whitesmoke',
                                   node_shape='o', node_size=150, edgecolors='gray')

        # --- DRAW SMART LABELS ---
        # Papers (Left side, Bold)
        pos_papers = {k: [v[0] - 0.1, v[1]] for k, v in pos.items() if k in papers}
        nx.draw_networkx_labels(B, pos_papers, labels={k: k for k in papers},
                                font_size=12, font_weight='bold', horizontalalignment='right')

        # Shared Features (Right side, Bold)
        pos_shared = {k: [v[0] + 0.1, v[1]] for k, v in pos.items() if k in shared_features}
        nx.draw_networkx_labels(B, pos_shared, labels={k: k for k in shared_features},
                                font_size=11, font_weight='bold', horizontalalignment='left')

        # Unique Features (Right side, Small, Gray)
        pos_unique = {k: [v[0] + 0.1, v[1]] for k, v in pos.items() if k in sorted_unique_features}
        nx.draw_networkx_labels(B, pos_unique, labels={k: k for k in sorted_unique_features},
                                font_size=9, font_weight='normal', font_color='dimgray', horizontalalignment='left')

        # --- CANVAS FORMATTING ---
        ax = plt.gca()
        # Widen X limits to give massive room for text on both sides
        ax.set_xlim([-2.5, 2.5])

        # Legend
        legend_elements = [
            Line2D([0], [0], marker='s', color='w', label='Scientific Paper', markerfacecolor='lightblue',
                   markersize=14,
                   markeredgecolor='black'),
            Line2D([0], [0], marker='o', color='w', label='Shared Feature (Meta-Analyzable)',
                   markerfacecolor='limegreen',
                   markersize=14, markeredgecolor='black'),
            Line2D([0], [0], marker='o', color='w', label='Unique Feature (Single Study)', markerfacecolor='whitesmoke',
                   markersize=8, markeredgecolor='gray'),
            Line2D([0], [0], color='crimson', lw=3, label='C22.1 (Intrahepatic)'),
            Line2D([0], [0], color='royalblue', lw=3, label='C24.1 (Extrahepatic)')
        ]
        plt.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.02), ncol=3, fontsize=11)

        plt.title("Hierarchical Evidence Map: Papers vs. Features", fontsize=18, fontweight='bold', pad=40)
        plt.axis('off')

        # Tight layout prevents text cutoff
        plt.tight_layout(pad=1.0)

        out_path = os.path.join(ANALYSIS_OUTPUT_DIR, "Bipartite_Evidence_Map.png")
        plt.savefig(out_path, bbox_inches='tight', dpi=300)
        plt.close()
        self.logger.info(f"✅ Bipartite Graph saved to {out_path}")