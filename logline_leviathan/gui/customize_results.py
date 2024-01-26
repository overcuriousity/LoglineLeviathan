from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton
from logline_leviathan.database.database_manager import get_db_session, EntitiesTable, DistinctEntitiesTable, EntityTypesTable, ContextTable, FileMetadata, session_scope
from sqlalchemy import func, label
from sqlalchemy.orm import aliased

class CustomizeResultsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_session = get_db_session()
        self.setWindowTitle("Customize Results")
        stylesheet = """
        /* Style for the main window */
        QWidget {
            background-color: #282C34; /* Dark grey background */
            color: white; /* White text */
        }

        /* Style for buttons */
        QPushButton {
            background-color: #4B5563; /* Dark grey background */
            color: white; /* White text */
            border-style: outset;
            border-width: 2px;
            border-radius: 1px; /* Rounded corners */
            border-color: #4A4A4A;
            padding: 6px;
            min-width: 60px;
            min-height: 20px;
        }

        QPushButton:hover {
            background-color: #6E6E6E; /* Slightly lighter grey on hover */
        }

        QPushButton:pressed {
            background-color: #484848; /* Even darker grey when pressed */
        }
        """
        self.layout = QVBoxLayout(self)
        self.setStyleSheet(stylesheet)

        self.comboBoxLayout = QHBoxLayout()
        self.layout.addLayout(self.comboBoxLayout)

        # Initially add one combo box
        self.addComboBox()

        # Button to add more combo boxes
        self.addButton = QPushButton("Add Column", self)
        self.addButton.clicked.connect(self.addComboBox)
        self.layout.addWidget(self.addButton)

        # OK and Cancel buttons
        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.clicked.connect(self.reject)
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.layout.addLayout(self.buttonLayout)

        self.selectedColumns = []

    def addComboBox(self):
        comboBox = QComboBox(self)
        comboBox.addItems(['Entity Type', 'Entity', 'Occurrence', 'File Name', 'Line Number', 'Timestamp', 'Context (Same Line)', 'Context (Some Lines)', 'Context (Many Lines)'])  
        self.comboBoxLayout.addWidget(comboBox)

    def comboBoxes(self):
        # Utility method to get all combo boxes
        return [self.comboBoxLayout.itemAt(i).widget() for i in range(self.comboBoxLayout.count())]
    
    def on_accept(self):
        self.selectedColumns = [comboBox.currentText() for comboBox in self.comboBoxes()]
        self.accept()

