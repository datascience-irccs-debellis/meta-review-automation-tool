# main.py
import argparse
from pipelines.step0_annotate import AnnotationPipeline
from pipelines.step1_meta_review import MetaReviewPipeline
from pipelines.step2_meta_analysis import MetaAnalysisPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Meta-Analysis Toolkit: A configurable pipeline for systematic reviews."
    )

    parser.add_argument(
        '--step',
        type=int,
        choices=[0, 1, 2],
        help="Specify which pipeline to run: 0 (Interactive-annotation), 1 (Meta-Review) or 2 (Meta-Analysis)."
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help="Run all steps (0, 1, 2) in sequence."
    )

    args = parser.parse_args()

    if args.all or args.step == 0:
        print("\n" + "=" * 50)
        print(" INITIALIZING STEP 0: INTERACTIVE ANNOTATION")
        print("=" * 50)
        pipeline0 = AnnotationPipeline()
        pipeline0.run()

    if args.all or args.step == 1:
        print("\n" + "=" * 50)
        print(" INITIALIZING STEP 1: META-REVIEW PIPELINE ")
        print("=" * 50)
        pipeline1 = MetaReviewPipeline()
        pipeline1.run()

    if args.all or args.step == 2:
        print("\n" + "=" * 50)
        print(" INITIALIZING STEP 2: META-ANALYSIS PIPELINE ")
        print("=" * 50)
        pipeline2 = MetaAnalysisPipeline()
        pipeline2.run()

    if not args.step and not args.all:
        parser.print_help()


if __name__ == "__main__":
    main()