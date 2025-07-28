import sys
from datetime import datetime

# Import modules from your project structure
import config
import api_service
import database_manager
import data_processor
import export_transformer

def main():
    """
    Main function to orchestrate the fetching, processing, storing, and exporting of recipe data.
    """
    print("Starting recipe data extraction process...")

    # Initialize data structure for JSON export
    all_recipes = {
        "metadata": {
            "source": "TheMealDB API",
            "extracted_on": datetime.now().isoformat(),
            "categories_limit": config.CATEGORIES_LIMIT,
            "recipes_per_category": config.RECIPES_PER_CATEGORY,
            "total_recipes": 0
        },
        "categories": {}
    }

    # Database setup
    conn = database_manager.create_connection(config.DATABASE_NAME)
    if conn is None:
        print("Error! Cannot create the database connection. Exiting.")
        sys.exit(1) # Exit if database connection fails

    database_manager.create_table(conn)

    # Get categories
    categories = api_service.fetch_categories(config.CATEGORIES_LIMIT)
    if not categories:
        print("No categories fetched. Aborting recipe collection.")
        conn.close()
        sys.exit(0)
    print(f"Selected {len(categories)} categories: {', '.join(categories)}")

    # Process each category
    for category in categories:
        print(f"\nProcessing category: {category}")
        all_recipes["categories"][category] = []

        # Get recipes in this category
        recipes = api_service.fetch_recipes_by_category(category, config.RECIPES_PER_CATEGORY)
        if not recipes:
            print(f"  No recipes found for category: {category}")
            continue

        # Process each recipe in the category
        for recipe in recipes:
            recipe_id = recipe['idMeal']
            print(f"  Fetching details for: {recipe['strMeal']} (ID: {recipe_id})")

            # Get full recipe details
            recipe_details = api_service.fetch_recipe_details(recipe_id)
            if recipe_details:
                # Add to JSON structure
                all_recipes["categories"][category].append(recipe_details)
                all_recipes["metadata"]["total_recipes"] += 1

                # Insert into database
                database_manager.insert_recipe(conn, recipe_details)
            else:
                print(f"  Could not fetch details for recipe ID: {recipe_id}")

    # Save the collected data to JSON
    output_json_filename = f"{config.JSON_OUTPUT_FILENAME_PREFIX}{datetime.now().strftime('%Y%m%d')}.json"
    data_processor.save_to_json(all_recipes, output_json_filename)

    # Close database connection
    conn.close()
    print("Database connection closed.")

    print(
        f"\n--- Data Collection Completed ---"
        f"\nSaved {all_recipes['metadata']['total_recipes']} recipes "
        f"(2 each from {len(categories)} categories) to JSON and database."
    )

    # --- Export and Transformation Steps ---
    print("\n--- Starting Export and Transformation ---")
    export_transformer.export_to_xml(config.DATABASE_NAME, config.XML_OUTPUT_FILENAME)
    export_transformer.transform_to_html(config.XML_OUTPUT_FILENAME, config.XSLT_FILENAME, config.HTML_OUTPUT_FILENAME)
    print("--- Export and Transformation Completed ---")

    print("\nProcess finished successfully!")
    print(f"You can view the generated recipe catalog by opening '{config.HTML_OUTPUT_FILENAME}' in your web browser.")

if __name__ == "__main__":
    main()