import logging
import os
import yaml
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QMessageBox, QLabel, QRadioButton, QPushButton
from logline_leviathan.gui.ui_helper import UIHelper

from logline_leviathan.database.database_manager import *




class DatabaseOperations:
    def __init__(self, main_window, db_init_func):
        self.main_window = main_window
        self.db_init_func = db_init_func
        self.selected_resolutions = []


    def ensureDatabaseExists(self):
        db_path = 'entities.db'
        db_exists = os.path.exists(db_path)
        if not db_exists:
            logging.info("Database does not exist. Creating new database...")
            self.db_init_func()  # This should call create_database
        else:
            logging.info("Database exists.")

    def loadRegexFromYAML(self):
        with open('./data/entities.yaml', 'r') as file:
            yaml_data = yaml.safe_load(file)
        clean_yaml_data = self.notify_duplicates_from_yaml(yaml_data)
        return clean_yaml_data
    
    def notify_duplicates_from_yaml(self, yaml_data):
        duplicates = []
        seen_fields = {'entity_type': {}, 'gui_name': {}, 'gui_tooltip': {}, 'regex_pattern': {}, 'script_parser': {}}

        for entity_name, entity_data in yaml_data.items():
            # Iterate through each field and check for duplicates
            for field in seen_fields:
                value = entity_data.get(field)
                if value:  # Only check non-empty values
                    if value in seen_fields[field]:
                        duplicates.append({
                            "duplicate_field": field,
                            "entity_name": entity_name,
                            "original_entity_name": seen_fields[field][value]
                        })
                    seen_fields[field][value] = entity_name

        if duplicates:
            self.show_duplicate_error_dialog(duplicates)
            raise ValueError("Duplicate entries found in YAML file. Aborting.")
        return yaml_data
    
    def show_duplicate_error_dialog(self, duplicates):
        dialog = DuplicateErrorDialog(duplicates)
        dialog.exec_()


    
    def show_resolve_inconsistencies_dialog(self, db_entity, yaml_entity):
        dialog = ResolveInconsistenciesDialog([(db_entity, yaml_entity)])
        result = dialog.exec_()
        if result == QDialog.Accepted:
            resolutions = dialog.getSelectedResolutions()
            if resolutions:
                return resolutions[0]  # Return the first (and only) resolution
        return None


    def populate_and_update_entities_from_yaml(self, yaml_data):
        with session_scope() as session:
            db_entities = session.query(EntityTypesTable).all()
            db_entity_dict = {entity.entity_type: entity for entity in db_entities}

            for entity_name, entity_data in yaml_data.items():
                entity_type = entity_data['entity_type']
                db_entity = db_entity_dict.get(entity_type)

                if db_entity is None:
                    db_entity = self.find_potentially_modified_entity(db_entities, entity_data)

                if db_entity:
                    if self.is_duplicate_or_inconsistent(db_entity, entity_data, db_entities):
                        logging.warning(f"Issue found with entity {db_entity} and {entity_data}. Handling resolution.")
                        resolution = self.show_resolve_inconsistencies_dialog(db_entity, entity_data)
                        if resolution:
                            self.apply_resolution([(resolution, db_entity)], session)  # Pass db_entity as part of the resolution
                    else:
                        for key, value in entity_data.items():
                            setattr(db_entity, key, value)
                else:
                    new_entity = EntityTypesTable(**entity_data)
                    session.add(new_entity)

            session.commit()

    def find_potentially_modified_entity(self, db_entities, yaml_entity):
        for db_ent in db_entities:
            if any(
                getattr(db_ent, key) == yaml_entity[key] 
                for key in ['entity_type', 'gui_name', 'gui_tooltip', 'regex_pattern', 'script_parser'] 
                if yaml_entity[key]
            ):
                return db_ent
        return None



    def is_duplicate_or_inconsistent(self, db_entity, yaml_entity, db_entities):
        if db_entity:
            # Check for inconsistency in existing entity
            for key, value in yaml_entity.items():
                if getattr(db_entity, key, None) != value and value is not None:
                    return True

        # Check for duplicate across all entities
        for db_ent in db_entities:
            if db_ent.entity_type == yaml_entity['entity_type']:
                continue

            if any(
                getattr(db_ent, key) == yaml_entity[key] and yaml_entity[key] is not None
                for key in ['entity_type', 'gui_name', 'gui_tooltip', 'regex_pattern', 'script_parser']
            ):
                logging.debug(f"Found duplicate entity: {db_ent}")
                return True

        return False




    def update_database_entry(self, db_entity, yaml_entity):
        for key, value in yaml_entity.items():
            setattr(db_entity, key, value)



    def apply_resolution(self, resolutions, session):
        with open('./data/entities.yaml', 'r') as file:
            yaml_data = yaml.safe_load(file)

        for (resolution, entity), db_entity in resolutions:
            if resolution == 'yaml':
                logging.debug(f"Resolving YAML entity: {entity} with resolution: yaml and db_entity: {db_entity}")
                if db_entity:
                    foreign_keys = self.capture_foreign_keys(db_entity.entity_type_id, session)
                    session.delete(db_entity)
                
                new_entity = EntityTypesTable(**entity)
                session.add(new_entity)
                session.flush()


            elif resolution == 'db':
                if entity:  # Existing database entity is chosen
                    yaml_data[entity.entity_type] = {
                        'entity_type': entity.entity_type,
                        'gui_name': entity.gui_name,
                        'gui_tooltip': entity.gui_tooltip,
                        'parent_type': entity.parent_type,
                        'regex_pattern': entity.regex_pattern,
                        'script_parser': entity.script_parser
                    }

        with open('./data/entities.yaml', 'w') as file:
            yaml.dump(yaml_data, file)


    def capture_foreign_keys(self, entity_id, session):
        foreign_keys = {}

        # Use entity_id to capture references
        distinct_entities_refs = session.query(DistinctEntitiesTable).filter_by(entity_types_id=entity_id).all()
        foreign_keys['distinct_entities'] = [ref.distinct_entities_id for ref in distinct_entities_refs]

        entities_refs = session.query(EntitiesTable).filter_by(entity_types_id=entity_id).all()
        foreign_keys['entities'] = [ref.entities_id for ref in entities_refs]

        return foreign_keys


    def reassign_foreign_keys(self, new_entity, foreign_keys, session):
        # Reassigning references in DistinctEntitiesTable
        for distinct_id in foreign_keys.get('distinct_entities', []):
            distinct_entity = session.query(DistinctEntitiesTable).get(distinct_id)
            distinct_entity.entity_types_id = new_entity.entity_type_id

        # Reassigning references in EntitiesTable
        for entity_id in foreign_keys.get('entities', []):
            entity = session.query(EntitiesTable).get(entity_id)
            entity.entity_types_id = new_entity.entity_type_id


    def checkScriptPresence(self):
        parser_directory = './data/parser'
        missing_scripts = []

        with session_scope() as session:
            all_entities = session.query(EntityTypesTable).all()
            for entity in all_entities:
                script_name = entity.script_parser
                if script_name:
                    script_path = os.path.join(parser_directory, script_name)
                    if not os.path.exists(script_path):
                        missing_scripts.append(script_name)

        if missing_scripts:
            missing_scripts_str = "\n".join(missing_scripts)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Missing Script Files")
            msg.setText("Some script files are missing:")
            msg.setInformativeText(missing_scripts_str)
            msg.exec_()  # Display the message box

        return missing_scripts


