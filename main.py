#Done By
#Tejesh
#Abijith
#Shriram

import requests
import json
from datetime import datetime


def fetch_categories(limit=5):
    """Fetch limited number of categories from TheMealDB API"""
    base_url = "https://www.themealdb.com/api/json/v1/1/"
    response = requests.get(f"{base_url}list.php?c=list")
    if response.status_code == 200:
        return [category['strCategory'] for category in response.json()['meals'][:limit]]
    return []


def fetch_recipes_by_category(category, limit=2):
    """Fetch limited recipes in a specific category"""
    base_url = "https://www.themealdb.com/api/json/v1/1/"
    response = requests.get(f"{base_url}filter.php?c={category}")
    if response.status_code == 200:
        return response.json()['meals'][:limit]
    return []


def fetch_recipe_details(recipe_id):
    """Fetch detailed information for a specific recipe"""
    base_url = "https://www.themealdb.com/api/json/v1/1/"
    response = requests.get(f"{base_url}lookup.php?i={recipe_id}")
    if response.status_code == 200:
        return response.json()['meals'][0]
    return None


def save_to_json(data, filename):
    """Save data to a JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data saved to {filename}")


def main():
    # Initialize data structure
    all_recipes = {
        "metadata": {
            "source": "TheMealDB API",
            "extracted_on": datetime.now().isoformat(),
            "categories_limit": 5,
            "recipes_per_category": 2,
            "total_recipes": 0
        },
        "categories": {}
    }

    # Get 5 categories
    categories = fetch_categories(5)
    print(f"Selected {len(categories)} categories: {', '.join(categories)}")

    # Process each category
    for category in categories:
        print(f"\nProcessing category: {category}")
        all_recipes["categories"][category] = []

        # Get 2 recipes in this category
        recipes = fetch_recipes_by_category(category, 2)
        if not recipes:
            continue

        # Process each recipe in the category
        for recipe in recipes:
            recipe_id = recipe['idMeal']
            print(f"  Fetching details for: {recipe['strMeal']} (ID: {recipe_id})")

            # Get full recipe details
            recipe_details = fetch_recipe_details(recipe_id)
            if recipe_details:
                all_recipes["categories"][category].append(recipe_details)
                all_recipes["metadata"]["total_recipes"] += 1

    # Save the collected data
    output_filename = f"limited_themealdb_recipes_{datetime.now().strftime('%Y%m%d')}.json"
    save_to_json(all_recipes, output_filename)

    print(
        f"\nCompleted! Saved {all_recipes['metadata']['total_recipes']} recipes (2 each from {len(categories)} categories) to {output_filename}")


import sqlite3


def print_recipes(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM recipes")
    recipes = cursor.fetchall()

    print("\nStored Recipes:")
    for recipe in recipes:
        print(f"{recipe[0]}: {recipe[1]}")

    conn.close()


import requests
import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    """Create a database connection to a SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to SQLite database: {db_file}")
        return conn
    except Error as e:
        print(e)
    return conn


def create_table(conn):
    """Create recipes table if it doesn't exist"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS recipes
                       (
                           id
                           TEXT
                           PRIMARY
                           KEY,
                           title
                           TEXT
                           NOT
                           NULL,
                           ingredients
                           TEXT
                           NOT
                           NULL,
                           instructions
                           TEXT
                           NOT
                           NULL
                       )
                       """)
        conn.commit()
        print("Created 'recipes' table")
    except Error as e:
        print(e)


def fetch_recipe_details(recipe_id):
    """Fetch detailed information for a specific recipe from TheMealDB API"""
    base_url = "https://www.themealdb.com/api/json/v1/1/"
    response = requests.get(f"{base_url}lookup.php?i={recipe_id}")
    if response.status_code == 200:
        return response.json()['meals'][0]
    return None


def parse_ingredients(recipe_data):
    """Extract and format ingredients with measurements"""
    if not recipe_data:  # Add this check
        return ""

    ingredients = []
    for i in range(1, 21):
        ingredient = recipe_data.get(f'strIngredient{i}', '')
        measure = recipe_data.get(f'strMeasure{i}', '')
        if ingredient and isinstance(ingredient, str) and measure and isinstance(measure, str):  # Added type checks
            ingredients.append(f"{measure.strip()} {ingredient.strip()}")
    return ", ".join(ingredients)


