#!/usr/bin/env python3
"""
Convert Paprika export files into a Nextcloud Cookbook–compatible folder structure.

Usage:
  python3 convert_paprika_to_nextcloud.py [input_path] [output_dir]

- If [input_path] is a directory, it processes all files ending with ".paprikarecipe".
- If [input_path] is a file (e.g. "My Recipes.paprikarecipes"), it is treated as a zip archive
  containing multiple ".paprikarecipe" files.

Each .paprikarecipe file is expected to be a gzip-compressed JSON file.
The script converts each recipe to a minimal schema.org/Recipe JSON format and writes it to
a folder named after a sanitized version of the recipe’s name. If "photo_data" is present,
it decodes that into a file called "full.jpg" and updates the "image" field accordingly.
"""

import sys
import os
import re
import json
import base64
import gzip
import shutil
import zipfile

def safe_dirname(name):
    """Return a filesystem-safe folder name from a recipe title."""
    s = name.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^\w\-]", "", s)
    return s or "unnamed_recipe"

def paprika_to_schemaorg(paprika_json):
    """
    Convert a Paprika recipe JSON (extracted from a .paprikarecipe file)
    to a minimal schema.org/Recipe dictionary.
    """
    name = paprika_json.get("name", "Untitled")
    image = paprika_json.get("image_url", "")
    directions = []
    if "directions" in paprika_json and isinstance(paprika_json["directions"], str):
        directions = [line.strip() for line in paprika_json["directions"].split("\n") if line.strip()]
    ingredients = []
    if "ingredients" in paprika_json and isinstance(paprika_json["ingredients"], str):
        ingredients = [line.strip() for line in paprika_json["ingredients"].split("\n") if line.strip()]

    schema = {
        "@context": "https://schema.org/",
        "@type": "Recipe",
        "name": name,
        "image": image,  # This will be replaced if photo_data is decoded.
        "recipeIngredient": ingredients,
        "recipeInstructions": directions,
        "description": paprika_json.get("description", ""),
        "cookTime": paprika_json.get("cook_time", ""),
        "prepTime": paprika_json.get("prep_time", ""),
        "totalTime": paprika_json.get("total_time", ""),
        "recipeYield": paprika_json.get("servings", ""),
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": paprika_json.get("rating", 0),
            "ratingCount": 1
        },
        "author": paprika_json.get("source", ""),
        "url": paprika_json.get("source_url", ""),
        "notes": paprika_json.get("notes", ""),
        "difficulty": paprika_json.get("difficulty", ""),
        "nutritionalInfo": paprika_json.get("nutritional_info", ""),
        "category": paprika_json.get("categories", []),
    }
    return schema

def process_recipe_data(paprika_data, output_dir, source_name=""):
    """
    Given a Paprika JSON (already loaded) from one recipe, convert and write
    it into the output directory.
    """
    schema_recipe = paprika_to_schemaorg(paprika_data)
    recipe_name = schema_recipe.get("name", "Untitled")
    folder_name = safe_dirname(recipe_name)
    recipe_folder = os.path.join(output_dir, folder_name)
    os.makedirs(recipe_folder, exist_ok=True)

    # Decode photo_data if present.
    photo_data = paprika_data.get("photo_data")
    if photo_data:
        try:
            raw = base64.b64decode(photo_data)
            full_path = os.path.join(recipe_folder, "full.jpg")
            with open(full_path, "wb") as fimg:
                fimg.write(raw)
            schema_recipe["image"] = "full.jpg"
        except Exception as e:
            print(f"Error decoding photo for recipe '{recipe_name}': {e}")

    # Write recipe.json.
    out_json_path = os.path.join(recipe_folder, "recipe.json")
    try:
        with open(out_json_path, "w", encoding="utf-8") as jf:
            json.dump(schema_recipe, jf, indent=2, ensure_ascii=False)
        print(f"Converted {source_name or recipe_name} -> {out_json_path}")
    except Exception as e:
        print(f"Error writing recipe '{recipe_name}': {e}")

def process_paprikarecipe_file(file_path, output_dir):
    """
    Process a single .paprikarecipe file (assumed to be gzip-compressed JSON).
    """
    try:
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            paprika_data = json.load(f)
        process_recipe_data(paprika_data, output_dir, source_name=os.path.basename(file_path))
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")

def process_bulk_export(zip_path, output_dir):
    """
    Process a bulk export file (e.g. ending with .paprikarecipes) that is a zip archive
    containing multiple .paprikarecipe files.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                if member.lower().endswith(".paprikarecipe"):
                    try:
                        with zf.open(member) as mf:
                            # Each member is still a gzip-compressed file.
                            compressed_data = mf.read()
                            # Decompress the gzip data.
                            text_data = gzip.decompress(compressed_data).decode("utf-8")
                            paprika_data = json.loads(text_data)
                            process_recipe_data(paprika_data, output_dir, source_name=member)
                    except Exception as e:
                        print(f"Error processing member {member} in {zip_path}: {e}")
    except Exception as e:
        print(f"Error processing bulk export file {zip_path}: {e}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 convert_paprika_to_nextcloud.py [input_path] [output_dir]")
        sys.exit(1)
    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    if os.path.isdir(input_path):
        # Process all .paprikarecipe files in the directory.
        for fname in os.listdir(input_path):
            file_path = os.path.join(input_path, fname)
            if os.path.isfile(file_path) and fname.lower().endswith(".paprikarecipe"):
                process_paprikarecipe_file(file_path, output_dir)
    elif os.path.isfile(input_path):
        # If the input is a file, check its extension.
        if input_path.lower().endswith(".paprikarecipes"):
            # This is a bulk export file (zip archive).
            process_bulk_export(input_path, output_dir)
        elif input_path.lower().endswith(".paprikarecipe"):
            process_paprikarecipe_file(input_path, output_dir)
        else:
            print(f"Unrecognized file type: {input_path}")
    else:
        print(f"Error: {input_path} is neither a directory nor a file.")
        sys.exit(1)

    print("Done. Output is in:", output_dir)

if __name__ == "__main__":
    main()
