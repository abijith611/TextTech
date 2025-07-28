# --- Configuration Settings ---

# API Endpoints
MEALDB_API_BASE_URL = "https://www.themealdb.com/api/json/v1/1/"
CALORIENINJAS_API_URL = "https://api.calorieninjas.com/v1/nutrition"

# API Keys (Replace "YOUR_API_KEY" with your actual key if needed)
CALORIENINJAS_API_KEY = "hDQLYashT6x+0JXeW/MNjQ==uj9EubnJF1h6QTbG"

# Data Limits for Fetching
CATEGORIES_LIMIT = 5
RECIPES_PER_CATEGORY = 2

# Output File Names
DATABASE_NAME = "recipes.db"
JSON_OUTPUT_FILENAME_PREFIX = "limited_themealdb_recipes_"
XML_OUTPUT_FILENAME = "recipes.xml"
XSLT_FILENAME = "recipes.xslt"
HTML_OUTPUT_FILENAME = "recipes.html"

# API Rate Limiting (seconds) - Be gentle with free APIs
CALORIENINJAS_API_DELAY = 0.5 # Delay for CalorieNinjas API calls