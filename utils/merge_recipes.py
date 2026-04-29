# ----------------------------------------------------------------------------------------------------
# Script to merge all recipe JSON files into a single JSONL file.
# Recursively finds all .json files in data/recipes and writes them as
# newline-delimited JSON to data/recipes.jsonl.
# ----------------------------------------------------------------------------------------------------
import json
import argparse
# ----------------------------------------------------------------------------------------------------
from pathlib import Path
# ----------------------------------------------------------------------------------------------------
def merge_recipes_to_jsonl(
    recipe_dir: Path,
    output_file: Path,
) -> None:
    """Merge all recipe JSON files into a single JSONL file.

    Args:
        recipe_dir: Directory containing recipe JSON files
        output_file: Path to write the merged JSONL file
    """
    with open(output_file, "w", encoding="utf-8") as jsonl_file:
        for recipe_json_file in recipe_dir.rglob("*.json"):
            try:
                with open(recipe_json_file, "r", encoding="utf-8") as recipe_file:
                    recipe = json.load(recipe_file)
                    # Write each recipe as a single line of JSON
                    jsonl_file.write(json.dumps(recipe, ensure_ascii=False) + "\n")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error processing {recipe_json_file}: {e}")
# ----------------------------------------------------------------------------------------------------
def main():
    """Main entry point for the merge script."""
    # Setup command line argument parser
    parser = argparse.ArgumentParser(
        description="Merge all recipe JSON files into a single JSONL file."
    )
    parser.add_argument(
        "--recipe-dir",
        type=str,
        default="data/recipes",
        help="Path to the recipe directory (default: data/recipes)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/recipes.jsonl",
        help="Output JSONL file path (default: data/recipes.jsonl)",
    )
    args = parser.parse_args()

    # Validate recipe directory
    recipe_directory = Path(args.recipe_dir)
    if not recipe_directory.exists():
        print(f"Recipe directory not found: {recipe_directory}")
        return

    output_file = Path(args.output)

    # Merge all recipe files
    merge_recipes_to_jsonl(recipe_directory, output_file)
    print(f"Output written to: {output_file}")
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------
