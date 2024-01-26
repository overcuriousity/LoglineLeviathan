from logline_leviathan.database.database_manager import ContextTable, EntityTypesTable, DistinctEntitiesTable, EntitiesTable, FileMetadata
from sqlalchemy import func, distinct
from PyQt5.QtCore import Qt



def generate_wordlist(output_file_path, db_session, checkboxes, only_crossmatches):
    # Check if there are any checkboxes selected
    if not checkboxes:
        raise ValueError("No entities selected")

    # Get selected entity types from checkboxes
    selected_entity_types = [item.entity_type for item in checkboxes if item.checkState(0) == Qt.Checked]

    # Prepare the query
    query = db_session.query(
        DistinctEntitiesTable.distinct_entity
    ).join(
        EntityTypesTable, DistinctEntitiesTable.entity_types_id == EntityTypesTable.entity_type_id
    ).filter(
        EntityTypesTable.entity_type.in_(selected_entity_types)
    )

    # If only crossmatches are required
    if only_crossmatches:
        query = query.join(
            EntitiesTable, DistinctEntitiesTable.distinct_entities_id == EntitiesTable.distinct_entities_id
        ).group_by(
            DistinctEntitiesTable.distinct_entity
        ).having(
            func.count(distinct(EntitiesTable.file_id)) > 1
        )

    # Execute the query and fetch all results
    results = query.all()

    # Write the results to the file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for result in results:
            file.write(result.distinct_entity + '\n')
