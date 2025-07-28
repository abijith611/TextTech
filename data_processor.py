import json
import re
import requests
import urllib.parse
import time
import config # Import config for CalorieNinjas API key and delay

def save_to_json(data: dict, filename: str):
    """
    Saves data to a JSON file.

    Args:
        data: The dictionary data to save.
        filename: The name of the JSON file.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to {filename}")
    except IOError as e:
        print(f"Error saving data to JSON file '{filename}': {e}")

def parse_ingredients(recipe_data: dict) -> str:
    """
    Extracts and formats ingredients with measurements from recipe data.

    Args:
        recipe_data: A dictionary containing recipe details from TheMealDB API.

    Returns:
        A comma-separated string of ingredients and their measurements.
        Returns an empty string if recipe_data is invalid or no ingredients found.
    """
    if not isinstance(recipe_data, dict):
        return ""

    ingredients = []
    for i in range(1, 21): # TheMealDB API provides up to 20 ingredients
        ingredient = recipe_data.get(f'strIngredient{i}', '').strip()
        measure = recipe_data.get(f'strMeasure{i}', '').strip()
        if ingredient and measure:
            ingredients.append(f"{measure} {ingredient}")
        elif ingredient: # Just the ingredient if measure is missing
            ingredients.append(ingredient)
    return ", ".join(ingredients)

def parse_measurement(measure_str: str) -> tuple[str, str, str]:
    """
    Separates quantity, unit, and item from a raw measurement string.

    Args:
        measure_str: The full measurement string (e.g., "1 cup flour", "2 large eggs").

    Returns:
        A tuple containing (quantity, unit, item).
    """
    measure_str = measure_str.strip()
    if not measure_str:
        return "", "", ""

    # Common unit abbreviations and their full forms
    unit_mapping = {
        'tbs': 'tablespoon', 'tbsp': 'tablespoon', 'tablespoons': 'tablespoon',
        'tsp': 'teaspoon', 'teaspoons': 'teaspoon',
        'ml': 'milliliter', 'l': 'liter', 'g': 'gram', 'kg': 'kilogram',
        'cup': 'cup', 'cups': 'cup', 'pinch': 'pinch', 'dash': 'dash',
        'oz': 'ounce', 'lb': 'pound', 'clove': 'clove', 'head': 'head',
        'sprig': 'sprig', 'stalk': 'stalk', 'can': 'can', 'packet': 'packet',
        'slice': 'slice', 'slices': 'slice', 'piece': 'piece', 'pieces': 'piece',
        'sheet': 'sheet', 'sheets': 'sheet', 'bottle': 'bottle'
    }

    # Regex to find quantity at the beginning (e.g., "1", "1/2", "2.5")
    # It handles whole numbers, fractions, and decimals.
    quantity_match = re.match(r'^(\d+\s*\d*/\d*|\d+\.\d+|\d+)\s*(.*)$', measure_str)

    quantity = ""
    remainder = measure_str

    if quantity_match:
        quantity = quantity_match.group(1).strip()
        remainder = quantity_match.group(2).strip()

    # Split the remainder into potential unit and item parts
    remainder_parts = remainder.split()

    unit = ""
    item_parts = []
    found_unit = False

    for i, part in enumerate(remainder_parts):
        lower_part = part.lower().rstrip('s') # Remove 's' to match singular units
        if lower_part in unit_mapping:
            unit = unit_mapping[lower_part] # Use the full form from mapping
            item_parts = remainder_parts[i+1:]
            found_unit = True
            break
        elif part.lower() in unit_mapping: # Check for exact match first (e.g., "cups")
            unit = unit_mapping[part.lower()]
            item_parts = remainder_parts[i+1:]
            found_unit = True
            break
        else:
            item_parts.append(part)

    item = " ".join(item_parts).strip()

    # Edge case: If quantity was extracted but no clear unit, and the remainder looks like an item
    # This also helps if the "unit" was actually part of the item, like "large" or "small"
    if not found_unit and remainder_parts and item == "":
        # If no unit was found, the whole remainder is the item
        item = remainder

    # Another edge case: If the original string was just a quantity and unit like "200ml"
    if not item and quantity and unit and measure_str.lower().startswith(f"{quantity.lower()}{unit.lower()}"):
        item = unit
        unit = ""


    return quantity, unit, item


def calculate_calories(ingredients_str: str) -> str | int:
    """
    Calculates total calories by querying a nutrition API for each ingredient.

    Args:
        ingredients_str: A comma-separated string of ingredients.

    Returns:
        The total calculated calories as an integer, or a descriptive string if
        API queries fail.
    """
    if not ingredients_str:
        return "N/A"

    ingredients = [ing.strip() for ing in ingredients_str.split(",") if ing.strip()]
    if not ingredients:
        return "N/A"

    total_calories = 0
    failed_queries = 0

    for ingredient in ingredients:
        try:
            url = f"{config.CALORIENINJAS_API_URL}?query={urllib.parse.quote(ingredient)}"
            headers = {"X-Api-Key": config.CALORIENINJAS_API_KEY} if config.CALORIENINJAS_API_KEY != "YOUR_API_KEY" else {}

            response = requests.get(url, headers=headers)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            items = response.json().get("items", [])
            if items:
                total_calories += sum(item["calories"] for item in items)
            else:
                failed_queries += 1
                # print(f"  No nutrition data found for '{ingredient}'") # Optional: debug output
        except requests.exceptions.RequestException as e:
            print(f"  API error for '{ingredient}': {e}")
            failed_queries += 1
        except json.JSONDecodeError as e:
            print(f"  JSON decode error for '{ingredient}': {e}")
            failed_queries += 1
        except Exception as e:
            print(f"  Unexpected error processing '{ingredient}': {str(e)}")
            failed_queries += 1

        # Be gentle with the API to avoid hitting rate limits
        time.sleep(config.CALORIENINJAS_API_DELAY)

    if failed_queries == len(ingredients):
        return "N/A (all queries failed)"
    elif failed_queries > 0:
        # Return approximate calories if some queries failed
        return f"{round(total_calories)} (partial)"
    return round(total_calories)

def highlight_actions(instruction_text: str) -> str:
    """
    Wraps common action verbs in the instruction text with <action> tags for highlighting.
    This uses a regex pattern to find whole words matching the action verbs.

    Args:
        instruction_text: The raw instruction string.

    Returns:
        The instruction string with action verbs highlighted within <action> tags.
    """
    action_verbs = [
        # Heat-related
        "preheat", "heat", "reheat", "warm", "toast", "bake", "broil", "grill",
        "roast", "sear", "fry", "deep-fry", "pan-fry", "saute", "sizzle",
        "simmer", "boil", "steam", "poach", "blanch", "scald", "reduce", "stir-fry",

        # Mixing/Prep
        "mix", "stir", "whisk", "beat", "fold", "blend", "combine", "knead",
        "massage", "toss", "shake", "whip", "cream", "emulsify", "incorporate",

        # Cutting
        "chop", "dice", "mince", "slice", "cut", "julienne", "cube", "shred",
        "grate", "peel", "zest", "segment", "trim", "butterfly", "fillet",
        "core", "pit", "devein",

        # Adding/Applying
        "add", "pour", "drizzle", "sprinkle", "dust", "coat", "layer", "top",
        "garnish", "decorate", "stuff", "fill", "insert", "inject", "apply", "spread",

        # Cooking processes
        "cook", "caramelize", "glaze", "thicken", "render", "smoke", "infuse", "steep",
        "marinate", "brine", "cure", "ferment", "proof", "rise", "rest", "chill",
        "freeze", "thaw", "drain", "strain", "sieve", "filter", "press", "mash",
        "puree", "blitz", "process", "grind", "crush", "pound", "tenderize", "juice",

        # Serving
        "plate", "serve", "portion", "divide", "share", "arrange", "present",

        # Specific techniques/actions from varied recipes
        "spray", "cover", "remove", "reserve", "break", "pick", "rinse", "set",
        "bloom", "taste", "tear", "store", "keep", "wait", "go", "settle", "jog",
        "place", "transfer", "check", "cool", "assemble", "crimp", "bring", "allow",
        "sit", "melt", "form", "flatten", "char", "repeat", "finish", "return", "let", "enjoy",
        "pat", "dry", "skewer", "thread", "wrap", "roll", "brush", "baste", "scoop", "scrape",
        "sift", "season", "salt", "pepper", "flour", "grease", "line", "drain", "whisk",
        "reduce", "simmer", "boil", "fry", "bake", "roast", "grill", "steam", "stir",
        "serve", "garnish", "chop", "dice", "mince", "slice", "cut", "peel", "grate",
        "squeeze", "extract", "dip", "dredge", "bread", "crumb", "press", "shape", "form",
        "refrigerate", "chill", "freeze", "thaw", "defrost", "defoliate"
    ]

    # Create a regex pattern that matches whole words only, case-insensitively
    pattern = re.compile(r'\b(' + '|'.join(action_verbs) + r')\b', re.IGNORECASE)

    # Replace matches while preserving original capitalization
    def wrap_match(match):
        return f"<action>{match.group(0)}</action>"

    return pattern.sub(wrap_match, instruction_text)