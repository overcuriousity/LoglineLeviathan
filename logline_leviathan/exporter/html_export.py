
from logline_leviathan.exporter.export_constructor import generate_dataframe
import re

def create_regex_pattern_from_entity(entity):
    words = entity.split()
    regex_pattern = "|".join(re.escape(word) for word in words)
    return re.compile(regex_pattern, re.IGNORECASE)

def highlight_entities_in_context(context, entity_regex):
    def replace_match(match):
        return f"<mark>{match.group()}</mark>"
    return re.sub(entity_regex, replace_match, context)

def generate_html_file(output_file_path, db_session, checkboxes, context_selection, only_crossmatches):
    # Fetch data using the new DataFrame constructor
    df = generate_dataframe(db_session, checkboxes, context_selection)

    # Add line breaks for HTML formatting where needed
    if context_selection == 'Compact Summary, no Context':
        df['Sources'] = df['Sources'].apply(lambda x: x.replace(' // ', ' // <br>'))
        df['Timestamp'] = df['Timestamp'].apply(lambda x: x.replace(' // ', ' // <br>'))

    # Iterate over the DataFrame to apply regex-based highlighting
    for index, row in df.iterrows():
        entity_regex = create_regex_pattern_from_entity(row['Entity'])
        df.at[index, 'Context'] = highlight_entities_in_context(row['Context'], entity_regex)

    # Replace newline characters with HTML line breaks in the 'Context' column
    df['Context'] = df['Context'].apply(lambda x: x.replace('\n', '<br>') if x else x)

    # Convert DataFrame to HTML table
    html_table = df.to_html(classes="table table-bordered", escape=False, index=False)

    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Logline Leviathan Report</title>
    <style>
        .table {{
            width: 100%;
            max-width: 100%;
            margin-bottom: 1rem;
            background-color: transparent;
        }}
        .table th, .table td {{
            padding: 0.75rem;
            vertical-align: top;
            border-top: 1px solid #dee2e6;
            max-width: 300px; /* Max width */
            word-wrap: break-word; /* Enable word wrapping */
        }}
        .table-bordered {{
            border: 1px solid #dee2e6;
        }}
        .table-bordered th, .table-bordered td {{
            border: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    {html_table}
</body>
</html>"""

    # Write the HTML template to the file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(html_template)
