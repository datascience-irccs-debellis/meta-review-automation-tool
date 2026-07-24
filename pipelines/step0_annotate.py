# pipelines/step0_annotate.py
import os
import pandas as pd
from config import RAW_REVIEW_DATABASE_PATH, ANNOTATED_REVIEW_DATABASE_PATH, ANNOTATION_TARGETS
from core.logger import setup_logger


class AnnotationPipeline:
    def __init__(self):
        self.logger = setup_logger("Step0_Annotation")

    def run(self):
        self.logger.info("Starting Step 0: Interactive Annotation Pipeline...")

        if not os.path.exists(RAW_REVIEW_DATABASE_PATH):
            self.logger.error(f"Input file not found: {RAW_REVIEW_DATABASE_PATH}")
            return

        df = pd.read_csv(RAW_REVIEW_DATABASE_PATH)
        self.logger.info(f"Loaded {len(df)} records for annotation.")
        # The first key of the annotation target must be the interested approach, without it we cannot delete N.A. paper
        df = df[df[list(ANNOTATION_TARGETS.keys())[0]].apply(lambda x: x != 'N.A.')]
        self.logger.info(f"Validated {len(df)} records for annotation.")

        for column, valid_options in ANNOTATION_TARGETS.items():
            if column not in df.columns:
                self.logger.warning(f"Annotation target column '{column}' not found in CSV. Skipping.")
                continue

            self.logger.info(f"--- Annotating Column: '{column}' ---")
            df = self._process_column(df, column, valid_options)

        df.to_csv(ANNOTATED_REVIEW_DATABASE_PATH, index=False)
        self.logger.info(f"Annotation complete. Standardized data saved to '{ANNOTATED_REVIEW_DATABASE_PATH}'")

    def _process_column(self, df, column_name, valid_options):
        for index, row in df.iterrows():
            current_values = str(row[column_name]).split(",")


            # If the value is already valid (or blank/NA), skip it
            if pd.isna(row[column_name]):
               continue

            correct_values = []
            for current_value in current_values:
                if current_value.strip() not in valid_options:
                    # --- Start Interactive Session ---
                    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen

                    print("=" * 60)
                    print(f"Record {index + 1} of {len(df)} | Column: '{column_name}'")
                    print("=" * 60)

                    # Display context from the paper (Title, Authors)
                    title = row.get('Title', 'N/A')
                    authors = row.get('Authors', 'N/A').split(',')[0] + ' et al.' if pd.notna(row.get('Authors')) else 'N/A'
                    print(f"Title: {title[:70]}...")
                    print(f"Author: {authors}")
                    print("-" * 60)

                    print(f"Current (unrecognized) value: '{current_value}'")
                    print("\nPlease select the correct category:")

                    for i, option in enumerate(valid_options):
                        print(f"  [{i + 1}] {option}")

                    while True:
                        choice = input("Enter number of your choice, or (s) to skip this record: ").strip().lower()
                        if choice == 's':
                            self.logger.info(f"Record {index + 1}: Skipped manual annotation for '{current_value}'.")
                            break
                        try:
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(valid_options):
                                chosen_option = valid_options[choice_idx]
                                correct_values.append(chosen_option)
                                self.logger.info(f"Record {index + 1}: Changed '{current_value}' -> '{chosen_option}'")
                                break
                            else:
                                print("Invalid number. Please try again.")
                        except ValueError:
                            print("Invalid input. Please enter a number or 's'.")
                else:
                    correct_values.append(current_value)
            df.at[index, column_name] = ", ".join(correct_values)

        return df