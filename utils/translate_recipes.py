# ----------------------------------------------------------------------------------------------------
# Recipe translation script using OpenAI API to translate structured JSON recipes
# ----------------------------------------------------------------------------------------------------
import json
import argparse
from pathlib import Path
from openai import OpenAI
from tqdm.auto import tqdm
from models import RecipeInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
# ----------------------------------------------------------------------------------------------------
LANGUAGE_CODE_TO_NAME = {
    "en": "English",
    "es": "Spanish",
    "ca": "Catalan",
    "da": "Danish",
}
# ----------------------------------------------------------------------------------------------------
def translate_recipe(
    recipe: dict,
    source_language: str,
    target_language: str,
    client: OpenAI
) -> dict:
    """Translate a recipe into the target language using OpenAI API.

    Args:
        recipe: Recipe data dict
        source_language: Source language code (e.g., "es")
        target_language: Target language code (e.g., "en")

    Returns:
        dict: Translated recipe data
    """
    recipe_json = json.dumps(recipe, ensure_ascii=False, indent=4)

    response = client.responses.parse(
        input=[
            {
                "role": "system",
                "content": f"""
                You are an expert recipe translator.
                Translate the following recipe from {source_language} into {LANGUAGE_CODE_TO_NAME[target_language]}.
                Keep the JSON structure intact.

                IMPORTANT: TRANSLATE ALL RECIPE CONTENT
                The input is a structured JSON recipe. Translate every textual field
                (title, ingredient names, quantities, preparation steps, notes) into the
                target language. Do NOT modify non-text fields (e.g., source_language, id).

                Guidelines:
                - Translate using correct culinary vocabulary in the target language.
                - Regional/specialty ingredients: use the natural culinary equivalent.
                - Preserve the name/quantity split: name = ingredient identity only,
                  quantity = all numeric values and units.
                - Do NOT invent, garble, or mix languages. If unsure, keep the original term.
                - Keep proper nouns with correct capitalization.
                - Output must read naturally to a native speaker with correct grammar,
                  spelling, and diacritics.

                This is the schema:
                {RecipeInfo.model_json_schema()}
                """,
            },
            {
                "role": "user",
                "content": f"""
                This is the recipe content:
                {recipe_json}
                """,
            }
        ],
        text_format=RecipeInfo,
    )

    translated = response.output_parsed
    output = translated.model_dump()
    output["source_language"] = source_language
    output["target_language"] = target_language
    output["id"] = f"{recipe['id']}.target.{target_language}"
    return output

def _run_task(task, client):
    """Wrapper to call translate_recipe and write the output file."""
    recipe, source_language, target_language, output_dir, output_name = task
    translated_data = translate_recipe(
        recipe=recipe,
        source_language=source_language,
        target_language=target_language,
        client=client,
    )
    output_path = Path(output_dir) / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(translated_data, output_file, indent=4, ensure_ascii=False)

def run_translation_tasks(
    tasks,
    client,
    max_workers,
    desc="Translating recipes",
):
    """Execute translation tasks in parallel and write output files."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_task, task, client) for task in tasks]
        for future in tqdm(as_completed(futures), total=len(futures), desc=desc):
            future.result()
# ----------------------------------------------------------------------------------------------------
def main():
    """Main entry point for the recipe translation script."""
    parser = argparse.ArgumentParser(
        description="Translate structured recipe JSON files into multiple languages."
    )
    parser.add_argument(
        "--recipe-dir",
        type=str,
        default="data/recipes",
        help="Path to the recipe directory (default: data/recipes)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=12,
        help="Maximum number of parallel workers (default: 12)",
    )
    parser.add_argument(
        "--target-languages",
        type=str,
        default="en,es,ca,da",
        help="Comma-separated list of target language codes (default: en,es,ca,da)",
    )
    args = parser.parse_args()

    target_languages = [lang.strip() for lang in args.target_languages.split(",")]

    client = OpenAI(
        base_url="http://localhost:3960/v1",
        api_key="EMPTY"
    )

    recipe_directory = Path(args.recipe_dir)
    if not recipe_directory.exists():
        print(f"Recipe directory not found: {recipe_directory}")
        return

    source_json_files = sorted(recipe_directory.rglob("*.source.*.json"))
    source_json_files = [
        source_json_file for source_json_file in source_json_files
        if ".source." in source_json_file.name and ".target." not in source_json_file.name
    ]

    target_tasks = []
    for source_json_file in source_json_files:
        with open(source_json_file, "r", encoding="utf-8") as json_file:
            source_json_data = json.load(json_file)
        source_language = source_json_data["source_language"]
        for target_language in target_languages:
            if target_language == source_language:
                continue
            base = source_json_file.stem
            output_name = f"{base}.target.{target_language}.json"
            target_tasks.append(
                (source_json_data, source_language, target_language, source_json_file.parent, output_name)
            )
    run_translation_tasks(
        tasks=target_tasks,
        client=client,
        max_workers=args.max_workers,
        desc="Translating recipes",
    )

# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------
