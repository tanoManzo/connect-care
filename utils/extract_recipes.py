# ----------------------------------------------------------------------------------------------------
# Recipe extraction script using OpenAI API to parse Markdown files into structured JSON
# ----------------------------------------------------------------------------------------------------
import os
import json
import argparse
# ----------------------------------------------------------------------------------------------------
from typing import List
from pathlib import Path
from openai import OpenAI
from tqdm.auto import tqdm
from models import RecipeInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
# ----------------------------------------------------------------------------------------------------
def extract_recipe_from_file(
    file_path: str,
    client: OpenAI
) -> RecipeInfo:
    """Read and extract recipe information from a Markdown file using OpenAI API.

    Args:
        file_path: Path to the Markdown file containing the recipe
        client: OpenAI client instance

    Returns:
        RecipeInfo: Structured recipe data in the source language
    """
    # Read the Markdown content from file
    with open(file_path, "r", encoding="utf-8") as input_file:
        content = input_file.read()

    # Call OpenAI API to parse and extract structured recipe data
    response = client.responses.parse(
        input=[
            {
                "role": "system",
                "content": f"""
                You are an expert recipe extraction assistant.
                Extract structured recipe information from the provided Markdown text.
                Keep all extracted text in the same language as the source.

                IMPORTANT: IGNORE PAGE NOISE
                The input Markdown may contain HTML tags, image references, navigation menus,
                footer links, and other web-scraping artifacts. Focus ONLY on the recipe content
                (title, ingredients, preparation steps, cooking time, nutritional notes).
                Discard all navigation, menus, image references, and boilerplate text.

                Guidelines:
                - You MUST use plain text only.
                - Do NOT invent, infer, or make up any data.
                - ONLY extract information that is explicitly present in the recipe.
                
                This is the schema:
                {RecipeInfo.model_json_schema()}
                """,
            },
            {
                "role": "user",
                "content": content,
            }
        ],
        text_format=RecipeInfo
    )

    return response.output_parsed
# ----------------------------------------------------------------------------------------------------
def main():
    """Main entry point for the recipe extraction script."""
    # Setup command line argument parser
    parser = argparse.ArgumentParser(
        description="Extract structured recipe information from Markdown files."
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
    args = parser.parse_args()

    # Initialize OpenAI client (connecting to local API server)
    client = OpenAI(
        base_url="http://localhost:3960/v1",
        api_key="EMPTY"
    )

    # Validate recipe directory
    recipe_directory = Path(args.recipe_dir)
    if not recipe_directory.exists():
        print(f"Recipe directory not found: {recipe_directory}")
        return

    # Find all Markdown files recursively
    md_files = list(recipe_directory.rglob("*.md"))

    # # Test with first recipe from each subfolder
    # md_files = [
    #     Path("data/recipes/amed.cat/carns-i-ous/conilla-rostida.md"),
    #     Path("data/recipes/canalsalut.gencat.cat/postres/batut-maduixa-platan-llet-00001.md"),
    #     Path("data/recipes/codinucat.cat/receptes-per-a-l-hivern/dolc-final/boles-de-coco.md"),
    #     Path("data/recipes/hjerteforeningen/aftensmad/2-stykker-smoerrebroed.md"),
    #     Path("data/recipes/hverdagsopskrifter/blomkaalstaerte.md"),
    #     Path("data/recipes/recetario-comunitario-intercultural/albondigas.md"),
    #     Path("data/recipes/sumavidasana.org/brochetas-de-fruta-con-fondue-de-menta.md"),
    # ]

    # Process files in parallel using thread pool
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # Submit all extraction tasks
        future_to_file = {
            executor.submit(extract_recipe_from_file, str(md_file), client): md_file
            for md_file in md_files
        }

        # Process results as they complete
        for future in tqdm(as_completed(future_to_file), total=len(future_to_file), desc="Extracting recipes"):
            recipe_file = future_to_file[future]
            try:
                recipe_data = future.result()

                # Generate unique recipe ID from relative path
                relative_path = recipe_file.relative_to(recipe_directory)
                recipe_id = f"{relative_path.with_suffix('')}.source.{recipe_data.source_language}"

                # Write extracted data to JSON file
                output_json_file = recipe_file.with_name(f"{recipe_file.stem}.source.{recipe_data.source_language}.json")
                with open(output_json_file, "w", encoding="utf-8") as output_file:
                    recipe_dict = recipe_data.model_dump()
                    recipe_dict["id"] = recipe_id
                    json.dump(recipe_dict, output_file, indent=4, ensure_ascii=False)

            except Exception as e:
                print(f"Error processing {recipe_file}: {e}")
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------