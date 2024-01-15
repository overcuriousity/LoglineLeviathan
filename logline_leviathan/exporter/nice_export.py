import re
from logline_leviathan.exporter.export_constructor import generate_dataframe

def create_regex_pattern_from_entity(entity):
    words = entity.split()
    regex_pattern = "|".join(re.escape(word) for word in words)
    return re.compile(regex_pattern, re.IGNORECASE)

def highlight_entities_in_context(context, entity_regex):
    def replace_match(match):
        return f"<mark>{match.group()}</mark>"
    return re.sub(entity_regex, replace_match, context)

def generate_niceoutput_file(output_file_path, db_session, checkboxes, context_selection, only_crossmatches):
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
    html_table = df.to_html(classes="display responsive nowrap", table_id="example", escape=False, index=False)

    # HTML template with doubled curly braces in JavaScript part and additional configurations
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Logline Leviathan Report</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css"/>
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/2.2.2/css/buttons.dataTables.min.css"/>
    <script type="text/javascript" src="https://code.jquery.com/jquery-3.5.1.js"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/buttons/2.2.2/js/dataTables.buttons.min.js"></script>
    <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.1.3/jszip.min.js"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.html5.min.js"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/buttons/2.2.2/js/buttons.print.min.js"></script>
</head>
<body>
    {0}
    <script type="text/javascript">
        $(document).ready(function () {{
            // DataTables initialization
            var table = $('#example').DataTable({{
                "dom": 'Blfrtip',
                "buttons": ['copy', 'csv', 'excel', 'pdf', 'print'],
                "searching": true,
                "fixedHeader": true,
                "autoWidth": true,
                "lengthChange": false,
                "pageLength": 10,
                "orderCellsTop": true,
            }});

            // Create dropdown filtering menus
            $('#example thead tr').clone(true).appendTo('#example thead');
            $('#example thead tr:eq(1) th').each(function (i) {{
                var title = $(this).text();
                if (title === 'Entity Type' || title === 'Entity' || title === 'Occurrences' || title === 'Timestamp' || title === 'Sources') {{
                    var select = $('<select><option value=""></option></select>')
                        .appendTo($(this).empty())
                        .on('change', function () {{
                            var val = $(this).val();
                            table.column(i)
                                 .search(val ? '^' + $(this).val() + '$' : val, true, false)
                                 .draw();
                        }});

                    table.column(i).data().unique().sort().each(function (d, j) {{
                        select.append('<option value="'+d+'">'+d+'</option>')
                    }});
                }} else {{
                    $(this).html('');
                }}
            }});
        }});
    </script>
</body>
</html>""".format(html_table)

    # Write the HTML template to the file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(html_template)