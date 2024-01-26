from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging



SessionFactory = sessionmaker(bind=create_engine('sqlite:///entities.db'))

Base = declarative_base()

class DistinctEntitiesTable(Base):
    __tablename__ = 'distinct_entities_table' 
    distinct_entities_id = Column(Integer, primary_key=True) #is the primary key of the distinct_entities_table
    distinct_entity = Column(String, index=True) # is the distinct entity iself, e.g. 192.168.1.1, 192.168.1.1, etc., bc1qy3h5l8n9, etc.
    entity_types_id = Column(Integer, ForeignKey('entity_types_table.entity_type_id')) # is the foreign key of the entity_types_table
    regex_library = relationship("EntityTypesTable")  
    individual_entities = relationship("EntitiesTable", back_populates="entity")

class EntitiesTable(Base):
    __tablename__ = 'entities_table' 
    entities_id = Column(Integer, primary_key=True) # is the primary key of the entities_table
    distinct_entities_id = Column(Integer, ForeignKey('distinct_entities_table.distinct_entities_id')) # is the foreign key of the distinct_entities_table
    entity_types_id = Column(Integer, ForeignKey('entity_types_table.entity_type_id')) # is the foreign key of the entity_types_table
    regex_library = relationship("EntityTypesTable")  
    file_id = Column(Integer, ForeignKey('file_metadata.file_id')) # is the foreign key of the file_metadata
    line_number = Column(Integer) # is the line number - the line inside the file which is available in the file_metadata
    entry_timestamp = Column(DateTime) # the timestamp which was obtained via regex from the original input file

    entity = relationship("DistinctEntitiesTable", back_populates="individual_entities")
    file = relationship("FileMetadata")
    context = relationship("ContextTable", uselist=False, back_populates="individual_entity")

class ContextTable(Base):
    __tablename__ = 'context_table' 
    context_id = Column(Integer, primary_key=True) # is the primary key of the context_table
    entities_id = Column(Integer, ForeignKey('entities_table.entities_id')) # is the foreign key of the entities_table
    context_small = Column(Text) # is the context of the entity which was parsed from the original file, by a specific number of lines before and after the entity
    context_medium = Column(Text) # is the context of the entity which was parsed from the original file, by a specific number of lines before and after the entity
    context_large = Column(Text, index=True)
    #context_indexed = Column(Text, index=True) # is the context of the entity which was parsed from the original file, by a specific number of lines before and after the entity
    individual_entity = relationship("EntitiesTable", back_populates="context")

class FileMetadata(Base):
    __tablename__ = 'file_metadata'
    # all stays as it is
    file_id = Column(Integer, primary_key=True) # is the primary key of the file_metadata
    file_name = Column(String, index=True) # is the name of the original input file
    file_path = Column(String) # is the path of the original input file
    file_mimetype = Column(String) # is the MIME type of the original input file

class EntityTypesTable(Base):
    __tablename__ = 'entity_types_table'
    entity_type_id = Column(Integer, primary_key=True) # is the primary key of the entity_types_table
    entity_type = Column(String) # is the entity type short form, e.g. ipv4, ipv6, btcaddr, etc
    regex_pattern = Column(String) # a regex pattern which could be used for parsing the files
    script_parser = Column(String) # the name of the python script which could be used for parsing the files
    gui_tooltip = Column(String) # the GUI tooltip
    gui_name = Column(String) # the GUI name which is more descriptive than entity_type
    parent_type = Column(String, default='root')  # hierarchical structure from yaml specs
    


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
        #populate_entity_types_table(session)

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
        
