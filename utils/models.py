# ----------------------------------------------------------------------------------------------------
from typing import List, Literal
from pydantic import BaseModel, Field
# ----------------------------------------------------------------------------------------------------

class IngredientItem(BaseModel):
    """Model for a single ingredient with name and quantity."""
    name: str = Field(
        title="name",
        description="""
        DESCRIPTION: Name of the ingredient.
        EXTRACTION INSTRUCTIONS:
        - Extract the name of the ingredient with quality adjectives (e.g., "ripe strawberries", "crispy chicken").
        - Do NOT include count, unit, or measure word. Those go in quantity.
        - Convert to lowercase.
        """
    )
    quantity: str | None = Field(
        title="quantity",
        description="""
        DESCRIPTION: Quantity of the ingredient.
        EXTRACTION INSTRUCTIONS:
        - Extract the quantity of the ingredient: the numeric value and unit.
        - Always put a space between the number and the unit (e.g., "350 g" not "350g").
        - Include measure words (e.g., "2 slices", "2 tbsp", "1/2").
        - If no quantity is mentioned, return JSON null.
        """
    )


class IngredientSections(BaseModel):
    """Model for a section of ingredients with a section name."""
    section_name: str = Field(
        title="section_name",
        description="""
        DESCRIPTION: Name of the ingredient section.
        EXTRACTION INSTRUCTIONS:
        - Extract the section name.
        - Capitalize the first letter.
        """
    )
    ingredients: List[IngredientItem] = Field(
        title="ingredients",
        description="""
        DESCRIPTION: List of ingredients in this section.
        EXTRACTION INSTRUCTIONS:
        - Extract all the ingredients in this section.
        """
    )


class RecipeInfo(BaseModel):
    """Main model containing all structured recipe information."""
    title: str = Field(
        title="title",
        description="""
        DESCRIPTION: Recipe title.
        EXTRACTION INSTRUCTIONS:
        - Extract the recipe title.
        - Capitalize the first letter.
        """
    )
    servings: str | None = Field(
        title="servings",
        description="""
        DESCRIPTION: Number of people the recipe serves.
        EXTRACTION INSTRUCTIONS:
        - Extract the number of people the recipe serves.
        - Preserve context, e.g., "4 people" not just "4".
        - If no servings information is mentioned, return JSON null.
        """
    )
    ingredient_sections: List[IngredientSections] = Field(
        title="ingredient_sections",
        description="""
        DESCRIPTION: List of ingredient sections.
        EXTRACTION INSTRUCTIONS:
        - Extract all ingredient sections from the recipe.
        - If a section name is not clear, use the translation of "Ingredients" into the source language.
        """
    )
    preparation: str | None = Field(
        title="preparation",
        description="""
        DESCRIPTION: Cooking/preparation instructions.
        EXTRACTION INSTRUCTIONS:
        - Extract all cooking/preparation instructions including any tips or notes about adjusting consistency.
        - Remove step numbers (e.g., "1.", "2.") and bullet points from the instructions.
        - Capitalize the first letter.
        - If no cooking/preparation instructions are mentioned, return JSON null.
        """
    )
    preparation_time: str | None = Field(
        title="preparation_time",
        description="""
        DESCRIPTION: Cooking/preparation time.
        EXTRACTION INSTRUCTIONS:
        - Extract the cooking/preparation time.
        - Preserve the format exactly as it appears (e.g., "1:30 h", "45 min", "2 hours").
        - If no cooking/preparation time is mentioned, return JSON null.
        """
    )
    notes: str | None = Field(
        title="notes",
        description="""
        DESCRIPTION: Nutritional information, tips or additional comments.
        EXTRACTION INSTRUCTIONS:
        - Extract nutritional information, tips or additional comments.
        - Remove step numbers and bullet points from the text.
        - Capitalize the first letter.
        - If no notes are mentioned, return JSON null.
        """
    )
    source_language: Literal["en", "es", "ca", "da"] = Field(
        title="source_language",
        description="""
        DESCRIPTION: Language code of the recipe source.
        EXTRACTION INSTRUCTIONS:
        - Set to the language code (en, es, ca, or da).
        """
    )
