# the parse_content receives the full_content string from the methods process_text_file, process_xlsx_file, process_pdf_file or similar along the abort_flag

import os
import re
import logging
import importlib
import multiprocessing
from logline_leviathan.database.database_manager import EntityTypesTable

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def parse_with_script(parser_module_name, full_content):
    parser_module_name = parser_module_name.replace('.py', '')  # Ensure no .py extension
    try:
        #logging.debug(f"Loading script parser module: {parser_module_name}")
        parser_module = importlib.import_module(parser_module_name)
        script_results = parser_module.parse(full_content)
        #logging.debug(f"Script parser results: {script_results}")
        return script_results
    except (ImportError, AttributeError) as e:
        logging.error(f"Error importing or using parser module {parser_module_name}: {e}")
        return []



def parse_with_regex(regex_pattern, full_content):
    try:
        #logging.debug(f"Using regex pattern: {regex_pattern}")
        regex_results = [(match.group(), match.start(), match.end()) for match in re.finditer(regex_pattern, full_content)]
        #logging.debug(f"Regex parser results: {regex_results}")
        return regex_results
    except re.error as e:
        logging.error(f"Invalid regex pattern: {regex_pattern}. Error: {e}")
        return []


def parse_entity_type(entity_type, full_content):
    try:
        if entity_type.script_parser and os.path.exists(os.path.join('data', 'parser', entity_type.script_parser)):
            # Assuming script_parser contains something like 'ipv6.py'
            # Convert this to 'data.parser.ipv6'
            parser_module_name = "data.parser." + entity_type.script_parser.replace('.py', '')
            #logging.debug(f"Attempting script-based parsing with: {parser_module_name}")
            return [(entity_type.entity_type_id, *match) for match in parse_with_script(parser_module_name, full_content)]
        elif entity_type.regex_pattern:
            #logging.debug(f"Attempting regex-based parsing with: {entity_type.regex_pattern}")
            return [(entity_type.entity_type_id, *match) for match in parse_with_regex(entity_type.regex_pattern, full_content)]
        else:
            #logging.debug(f"No parser found for entity type: {entity_type}")
            return []
    except Exception as e:
        logging.error(f"Error in parse_entity_type for {entity_type}: {e}")
        return []




def parse_content(full_content, abort_flag, db_session):
    #logging.debug("Starting parsing content")
    entity_types = db_session.query(EntityTypesTable).all()
    matches = []

    with multiprocessing.Pool() as pool:
        results = [pool.apply_async(parse_entity_type, (et, full_content)) for et in entity_types]

        for result in results:
            if abort_flag():
                logging.debug("Aborting parsing due to flag")
                break
            try:
                match_result = result.get()
                #logging.debug(f"Match result: {match_result}")
                matches.extend(match_result)
            except Exception as e:
                logging.error(f"Error parsing entity type: {e}")
    for match in matches:
        if len(match) != 4:
            logging.error(f"Unexpected format for parsd entity: {match}")
    #logging.debug(f"Finished parsing content. Total matches: {len(matches)}")
    return matches    




# for line number calculation, the parse_content should return the start_pos and end_pos calculated from the character positions in the full_content string
# parse_content should return the data in the expected format (entity_type_id, match_text, start_pos, end_pos)


""" Key Enhancements and Considerations:
Validation of Script-Based Parsers: If new script-based parsers are added in the future, 
ensure they conform to the expected interface (i.e., they should have a parse function that behaves as expected).
"""