class ResolveInconsistenciesDialog(QDialog):
    def __init__(self, inconsistencies, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resolve Inconsistencies")
        self.inconsistencies = inconsistencies
        self.resolution_choices = []
        self.selected_entity = None 
        self.selected_entities = []
        self.selected_resolutions = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        for db_entity, yaml_entity in self.inconsistencies:
            db_entity_str = self.format_entity_for_display(db_entity)
            yaml_entity_str = self.format_entity_for_display(yaml_entity)

            # Create labels and radio buttons for each inconsistency
            db_label = QLabel(f"Database Entry: {db_entity_str}")
            yaml_label = QLabel(f"YAML Entry: {yaml_entity_str}")
            db_radio = QRadioButton("Keep Database Entry")
            yaml_radio = QRadioButton("Keep YAML Entry")

            layout.addWidget(db_label)
            layout.addWidget(db_radio)
            layout.addWidget(yaml_label)
            layout.addWidget(yaml_radio)

            self.resolution_choices.append((db_radio, yaml_radio))

        # Buttons for OK and Cancel
        btn_ok = QPushButton("OK", self)
        btn_ok.clicked.connect(self.on_ok)
        btn_cancel = QPushButton("Cancel", self)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_ok)
        layout.addWidget(btn_cancel)

    def on_ok(self):
        self.selected_resolutions = []  # Reset the list before storing new selections
        for (db_radio, yaml_radio), (db_entity, yaml_entity) in zip(self.resolution_choices, self.inconsistencies):
            if db_radio.isChecked():
                self.selected_resolutions.append(('db', db_entity))
            elif yaml_radio.isChecked():
                self.selected_resolutions.append(('yaml', yaml_entity))
            else:
                self.selected_resolutions.append((None, None))

        self.accept()


    def getSelectedResolutions(self):
        return self.selected_resolutions
    
    def format_entity_for_display(self, entity):
        if isinstance(entity, dict):
            # YAML entity is already a dictionary
            return "\n".join(f"{key}: {value}" for key, value in entity.items())
        else:
            # Database entity needs to be formatted
            return "\n".join(f"{attr}: {getattr(entity, attr)}" for attr in ['entity_type', 'gui_name', 'gui_tooltip', 'parent_type', 'regex_pattern', 'script_parser'])



class DuplicateErrorDialog(QDialog):
    def __init__(self, duplicates, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Entries Found")
        self.duplicates = duplicates
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Display duplicate entries
        error_label = QLabel("Duplicate entries found in entities.yaml:")
        layout.addWidget(error_label)

        for dup in self.duplicates:
            dup_str = self.format_entity_for_display(dup)
            dup_label = QLabel(dup_str)
            layout.addWidget(dup_label)

        # Buttons
        open_button = QPushButton("Open YAML File", self)
        open_button.clicked.connect(self.openYAML)
        exit_button = QPushButton("Exit", self)
        exit_button.clicked.connect(self.close)

        layout.addWidget(open_button)
        layout.addWidget(exit_button)

    def format_entity_for_display(self, entity):
        if isinstance(entity, dict):
            return "\n".join(f"{key}: {value}" for key, value in entity.items())

    def openYAML(self):
        ui_helper = UIHelper(main_window=self)
        ui_helper.openFile('data/entities.yaml')


