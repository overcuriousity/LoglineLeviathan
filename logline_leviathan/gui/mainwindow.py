import sys
import os
import logging
import shutil
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog, QLabel
from logline_leviathan.file_processor.file_processor_thread import FileProcessorThread
from logline_leviathan.database.database_manager import get_db_session, EntityTypesTable, EntitiesTable, session_scope
from logline_leviathan.database.database_utility import DatabaseUtility
from logline_leviathan.database.database_operations import DatabaseOperations
from logline_leviathan.gui.checkbox_panel import *
from logline_leviathan.gui.initui import initialize_main_window
from logline_leviathan.gui.ui_helper import UIHelper, format_time
from logline_leviathan.exporter.html_export import generate_html_file
from logline_leviathan.exporter.xlsx_export import generate_xlsx_file
from logline_leviathan.exporter.nice_export import generate_niceoutput_file
from sqlalchemy import func
from datetime import datetime



class MainWindow(QWidget):
    def __init__(self, app, db_init_func, directory=""):
        super().__init__()
        logging.basicConfig(level=logging.DEBUG)
        self.app = app
        self.ui_helper = UIHelper(self)
        self.db_init_func = db_init_func
        self.database_operations = DatabaseOperations(self, db_init_func)
        self.directory = directory
        self.filePaths = []
        self.outputDir = None
        self.outputFilePath = os.path.join(os.getcwd(), 'output', 'entities_export')
        self.external_db_path = None
        self.processing_thread = None
        self.checkboxPanel = CheckboxPanel()


        self.database_operations.ensureDatabaseExists()

        self.initUI()

        self.ui_helper = UIHelper(self)
        self.database_utility = DatabaseUtility(self)

        #self.loadRegexFromYAML()
        # Load data and update checkboxes
        self.refreshApplicationState()

        # Load files from the directory if specified
        if self.directory and os.path.isdir(self.directory):
            self.loadFilesFromDirectory(self.directory)


    def loadFilesFromDirectory(self, directory):
        for root, dirs, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                self.filePaths.append(file_path)
        self.fileCountLabel.setText(f"   {len(self.filePaths)} FILES SELECTED")


    def initUI(self):
        initialize_main_window(self, self.app)

    def openFileNameDialog(self):
        self.ui_helper.openFileNameDialog()

    def openDirNameDialog(self):
        self.ui_helper.openDirNameDialog()

    def clearFileSelection(self):
        self.ui_helper.clearFileSelection()



    def refreshApplicationState(self):
        self.db_session = get_db_session()
        yaml_data = self.database_operations.loadRegexFromYAML()
        #self.database_operations.populate_entity_types_table_from_yaml(yaml_data)
        self.database_operations.populate_and_update_entities_from_yaml(yaml_data)

        self.updateCheckboxes()

    def quickStartWorkflow(self):
        self.clearFileSelection()
        self.purgeDatabase()
        self.openDirNameDialog()
        self.processFiles()

    def purgeDatabase(self):
        self.database_utility.purgeDatabase()

    def importDatabase(self):
        self.database_utility.importDatabase()

    def exportDatabase(self):
        self.database_utility.exportDatabase()
    

    def processFiles(self):
        try:
            fileCount = len(self.filePaths)
            if fileCount > 0:
                self.progressBar.setMaximum(fileCount)
                self.db_init_func()
                self.processing_thread = FileProcessorThread(self.filePaths)  # Assign the thread to processing_thread
                self.processing_thread.finished.connect(self.onProcessingFinished)
                self.processing_thread.update_progress.connect(self.progressBar.setValue)
                self.processing_thread.update_status.connect(self.statusLabel.setText)
                self.processing_thread.update_rate.connect(self.updateEntityRate)
                self.processing_thread.start()
            else:
                self.message("Information", "No files Selected, select files first. Aborted.")
        except Exception as e:
            logging.error(f"Error processing files: {e}")

    def abortAnalysis(self):
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.abort()
            self.processing_thread.wait() 
            #self.processing_thread = None
            self.statusLabel.setText("   Analysis aborted by user.")
            logging.info(f"Analysis aborted manually.")
            self.refreshApplicationState()

    def onProcessingFinished(self):
        if self.processing_thread:
            summary = self.getProcessingSummary()
            unsupported_files_count = self.processing_thread.getUnsupportedFilesCount()

            # Generate CSV files for unprocessed and processed files
            current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unprocessed_files_log = f"{self.outputFilePath}_{current_timestamp}_unprocessed_files_log.csv"
            processed_files_log = f"{self.outputFilePath}_{current_timestamp}_processed_files_log.csv"

            self.ui_helper.generate_files_log(unprocessed_files_log, self.processing_thread.all_unsupported_files)
            processed_files = set(self.processing_thread.file_paths) - set(self.processing_thread.all_unsupported_files)
            self.ui_helper.generate_files_log(processed_files_log, list(processed_files))

            if unsupported_files_count > 0:
                summary += f"\nSkipped {unsupported_files_count} unsupported files."
                link_label = QLabel(f'<a href="#">Open list of all unsupported files...</a>')
                link_label.linkActivated.connect(lambda: self.ui_helper.openFile(unprocessed_files_log))
                self.message("Processing Summary", summary, link_label)
            else:
                self.message("Processing Summary", summary)

            if self.external_db_path:
                try:
                    shutil.copy('entities.db', self.external_db_path)
                    self.statusLabel.setText(f"   Database saved at: {self.external_db_path}")
                except Exception as e:
                    logging.error(f"Error exporting database: {e}")
                    self.statusLabel.setText(f"   Error exporting database: {e}")

            self.refreshApplicationState()
            self.processing_thread = None

    def getProcessingSummary(self):
        with session_scope() as session:
            entity_counts = session.query(EntityTypesTable.gui_name, func.count(EntitiesTable.entities_id)) \
                                   .join(EntityTypesTable, EntitiesTable.entity_types_id == EntityTypesTable.entity_type_id) \
                                   .group_by(EntityTypesTable.gui_name) \
                                   .all()

            summary = "Analysis Summary:\n\n"
            for gui_name, count in entity_counts:
                summary += f"{gui_name}: {count} entities found\n"

            return summary

    def getUnsupportedFilesCount(self):
        if self.processing_thread:
            return self.processing_thread.getUnsupportedFilesCount()
        return 0

    def isProcessing(self):
        return self.processing_thread and self.processing_thread.isRunning()

    def showProcessingWarning(self):
        self.message("Operation Blocked", "Cannot perform this operation while file processing is running.")

    def updateEntityRate(self, entity_rate, total_entities, file_rate, total_files_processed, estimated_time):
        formatted_time = format_time(estimated_time)
        rate_text = f"{entity_rate:.2f} entities/second, Total: {total_entities} // {file_rate:.2f} files/second, Total: {total_files_processed}, Estimated Completion: {formatted_time}"
        self.entityRateLabel.setText(rate_text)

    def openRegexLibrary(self):
        path_to_yaml = os.path.join(os.getcwd(), 'data', 'entities.yaml')
        if os.path.exists(path_to_yaml):
            self.ui_helper.openFile(path_to_yaml)  # Call openFile method on the UIHelper instance
        else:
            self.statusLabel.setText("   entities.yaml not found in the data directory.")

    def updateCheckboxes(self):
        with session_scope() as session:
            self.checkboxPanel.updateCheckboxes(session)

    def updateOutputFilePathLabel(self):
        outputDirPath = os.path.dirname(self.outputFilePath)
        display_text = f'{outputDirPath}{self.outputFilePath}'
        self.outputFilePathLabel.setText(display_text)

    def openOutputFilepath(self):
        outputDirPath = os.path.dirname(self.outputFilePath)
        self.ui_helper.openFile(outputDirPath)

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

    def start_export_process(self):
        if self.isProcessing():
            self.showProcessingWarning()
            return

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

                    if output_format == 'html':
                        generate_html_file(unique_output_path, session, selected_checkboxes, self.exportContextList.currentItem().text(), only_crossmatches)
                    elif output_format == 'interactive html':
                        generate_niceoutput_file(unique_output_path, session, selected_checkboxes, self.exportContextList.currentItem().text(), only_crossmatches)
                    elif output_format == 'xlsx':
                        generate_xlsx_file(unique_output_path, session, selected_checkboxes, self.exportContextList.currentItem().text(), only_crossmatches)
                    else:
                        raise ValueError(f"Unsupported format: {output_format}")

                    self.statusLabel.setText(f"   Exported to {unique_output_path}")
            except Exception as e:
                self.statusLabel.setText(f"   Export Error: {str(e)}")
                logging.error(f"Export Error: {str(e)}")
        else:
            self.message("Operation Blocked", "Specify Output Format and Context Scope")

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



def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

