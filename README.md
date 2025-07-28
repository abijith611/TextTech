# Recipe Data Extractor and Transformer

This project is a Python application designed to fetch recipe data from TheMealDB API, store it in a SQLite database, export it to an XML file, and finally transform the XML into a human-readable HTML page using XSLT.

---

## Features

-   **API Integration:** Fetches food categories and detailed recipe information from TheMealDB API.
-   **Data Persistence:** Stores extracted recipe data in a SQLite database for easy access and management.
-   **JSON Export:** Saves the collected recipe data into a structured JSON file.
-   **XML Export:** Exports all recipes from the database into an XML format.
-   **Data Transformation:** Transforms the XML recipe data into an HTML page using an XSLT stylesheet, highlighting action verbs in instructions and parsing ingredients.
-   **Calorie Estimation:** Attempts to calculate calories for ingredients using the CalorieNinjas API (requires an API key).

---

## Project Files

This project consists of the following files:

-   `script.py`: The main Python script that handles data fetching, storage, and transformation.
-   `recipes.xslt`: The XSLT stylesheet used to transform the XML recipe data into HTML.
-   `recipes.db`: (Generated) The SQLite database file containing all the fetched recipe data.
-   `limited_themealdb_recipes_YYYYMMDD.json`: (Generated) A JSON file with the raw data fetched from the API, categorized by food type.
-   `recipes.xml`: (Generated) An XML representation of the recipes extracted from the database.
-   `recipes.html`: (Generated) The final web page, generated from `recipes.xml` using `recipes.xslt`.

---

## Setup and Installation

### Prerequisites

-   **Python 3.x**
-   **`requests` library:** For making API calls.
-   **`lxml` library:** For XML parsing and XSLT transformations.

You can install these Python libraries using pip:

```bash
pip install requests lxml