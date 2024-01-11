from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QCheckBox, QToolTip, QSizePolicy, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor
import logging
import os
from logline_leviathan.database.database_manager import EntitiesTable, DistinctEntitiesTable, EntityTypesTable


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

        # Create a Scroll Area and set its widget as the Tree Widget
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.treeWidget)

        layout.addWidget(self.scrollArea)


    def updateAvailableCheckboxes(self, regex_entities):
        
        self.treeWidget.clear()  # Clear existing items
        parentItems = {}  # Dictionary to store parent tree items

        for entity in regex_entities:
            parent_type = entity.parent_type if hasattr(entity, 'parent_type') else 'root'

            treeItem = QTreeWidgetItem()
            treeItem.setFlags(treeItem.flags() | Qt.ItemIsUserCheckable)  # Add checkbox
            treeItem.setText(0, entity.gui_name)
            treeItem.setCheckState(0, Qt.Unchecked)  # Default state
            treeItem.setToolTip(0, entity.gui_tooltip)  # Set tooltip for the item
            treeItem.entity_type_id = entity.entity_type_id  # Store the entity_type_id
            treeItem.entity_type = entity.entity_type  # Store the entity_type

            if parent_type == 'root':
                self.treeWidget.addTopLevelItem(treeItem)
                parentItems[entity.entity_type] = treeItem
            else:
                parentItem = parentItems.get(parent_type)
                if parentItem:
                    parentItem.addChild(treeItem)

        self.treeWidget.expandAll()  # Optional: Expand all tree items



    def updateCheckboxesBasedOnDatabase(self, db_session):
        logging.info("Updating checkboxes based on database content")
        entity_type_id_to_name = {regex.entity_type_id: regex.gui_name for regex in db_session.query(EntityTypesTable).all()}

        used_ids = {d.entity_types_id for d in db_session.query(DistinctEntitiesTable.entity_types_id).distinct()}

        def updateTreeItem(treeItem):
            entity_type_id = int(treeItem.entity_type_id)
            count = db_session.query(EntitiesTable).filter(EntitiesTable.entity_types_id == entity_type_id).count()
            treeItem.setText(0, f"{entity_type_id_to_name[entity_type_id]} ({count} occurrences found)")
            
            if count > 0:
                treeItem.setForeground(0, QColor('green'))
            else:
                treeItem.setForeground(0, QColor('white'))
            
            treeItem.setDisabled(entity_type_id not in used_ids)

            # Update child items
            for i in range(treeItem.childCount()):
                updateTreeItem(treeItem.child(i))

        # Update all top-level items
        for i in range(self.treeWidget.topLevelItemCount()):
            updateTreeItem(self.treeWidget.topLevelItem(i))

    def filterCheckboxes(self, filter_text):
        def filterTreeItem(treeItem):
            # Check if filter text is in the tree item
            match = any(filter_text.lower() in treeItem.text(0).lower() for keyword in ['gui_name', 'entity_type', 'gui_tooltip'])
            treeItem.setHidden(not match)

            # Do the same for child items
            for j in range(treeItem.childCount()):
                filterTreeItem(treeItem.child(j))

        # Filter all top-level items
        for i in range(self.treeWidget.topLevelItemCount()):
            filterTreeItem(self.treeWidget.topLevelItem(i))

