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

    # Database setup
    database = "recipes.db"
    conn = create_connection(database)
    if conn is not None:
        create_table(conn)
    else:
        print("Error! Cannot create the database connection.")
        return

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
                # Add to JSON structure
                all_recipes["categories"][category].append(recipe_details)
                all_recipes["metadata"]["total_recipes"] += 1

                # Insert into database
                insert_recipe(conn, recipe_details)

    # Save the collected data to JSON
    output_filename = f"limited_themealdb_recipes_{datetime.now().strftime('%Y%m%d')}.json"
    save_to_json(all_recipes, output_filename)

    # Close database connection
    conn.close()
    print("Database connection closed")

    print(
        f"\nCompleted! Saved {all_recipes['metadata']['total_recipes']} recipes (2 each from {len(categories)} categories) to both JSON and database")


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
            CREATE TABLE IF NOT EXISTS recipes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                instructions TEXT NOT NULL,
                calories REAL
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
    ingredients = parse_ingredients(recipe_data)
    calories = calculate_calories(ingredients)

    sql = """INSERT OR REPLACE INTO recipes(id, title, ingredients, instructions, calories)
              VALUES(?,?,?,?,?)"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            recipe_data['idMeal'],
            recipe_data['strMeal'],
            ingredients,
            recipe_data['strInstructions'],
            calories
        ))
        conn.commit()
        print(f"Inserted recipe: {recipe_data['strMeal']} (Calories: {calories})")
        return cursor.lastrowid
    except Error as e:
        print(f"Error inserting recipe {recipe_data['idMeal']}: {e}")
    return None

import xml.etree.ElementTree as ET


def parse_measurement(measure_str):
    """Separate quantity, unit, and item from measurement string"""
    measure_str = measure_str.strip()
    if not measure_str:
        return "", "", ""

    # Common unit abbreviations and their full forms
    unit_mapping = {
        'tbs': 'tablespoon', 'tbsp': 'tablespoon', 'tablespoons': 'tablespoon',
        'tsp': 'teaspoon', 'teaspoons': 'teaspoon',
        'ml': 'milliliter', 'l': 'liter',
        'g': 'gram', 'kg': 'kilogram',
        'cup': 'cup', 'cups': 'cup',
        'pinch': 'pinch', 'dash': 'dash',
        'oz': 'ounce', 'lb': 'pound'
    }

    # Split into parts
    parts = re.split(r'(\d+[/.]?\d*|\s+)', measure_str)
    parts = [p.strip() for p in parts if p.strip()]

    if not parts:
        return "", "", measure_str

    # Extract quantity (first numeric part)
    quantity = ""
    remaining_parts = []
    for i, part in enumerate(parts):
        if re.match(r'^\d+[/.]?\d*$', part):
            quantity = part
            remaining_parts = parts[i + 1:]
            break
        else:
            remaining_parts.append(part)

    if not remaining_parts:
        return quantity, "", ""

    # Check if the first remaining part is a known unit
    unit = ""
    item_parts = remaining_parts

    # Try to match known units
    for abbrev, full_unit in unit_mapping.items():
        # Check if any part matches a unit (abbreviation or full)
        for i, part in enumerate(remaining_parts):
            if part.lower() == abbrev or part.lower() == full_unit:
                unit = full_unit
                item_parts = remaining_parts[:i] + remaining_parts[i + 1:]
                break
        if unit:
            break

    # If no unit found and quantity exists, consider first word as item
    if not unit and quantity:
        if len(remaining_parts) > 1:
            # Check if first word looks like a unit (plural/singular forms)
            first_word = remaining_parts[0].lower()
            if first_word.endswith('s') and first_word[:-1] in unit_mapping.values():
                unit = first_word[:-1]  # Remove 's' to get singular form
                item_parts = remaining_parts[1:]
            else:
                # No unit found, treat everything as item
                item_parts = remaining_parts
        else:
            # Only one word remaining, treat as item
            item_parts = remaining_parts

    item = " ".join(item_parts).strip()

    # Special case: if the entire string was a quantity (like "200ml")
    if not item and unit and quantity:
        item = unit
        unit = ""

    return quantity, unit, item



import re


def highlight_actions(instruction_text):
    """Wrap action verbs in <action> tags"""
    action_verbs = [
        # Heat-related
        "preheat", "heat", "reheat", "warm", "toast", "bake", "broil", "grill",
        "roast", "sear", "fry", "deep-fry", "pan-fry", "saute", "sizzle",
        "simmer", "boil", "steam", "poach", "blanch", "scald", "reduce",

        # Mixing/Prep
        "mix", "stir", "whisk", "beat", "fold", "blend", "combine", "knead",
        "massage", "toss", "shake", "whip", "cream", "emulsify",

        # Cutting
        "chop", "dice", "mince", "slice", "cut", "julienne", "cube", "shred",
        "grate", "peel", "zest", "segment", "trim", "butterfly", "fillet",

        # Adding
        "add", "pour", "drizzle", "sprinkle", "dust", "coat", "layer", "top",
        "garnish", "decorate", "stuff", "fill", "insert", "inject",

        # Cooking processes
        "cook", "caramelize", "glaze", "reduce", "thicken", "reduce",
        "render", "smoke", "infuse", "steep", "marinate", "brine", "cure",
        "ferment", "proof", "rise", "rest", "chill", "freeze", "thaw",

        # Specific actions
        "season", "salt", "pepper", "flavor", "spice", "rub", "brush", "glaze",
        "baste", "drain", "strain", "sieve", "filter", "press", "mash", "puree",
        "blitz", "process", "grind", "crush", "pound", "tenderize", "juice",

        # Serving
        "plate", "serve", "portion", "divide", "share", "arrange", "present",

        # Special techniques
        "flambe", "sous-vide", "temper", "clarify", "deglaze", "reduce",
        "thicken", "bind", "emulsify", "aerate", "fold", "laminate",

        # From your recipes
        "spray", "shred", "steam", "cover", "remove", "reserve", "break",
        "congratulate", "pick", "rinse", "drain", "set", "bloom", "blend",
        "taste", "crush", "tear", "thicken", "store", "keep", "wait", "go",
        "settle", "jog", "place", "transfer", "check", "cool", "assemble",
        "trim", "crimp", "bring", "allow", "sit", "melt", "form", "flatten",
        "char", "repeat", "carefully", "lightly", "spread", "finish", "wait",
        "gently", "return", "let", "enjoy"
    ]

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
        ET.SubElement(recipe_elem, "calories").text = str(recipe[4])  # Add calories

        # Ingredients with separated quantity/unit/item
        ingredients_elem = ET.SubElement(recipe_elem, "ingredients")
        for ingredient_line in recipe[2].split(","):
            ingredient_line = ingredient_line.strip()
            if ingredient_line:
                ingredient_elem = ET.SubElement(ingredients_elem, "ingredient")
                quantity, unit, item = parse_measurement(ingredient_line)  # Changed to unpack 3 values
                ET.SubElement(ingredient_elem, "quantity").text = quantity
                ET.SubElement(ingredient_elem, "unit").text = unit
                ET.SubElement(ingredient_elem, "item").text = item

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

import urllib.parse
import time


def calculate_calories(ingredients_str):
    """Calculate calories by querying each ingredient separately"""
    if not ingredients_str:
        return "N/A"

    # Split into individual ingredients (comma-separated)
    ingredients = [ing.strip() for ing in ingredients_str.split(",") if ing.strip()]
    if not ingredients:
        return "N/A"

    total_calories = 0
    failed_queries = 0
    api_key = "hDQLYashT6x+0JXeW/MNjQ==uj9EubnJF1h6QTbG"

    for ingredient in ingredients:
        try:
            url = f"https://api.calorieninjas.com/v1/nutrition?query={urllib.parse.quote(ingredient)}"
            headers = {"X-Api-Key": api_key} if api_key != "YOUR_API_KEY" else {}

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                items = response.json().get("items", [])
                if items:
                    total_calories += sum(item["calories"] for item in items)
                else:
                    failed_queries += 1
            else:
                print(f"API error for '{ingredient}': {response.text}")
                failed_queries += 1

            # Be gentle with the free API
            time.sleep(0.5 if not api_key else 0.1)

        except Exception as e:
            print(f"Error processing '{ingredient}': {str(e)}")
            failed_queries += 1

    # Return results based on success rate
    if failed_queries == len(ingredients):
        return "N/A (all queries failed)"
    elif failed_queries > 0:
        return f"{round(total_calories)}"
    return round(total_calories)

# Add this at the end of your __main__ block:
if __name__ == "__main__":
    main()
    print_recipes("recipes.db")
    export_to_xml("recipes.db", "recipes.xml")  # Add this line
    transform_to_html("recipes.xml", "recipes.xslt", "recipes.html")  # Add this line

