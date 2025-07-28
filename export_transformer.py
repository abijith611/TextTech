import sqlite3
# import xml.etree.ElementTree as ET # REMOVE THIS IMPORT
from lxml import etree # Keep this import and use it for XML building
import config # Import config for filenames
import data_processor # Import data_processor for parsing and highlighting

def export_to_xml(db_file: str, xml_file: str):
    """
    Exports all recipes from the SQLite database to an XML file.
    Ingredients are parsed into quantity, unit, and item.
    Instructions have action verbs highlighted and are placed in CDATA sections.

    Args:
        db_file: The path to the SQLite database file.
        xml_file: The name of the XML file to create.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes")
        recipes = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error accessing database for XML export: {e}")
        return
    finally:
        if conn:
            conn.close()

    # Use lxml.etree to build the XML
    root = etree.Element("recipes")

    for recipe in recipes:
        recipe_elem = etree.SubElement(root, "recipe")
        etree.SubElement(recipe_elem, "id").text = recipe[0]
        etree.SubElement(recipe_elem, "title").text = recipe[1]
        etree.SubElement(recipe_elem, "calories").text = str(recipe[4] if recipe[4] is not None else "N/A")
        etree.SubElement(recipe_elem, "image_url").text = recipe[5]

        # Only add video_url to XML if it's not empty or None
        if recipe[7]:
            etree.SubElement(recipe_elem, "video_url").text = recipe[7]

        # Ingredients with separated quantity/unit/item
        ingredients_elem = etree.SubElement(recipe_elem, "ingredients")
        # Split the combined ingredients string from DB back into individual lines
        for ingredient_line in recipe[2].split(","):
            ingredient_line = ingredient_line.strip()
            if ingredient_line:
                ingredient_elem = etree.SubElement(ingredients_elem, "ingredient")
                # Use data_processor to parse each ingredient line
                quantity, unit, item = data_processor.parse_measurement(ingredient_line)
                etree.SubElement(ingredient_elem, "quantity").text = quantity
                etree.SubElement(ingredient_elem, "unit").text = unit
                etree.SubElement(ingredient_elem, "item").text = item

        # Instructions with highlighted actions in CDATA
        instructions_elem = etree.SubElement(recipe_elem, "instructions")
        # Use data_processor to highlight actions
        instructions_text = data_processor.highlight_actions(recipe[3])
        # Use lxml.etree.CDATA to wrap instructions text
        instructions_elem.text = etree.CDATA(instructions_text)


    # Write to XML file
    try:
        # Use lxml's etree.tostring for pretty printing and writing to file
        # The 'pretty_print=True' argument indents the XML for readability.
        # The 'xml_declaration=True' includes <?xml version="1.0" encoding="utf-8"?>
        xml_string = etree.tostring(root, encoding='utf-8', pretty_print=True, xml_declaration=True)
        with open(xml_file, 'wb') as f:
            f.write(xml_string)
        print(f"Successfully exported recipes to {xml_file}")
    except Exception as e:
        print(f"Error writing XML file '{xml_file}': {e}")


def transform_to_html(xml_file: str, xslt_file: str, output_html: str):
    """
    Transforms an XML file into an HTML file using an XSLT stylesheet.

    Args:
        xml_file: The path to the input XML file.
        xslt_file: The path to the XSLT stylesheet.
        output_html: The path to the output HTML file.
    """
    try:
        # Parse XML and XSLT using lxml.etree
        xml_doc = etree.parse(xml_file)
        xslt_doc = etree.parse(xslt_file)

        # Create transformer and apply transformation
        transform = etree.XSLT(xslt_doc)
        html_result = transform(xml_doc)

        # Write output
        with open(output_html, 'wb') as f:
            f.write(html_result)

        print(f"Successfully created HTML page at {output_html}")
    except etree.XSLTParseError as e:
        print(f"Error parsing XSLT file '{xslt_file}': {e}")
    except etree.XMLSyntaxError as e:
        print(f"Error parsing XML file '{xml_file}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during XML to HTML transformation: {e}")