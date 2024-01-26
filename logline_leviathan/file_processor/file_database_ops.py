import logging
import os
from logline_leviathan.database.database_manager import FileMetadata, DistinctEntitiesTable, EntitiesTable, ContextTable
from datetime import datetime


def handle_file_metadata(db_session, file_path, file_mimetype, sheet_name=None):
    try:
        # Construct file name with or without sheet name
        base_file_name = os.path.basename(file_path)
        modified_file_name = f"{base_file_name}_{sheet_name}" if sheet_name else base_file_name

        # Search for existing metadata using the modified file name
        file_metadata = db_session.query(FileMetadata).filter_by(file_path=file_path, file_name=modified_file_name).first()

        if not file_metadata:
            file_metadata = FileMetadata(file_name=modified_file_name, file_path=file_path, file_mimetype=file_mimetype)
            db_session.add(file_metadata)
        else:
            # Update the MIME type if the record already exists
            file_metadata.file_mimetype = file_mimetype

        db_session.commit()
        return file_metadata
    except Exception as e:
        logging.error(f"Error handling file metadata for {file_path}: {e}")
        return None



def handle_distinct_entity(db_session, match_text, entity_type_id):
    try:
        distinct_entity = db_session.query(DistinctEntitiesTable).filter_by(distinct_entity=match_text, entity_types_id=entity_type_id).first()
        if not distinct_entity:
            distinct_entity = DistinctEntitiesTable(distinct_entity=match_text, entity_types_id=entity_type_id)
            db_session.add(distinct_entity)
            db_session.commit()

        return distinct_entity
    except Exception as e:
        logging.error(f"Error handling distinct entity {match_text}: {e}")
        return None



def handle_individual_entity(db_session, entity, file_metadata, line_number, timestamp, entity_types_id, abort_flag, thread_instance):
    try:
        if abort_flag():
            return None
        if timestamp and isinstance(timestamp, str):
            try:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                logging.warning(f"Invalid timestamp format: {timestamp}")
                timestamp = None

        individual_entity = db_session.query(EntitiesTable).filter_by(
            distinct_entities_id=entity.distinct_entities_id, 
            file_id=file_metadata.file_id, 
            line_number=line_number
        ).first()

        if not individual_entity:
            individual_entity = EntitiesTable(
                distinct_entities_id=entity.distinct_entities_id,
                file_id=file_metadata.file_id,
                line_number=line_number,
                entry_timestamp=timestamp,
                entity_types_id=entity_types_id
            )
            db_session.add(individual_entity)
            db_session.commit()

            thread_instance.total_entities_count_lock.lock()  # Lock the mutex
            try:
                thread_instance.total_entities_count += 1
            finally:
                thread_instance.total_entities_count_lock.unlock()  # Unlock the mutex

            thread_instance.calculate_and_emit_rate()

        return individual_entity
    except Exception as e:
        logging.error(f"Error handling individual entity in {file_metadata.file_path}, line {line_number}: {e}")
        return None


def count_newlines(content, start, end):
    return content[start:end].count('\n')

def handle_context_snippet(db_session, individual_entity, content, start_line, end_line):
    context_sizes = {
        'Single-Line Context': 0,
        'Medium Context': 8,
        'Large Context': 15
        #'Index Context': 30
    }

    context_snippets = {}
    for size, lines in context_sizes.items():
        context_start = max(0, start_line - lines)
        context_end = min(len(content), end_line + lines + 1)
        context_snippets[size] = "\n".join(content[context_start:context_end])

    context = ContextTable(entities_id=individual_entity.entities_id,
                           context_small=context_snippets['Single-Line Context'],
                           context_medium=context_snippets['Medium Context'],
                           context_large=context_snippets['Large Context']
                           )
    db_session.add(context)
    db_session.commit()