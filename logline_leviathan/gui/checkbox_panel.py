from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QToolTip, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import logging
from logline_leviathan.database.database_manager import EntitiesTable, DistinctEntitiesTable, EntityTypesTable
from sqlalchemy import func

class CustomCheckBox(QCheckBox):
    def __init__(self, *args, **kwargs):
        super(CustomCheckBox, self).__init__(*args, **kwargs)
        self.setMouseTracking(True)  # Enable mouse tracking
        self.setStyleSheet("QCheckBox { color: white; }")

    def mouseMoveEvent(self, event):
        QToolTip.showText(event.globalPos(), self.toolTip())  # Show tooltip at mouse position
        super(CustomCheckBox, self).mouseMoveEvent(event)

class CheckboxPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderHidden(True)  # Hide the header

        layout.addWidget(self.treeWidget)

    def _addChildren(self, parentItem, parent_entity_type, db_session, used_ids):
        child_entity_types = db_session.query(EntityTypesTable).filter(EntityTypesTable.parent_type == parent_entity_type).all()
        for child_entity_type in child_entity_types:
            count = db_session.query(EntitiesTable).filter(EntitiesTable.entity_types_id == child_entity_type.entity_type_id).count()
            text = f"{child_entity_type.gui_name} ({count} occurrences found)"
            childItem = QTreeWidgetItem(parentItem)
            childItem.setFlags(childItem.flags() | Qt.ItemIsUserCheckable)
            childItem.setCheckState(0, Qt.Unchecked)
            childItem.setText(0, text)
            childItem.setToolTip(0, child_entity_type.gui_tooltip)
            childItem.entity_type_id = child_entity_type.entity_type_id
            childItem.entity_type = child_entity_type.entity_type

            # Set color and enable/disable based on usage
            childItem.setForeground(0, QColor('green' if child_entity_type.entity_type_id in used_ids else 'white'))
            childItem.setDisabled(child_entity_type.entity_type_id not in used_ids)

            # Recursive call to add children of this child
            self._addChildren(childItem, child_entity_type.entity_type, db_session, used_ids)


    def updateCheckboxes(self, db_session):
        logging.info("Updating checkboxes with database content")

        try:
            # Query database for entity types
            entity_types = db_session.query(EntityTypesTable).all()
            logging.debug(f"Number of entity types found: {len(entity_types)}")
            for entity_type in entity_types[:5]:  # Log first 5 entity types
                logging.debug(f"Entity Type: {entity_type}, Parent: {entity_type.parent_type}")
            # Query used entity type ids
            used_ids = {d.entity_types_id for d in db_session.query(DistinctEntitiesTable.entity_types_id).distinct()}
            logging.debug(f"Used entity type ids: {used_ids}")
            # Clear existing items
            self.treeWidget.clear()
            rootItems = {}

            # Construct hierarchical tree structure
            for entity_type in entity_types:
                logging.debug(f"entered loop for constructing the tree structure for entity type: {entity_type} and its parent: {entity_type.parent_type}")
                if entity_type.parent_type != 'root':  # Skip non-root items
                    logging.debug(f"Skipping non-root item: {entity_type}")
                    continue

                count = db_session.query(EntitiesTable).filter(EntitiesTable.entity_types_id == entity_type.entity_type_id).count()
                text = f"{entity_type.gui_name}"
                treeItem = QTreeWidgetItem()
                #treeItem.setText(0, text)
                treeItem.setToolTip(0, entity_type.gui_tooltip)
                treeItem.entity_type_id = entity_type.entity_type_id
                treeItem.entity_type = entity_type.entity_type
                if entity_type.regex_pattern:
                    treeItem.setFlags(treeItem.flags() | Qt.ItemIsUserCheckable)
                    treeItem.setCheckState(0, Qt.Unchecked)
                    text = f"{entity_type.gui_name} ({count} occurrences found)"
                treeItem.setText(0, text)
                # Add item to tree widget
                self.treeWidget.addTopLevelItem(treeItem)
                rootItems[entity_type.entity_type_id] = treeItem

                # Call recursive function to add children
                self._addChildren(treeItem, entity_type.entity_type, db_session, used_ids)
                logging.debug(f"Entity Type: {entity_type.gui_name}, Parent: {entity_type.parent_type}")
            # Optionally expand all tree items
            self.treeWidget.expandAll()

        except Exception as e:
            logging.error("Error updating checkboxes", exc_info=True)

    def filterCheckboxes(self, filter_text):
        def filterTreeItem(treeItem):
            match = any(filter_text.lower() in treeItem.text(0).lower() for keyword in ['gui_name', 'entity_type', 'gui_tooltip'])
            treeItem.setHidden(not match)
            # Do the same for child items
            for j in range(treeItem.childCount()):
                filterTreeItem(treeItem.child(j))

        # Filter all top-level items
        for i in range(self.treeWidget.topLevelItemCount()):
            filterTreeItem(self.treeWidget.topLevelItem(i))

