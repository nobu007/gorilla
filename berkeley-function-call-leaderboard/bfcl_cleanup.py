#!/usr/bin/env python3
"""
BFCL Selective Cleanup Utility

This utility allows selective deletion of test results that failed or scored below a threshold.
Usage: python bfcl_cleanup.py --model <model_name> [--threshold <percentage>] [--dry-run]
"""

import json
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Set


def load_test_categories() -> Dict[str, Dict[str, str]]:
    """Load the mapping of test categories to their file patterns."""
    # Based on the directory structure we observed
    return {
        # Non-live tests
        "simple_java": {
            "score": "non_live/BFCL_v4_simple_java_score.json",
            "result": "non_live/BFCL_v4_simple_java_result.json"
        },
        "simple_javascript": {
            "score": "non_live/BFCL_v4_simple_javascript_score.json",
            "result": "non_live/BFCL_v4_simple_javascript_result.json"
        },
        "simple_python": {
            "score": "non_live/BFCL_v4_simple_python_score.json",
            "result": "non_live/BFCL_v4_simple_python_result.json"
        },
        "parallel": {
            "score": "non_live/BFCL_v4_parallel_score.json",
            "result": "non_live/BFCL_v4_parallel_result.json"
        },
        "parallel_multiple": {
            "score": "non_live/BFCL_v4_parallel_multiple_score.json",
            "result": "non_live/BFCL_v4_parallel_multiple_result.json"
        },
        "multiple": {
            "score": "non_live/BFCL_v4_multiple_score.json",
            "result": "non_live/BFCL_v4_multiple_result.json"
        },
        "irrelevance": {
            "score": "non_live/BFCL_v4_irrelevance_score.json",
            "result": "non_live/BFCL_v4_irrelevance_result.json"
        },

        # Live tests
        "live_simple": {
            "score": "live/BFCL_v4_live_simple_score.json",
            "result": "live/BFCL_v4_live_simple_result.json"
        },
        "live_parallel": {
            "score": "live/BFCL_v4_live_parallel_score.json",
            "result": "live/BFCL_v4_live_parallel_result.json"
        },
        "live_multiple": {
            "score": "live/BFCL_v4_live_multiple_score.json",
            "result": "live/BFCL_v4_live_multiple_result.json"
        },
        "live_parallel_multiple": {
            "score": "live/BFCL_v4_live_parallel_multiple_score.json",
            "result": "live/BFCL_v4_live_parallel_multiple_result.json"
        },
        "live_relevance": {
            "score": "live/BFCL_v4_live_relevance_score.json",
            "result": "live/BFCL_v4_live_relevance_result.json"
        },
        "live_irrelevance": {
            "score": "live/BFCL_v4_live_irrelevance_score.json",
            "result": "live/BFCL_v4_live_irrelevance_result.json"
        },

        # Multi-turn tests
        "multi_turn_base": {
            "score": "multi_turn/BFCL_v4_multi_turn_base_score.json",
            "result": "multi_turn/BFCL_v4_multi_turn_base_result.json"
        },
        "multi_turn_miss_func": {
            "score": "multi_turn/BFCL_v4_multi_turn_miss_func_score.json",
            "result": "multi_turn/BFCL_v4_multi_turn_miss_func_result.json"
        },
        "multi_turn_miss_param": {
            "score": "multi_turn/BFCL_v4_multi_turn_miss_param_score.json",
            "result": "multi_turn/BFCL_v4_multi_turn_miss_param_result.json"
        },
        "multi_turn_long_context": {
            "score": "multi_turn/BFCL_v4_multi_turn_long_context_score.json",
            "result": "multi_turn/BFCL_v4_multi_turn_long_context_result.json"
        },

        # Agentic tests
        "web_search_base": {
            "score": "agentic/BFCL_v4_web_search_base_score.json",
            "result": "agentic/BFCL_v4_web_search_base_result.json"
        },
        "web_search_no_snippet": {
            "score": "agentic/BFCL_v4_web_search_no_snippet_score.json",
            "result": "agentic/BFCL_v4_web_search_no_snippet_result.json"
        },
        "memory_vector": {
            "score": "agentic/memory/vector/BFCL_v4_memory_vector_score.json",
            "result": "agentic/memory/vector/BFCL_v4_memory_vector_result.json"
        },
        "memory_rec_sum": {
            "score": "agentic/memory/rec_sum/BFCL_v4_memory_rec_sum_score.json",
            "result": "agentic/memory/rec_sum/BFCL_v4_memory_rec_sum_result.json"
        },
        "memory_kv": {
            "score": "agentic/memory/kv/BFCL_v4_memory_kv_score.json",
            "result": "agentic/memory/kv/BFCL_v4_memory_kv_result.json"
        },
    }


def get_accuracy_from_file(file_path: str) -> float:
    """Extract accuracy from a score JSON file."""
    try:
        with open(file_path, 'r') as f:
            first_line = f.readline().strip()
            if first_line:
                data = json.loads(first_line)
                return data.get("accuracy", 0.0)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return 0.0


def find_failed_tests(model_name: str, threshold: float) -> List[str]:
    """Find test categories that scored below the threshold."""
    base_dir = Path("score") / model_name
    categories = load_test_categories()
    failed_tests = []

    for category, file_patterns in categories.items():
        file_path = base_dir / file_patterns["score"]
        if file_path.exists():
            accuracy = get_accuracy_from_file(str(file_path))
            print(f"{category}: {accuracy:.2f}%")
            if accuracy < threshold:
                failed_tests.append(category)
        else:
            print(f"{category}: File not found")
            failed_tests.append(category)  # Treat missing files as failed

    return failed_tests


