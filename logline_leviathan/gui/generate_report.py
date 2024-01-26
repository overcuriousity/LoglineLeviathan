import os
import logging
from PyQt5.QtWidgets import (QMessageBox, QWidget, QApplication,
                             QFileDialog)
from PyQt5.QtCore import Qt
from logline_leviathan.gui.initui_report_window import initialize_generate_report_window
from logline_leviathan.gui.checkbox_panel import CheckboxPanel
from logline_leviathan.gui.ui_helper import UIHelper
from logline_leviathan.gui.customize_results import CustomizeResultsDialog
from logline_leviathan.database.database_manager import session_scope
from logline_leviathan.exporter.html_export import generate_html_file
from logline_leviathan.exporter.xlsx_export import generate_xlsx_file
from logline_leviathan.exporter.nice_export import generate_niceoutput_file




class GenerateReportWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.checkboxPanel = CheckboxPanel()
        self.ui_helper = UIHelper(self)
        self.outputFilePath = os.path.join(os.getcwd(), 'output', 'entities_export')

        initialize_generate_report_window(self, app)

        self.updateCheckboxes()




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
    
    def updateOutputFilePathLabel(self):
        outputDirPath = os.path.dirname(self.outputFilePath)
        display_text = f'{outputDirPath}/'
        self.outputFilePathLabel.setText(display_text)

    def openOutputFilepath(self):
        outputDirPath = os.path.dirname(self.outputFilePath)
        self.ui_helper.openFile(outputDirPath)

    def openCustomizeResultsDialog(self):
        dialog = CustomizeResultsDialog()
        if dialog.exec_():
            selected_columns = [dialog.comboBoxLayout.itemAt(i).widget().currentText() for i in range(dialog.comboBoxLayout.count())]

    def start_export_process(self):
        current_item = self.outputFormatList.currentItem()
        if current_item is not None:
            output_format = current_item.text().lower()
            extension_map = {'html': '.html', 'interactive html': '.html', 'xlsx': '.xlsx'}
            selected_extension = extension_map.get(output_format, '.html')
            only_crossmatches = self.crossmatchesCheckbox.isChecked()
            # Generate the initial output file path
            initial_output_path = f"{self.outputFilePath}{selected_extension}"
            
            unique_output_path = self.get_unique_filename(initial_output_path)

            try:
                with session_scope() as session:
                    selected_checkboxes = self.getSelectedCheckboxes()  # Get selected checkboxes from the tree
                    if not selected_checkboxes:
                        self.message("Operation Blocked", "No entities selected")
                        return

                    if output_format == 'html':
                        logging.debug(f"only_crossmatches: {only_crossmatches}")
                        generate_html_file(unique_output_path, session, selected_checkboxes, self.exportContextList.currentItem().text(), only_crossmatches)
                    elif output_format == 'interactive html':
                        logging.debug(f"only_crossmatches: {only_crossmatches}")
                        generate_niceoutput_file(unique_output_path, session, selected_checkboxes, self.exportContextList.currentItem().text(), only_crossmatches)
                    elif output_format == 'xlsx':
                        logging.debug(f"only_crossmatches: {only_crossmatches}")
                        generate_xlsx_file(unique_output_path, session, selected_checkboxes, self.exportContextList.currentItem().text(), only_crossmatches)
                    else:
                        raise ValueError(f"Unsupported format: {output_format}")

                    self.statusLabel.setText(f"   Exported to {unique_output_path}")
            except Exception as e:
                self.statusLabel.setText(f"   Export Error: {str(e)}")
                logging.error(f"Export Error: {str(e)}")
        else:
            self.message("Operation Blocked", "Specify Output Format and Context Scope")

    def selectOutputFile(self):
        options = QFileDialog.Options()
        output_format = self.outputFormatList.currentItem().text().lower()
        extension_map = {'html': '.html', 'xlsx': '.xlsx'}
        default_extension = extension_map.get(output_format, '')

        selected_file, _ = QFileDialog.getSaveFileName(
            self, 
            "Select Output File", 
            self.outputFilePath, 
            f"{output_format.upper()} Files (*{default_extension});;All Files (*)", 
            options=options
        )

        if selected_file:
            if not selected_file.endswith(default_extension):
                selected_file += default_extension
            self.outputFilePath = selected_file
            self.outputDir = os.path.dirname(selected_file)
            self.updateOutputFilePathLabel()


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
