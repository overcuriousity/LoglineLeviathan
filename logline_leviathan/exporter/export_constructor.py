import pandas as pd
from PyQt5.QtCore import Qt
from sqlalchemy import func, cast, String, distinct
from logline_leviathan.database.database_manager import ContextTable, EntityTypesTable, DistinctEntitiesTable, EntitiesTable, FileMetadata

def generate_dataframe(db_session, tree_items, context_selection, only_crossmatches=False, custom_columns=None):
    if not db_session:
        raise ValueError("Database session is None")

    data = []
    # Extract entity_type from selected tree items
    selected_entity_types = [item.entity_type for item in tree_items if item.checkState(0) == Qt.Checked]

    context_field = {
        'Compact Summary, no Context': None,
        'Single-Line Context': ContextTable.context_small,
        'Medium Context': ContextTable.context_medium,
        'Large Context': ContextTable.context_large
    }.get(context_selection)

    # Creating a subquery to count distinct file IDs
    file_count_subquery = db_session.query(
        EntitiesTable.distinct_entities_id,
        func.count(distinct(EntitiesTable.file_id)).label('file_count')
    ).group_by(EntitiesTable.distinct_entities_id)

    if only_crossmatches:
        file_count_subquery = file_count_subquery.having(func.count(distinct(EntitiesTable.file_id)) > 1)

    file_count_subquery = file_count_subquery.subquery()

    for entity_type in selected_entity_types:
        if context_selection == 'Compact Summary, no Context':
            # Query for 'Compact Summary, no Context'
            query = db_session.query(
                EntityTypesTable.entity_type,
                DistinctEntitiesTable.distinct_entity,
                func.count(EntitiesTable.entities_id).label('occurrences'),
                func.group_concat(
                    FileMetadata.file_name + ':line' + cast(EntitiesTable.line_number, String)
                ).label('sources'),
                func.group_concat(
                    cast(EntitiesTable.entry_timestamp, String)
                ).label('timestamps')
            ).join(EntityTypesTable, DistinctEntitiesTable.entity_types_id == EntityTypesTable.entity_type_id
            ).join(EntitiesTable, DistinctEntitiesTable.distinct_entities_id == EntitiesTable.distinct_entities_id
            ).join(FileMetadata, EntitiesTable.file_id == FileMetadata.file_id
            ).join(file_count_subquery, DistinctEntitiesTable.distinct_entities_id == file_count_subquery.c.distinct_entities_id
            ).filter(EntityTypesTable.entity_type == entity_type
            ).group_by(DistinctEntitiesTable.distinct_entity)

        else:
            # Query for other context selections
            query = db_session.query(
                EntityTypesTable.entity_type,
                DistinctEntitiesTable.distinct_entity,
                func.count(EntitiesTable.entities_id).over(partition_by=DistinctEntitiesTable.distinct_entity).label('occurrences'),
                FileMetadata.file_name,
                EntitiesTable.line_number,
                context_field,
                EntitiesTable.entry_timestamp
            ).select_from(EntitiesTable
            ).join(DistinctEntitiesTable, EntitiesTable.distinct_entities_id == DistinctEntitiesTable.distinct_entities_id
            ).join(EntityTypesTable, DistinctEntitiesTable.entity_types_id == EntityTypesTable.entity_type_id
            ).join(FileMetadata, EntitiesTable.file_id == FileMetadata.file_id
            ).outerjoin(ContextTable, EntitiesTable.entities_id == ContextTable.entities_id
            ).join(file_count_subquery, DistinctEntitiesTable.distinct_entities_id == file_count_subquery.c.distinct_entities_id
            ).filter(EntityTypesTable.entity_type == entity_type)

            if not context_selection == 'Custom' and not context_selection == 'Compact Summary, no Context':
                for row in query.all():
                    file_name = row[3]
                    line_number = row[4]
                    entry_timestamp = row[6].strftime('%Y-%m-%d %H:%M:%S') if row[6] is not None else ''
                    context_info = row[5] if row[5] is not None else ''
                    data.append([row[0], row[1], row[2], entry_timestamp, file_name, line_number, context_info])

                return pd.DataFrame(data, columns=["Entity Type", "Entity", "Occurrences", "Timestamp", "Source File", "Line Number", "Context"])

        
        if context_selection == 'Compact Summary, no Context':
            for row in query.all():
                sources = row[3].replace(',', ' // ') if row[3] is not None else ''
                timestamps = row[4].replace(',', ' // ') if row[4] is not None else ''
                data.append([row[0], row[1], row[2], timestamps, sources, ''])
            return pd.DataFrame(data, columns=["Entity Type", "Entity", "Occurrences", "Timestamp", "Sources", "Context"])


        else:
            # Define a mapping from column names to their corresponding database fields
            column_to_field_mapping = {
                'Entity Type': EntityTypesTable.entity_type,
                'Entity': DistinctEntitiesTable.distinct_entity,
                'Occurrence': func.count(EntitiesTable.entities_id).label('occurrences'),
                'File Name': FileMetadata.file_name,
                'Line Number': cast(EntitiesTable.line_number, String),
                'Timestamp': cast(EntitiesTable.entry_timestamp, String),
                'Context (Same Line)': ContextTable.context_small,
                'Context (Some Lines)': ContextTable.context_medium,
                'Context (Many Lines)': ContextTable.context_large
            }

            if context_selection == 'Custom' and custom_columns:
                # Prepare the columns for the query based on custom_columns
                query_columns = [column_to_field_mapping[col] for col in custom_columns if col in column_to_field_mapping]

                query = db_session.query(*query_columns)

                # Add necessary joins depending on selected columns
                if any(col in custom_columns for col in ['Entity Type', 'Entity']):
                    query = query.join(DistinctEntitiesTable, DistinctEntitiesTable.distinct_entities_id == EntitiesTable.distinct_entities_id)
                if 'File Name' in custom_columns or 'Timestamp' in custom_columns:
                    query = query.join(FileMetadata, EntitiesTable.file_id == FileMetadata.file_id)
                if any(col.startswith('Context') for col in custom_columns):
                    query = query.outerjoin(ContextTable, EntitiesTable.entities_id == ContextTable.entities_id)

                # Apply filters for selected entity types
                query = query.filter(EntityTypesTable.entity_type.in_(selected_entity_types))

                # Group by and order might be necessary depending on the query

                # Execute the query and construct the DataFrame
                results = query.all()
                data = [dict(zip(custom_columns, row)) for row in results]
                return pd.DataFrame(data)