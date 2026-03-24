# ----------------------------------------------------------------------------------------------------
import os
import json
import multiprocessing
# ----------------------------------------------------------------------------------------------------
from typing import List
from pathlib import Path
from openai import OpenAI
from tqdm.auto import tqdm
from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor, as_completed
# ----------------------------------------------------------------------------------------------------
class IngredientItem(
    BaseModel
):
    name: str = Field(
        title="name",
        description="""
        DESCRIPTION: Name of the ingredient.
        EXTRACTION INSTRUCTIONS:
        - Do NOT include the quantity in the name field.
        - If the ingredient line starts with a quantity (e.g., "500 g of pork ribs..."), extract ONLY the quantity part (e.g., "500 g") and put the rest as the ingredient name (e.g., "pork ribs...").
        """
    )
    quantity: str | None = Field(
        title="quantity",
        description="""
        DESCRIPTION: Quantity of the ingredient.
        EXTRACTION INSTRUCTIONS:
        - Standalone numbers that appear BEFORE an ingredient name are quantities (e.g., "1 onion" -> quantity: "1", name: "onion"); (e.g., "2 or 3 green chilies" -> quantity: "2 or 3", name: "green chilies").
        - Numbers at the start of ingredient lines are quantities, NOT list enumeration markers.
        - Include units when present (e.g., "50 g", "1 litre", "2 tablespoons").
        - Include descriptive quantities (e.g., "a little", "a handful", "a few minutes").
        - Normalize number words to digits: "one" -> "1", "a" -> "1", "an" -> "1", "two" -> "2", "three" -> "3", "four" -> "4", "five" -> "5", "six" -> "6", "seven" -> "7", "eight" -> "8", "nine" -> "9", "of a" -> "1".
        - For ranges, extract the full range (e.g., "3-4 olives" -> quantity: "3-4").
        - If no quantity is specified, return null.
        """
    )

class IngredientGroup(
    BaseModel
):
    group: str | None = Field(
        title="group",
        description="Name of the ingredient group"
    )
    items: List[IngredientItem] = Field(
        title="items",
        description="List of ingredients in this group"
    )

class RecipeInfo(
    BaseModel
):
    title: str = Field(
        title="title",
        description="Recipe title"
    )
    servings: str | None = Field(
        title="servings",
        description="""
        DESCRIPTION: Number of people the recipe serves.
        EXTRACTION INSTRUCTIONS:
        - Extract the number of people the recipe serves.
        - ONLY extract if there is an explicit statement about how many people the recipe serves.
        - Preserve the EXACT text as it appears in the original recipe: include units, descriptors, and full phrases.
        - Do NOT extract numbers that are just page numbers or section markers.
        - If no explicit servings information is found, return null.
        """
    )
    ingredients: List[IngredientGroup] = Field(
        title="ingredients",
        description="""
        DESCRIPTION: List of ingredient groups with their items.
        EXTRACTION INSTRUCTIONS:
        - Extract all ingredients from ingredient lists.
        - Group ingredients by section headers, even if short or minimal (e.g., "Desuden").
        - If no grouping is evident, put all ingredients in a single group with null.
        """
    )
    preparation: str | list[str] = Field(
        title="preparation",
        description="""
        DESCRIPTION: Step-by-step cooking/preparation instructions.
        EXTRACTION INSTRUCTIONS:
        - Extract step-by-step cooking/preparation instructions.
        - Look for numbered steps or sections with cooking/preparation instructions.
        - Return as a list of strings if steps are numbered, otherwise return as a single string.
        """
    )
    preparation_time: str | None = Field(
        title="preparation_time",
        description="""
        DESCRIPTION: Cooking/preparation time.
        EXTRACTION INSTRUCTIONS:
        - Extract cooking/preparation time durations mentioned in the recipe.
        - If no cooking/preparation time is found, return null.
        """
    )
    notes: str | None = Field(
        title="notes",
        description="""
        DESCRIPTION: Nutritional information, tips or additional comments.
        EXTRACTION INSTRUCTIONS:
        - Extract nutritional information, tips, or additional comments found in the recipe.
        - If no notes are found, return null.
        """
    )
# ----------------------------------------------------------------------------------------------------
def extract_recipe_from_file(
    file_path: str,
    client: OpenAI
) -> RecipeInfo:
    """Read and extract recipe information from an MD file."""

    with open(file_path, "r", encoding="utf-8") as input_file:
        content = input_file.read()

    response = client.responses.parse(
        input=[
            {
                "role": "system",
                "content": f"""
                Extract the recipe information from the provided Markdown recipe.
                Use plain text only, no Markdown formatting such as bold or italics.
                You are ONLY allowed to extract information that is explicitly present in the recipe.
                Do NOT invent information, add values that are not there, or make up data.

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
def main() -> None:
    """Process recipe files and extract structured information."""

    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="EMPTY"
    )

    recipe_directory = Path("data/recipes")
    md_files = list(recipe_directory.rglob("*.md"))

    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        future_to_file = {
            executor.submit(extract_recipe_from_file, str(md_file), client): md_file
            for md_file in md_files
        }
        for future in tqdm(as_completed(future_to_file), total=len(future_to_file), desc="Extracting recipes"):
            recipe_file = future_to_file[future]
            try:
                recipe_data = future.result()
                output_json_file = recipe_file.with_suffix(".json")
                with open(output_json_file, "w", encoding="utf-8") as output_file:
                    json.dump(recipe_data.model_dump(), output_file, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Error processing {recipe_file}: {e}")
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------