def delete_test_results(model_name: str, categories: List[str], dry_run: bool = True) -> List[str]:
    """Delete result files for specified test categories."""
    score_dir = Path("score") / model_name
    result_dir = Path("result") / model_name
    all_categories = load_test_categories()
    deleted_files = []

    for category in categories:
        if category in all_categories:
            file_patterns = all_categories[category]

            # Delete score file
            score_file = score_dir / file_patterns["score"]
            if score_file.exists():
                if dry_run:
                    print(f"[DRY RUN] Would delete score: {score_file}")
                else:
                    try:
                        score_file.unlink()
                        print(f"Deleted score: {score_file}")
                        deleted_files.append(str(score_file))
                    except OSError as e:
                        print(f"Error deleting score {score_file}: {e}")
            else:
                print(f"Score file not found: {score_file}")

            # Delete result file
            result_file = result_dir / file_patterns["result"]
            if result_file.exists():
                if dry_run:
                    print(f"[DRY RUN] Would delete result: {result_file}")
                else:
                    try:
                        result_file.unlink()
                        print(f"Deleted result: {result_file}")
                        deleted_files.append(str(result_file))
                    except OSError as e:
                        print(f"Error deleting result {result_file}: {e}")
            else:
                print(f"Result file not found: {result_file}")

            # For memory and agentic tests, also delete the entire directory structure
            if category.startswith("memory_") or category.startswith("web_search_"):
                memory_dir = result_dir / file_patterns["result"].rsplit("/", 1)[0]
                if memory_dir.exists() and memory_dir.is_dir():
                    if dry_run:
                        print(f"[DRY RUN] Would delete directory: {memory_dir}")
                    else:
                        try:
                            import shutil
                            shutil.rmtree(memory_dir)
                            print(f"Deleted directory: {memory_dir}")
                            deleted_files.append(str(memory_dir))
                        except OSError as e:
                            print(f"Error deleting directory {memory_dir}: {e}")
        else:
            print(f"Unknown category: {category}")

    return deleted_files


def list_all_results(model_name: str) -> None:
    """List all test results and their accuracies."""
    base_dir = Path("score") / model_name
    categories = load_test_categories()

    print(f"\n=== Test Results for {model_name} ===")
    for category, file_patterns in sorted(categories.items()):
        file_path = base_dir / file_patterns["score"]
        if file_path.exists():
            accuracy = get_accuracy_from_file(str(file_path))
            status = "✅ PASS" if accuracy > 0 else "❌ FAIL"
            print(f"{category:20} {accuracy:6.2f}% {status}")
        else:
            print(f"{category:20} N/A     ❌ MISSING")


def main():
    parser = argparse.ArgumentParser(
        description="Selective cleanup utility for BFCL test results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all results
  python bfcl_cleanup.py --model glm-4.5-FC --list

  # Show what would be deleted (dry run)
  python bfcl_cleanup.py --model glm-4.5-FC --threshold 10 --dry-run

  # Actually delete failed tests (scoring below threshold)
  python bfcl_cleanup.py --model glm-4.5-FC --threshold 10

  # Delete specific categories
  python bfcl_cleanup.py --model glm-4.5-FC --categories web_search_base,memory_vector
        """
    )

    parser.add_argument("--model", required=True, help="Model name (e.g., glm-4.5-FC, glm-4.6-FC)")
    parser.add_argument("--threshold", type=float, default=1.0,
                       help="Accuracy threshold below which tests are considered failed (default: 1.0)")
    parser.add_argument("--categories", help="Comma-separated list of specific categories to delete")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be deleted without actually deleting")
    parser.add_argument("--list", action="store_true", help="List all test results and accuracies")

    args = parser.parse_args()

    # Check if model directory exists
    model_dir = Path("score") / args.model
    if not model_dir.exists():
        print(f"Error: Model directory '{model_dir}' not found.")
        sys.exit(1)

    if args.list:
        list_all_results(args.model)
        return

    if args.categories:
        # Delete specific categories
        categories = [cat.strip() for cat in args.categories.split(",")]
        print(f"Deleting specific categories: {categories}")
    else:
        # Find failed tests based on threshold
        print(f"Finding tests with accuracy < {args.threshold}%...")
        failed_tests = find_failed_tests(args.model, args.threshold)

        if not failed_tests:
            print("No tests found below the threshold.")
            return

        print(f"\nFound {len(failed_tests)} tests to delete:")
        for test in failed_tests:
            print(f"  - {test}")

        categories = failed_tests

    if not args.dry_run:
        # Ask for confirmation
        print(f"\n{'='*50}")
        print("WARNING: This will permanently delete test result files!")
        print(f"Categories to delete: {len(categories)}")
        print(f"Model: {args.model}")
        print(f"{'='*50}")

        response = input("Are you sure you want to continue? (y/N): ").lower()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return
    else:
        print(f"\n[DRY RUN] Would delete {len(categories)} test result files:")

    # Delete the files
    deleted_files = delete_test_results(args.model, categories, args.dry_run)

    if args.dry_run:
        print(f"\n[DRY RUN] Total files that would be deleted: {len(deleted_files)}")
    else:
        print(f"\nSuccessfully deleted {len(deleted_files)} files.")
        print("You can now re-run the evaluation for these specific categories.")


if __name__ == "__main__":
    main()