from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlparse
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def add_column_aliases(sql):
    """
    Adds aliases to columns in the main SELECT statement.
    """
    # First, standardize the SQL
    sql = sqlparse.format(sql, strip_comments=True)
    
    if sql.upper().strip().startswith('WITH'):
        # Find the main SELECT statement after all CTEs
        pattern = r'(\)\s*SELECT\s*)([\s\S]*?)(\s*FROM\s*)'
        match = re.search(pattern, sql, re.IGNORECASE)
        
        if match:
            before_select = sql[:match.start(1)]
            select_columns = match.group(2)
            after_from = sql[match.end(2):]
            
            # Process the columns
            columns = [col.strip() for col in select_columns.split(',')]
            formatted_columns = []
            
            for col in columns:
                # Skip if column already has an alias
                if ' AS ' in col.upper():
                    formatted_columns.append(col)
                    continue
                    
                # Skip if it's a function
                if any(col.upper().startswith(func + '(') for func in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'STRING_AGG', 'DATE_TRUNC', 'RANK']):
                    formatted_columns.append(col)
                    continue
                    
                # Process regular table columns
                if '.' in col:
                    table_alias, column_name = col.split('.')
                    formatted_columns.append(
                        f"{table_alias}.{column_name} AS {table_alias}_{column_name}"
                    )
                else:
                    formatted_columns.append(col)
            
            # Reconstruct the query
            final_sql = (
                before_select + 
                ')\nSELECT\n    ' + 
                ',\n    '.join(formatted_columns) + 
                '\nFROM' + 
                after_from
            )
        else:
            final_sql = sql
    else:
        final_sql = sql
    
    # Final formatting
    formatted_sql = sqlparse.format(
        final_sql,
        reindent=True,
        keyword_case='upper',
        indent_width=4
    )
    
    return formatted_sql

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/format/', methods=['POST', 'OPTIONS'])
def format_sql():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        return ('', 204, headers)

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        sql = data.get('sql', '')
        add_aliases = data.get('add_aliases', False)
        
        if not sql:
            return jsonify({'error': 'No SQL provided'}), 400
        
        if add_aliases:
            formatted_sql = add_column_aliases(sql)
        else:
            formatted_sql = sqlparse.format(
                sql,
                reindent=True,
                keyword_case='upper',
                indent_width=4
            )
        
        return jsonify({'formatted_sql': formatted_sql})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)