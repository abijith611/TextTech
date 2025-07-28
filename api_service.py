import requests
import config

def fetch_categories(limit: int = 5) -> list[str]:
    """
    Fetches a limited number of food categories from TheMealDB API.

    Args:
        limit: The maximum number of categories to fetch.

    Returns:
        A list of category names (strings). Returns an empty list on failure.
    """
    try:
        response = requests.get(f"{config.MEALDB_API_BASE_URL}list.php?c=list")
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        if data and 'meals' in data:
            return [category['strCategory'] for category in data['meals'][:limit]]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching categories from TheMealDB API: {e}")
    return []

def fetch_recipes_by_category(category: str, limit: int = 2) -> list[dict]:
    """
    Fetches a limited number of recipes within a specific category from TheMealDB API.

    Args:
        category: The category name to filter recipes by.
        limit: The maximum number of recipes to fetch for the category.

    Returns:
        A list of recipe dictionaries. Returns an empty list on failure.
    """
    try:
        response = requests.get(f"{config.MEALDB_API_BASE_URL}filter.php?c={category}")
        response.raise_for_status()
        data = response.json()
        if data and 'meals' in data:
            return data['meals'][:limit]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recipes for category '{category}' from TheMealDB API: {e}")
    return []

def fetch_recipe_details(recipe_id: str) -> dict | None:
    """
    Fetches detailed information for a specific recipe from TheMealDB API.

    Args:
        recipe_id: The ID of the recipe to fetch details for.

    Returns:
        A dictionary containing recipe details, or None if not found or on error.
    """
    try:
        response = requests.get(f"{config.MEALDB_API_BASE_URL}lookup.php?i={recipe_id}")
        response.raise_for_status()
        data = response.json()
        if data and 'meals' in data and data['meals']:
            return data['meals'][0]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for recipe ID {recipe_id} from TheMealDB API: {e}")
    return None