# ----------------------------------------------------------------------------------------------------
# Recipe extraction script using OpenAI API to parse Markdown files into structured JSON
# Extracts recipe data (title, ingredients, preparation, etc.) and translates to multiple languages
# ----------------------------------------------------------------------------------------------------
import os
import json
import argparse
# ----------------------------------------------------------------------------------------------------
from typing import List
from pathlib import Path
from openai import OpenAI
from tqdm.auto import tqdm
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor, as_completed
# ----------------------------------------------------------------------------------------------------
class MultilingualText(BaseModel):
    """Model for text content in multiple languages (EN, ES, CA, DA)."""
    en: str | None = Field(
        title="en",
        description="""
        DESCRIPTION: English translation.
        EXTRACTION INSTRUCTIONS:
        - Translate into English.
        - Return JSON null (not the string "null") if the value cannot be extracted.
        """
    )
    es: str | None = Field(
        title="es",
        description="""
        DESCRIPTION: Spanish translation.
        EXTRACTION INSTRUCTIONS:
        - Translate into Spanish.
        - Return JSON null (not the string "null") if the value cannot be extracted.
        """
    )
    ca: str | None = Field(
        title="ca",
        description="""
        DESCRIPTION: Catalan translation.
        EXTRACTION INSTRUCTIONS:
        - Translate into Catalan.
        - Return JSON null (not the string "null") if the value cannot be extracted.
        """
    )
    da: str | None = Field(
        title="da",
        description="""
        DESCRIPTION: Danish translation.
        EXTRACTION INSTRUCTIONS:
        - Translate into Danish.
        - Return JSON null (not the string "null") if the value cannot be extracted.
        """
    )


class IngredientItem(BaseModel):
    """Model for a single ingredient with name and quantity in multiple languages."""
    name: MultilingualText = Field(
        title="name",
        description="""
        DESCRIPTION: Name of the ingredient.
        EXTRACTION INSTRUCTIONS:
        - Extract and translate the ingredient name into English, Spanish, Catalan, and Danish.
        - Do NOT include the quantity in the name field.
        - If the ingredient line starts with a quantity (e.g., "500 g of pork ribs..."), extract ONLY the quantity part (e.g., "500 g") and put the rest as the ingredient name (e.g., "pork ribs...").
        """
    )
    quantity: MultilingualText = Field(
        title="quantity",
        description="""
        DESCRIPTION: Quantity of the ingredient.
        EXTRACTION INSTRUCTIONS:
        - Extract and translate the quantity into English, Spanish, Catalan, and Danish.
        - Standalone numbers that appear BEFORE an ingredient name are quantities (e.g., "1 onion" -> quantity: "1", name: "onion"); (e.g., "2 or 3 green chilies" -> quantity: "2 or 3", name: "green chilies").
        - Numbers at the start of ingredient lines are quantities, NOT list enumeration markers.
        - Include units when present (e.g., "50 g", "1 litre", "2 tablespoons").
        - Include descriptive quantities (e.g., "a little", "a handful", "a few minutes").
        - Normalize number words to digits: "one" -> "1", "a" -> "1", "an" -> "1", "two" -> "2", "three" -> "3", "four" -> "4", "five" -> "5", "six" -> "6", "seven" -> "7", "eight" -> "8", "nine" -> "9", "of a" -> "1".
        - Convert Unicode fraction characters to ASCII format: "¼" -> "1/4", "½" -> "1/2", "¾" -> "3/4", "⅓" -> "1/3", "⅔" -> "2/3", "⅕" -> "1/5", etc.
        - For ranges, extract the full range (e.g., "3-4 olives" -> quantity: "3-4").
        - Preserve numeric values the same across all languages, only translate unit words and descriptive terms.
        - If there is NO explicit quantity, return JSON null (not the string "null") for all languages.
        """
    )


class RecipeInfo(BaseModel):
    """Main model containing all structured recipe information."""
    title: MultilingualText = Field(
        title="title",
        description="""
        DESCRIPTION: Recipe title.
        EXTRACTION INSTRUCTIONS:
        - Extract and translate the recipe title into English, Spanish, Catalan, and Danish.
        """
    )
    servings: MultilingualText = Field(
        title="servings",
        description="""
        DESCRIPTION: Number of people the recipe serves.
        EXTRACTION INSTRUCTIONS:
        - Extract and translate the number of people the recipe serves into English, Spanish, Catalan, and Danish.
        - ONLY extract if there is an explicit statement about how many people the recipe serves.
        - Do NOT extract numbers that are just page numbers or section markers.
        - If there is NO explicit servings information, return JSON null (not the string "null") for all languages.
        """
    )
    ingredients: List[IngredientItem] = Field(
        title="ingredients",
        description="""
        DESCRIPTION: List of ingredients.
        EXTRACTION INSTRUCTIONS:
        - Extract and translate all ingredients into English, Spanish, Catalan, and Danish.
        """
    )
    preparation: MultilingualText = Field(
        title="preparation",
        description="""
        DESCRIPTION: Cooking/preparation instructions.
        EXTRACTION INSTRUCTIONS:
        - Extract and translate cooking/preparation instructions into English, Spanish, Catalan, and Danish.
        """
    )
    preparation_time: MultilingualText = Field(
        title="preparation_time",
        description="""
        DESCRIPTION: Cooking/preparation time.
        EXTRACTION INSTRUCTIONS:
        - Extract and translate cooking/preparation time durations into English, Spanish, Catalan, and Danish.
        - Preserve the original format exactly (e.g., "1:30 h", "45 min", "2 hours").
        - If there is NO explicit preparation time, return JSON null (not the string "null") for all languages.
        """
    )
    notes: MultilingualText = Field(
        title="notes",
        description="""
        DESCRIPTION: Nutritional information, tips or additional comments.
        EXTRACTION INSTRUCTIONS:
        - Extract and translate nutritional information, tips, or additional comments into English, Spanish, Catalan, and Danish.
        - If there is NO explicit notes information, return JSON null (not the string "null") for all languages.
        """
    )
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
        RecipeInfo: Structured recipe data with multilingual translations
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
                You are an expert multilingual recipe extraction assistant.
                Extract structured recipe information from the provided Markdown text and translate all the content into four languages: English (en), Spanish (es), Catalan (ca), and Danish (da).

                Guidelines:
                - Use plain text only, without any Markdown formatting such as bold or italics.
                - ONLY extract information that is explicitly present in the recipe.
                - Do NOT invent, infer, or make up any data.
                - Translate all extracted text into English, Spanish, Catalan, and Danish.
                - All output must be valid UTF-8 encoded text using proper characters for each language.

                This is the schema:
                {RecipeInfo.model_json_schema()}
                """,
            },
            {
                "role": "user",
                "content": content,
            }
        ],
        text_format=RecipeInfo,
        temperature=0
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
        api_key="EMPTY",
        timeout=1200,
    )

    # Validate recipe directory
    recipe_directory = Path(args.recipe_dir)
    if not recipe_directory.exists():
        print(f"Recipe directory not found: {recipe_directory}")
        return

    # Find all Markdown files recursively
    md_files = list(recipe_directory.rglob("*.md"))
    # md_files = [Path("data/recipes/canalsalut.gencat.cat/primers-plats/pate-olives.md")]

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
                recipe_id = str(relative_path.with_suffix(""))

                # Write extracted data to JSON file
                output_json_file = recipe_file.with_suffix(".json")
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
