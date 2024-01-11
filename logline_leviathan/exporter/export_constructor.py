import pandas as pd
from PyQt5.QtCore import Qt
from sqlalchemy import func, cast, String, literal_column, distinct
from logline_leviathan.database.database_manager import ContextTable, EntityTypesTable, DistinctEntitiesTable, EntitiesTable, FileMetadata

def generate_dataframe(db_session, tree_items, context_selection):
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

    subquery = db_session.query(
        EntitiesTable.distinct_entities_id,
        func.count(distinct(EntitiesTable.file_id)).label('file_count')
    ).group_by(EntitiesTable.distinct_entities_id).subquery()

    for entity_type in selected_entity_types:
        if context_selection == 'Compact Summary, no Context':
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
            ).join(subquery, DistinctEntitiesTable.distinct_entities_id == subquery.c.distinct_entities_id
            ).filter(EntityTypesTable.entity_type == entity_type
            ).group_by(DistinctEntitiesTable.distinct_entity)

        else:
            # Fetch each entity with context
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
            ).filter(EntityTypesTable.entity_type == entity_type)

        for row in query.all():
            if context_selection == 'Compact Summary, no Context':
                sources = row[3].replace(',', ' // ') if row[3] is not None else ''
                timestamps = row[4].replace(',', ' // ') if row[4] is not None else ''
                data.append([row[0], row[1], row[2], timestamps, sources, ''])
            else:
                source_info = f"{row[3]}:line{row[4]}"
                entry_timestamp = row[6].strftime('%Y-%m-%d %H:%M:%S') if row[6] is not None else ''
                context_info = row[5] if row[5] is not None else ''
                data.append([row[0], row[1], row[2], entry_timestamp, source_info, context_info])


    return pd.DataFrame(data, columns=["Entity Type", "Entity", "Occurrences", "Timestamp", "Sources", "Context"])