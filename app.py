import os
from flask import Flask, render_template, request
import sqlparse
import re

# Ensure Flask can find the "templates" folder.
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates")
)

def add_column_aliases(sql):
    """
    An example function that adds column aliases.
    This simple implementation uses regex to replace the SELECT clause.
    Modify this logic as needed for your use case.
    """
    # A simple pattern for demonstration; adjust as necessary.
    pattern = r"(\bSELECT\b)([\s\S]*?)(\bFROM\b)"
    
    def add_aliases(match):
        columns_part = match.group(2)
        columns = columns_part.split(",")
        new_columns = []
        for col in columns:
            col_stripped = col.strip()
            # If already has an alias (contains "AS"), leave it unchanged
            if " AS " in col_stripped.upper():
                new_columns.append(col_stripped)
            elif "." in col_stripped:
                parts = col_stripped.split(".")
                if len(parts) == 2:
                    alias = f"{parts[0]}_{parts[1]}"
                    new_columns.append(f"{col_stripped} AS {alias}")
                else:
                    new_columns.append(col_stripped)
            else:
                new_columns.append(col_stripped)
        new_columns_str = ", ".join(new_columns)
        return f"SELECT {new_columns_str} FROM"
    
    formatted_sql = sqlparse.format(
        sql,
        reindent=True,
        keyword_case="upper",
        indent_width=4
    )
    result = re.sub(pattern, add_aliases, formatted_sql, flags=re.IGNORECASE)
    return result

@app.route("/", methods=["GET", "POST"])
def index():
    formatted_sql = None
    if request.method == "POST":
        try:
            sql = request.form.get("sql", "")
            add_aliases = request.form.get("add_aliases") == "on"
            if sql:
                if add_aliases:
                    formatted_sql = add_column_aliases(sql)
                else:
                    formatted_sql = sqlparse.format(
                        sql,
                        reindent=True,
                        keyword_case="upper",
                        indent_width=4
                    )
        except Exception as e:
            formatted_sql = f"Error: {e}"
    return render_template("index.html", formatted_sql=formatted_sql)

if __name__ == "__main__":
    app.run(debug=True)

