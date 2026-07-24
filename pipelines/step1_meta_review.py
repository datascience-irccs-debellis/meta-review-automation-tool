# pipelines/step1_meta_review.py
import os
from fileinput import filename

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from config import ANNOTATED_REVIEW_DATABASE_PATH, REVIEW_OUTPUT_DIR, META_REVIEW_PLOT_CONFIG, RESULT_CATS, \
    ANNOTATION_TARGETS
from core.logger import setup_logger
from core.data_processor import categorize_multiple, extract_micro_multiple
from collections import Counter


class MetaReviewPipeline:
    def __init__(self):
        self.logger = setup_logger("Step1_MetaReview")
        os.makedirs(REVIEW_OUTPUT_DIR, exist_ok=True)
        sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)

    def run(self):
        self.logger.info("Starting Step 1: Meta-Review Pipeline...")

        if not os.path.exists(ANNOTATED_REVIEW_DATABASE_PATH):
            self.logger.error(f"Annotated input file not found: {ANNOTATED_REVIEW_DATABASE_PATH}")
            self.logger.error("Please run Step 0 (Annotation) first!")
            return

        try:
            df = pd.read_csv(ANNOTATED_REVIEW_DATABASE_PATH)
            self.logger.info(f"Loaded {len(df)} records from database.")
        except Exception as e:
            self.logger.error(f"Failed to load CSV: {e}")
            return

        for i, plot_config in enumerate(META_REVIEW_PLOT_CONFIG):
            plot_type = plot_config['type']
            column = plot_config['column']
            title = plot_config['title']
            filename = f"{i + 1:02d}_{title.replace(' ', '_')}.png"

            if column not in df.columns:
                self.logger.warning(f"Column '{column}' not in data, skipping '{title}' plot.")
                continue

            try:
                if plot_type == 'pubxyear':
                    self._generate_pubs_per_year(df, column, filename)
                elif plot_type == 'topkeyword':
                    self._generate_keyword_list(df, column, filename)
                elif plot_type == 'piechart':
                    self._generate_role(df, column, filename)
                elif plot_type == 'approachdist':
                    self._generate_approach_label(df, column, filename)
                elif plot_type == 'resultsmacro':
                    self._generate_results_label(df, column, filename)
                elif plot_type == 'resultsmicro':
                    self._generate_micro_label(df, column, filename)
                elif plot_type == 'appxyear':
                    self._generate_approach_over_time(df, column, filename)
                elif plot_type == 'resxyear':
                    self._generate_results_over_time(df, column, filename)
                elif plot_type == 'microxyear':
                    self._generate_micro_over_time(df, column, filename)
                elif plot_type == 'focusxsource':
                    self._generate_source_focus(df, column, filename)
                elif plot_type == 'focusxcitations':
                    self._generate_citations_focus(df, column, filename)
                elif plot_type == 'rolexyear':
                    self._generate_role_over_year(df, column, filename)
                elif plot_type == 'focxcitxyear':
                    self._generate_focus_citation_time(df, column, filename)
                elif plot_type == 'appxres':
                    self._generate_approach_results(df, column, filename)
                elif plot_type == 'appxmicro':
                    self._generate_approach_micro(df, column, filename)

            except Exception as e:
                self.logger.error(f"Failed to generate plot for '{column}': {e}")

        self.logger.info("Step 1 Complete. Check the outputs and logs.")

    def _generate_pubs_per_year(self, df, column, filename):
        plt.figure(figsize=(8, 5))
        sns.countplot(data=df, x=column, palette='viridis')
        plt.title('Number of Publications per Year')
        plt.ylabel('Count')
        plt.tight_layout()
        out_path = os.path.join(REVIEW_OUTPUT_DIR, filename)
        plt.savefig(out_path)
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_keyword_list(self, df, column, filename):
        # Transforming the list of keyword contained in a string into a real list of string
        df['Keyword_List'] = df[column].apply(
            lambda x: [k.strip().title() for k in str(x).split(',')]
            if pd.notna(x) and str(x).strip().lower() not in ['n.a.', 'na', 'n/a', 'none', '']
            else ['N.A.']
        )

        # Computing the most frequent keywords (cutoff default 10)
        all_keywords = [kw for sublist in df['Keyword_List'] for kw in sublist if kw and kw != 'N.A.']
        kw_counts = Counter(all_keywords).most_common(10)
        kw_df = pd.DataFrame(kw_counts, columns=[column, 'Count'])

        plt.figure(figsize=(10, 6))
        sns.barplot(data=kw_df, y=column, x='Count', palette='magma')
        plt.title('Top 10 Most Frequent Keywords', fontsize=14, fontweight='bold')
        plt.xlabel('Occurrences')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_role(self,df, column, filename):
        plt.figure(figsize=(7, 5))
        counts = df[column].value_counts()
        plt.pie(counts, labels=counts.index, autopct='%1.1f%%',
                colors=sns.color_palette("Set2"), startangle=90,
                wedgeprops={'edgecolor': 'white'})
        plt.title(f'{column} in the Studies', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_approach_label(self,df, column, filename):
        # The analysis is only on the main approach (single one)
        df['Approach_Label'] = df[column].apply(
            lambda x: categorize_multiple(x, ANNOTATION_TARGETS["Approach"])
        )
        df_app = df.explode('Approach_Label').reset_index(drop=True)
        plt.figure(figsize=(8, 5))
        sns.countplot(data=df_app, y='Approach_Label', palette='cubehelix',
                      order=df_app['Approach_Label'].value_counts().index)
        plt.title('Main Interest of Researchers (Methodological Approaches)', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Mentions')
        plt.ylabel('Approach Category')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_results_label(self,df, column, filename):
        df['Results_Label'] = df[column].apply(
            lambda x: categorize_multiple(x, RESULT_CATS)
        )
        df_res = df.explode('Results_Label').reset_index(drop=True)
        plt.figure(figsize=(8, 5))
        sns.countplot(data=df_res, y='Results_Label', palette='mako',
                      order=df_res['Results_Label'].value_counts().index)
        plt.title('State of the Art Knowledge (Macro Results)', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Mentions')
        plt.ylabel('Macro Result Category')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}.png")

    def _generate_micro_label(self, df, column, filename):
        df['Results_Micro_Label'] = df[column].apply(
            lambda x: extract_micro_multiple(x, RESULT_CATS)
        )
        df_micro = df.explode('Results_Micro_Label').reset_index(drop=True)
        plt.figure(figsize=(8, 5))
        sns.countplot(data=df_micro, y='Results_Micro_Label', palette='flare',
                      order=df_micro['Results_Micro_Label'].value_counts().index)
        plt.title('Fine-Grained Discoveries (Micro Results)', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Mentions')
        plt.ylabel('Micro Result Value')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_approach_over_time(self,df, column, filename):
        # Year must be present in the csv
        df['Approach_Label'] = df[column].apply(
            lambda x: categorize_multiple(x, ANNOTATION_TARGETS["Approach"])
        )
        df_app = df.explode('Approach_Label').reset_index(drop=True)
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df_app, x='Year', hue='Approach_Label', multiple="stack", palette='cubehelix', binwidth=1)
        plt.title('Evolution of Researcher Interests (Approaches Over Time)', fontsize=14, fontweight='bold')
        plt.xticks(sorted(df_app['Year'].dropna().unique()))
        plt.ylabel('Number of Papers')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_results_over_time(self,df, column, filename):
        # Year must be present in the csv
        df['Results_Label'] = df[column].apply(
            lambda x: categorize_multiple(x, RESULT_CATS)
        )
        df_res_yr = df.explode('Results_Label').reset_index(drop=True)
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df_res_yr, x='Year', hue='Results_Label', multiple="stack", palette='mako', binwidth=1)
        plt.title('Evolution of Scientific Discoveries (Macro Results Over Time)', fontsize=14, fontweight='bold')
        plt.xticks(sorted(df['Year'].dropna().unique()))
        plt.ylabel('Number of Papers')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_micro_over_time(self,df, column, filename):
        # Year must be present in the csv
        df['Results_Micro_Label'] = df[column].apply(
            lambda x: extract_micro_multiple(x, RESULT_CATS)
        )
        df_micro_yr = df.explode('Results_Micro_Label').reset_index(drop=True)
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df_micro_yr, x='Year', hue='Results_Micro_Label', multiple="stack", palette='flare',
                     binwidth=1)
        plt.title('Evolution of Fine-Grained Discoveries (Micro Results Over Time)', fontsize=14, fontweight='bold')
        plt.xticks(sorted(df['Year'].dropna().unique()))
        plt.ylabel('Number of Papers')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_source_focus(self, df, column, filename):
        # Database must be present in the csv
        plt.figure(figsize=(8, 6))
        sns.countplot(data=df, x=column, hue='Database', palette='Set1')
        plt.title('Literature Focus by Database Source', fontsize=14, fontweight='bold')
        plt.ylabel('Number of Papers')
        plt.legend(title='Database', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_citations_focus(self, df, column, filename):
        # Citation Number must be present in the csv
        plt.figure(figsize=(8, 6))
        sns.boxplot(data=df, x=column, y='Citation Number', palette='Pastel1')
        sns.stripplot(data=df, x=column, y='Citation Number', color=".25", size=6, jitter=True)
        plt.title('Citations Distribution based on Paper Focus', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_role_over_year(self, df , column, filename):
        # Year must be present in the csv
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df, x='Year', hue=column, multiple="stack", palette='Set2', binwidth=1)
        plt.title('Evolution of UK Biobank Usage Over Time', fontsize=14, fontweight='bold')
        plt.xticks(sorted(df['Year'].dropna().unique()))
        plt.ylabel('Number of Papers')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_focus_citation_time(self, df, column, filename):
        # Year and Citation Number must be present in the csv
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df, x='Year', y='Citation Number', hue=column, size='Citation Number',
                        sizes=(50, 500), alpha=0.7, palette='Dark2')
        plt.title('Citation Trends Over Years Segmented by Focus', fontsize=14, fontweight='bold')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
        plt.xticks(sorted(df['Year'].dropna().unique()))
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_approach_results(self, df, column, filename):
        df['Results_Label'] = df[column].apply(
            lambda x: categorize_multiple(x, RESULT_CATS)
        )
        df['Approach_Label'] = df['Approach'].apply(
            lambda x: categorize_multiple(x, ANNOTATION_TARGETS["Approach"])
        )
        df_exploded = df.explode('Approach_Label').explode('Results_Label').reset_index(drop=True)
        cross_tab = pd.crosstab(df_exploded['Approach_Label'], df_exploded['Results_Label'])
        plt.figure(figsize=(8, 6))
        sns.heatmap(cross_tab, annot=True, cmap='Blues', fmt='d', linewidths=.5)
        plt.title('Heatmap: Approach vs. Macro Results', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")

    def _generate_approach_micro(self, df, column, filename):
        df['Results_Micro_Label'] = df[column].apply(
            lambda x: extract_micro_multiple(x, RESULT_CATS)
        )
        df['Approach_Label'] = df['Approach'].apply(
            lambda x: categorize_multiple(x, ANNOTATION_TARGETS["Approach"])
        )
        df_exploded = df.explode('Approach_Label').explode('Results_Micro_Label').reset_index(drop=True)
        cross_tab = pd.crosstab(df_exploded['Approach_Label'], df_exploded['Results_Micro_Label'])
        plt.figure(figsize=(10, 6))
        sns.heatmap(cross_tab, annot=True, cmap='Purples', fmt='d', linewidths=.5)
        plt.title('Fine-Grained Heatmap: Approach vs. Micro Results', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(REVIEW_OUTPUT_DIR, filename))
        plt.close()
        self.logger.info(f"Successfully generated: {filename}")
