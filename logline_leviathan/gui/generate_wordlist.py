import os
from PyQt5.QtWidgets import (QMessageBox, QWidget, QApplication,
                             QFileDialog, QLabel, QPushButton, QGridLayout, QGroupBox, QHBoxLayout, QVBoxLayout, QLineEdit)
from PyQt5.QtCore import Qt
from logline_leviathan.gui.checkbox_panel import *
from logline_leviathan.gui.ui_helper import UIHelper
from logline_leviathan.database.database_manager import session_scope
from logline_leviathan.exporter.wordlist_export import generate_wordlist
from logline_leviathan.gui.checkbox_panel import *
import shutil
import glob




class GenerateWordlistWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.checkboxPanel = CheckboxPanel()
        self.ui_helper = UIHelper(self)
        self.WordlistPath = os.path.join(os.getcwd(), 'data', 'wordlist')
        os.makedirs(self.WordlistPath, exist_ok=True)

        self.initialize_generate_wordlist_window(app)


        self.updateCheckboxes()



    def initialize_generate_wordlist_window(generate_wordlist_window, app):
        generate_wordlist_window.setWindowTitle('Logline Leviathan')
        generate_wordlist_window.mainLayout = QVBoxLayout(generate_wordlist_window)
        #generate_wordlist_window.extendedLayout = QHBoxLayout(generate_wordlist_window)
        generate_wordlist_window.db_session = None
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
            min-width: 50px;
            min-height: 15px;
        }

        QPushButton:hover {
            background-color: #6E6E6E; /* Slightly lighter grey on hover */
        }

        QPushButton:pressed {
            background-color: #484848; /* Even darker grey when pressed */
        }
        """
        
        highlited_button_style = """
        QPushButton {
            background-color: #3C8CCE; /* Lighter blue background */
            color: white; /* White text */
            border-style: outset;
            border-width: 2px;
            border-radius: 1px; /* Rounded corners */
            border-color: #4A4A4A;
            padding: 6px;
            min-width: 50px;
            min-height: 15px;
        }

        QPushButton:hover {
            background-color: #7EC0EE; /* Even lighter blue on hover */
        }

        QPushButton:pressed {
            background-color: #4A86E8; /* Slightly darker blue when pressed */
        }
        """


        generate_wordlist_window.setStyleSheet(stylesheet)
        generate_wordlist_window.statusLabel = QLabel('   Awaiting Selection for which Entities to include.', generate_wordlist_window)
        generate_wordlist_window.statusLabel.setWordWrap(True)
        generate_wordlist_window.statusLabel.setMinimumHeight(40)
        generate_wordlist_window.statusLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        generate_wordlist_window.mainLayout.addWidget(generate_wordlist_window.statusLabel)
        # Create a GroupBox for the CheckboxPanel
        exportOptionsGroupBox = QGroupBox("EXPORT OPTIONS", generate_wordlist_window)
        exportOptionsLayout = QVBoxLayout(exportOptionsGroupBox)
        generate_wordlist_window.checkboxPanel = CheckboxPanel()
        # Create a horizontal layout
        filterLayout = QHBoxLayout()

        # Create the "Check All" button
        checkAllButton = QPushButton("Check All", generate_wordlist_window)
        checkAllButton.clicked.connect(lambda: generate_wordlist_window.checkboxPanel.checkAllVisible())

        # Create the "Uncheck All" button
        uncheckAllButton = QPushButton("Uncheck All", generate_wordlist_window)
        uncheckAllButton.clicked.connect(lambda: generate_wordlist_window.checkboxPanel.uncheckAllVisible())

        expandAllButton = QPushButton("Expand All", generate_wordlist_window)
        expandAllButton.clicked.connect(lambda: generate_wordlist_window.checkboxPanel.expandAllTreeItems())

        collapseAllButton = QPushButton("Collapse All", generate_wordlist_window)
        collapseAllButton.clicked.connect(lambda: generate_wordlist_window.checkboxPanel.collapseAllTreeItems())

        # Add buttons to the filter layout, to the left of the filter label
        filterLayout.addWidget(checkAllButton)
        filterLayout.addWidget(uncheckAllButton)
        filterLayout.addWidget(expandAllButton)
        filterLayout.addWidget(collapseAllButton)
        
        # Create the label for the filter
        filterLabel = QLabel("Filter options:")
        filterLayout.addWidget(filterLabel)  # Add label to the horizontal layout

        # Add Text Input for Filtering
        filterLineEdit = QLineEdit(generate_wordlist_window)
        filterLineEdit.setPlaceholderText("   enter shortcuts, tooltips, or entity types")
        filterLineEdit.setStyleSheet("""
            QLineEdit {
                background-color: #3C4043; /* Background color */
                color: white; /* Text color */
                min-height: 20px;
            }
        """)
        filterLayout.addWidget(filterLineEdit)  # Add line edit to the horizontal layout

        exportOptionsLayout.addLayout(filterLayout)  # Add the horizontal layout to the export options layout


        # Add CheckboxPanel to the GroupBox's Layout
        exportOptionsLayout.addWidget(generate_wordlist_window.checkboxPanel)


        # Connect the textChanged signal of QLineEdit to a new method
        filterLineEdit.textChanged.connect(generate_wordlist_window.checkboxPanel.filterCheckboxes)

        generate_wordlist_window.mainLayout.addWidget(exportOptionsGroupBox)

        copyWordlistToParserDirButton = QPushButton('Copy Wordlist to Parser Directory', generate_wordlist_window)
        copyWordlistToParserDirButton.clicked.connect(generate_wordlist_window.copyWordlistToParserDir)
        generate_wordlist_window.mainLayout.addWidget(copyWordlistToParserDirButton)

        # Exit Button Layout
        bottomLayout = QGridLayout()


        generate_wordlist_window.openWordlistPathButton = QPushButton('Open Wordlist Directory', generate_wordlist_window)
        generate_wordlist_window.openWordlistPathButton.clicked.connect(generate_wordlist_window.openWordlistPath)
        bottomLayout.addWidget(generate_wordlist_window.openWordlistPathButton, 1, 1)

        # Start Export Button
        generate_wordlist_window.startExportButton = QPushButton('Generate Wordlist', generate_wordlist_window)
        generate_wordlist_window.startExportButton.clicked.connect(generate_wordlist_window.start_export_process)
        generate_wordlist_window.startExportButton.setStyleSheet(highlited_button_style)
        bottomLayout.addWidget(generate_wordlist_window.startExportButton, 1, 2) 
        

        # Output File Directory
        generate_wordlist_window.selectOutputFileButton = QPushButton('Specify Output File', generate_wordlist_window)
        generate_wordlist_window.selectOutputFileButton.clicked.connect(generate_wordlist_window.selectOutputFile)
        bottomLayout.addWidget(generate_wordlist_window.selectOutputFileButton, 2, 1)

        # Exit Button
        generate_wordlist_window.exitButton = QPushButton('Exit', generate_wordlist_window)
        generate_wordlist_window.exitButton.clicked.connect(generate_wordlist_window.close)
        bottomLayout.addWidget(generate_wordlist_window.exitButton, 2, 2)



        generate_wordlist_window.crossmatchesCheckbox = QCheckBox('Include Only Crossmatches (Entities, which show up in multiple analyzed files)', generate_wordlist_window)
        bottomLayout.addWidget(generate_wordlist_window.crossmatchesCheckbox, 0, 1)

        # Output File Path Label 
        generate_wordlist_window.WordlistPathLabel = QLabel('', generate_wordlist_window)
        generate_wordlist_window.updateWordlistPathLabel()  # Call this method to set the initial text
        bottomLayout.addWidget(generate_wordlist_window.WordlistPathLabel, 0, 2)

        generate_wordlist_window.mainLayout.addLayout(bottomLayout)
        generate_wordlist_window.setLayout(generate_wordlist_window.mainLayout)


    def updateCheckboxes(self):
        with session_scope() as session:
            self.checkboxPanel.updateCheckboxes(session)

    def getSelectedCheckboxes(self):
        selected_checkboxes = []
        def traverseTreeItems(treeItem):
            if treeItem.checkState(0) == Qt.Checked:
                selected_checkboxes.append(treeItem)
            for i in range(treeItem.childCount()):
                traverseTreeItems(treeItem.child(i))
        for i in range(self.checkboxPanel.treeWidget.topLevelItemCount()):
            traverseTreeItems(self.checkboxPanel.treeWidget.topLevelItem(i))
        return selected_checkboxes
    
    def updateWordlistPathLabel(self):
        outputDirPath = os.path.dirname(self.WordlistPath)
        display_text = f'{outputDirPath}/'
        self.WordlistPathLabel.setText(display_text)

    def openWordlistPath(self):
        outputDirPath = os.path.dirname(self.WordlistPath)
        wordlistPath = os.path.join(outputDirPath, 'wordlist')
        self.ui_helper.openFile(wordlistPath)



    def selectOutputFile(self):
        options = QFileDialog.Options()
        output_format = self.outputFormatList.currentItem().text().lower()
        extension_map = {'html': '.html', 'xlsx': '.xlsx'}
        default_extension = extension_map.get(output_format, '')

        selected_file, _ = QFileDialog.getSaveFileName(
            self, 
            "Select Output File", 
            self.WordlistPath, 
            f"{output_format.upper()} Files (*{default_extension});;All Files (*)", 
            options=options
        )

        if selected_file:
            if not selected_file.endswith(default_extension):
                selected_file += default_extension
            self.WordlistPath = selected_file
            self.outputDir = os.path.dirname(selected_file)
            self.updateWordlistPathLabel()


    def get_unique_filename(self, base_path):
        directory, filename = os.path.split(base_path)
        name, extension = os.path.splitext(filename)
        counter = 1

        new_path = base_path
        while os.path.exists(new_path):
            new_filename = f"{name}_{counter}{extension}"
            new_path = os.path.join(directory, new_filename)
            counter += 1

        return new_path

    def copyWordlistToParserDir(self):
        try:
            # Path to the parser directory
            parser_dir = os.path.join(os.getcwd(), 'data', 'parser')

            # Ensure the parser directory exists
            os.makedirs(parser_dir, exist_ok=True)

            # Find the newest .txt file in the WordlistPath directory
            list_of_files = glob.glob(os.path.join(self.WordlistPath, '*.txt'))
            if not list_of_files:
                raise FileNotFoundError("No .txt files found in the WordlistPath directory.")

            newest_file = max(list_of_files, key=os.path.getctime)

            # Destination file path
            destination_file = os.path.join(parser_dir, 'wordlist.txt')

            # Copy and overwrite the newest file to the destination
            shutil.copy2(newest_file, destination_file)

            self.statusLabel.setText(f"   Wordlist copied successfully to {destination_file}")
        except Exception as e:
            self.message("Copy Error", f"An error occurred: {str(e)}")



    def start_export_process(self):
        # Base filename for the wordlist file
        base_filename = "wordlist.txt"

        # Construct the full path with the base filename
        full_output_path = os.path.join(self.WordlistPath, base_filename)

        # Generate a unique filename to avoid overwriting existing files
        unique_output_path = self.get_unique_filename(full_output_path)

        try:
            with session_scope() as session:
                selected_checkboxes = self.getSelectedCheckboxes()
                if not selected_checkboxes:
                    self.message("Operation Blocked", "No entities selected")
                    return

                only_crossmatches = self.crossmatchesCheckbox.isChecked()

                generate_wordlist(unique_output_path, session, selected_checkboxes, only_crossmatches)
                self.statusLabel.setText(f"   Exported to {unique_output_path}")
        except Exception as e:
            self.statusLabel.setText(f"   Export Error: {str(e)}")
            logging.error(f"Export Error: {str(e)}")


    def message(self, title, text, extra_widget=None):
        msgBox = QMessageBox()
        msgBox.setStyleSheet("""
            QMessageBox {
                background-color: #282C34; /* Dark grey background */
            }
            QLabel {
                color: white; /* White text */
            }
            QPushButton {
                color: white; /* White text for buttons */
                background-color: #4B5563; /* Dark grey background for buttons */
                border-style: solid;
                border-width: 2px;
                border-radius: 5px;
                border-color: #4A4A4A;
                padding: 6px;
                min-width: 80px;
                min-height: 30px;
            }
        """)
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle(title)
        msgBox.setText(text)
        if extra_widget:
            msgBox.setInformativeText('')
            msgBox.layout().addWidget(extra_widget, 1, 1)
        msgBox.exec_()
