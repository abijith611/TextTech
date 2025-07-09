<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" doctype-system="about:legacy-compat" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Recipe Collection</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #e74c3c;
            padding-bottom: 10px;
        }
        .recipe {
            background: white;
            border-radius: 8px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            padding: 20px;
            overflow: hidden;
        }
        .recipe-title {
            color: #e74c3c;
            margin-top: 0;
        }
        .ingredients {
            background: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .ingredient {
            margin-bottom: 5px;
        }
        .quantity {
            font-weight: bold;
            color: #2c3e50;
        }
        .unit {
            font-style: italic;
        }
        .instructions {
            white-space: pre-line;
        }
        action {
            background-color: #ffeaa7;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: bold;
        }
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            .recipe {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <h1>Recipe Collection</h1>
    <xsl:for-each select="recipes/recipe">
        <div class="recipe">
            <h2 class="recipe-title"><xsl:value-of select="title"/></h2>
            <h3>Calories: <xsl:value-of select="calories"/></h3>
            <div class="ingredients">
                <h3>Ingredients</h3>
                <ul>
                    <xsl:for-each select="ingredients/ingredient">
                        <li class="ingredient">
                            <span class="quantity"><xsl:value-of select="quantity"/></span>
                            <xsl:text> </xsl:text>
                            <span class="unit"><xsl:value-of select="unit"/></span>
                            <xsl:text> </xsl:text>
                            <span class="item"><xsl:value-of select="item"/></span>
                        </li>
                    </xsl:for-each>
                </ul>
            </div>

            <div class="instructions">
                <h3>Instructions</h3>
                <xsl:value-of select="instructions" disable-output-escaping="yes"/>
            </div>
        </div>
    </xsl:for-each>
</body>
</html>
</xsl:template>
</xsl:stylesheet>