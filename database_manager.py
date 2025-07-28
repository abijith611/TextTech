import sqlite3
from sqlite3 import Error
import data_processor # Import data_processor for calorie calculation and ingredient parsing
import config # Import config for database name

def create_connection(db_file: str) -> sqlite3.Connection | None:
    """
    Creates a database connection to a SQLite database specified by db_file.

    Args:
        db_file: The path to the SQLite database file.

    Returns:
        A SQLite connection object, or None if connection fails.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to SQLite database: {db_file}")
        return conn
    except Error as e:
        print(f"Error connecting to database '{db_file}': {e}")
    return conn

def create_table(conn: sqlite3.Connection):
    """
    Creates the 'recipes' table in the database if it doesn't already exist.

    Args:
        conn: The SQLite database connection object.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                instructions TEXT NOT NULL,
                calories REAL,
                image_url TEXT,
                thumbnail_url TEXT,
                video_url TEXT,
                tags TEXT
            )
        """)
        conn.commit()
        print("Created 'recipes' table (if it didn't exist).")
    except Error as e:
        print(f"Error creating table: {e}")

def insert_recipe(conn: sqlite3.Connection, recipe_data: dict) -> int | None:
    """
    Inserts or replaces recipe data into the 'recipes' table.

    Args:
        conn: The SQLite database connection object.
        recipe_data: A dictionary containing recipe details fetched from the API.

    Returns:
        The row ID of the inserted or replaced record, or None if insertion fails.
    """
    ingredients_str = data_processor.parse_ingredients(recipe_data)
    calories_val = data_processor.calculate_calories(ingredients_str)

    # Convert calories to a suitable type for DB (None if "N/A" or string)
    if isinstance(calories_val, str) and "N/A" in calories_val:
        calories_for_db = None
    else:
        try:
            calories_for_db = float(calories_val)
        except (ValueError, TypeError):
            calories_for_db = None # Handle cases where calorie calculation might return non-numeric string

    sql = """INSERT OR REPLACE INTO recipes(
                id, title, ingredients, instructions,
                calories, image_url, thumbnail_url, video_url, tags
              ) VALUES(?,?,?,?,?,?,?,?,?)"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (
            recipe_data['idMeal'],
            recipe_data['strMeal'],
            ingredients_str,
            recipe_data['strInstructions'],
            calories_for_db,
            recipe_data.get('strMealThumb', ''),
            recipe_data.get('strMealThumb', ''),
            recipe_data.get('strYoutube', ''),
            ','.join(filter(None, [
                recipe_data.get('strArea', ''),
                recipe_data.get('strCategory', ''),
                recipe_data.get('strTags', '')
            ]))
        ))
        conn.commit()
        print(f"  Inserted/Updated recipe: {recipe_data['strMeal']} (Calories: {calories_val})")
        return cursor.lastrowid
    except Error as e:
        print(f"Error inserting recipe {recipe_data['idMeal']}: {e}")
    return None

def print_recipes(db_file: str):
    """
    Prints the IDs and titles of all recipes currently stored in the database.

    Args:
        db_file: The path to the SQLite database file.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM recipes")
        recipes = cursor.fetchall()

        print("\n--- Stored Recipes in Database ---")
        if recipes:
            for recipe in recipes:
                print(f"ID: {recipe[0]}, Title: {recipe[1]}")
        else:
            print("No recipes found in the database.")
    except Error as e:
        print(f"Error reading recipes from database: {e}")
    finally:
        if conn:
            conn.close()