def insert_recipe(conn, recipe_data):
    """Insert recipe data into the database"""
    sql = """INSERT OR REPLACE INTO recipes(id, title, ingredients, instructions)
              VALUES(?,?,?,?)"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            recipe_data['idMeal'],
            recipe_data['strMeal'],
            parse_ingredients(recipe_data),
            recipe_data['strInstructions']
        ))
        conn.commit()
        print(f"Inserted recipe: {recipe_data['strMeal']}")
        return cursor.lastrowid
    except Error as e:
        print(f"Error inserting recipe {recipe_data['idMeal']}: {e}")
    return None


def setup_db():
    # Database setup
    database = "recipes.db"
    conn = create_connection(database)

    if conn is not None:
        create_table(conn)

        # Example recipe IDs - you can modify this list
        recipe_ids = [
            "52772",  # Teriyaki Chicken Casserole
            "52874",  # Beef and Oyster pie
            "52928",  # Toad In The Hole
            "53013",  # Big Mac
            "52977"  # Corba (Turkish soup)
        ]

        # Fetch and store each recipe
        for recipe_id in recipe_ids:
            recipe_data = fetch_recipe_details(recipe_id)
            if recipe_data:
                insert_recipe(conn, recipe_data)

        conn.close()
        print("Database connection closed")
    else:
        print("Error! Cannot create the database connection.")


import xml.etree.ElementTree as ET
from fractions import Fraction

import xml.etree.ElementTree as ET
from fractions import Fraction


def parse_measurement(measure_str):
    """Separate quantity and unit from measurement string"""
    try:
        # Try to parse fraction/number at start of string
        parts = measure_str.split(maxsplit=1)
        if len(parts) > 0:
            try:
                quantity = str(Fraction(parts[0]))
                unit = parts[1] if len(parts) > 1 else ""
                return quantity, unit
            except (ValueError, TypeError):
                return "", measure_str
        return "", measure_str
    except AttributeError:
        return "", measure_str



import re


def highlight_actions(instruction_text):
    """Wrap action verbs in <action> tags"""
    action_verbs = ["chop", "mix", "stir", "heat", "preheat", "bake", "fry",
                    "whisk", "boil", "simmer", "dice", "slice", "grate",
                    "pour", "add", "season", "cook", "beat", "fold"]

    # Create regex pattern that matches whole words only
    pattern = re.compile(r'\b(' + '|'.join(action_verbs) + r')\b', re.IGNORECASE)

    # Replace matches while preserving original capitalization
    def wrap_match(match):
        return f"<action>{match.group(0)}</action>"

    return pattern.sub(wrap_match, instruction_text)


def export_to_xml(db_file, xml_file):
    """Export all recipes from database to XML file"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes")
    recipes = cursor.fetchall()
    conn.close()

    root = ET.Element("recipes")

    for recipe in recipes:
        recipe_elem = ET.SubElement(root, "recipe")
        ET.SubElement(recipe_elem, "id").text = recipe[0]
        ET.SubElement(recipe_elem, "title").text = recipe[1]

        # Ingredients with separated quantity/unit
        ingredients_elem = ET.SubElement(recipe_elem, "ingredients")
        for ingredient_line in recipe[2].split(","):
            ingredient_line = ingredient_line.strip()
            if ingredient_line:
                ingredient_elem = ET.SubElement(ingredients_elem, "ingredient")
                quantity, unit = parse_measurement(ingredient_line)
                ET.SubElement(ingredient_elem, "quantity").text = quantity
                ET.SubElement(ingredient_elem, "unit").text = unit
                ET.SubElement(ingredient_elem, "item").text = ingredient_line.replace(f"{quantity} {unit}", "").strip()

        # Instructions with highlighted actions
        instructions_elem = ET.SubElement(recipe_elem, "instructions")
        instructions_text = highlight_actions(recipe[3])
        instructions_elem.text = instructions_text

    # Write to XML file
    tree = ET.ElementTree(root)
    tree.write(xml_file, encoding='utf-8', xml_declaration=True)
    print(f"Successfully exported recipes to {xml_file}")

from lxml import etree


def transform_to_html(xml_file, xslt_file, output_html):
    """Transform XML to HTML using XSLT"""
    try:
        # Parse XML and XSLT
        xml = etree.parse(xml_file)
        xslt = etree.parse(xslt_file)

        # Create transformer and apply transformation
        transform = etree.XSLT(xslt)
        html = transform(xml)

        # Write output
        with open(output_html, 'wb') as f:
            f.write(html)

        print(f"Successfully created HTML page at {output_html}")
    except Exception as e:
        print(f"Error transforming XML to HTML: {e}")

# Add this at the end of your __main__ block:
if __name__ == "__main__":
    main()
    setup_db()
    print_recipes("recipes.db")
    export_to_xml("recipes.db", "recipes.xml")  # Add this line
    transform_to_html("recipes.xml", "recipes.xslt", "recipes.html")  # Add this line

