import logging
import re
import pdfplumber
from datetime import datetime
from logline_leviathan.database.database_manager import EntityTypesTable, session_scope
from logline_leviathan.file_processor.file_database_ops import handle_file_metadata, handle_individual_entity, handle_distinct_entity, handle_context_snippet

logging.getLogger('pdfminer').setLevel(logging.WARNING)

def read_pdf_content(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
        return pages
    except Exception as e:
        logging.error(f"Error reading PDF file {file_path}: {e}")
        return None

def process_pdf_file(file_path, file_mimetype, thread_instance, db_session, abort_flag):
    try:
        logging.info(f"Starting processing of PDF file: {file_path}")
        pages = read_pdf_content(file_path)
        regex_patterns = db_session.query(EntityTypesTable).all()

        if pages is None:
            return 0

        entity_count = 0
        file_metadata = handle_file_metadata(db_session, file_path, file_mimetype)

        for page_number, content in enumerate(pages):
            if content is None:
                continue  # Skip empty pages

            if abort_flag():
                logging.info("Processing aborted.")
                return entity_count

            full_content = content
            for regex in regex_patterns:
                if not regex.regex_pattern.strip():
                    continue
                for match in re.finditer(regex.regex_pattern, full_content):
                    if abort_flag():
                        logging.info("Processing aborted during regex matching.")
                        return entity_count

                    match_text = match.group()
                    if not match_text.strip():
                        continue

                    timestamp = None  # Handling timestamp in PDF might need a different approach
                    match_start_line, match_end_line = get_line_numbers_from_pos(content, match.start(), match.end())

                    entity = handle_distinct_entity(db_session, match_text, regex.entity_type_id)
                    individual_entity = handle_individual_entity(db_session, entity, file_metadata, page_number + 1, timestamp, regex.entity_type_id, abort_flag)

                    if individual_entity:
                        handle_context_snippet(db_session, individual_entity, [content], match_start_line, match_end_line)
                        entity_count += 1

            thread_instance.update_status.emit(f"   Finished processing {file_path}, page {page_number + 1}")

        logging.info(f"   Finished processing PDF file: {file_path}")
        return entity_count
    except Exception as e:
        db_session.rollback()
        logging.error(f"Error processing PDF file {file_path}: {e}")
        return 0

def get_line_numbers_from_pos(content, start_pos, end_pos):
    start_line = content[:start_pos].count('\n') + 1
    end_line = content[:end_pos].count('\n') + 1
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

