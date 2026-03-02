# ----------------------------------------------------------------------------------------------------
import os
import json
# ----------------------------------------------------------------------------------------------------
from typing import List
from pathlib import Path
from openai import OpenAI
from tqdm.auto import tqdm
from pydantic import BaseModel, Field
# ----------------------------------------------------------------------------------------------------
class IngredientItem(
    BaseModel
):
    name: str = Field(
        title="name",
        description="Name of the ingredient"
    )
    quantity: str | None = Field(
        title="quantity",
        description="Quantity of the ingredient, can be None"
    )

class IngredientGroup(
    BaseModel
):
    group: str | None = Field(
        title="group",
        description="Name of the ingredient group, can be None for flat ingredient lists"
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
    ingredients: List[IngredientGroup] = Field(
        title="ingredients",
        description="List of ingredient groups with their items"
    )
    preparation: str | list[str] = Field(
        title="preparation",
        description="Step-by-step preparation instructions, can be a string or a list of strings"
    )
    notes: str | None = Field(
        title="notes",
        description="Additional notes about the recipe, can be None"
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
                Extract the recipe information from the provided markdown recipe.
                Use plain text only, no markdown formatting such as bold or italics.
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
        text_format=RecipeInfo
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

    for recipe_file in tqdm(md_files, desc="Extracting recipes"):
        recipe_data = extract_recipe_from_file(str(recipe_file), client)
        output_json_file = recipe_file.with_suffix(".json")
        with open(output_json_file, "w", encoding="utf-8") as output_file:
            json.dump(recipe_data.model_dump(), output_file, indent=4, ensure_ascii=False)
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------