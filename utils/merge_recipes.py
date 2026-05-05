# ----------------------------------------------------------------------------------------------------
# Script to merge recipe JSON files by language into per-language JSONL files.
# Recursively finds all .source.*.json and .target.*.json files in data/recipes,
# groups them by language code, and writes one JSONL per language.
# ----------------------------------------------------------------------------------------------------
import json
import argparse
# ----------------------------------------------------------------------------------------------------
from pathlib import Path
from collections import defaultdict
# ----------------------------------------------------------------------------------------------------
def merge_recipes_by_language(recipe_dir: Path, output_dir: Path = None) -> None:
    """Merge recipe JSON files into per-language JSONL files.

    Files matching *.source.<language>.json or *.target.<language>.json are grouped
    by language and written to recipes.<language>.jsonl.

    Args:
        recipe_dir: Directory containing recipe JSON files
        output_dir: Directory to write per-language JSONL files
    """
    language_recipes = defaultdict(list)

    for recipe_json_file in recipe_dir.rglob("*.json"):
        name = recipe_json_file.name
        # Extract language from *.source.<language>.json or *.target.<language>.json
        if ".source." not in name and ".target." not in name:
            continue
        language = name.rsplit(".", 2)[-2]

        with open(recipe_json_file, "r", encoding="utf-8") as f:
            recipe = json.load(f)
            language_recipes[language].append(recipe)

    for language, recipes in language_recipes.items():
        output_file = output_dir / f"recipes.{language}.jsonl"
        with open(output_file, "w", encoding="utf-8") as jsonl_file:
            for recipe in recipes:
                jsonl_file.write(json.dumps(recipe, ensure_ascii=False) + "\n")
 # ----------------------------------------------------------------------------------------------------
def main():
    """Main entry point for the merge script."""
    parser = argparse.ArgumentParser(
        description="Merge recipe JSON files into per-language JSONL files."
    )
    parser.add_argument(
        "--recipe-dir",
        type=str,
        default="data/recipes",
        help="Path to the recipe directory (default: data/recipes)",
    )
    args = parser.parse_args()

    recipe_directory = Path(args.recipe_dir)
    if not recipe_directory.exists():
         return

    merge_recipes_by_language(recipe_directory, recipe_directory.parent)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------
