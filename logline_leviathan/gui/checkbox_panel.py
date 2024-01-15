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
        self.treeWidget.setStyleSheet("""
            QTreeWidget::branch {color: white; /* White color for branches */
        }
        """)
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
            used_ids = {d.entity_types_id for d in db_session.query(DistinctEntitiesTable.entity_types_id).distinct()}
            # Clear existing items
            self.treeWidget.clear()
            rootItems = {}

            # Construct hierarchical tree structure
            for entity_type in entity_types:
                if entity_type.parent_type != 'root':  # Skip non-root items
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
            # Optionally expand all tree items
            self.treeWidget.expandAll()

        except Exception as e:
            logging.error("Error updating checkboxes", exc_info=True)

    def filterCheckboxes(self, filter_text):
        def filterTreeItem(treeItem):
            # Check if the current item or any of its properties match the filter text
            try:
                match = filter_text.lower() in treeItem.text(0).lower() or filter_text.lower() in treeItem.toolTip(0).lower()
            except Exception as e:
                logging.error(f"Error checking filter match for tree item: {e}")
                match = False

            # Recursively check child items and set 'childMatch' if any child matches
            childMatch = False
            for j in range(treeItem.childCount()):
                if filterTreeItem(treeItem.child(j)):
                    childMatch = True

            # Unhide the item and its parents if there's a match in the item or its children
            if match or childMatch:
                treeItem.setHidden(False)
                parent = treeItem.parent()
                while parent:
                    parent.setHidden(False)
                    parent = parent.parent()
                return True
            else:
                treeItem.setHidden(True)
                return False

        # Filter all top-level items
        for i in range(self.treeWidget.topLevelItemCount()):
            filterTreeItem(self.treeWidget.topLevelItem(i))


    def checkAllVisible(self):
        self._setCheckStateForVisibleItems(Qt.Checked)

    def uncheckAllVisible(self):
        self._setCheckStateForVisibleItems(Qt.Unchecked)

    def _setCheckStateForVisibleItems(self, state):
        def setCheckState(item):
            # Check if the item is supposed to be user checkable, not hidden, not a root item, and has occurrences
            if (item.flags() & Qt.ItemIsUserCheckable) and not item.isHidden() and item.parent():
                # Parse the text to get the number of occurrences
                text = item.text(0)
                occurrences = int(text.split('(')[-1].split()[0])
                if occurrences > 0:
                    item.setCheckState(0, state)

            # Apply state to child items
            for i in range(item.childCount()):
                childItem = item.child(i)
                setCheckState(childItem)

        # Apply state to all top-level items
        for i in range(self.treeWidget.topLevelItemCount()):
            topItem = self.treeWidget.topLevelItem(i)
            setCheckState(topItem)

    def expandAllTreeItems(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            self.treeWidget.topLevelItem(i).setExpanded(True)

    def collapseAllTreeItems(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            self.treeWidget.topLevelItem(i).setExpanded(False)