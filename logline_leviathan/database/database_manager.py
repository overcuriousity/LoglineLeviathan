from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
import yaml
from contextlib import contextmanager
import logging


SessionFactory = sessionmaker(bind=create_engine('sqlite:///entities.db'))

Base = declarative_base()

class DistinctEntitiesTable(Base):
    __tablename__ = 'distinct_entities_table' 
    distinct_entities_id = Column(Integer, primary_key=True)
    distinct_entity = Column(String)
    entity_types_id = Column(Integer, ForeignKey('entity_types_table.entity_type_id'))
    regex_library = relationship("EntityTypesTable")  
    individual_entities = relationship("EntitiesTable", back_populates="entity")

class EntitiesTable(Base):
    __tablename__ = 'entities_table' 
    entities_id = Column(Integer, primary_key=True)
    distinct_entities_id = Column(Integer, ForeignKey('distinct_entities_table.distinct_entities_id'))
    entity_types_id = Column(Integer, ForeignKey('entity_types_table.entity_type_id'))
    regex_library = relationship("EntityTypesTable")  
    file_id = Column(Integer, ForeignKey('file_metadata.file_id')) 
    line_number = Column(Integer) 
    entry_timestamp = Column(DateTime)

    entity = relationship("DistinctEntitiesTable", back_populates="individual_entities")
    file = relationship("FileMetadata")
    context = relationship("ContextTable", uselist=False, back_populates="individual_entity")

class ContextTable(Base):
    __tablename__ = 'context_table' 
    context_id = Column(Integer, primary_key=True)
    entities_id = Column(Integer, ForeignKey('entities_table.entities_id'))
    context_small = Column(Text) 
    context_medium = Column(Text) 
    context_large = Column(Text) 
    individual_entity = relationship("EntitiesTable", back_populates="context")

class FileMetadata(Base):
    __tablename__ = 'file_metadata'
    # all stays as it is
    file_id = Column(Integer, primary_key=True)
    file_name = Column(String)
    file_path = Column(String)
    file_mimetype = Column(String)

class EntityTypesTable(Base):
    __tablename__ = 'entity_types_table'
    entity_type_id = Column(Integer, primary_key=True)
    entity_type = Column(String)
    regex_pattern = Column(String)
    gui_tooltip = Column(String)
    gui_name = Column(String)
    parent_type = Column(String, default='root')  # hierarchical structure from yaml specs


def populate_entity_types_table(db_session, yaml_path='data/entities.yaml'):
    logging.debug(f"Populating entity_types_table from: {yaml_path}")
    try:
        with open(yaml_path, 'r') as file:
            entities = yaml.safe_load(file)

        # Use a set for existing types for easier existence checking
        existing_types = {et.entity_type for et in db_session.query(EntityTypesTable).all()}

        for entity_key, entity_attrs in entities.items():
            entity_type = entity_attrs['entity_type'] 
            gui_name = entity_attrs['gui_name']
            regex_pattern = entity_attrs['regex']
            tooltip = entity_attrs['tooltip']
            parent_type = entity_attrs.get('parent', 'root')
            # Check if the entity_type already exists
            if entity_type not in existing_types:
                entity_type_entry = EntityTypesTable(
                    entity_type=entity_type, 
                    gui_name=gui_name, 
                    regex_pattern=regex_pattern, 
                    gui_tooltip=tooltip,
                    parent_type=parent_type
                )
                db_session.add(entity_type_entry)
                logging.debug(f"Adding new entry to entity_types_table: {entity_type_entry}")

        db_session.commit()
    except Exception as e:
        logging.error(f"Error in populate_entity_types_table: {e}")
        return None



def create_database(db_path='sqlite:///entities.db'):
    engine = create_engine(db_path)
    logging.debug(f"Create Database Engine")
    Base.metadata.create_all(engine)
    logging.debug(f"Created all Metadata")
    engine.dispose()
    logging.debug(f"Disposed Engine")

    # Start a new session
    session = SessionFactory()
    logging.debug(f"Started new session with session factory")
    
    # Check if EntityTypesTable is empty
    if not session.query(EntityTypesTable).first():  
        # Populate EntityTypesTable from the YAML file
        logging.debug(f"Didnt find the EntityTypesTable, running populate_entity_types_table")
        populate_entity_types_table(session)

    session.close()


def get_db_session():
    return SessionFactory()


if __name__ == "__main__":
    create_database()

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()