import re
import logging
from logline_leviathan.file_processor.parser_thread import parse_content
from datetime import datetime
from logline_leviathan.file_processor.file_database_ops import handle_file_metadata, handle_individual_entity, handle_context_snippet, handle_distinct_entity

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.readlines()
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return None


def process_text_file(file_path, file_mimetype, thread_instance, db_session, abort_flag):
    try:
        #logging.info(f"Starting processing of text file: {file_path}")
        file_metadata = handle_file_metadata(db_session, file_path, file_mimetype)
        content = read_file_content(file_path)
        full_content = ''.join(content)  # Join all lines into a single string
        thread_instance.update_status.emit(f"   Processing now: {file_path}")

        # Call the new parser and get matches along with entity types
        parsed_entities = parse_content(full_content, abort_flag, db_session)

        entity_count = 0
        for entity_type_id, match_text, start_pos, end_pos in parsed_entities:
            if not match_text.strip():
                continue

            timestamp = find_timestamp_before_match(full_content, start_pos)
            match_start_line, match_end_line = get_line_numbers_from_pos(content, start_pos, end_pos)

            entity = handle_distinct_entity(db_session, match_text, entity_type_id)
            individual_entity = handle_individual_entity(db_session, entity, file_metadata, match_start_line, timestamp, entity_type_id, abort_flag, thread_instance)
                
            if individual_entity:
                entity_count += 1
                handle_context_snippet(db_session, individual_entity, content, match_start_line, match_end_line)

        return entity_count
    except Exception as e:
        db_session.rollback()
        logging.error(f"Error processing text file {file_path}: {e}")
        return 0


def get_line_numbers_from_pos(content, start_pos, end_pos):
    start_line = end_line = 0
    current_pos = 0
    for i, line in enumerate(content):
        current_pos += len(line)
        if start_pos < current_pos:
            start_line = i
            break
    for i, line in enumerate(content[start_line:], start=start_line):
        current_pos += len(line)
        if end_pos <= current_pos:
            end_line = i
            break
    return start_line, end_line


def find_timestamp_before_match(content, match_start_pos):
    search_content = content[:match_start_pos]
    timestamp_patterns = [
        (r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', '%Y-%m-%d %H:%M:%S'),  # ISO 8601 Extended
        (r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}', '%Y/%m/%d %H:%M:%S'),  # ISO 8601 with slashes
        (r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}', '%d/%m/%Y %H:%M:%S'),  # European Date Format
        (r'\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}', '%m-%d-%Y %H:%M:%S'),  # US Date Format
        (r'\d{8}_\d{6}', '%Y%m%d_%H%M%S'),                             # Compact Format
        (r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '%Y-%m-%dT%H:%M:%S'),  # ISO 8601 Basic
        (r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2}', '%d.%m.%Y %H:%M:%S'),# German Date Format
        (r'\d{4}\d{2}\d{2} \d{2}:\d{2}:\d{2}', '%Y%m%d %H:%M:%S'),      # Basic Format without Separators
        (r'\d{1,2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', '%d-%b-%Y %H:%M:%S'), # English Date Format with Month Name
        (r'(?:19|20)\d{10}', '%Y%m%d%H%M'),                             # Compact Numeric Format
        # Add more patterns as needed
    ]
    for pattern, date_format in timestamp_patterns:
        for timestamp_match in reversed(list(re.finditer(pattern, search_content))):
            try:
                # Convert the matched timestamp to the standardized format
                matched_timestamp = datetime.strptime(timestamp_match.group(), date_format)
                return matched_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue  # If conversion fails, continue to the next pattern
    return None

