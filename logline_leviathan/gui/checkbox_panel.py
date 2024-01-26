from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QToolTip, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import logging
from logline_leviathan.database.database_manager import EntitiesTable, DistinctEntitiesTable, EntityTypesTable, get_db_session
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
        self.treeWidget.setHeaderHidden(True)  
        self.treeWidget.setStyleSheet("""
            QTreeWidget::branch {color: white; /* White color for branches */
        }
        """)
        layout.addWidget(self.treeWidget)

    def _addChildren(self, parentItem, parent_entity_type, db_session, used_ids, depth=0):
        # Log the depth of recursion
        #logging.debug(f"Adding children at depth: {depth}, parent entity type: {parent_entity_type}")

        child_entity_types = db_session.query(EntityTypesTable).filter(EntityTypesTable.parent_type == parent_entity_type).all()
        for child_entity_type in child_entity_types:
            count = db_session.query(EntitiesTable).filter(EntitiesTable.entity_types_id == child_entity_type.entity_type_id).count()
            text = f"{child_entity_type.gui_name}"
            childItem = QTreeWidgetItem(parentItem)

            isCheckable = not child_entity_type.entity_type.startswith("category_")
            childItem.setFlags(childItem.flags() | Qt.ItemIsUserCheckable) if isCheckable else None
            childItem.setCheckState(0, Qt.Unchecked) if isCheckable else None
            text += f" ({count} occurrences found)" if isCheckable else ""
            childItem.setText(0, text)
            childItem.setToolTip(0, child_entity_type.gui_tooltip)
            childItem.entity_type_id = child_entity_type.entity_type_id
            childItem.entity_type = child_entity_type.entity_type

            childItem.setForeground(0, QColor('green' if child_entity_type.entity_type_id in used_ids else 'white'))

            # Recursive call with increased depth
            depth = depth + 1
            self._addChildren(childItem, child_entity_type.entity_type, db_session, used_ids, depth)




    def updateCheckboxes(self, db_session):
        #logging.info("Updating checkboxes with database content")

        try:
            # Query database for entity types
            entity_types = db_session.query(EntityTypesTable).all()
            used_ids = {d.entity_types_id for d in db_session.query(DistinctEntitiesTable.entity_types_id).distinct()}
            #logging.debug(f"Used IDs: {used_ids}")
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
                treeItem.setToolTip(0, entity_type.gui_tooltip)
                treeItem.entity_type_id = entity_type.entity_type_id
                treeItem.entity_type = entity_type.entity_type
                if not entity_type.entity_type.startswith("category_"):
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
        self.db_session = get_db_session()
        used_ids = self.getUsedIds(self.db_session)
        self._setCheckStateForVisibleItems(Qt.Checked, used_ids)

    def uncheckAllVisible(self):
        self.db_session = get_db_session()
        used_ids = self.getUsedIds(self.db_session)
        self._setCheckStateForVisibleItems(Qt.Unchecked, used_ids)



    def _setCheckStateForVisibleItems(self, state, used_ids):
        def setCheckState(item):
            try:
                if (item.flags() & Qt.ItemIsUserCheckable) and not item.isHidden(): # and item.parent():
                    # Check if entity_type_id is in used_ids
                    if hasattr(item, 'entity_type_id') and item.entity_type_id in used_ids:
                        item.setCheckState(0, state)
                        #logging.debug(f"Set check state for item with entity_type_id: {item.entity_type_id}")
                    #else:
                        #logging.debug(f"Item with entity_type_id: {getattr(item, 'entity_type_id', 'N/A')} skipped")

                for i in range(item.childCount()):
                    childItem = item.child(i)
                    setCheckState(childItem)
            except Exception as e:
                logging.error(f"Error in setCheckState: {e}")

        try:
            for i in range(self.treeWidget.topLevelItemCount()):
                topItem = self.treeWidget.topLevelItem(i)
                setCheckState(topItem)
        except Exception as e:
            logging.error(f"Error in _setCheckStateForVisibleItems: {e}")



    def getUsedIds(self, db_session):
        # Assuming db_session is your database session object
        try:
            used_ids = {d.entity_types_id for d in db_session.query(DistinctEntitiesTable.entity_types_id).distinct()}
            return used_ids
        except Exception as e:
            logging.error(f"Error in getUsedIds: {e}")
            return set()

    


    def expandAllTreeItems(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            self.treeWidget.topLevelItem(i).setExpanded(True)

    def collapseAllTreeItems(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            self.treeWidget.topLevelItem(i).setExpanded(False)

class DatabasePanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderHidden(True)  # Hide the header
        self.treeWidget.setStyleSheet("""QTreeWidget::branch {color: white; /* White color for branches */}""")
        layout.addWidget(self.treeWidget)


    def _getTotalCountForChildren(self, entity_type, db_session):
        # Recursive function to get total count
        total_count = db_session.query(EntitiesTable).filter(EntitiesTable.entity_types_id == entity_type.entity_type_id).count()
        child_entity_types = db_session.query(EntityTypesTable).filter(EntityTypesTable.parent_type == entity_type.entity_type).all()
        for child_entity_type in child_entity_types:
            total_count += self._getTotalCountForChildren(child_entity_type, db_session)
        return total_count

    def _addChildren(self, parentItem, parent_entity_type, db_session, used_ids, depth=0):
        # Log the depth of recursion
        #logging.debug(f"Adding children at depth: {depth}, parent entity type: {parent_entity_type}")

        child_entity_types = db_session.query(EntityTypesTable).filter(EntityTypesTable.parent_type == parent_entity_type).all()
        for child_entity_type in child_entity_types:
            if not child_entity_type.entity_type.startswith("category_"):
                count = db_session.query(EntitiesTable).filter(EntitiesTable.entity_types_id == child_entity_type.entity_type_id).count()
                text = f" {count} - {child_entity_type.gui_name} ({child_entity_type.entity_type})"
            else:
                # Use the new method to get the total count for this category
                total_count = self._getTotalCountForChildren(child_entity_type, db_session)
                text = f" {total_count} - {child_entity_type.gui_name} (Total)"

            childItem = QTreeWidgetItem(parentItem)
            childItem.setText(0, text)
            childItem.setToolTip(0, child_entity_type.gui_tooltip)
            childItem.entity_type_id = child_entity_type.entity_type_id
            childItem.entity_type = child_entity_type.entity_type
            childItem.setForeground(0, QColor('green' if child_entity_type.entity_type_id in used_ids else 'white'))

            # Recursive call with increased depth
            depth = depth + 1
            self._addChildren(childItem, child_entity_type.entity_type, db_session, used_ids, depth)



    def updateTree(self, db_session):
        #logging.info("Updating checkboxes with database content")

        try:
            # Query database for entity types
            entity_types = db_session.query(EntityTypesTable).all()
            used_ids = {d.entity_types_id for d in db_session.query(DistinctEntitiesTable.entity_types_id).distinct()}
            #logging.debug(f"Used IDs: {used_ids}")
            # Clear existing items
            self.treeWidget.clear()
            rootItems = {}

            # Construct hierarchical tree structure
            for entity_type in entity_types:
                if entity_type.parent_type != 'root':  # Skip non-root items
                    continue

                if not entity_type.entity_type.startswith("category_"):
                    count = db_session.query(EntitiesTable).filter(EntitiesTable.entity_types_id == entity_type.entity_type_id).count()
                    text = f"{count} - {entity_type.gui_name} {entity_type.entity_type}"
                else:
                    # Use the new method to get the total count for this category
                    total_count = self._getTotalCountForChildren(entity_type, db_session)
                    text = f"{total_count} - {entity_type.gui_name} (Total)"

                treeItem = QTreeWidgetItem()
                treeItem.setText(0, text)
                treeItem.setToolTip(0, entity_type.gui_tooltip)
                treeItem.entity_type_id = entity_type.entity_type_id
                treeItem.entity_type = entity_type.entity_type
                treeItem.setForeground(0, QColor('green' if entity_type.entity_type_id in used_ids else 'white'))
                self.treeWidget.addTopLevelItem(treeItem)

                # Call recursive function to add children
                self._addChildren(treeItem, entity_type.entity_type, db_session, used_ids)
            # Optionally expand all tree items
            #self.treeWidget.collapseAll()

        except Exception as e:
            logging.error("Error updating database tree", exc_info=True)

    def expandAllTreeItems(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            self.treeWidget.topLevelItem(i).setExpanded(True)

    def collapseAllTreeItems(self):
        for i in range(self.treeWidget.topLevelItemCount()):
            self.treeWidget.topLevelItem(i).setExpanded(False)