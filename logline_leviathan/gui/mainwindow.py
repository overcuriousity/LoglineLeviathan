import sys
import os
import logging
import shutil
import multiprocessing
import logline_leviathan.gui.versionvars as versionvars
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QFileDialog, QLabel
from logline_leviathan.file_processor.file_processor_thread import FileProcessorThread
from logline_leviathan.database.database_manager import get_db_session, EntityTypesTable, EntitiesTable, session_scope
from logline_leviathan.database.database_utility import DatabaseUtility
from logline_leviathan.database.database_operations import DatabaseOperations
from logline_leviathan.gui.checkbox_panel import *
from logline_leviathan.gui.initui_mainwindow import initialize_main_window
from logline_leviathan.gui.generate_report import GenerateReportWindow
from logline_leviathan.gui.generate_wordlist import GenerateWordlistWindow
from logline_leviathan.gui.ui_helper import UIHelper, format_time

from logline_leviathan.database.query import DatabaseGUIQuery, ResultsWindow
from sqlalchemy import func
from datetime import datetime



class MainWindow(QWidget):
    def __init__(self, app, db_init_func, directory=""):
        super().__init__()
        logging_level = getattr(logging, versionvars.loglevel, None)
        if isinstance(logging_level, int):
            logging.basicConfig(level=logging_level)
        else:
            logging.warning(f"Invalid log level: {versionvars.loglevel}")

        self.app = app
        self.ui_helper = UIHelper(self)
        self.db_init_func = db_init_func
        db_init_func()
        self.database_operations = DatabaseOperations(self, db_init_func)
        self.current_db_path = 'entities.db'  # Default database path
        self.directory = directory
        self.filePaths = []
        self.log_dir = os.path.join(os.getcwd(), 'output', 'entities_export', 'log')
        os.makedirs(self.log_dir, exist_ok=True)

        self.external_db_path = None
        self.processing_thread = None
        self.generate_report_window = None
        #self.checkboxPanel = CheckboxPanel()
        self.databaseTree = DatabasePanel()

        self.db_query_instance = DatabaseGUIQuery()
        self.results_window = ResultsWindow(self.db_query_instance, parent=self)
        self.generate_wordlist_window = GenerateWordlistWindow(self.db_query_instance)
        self.generate_report_window = GenerateReportWindow(self.app)

        self.database_operations.ensureDatabaseExists()

        self.initUI()

        self.ui_helper = UIHelper(self)
        self.database_utility = DatabaseUtility(self)

        #self.loadRegexFromYAML()
        # Load data and update checkboxes
        self.refreshApplicationState()

        self.database_operations.checkScriptPresence()

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
        self.database_operations.populate_and_update_entities_from_yaml(yaml_data)
        self.updateDatabaseStatusLabel()
        self.updateTree()

    def updateTree(self):
        with session_scope() as session:
            self.databaseTree.updateTree(session)
        self.processing_thread = FileProcessorThread(self.filePaths)
        self.processing_thread.update_checkboxes_signal.connect(self.generate_report_window.updateCheckboxes)   
        self.processing_thread.update_checkboxes_signal.connect(self.generate_wordlist_window.updateCheckboxes)  

    def updateDatabaseStatusLabel(self):
        with session_scope() as session:
            entity_count = session.query(EntitiesTable).count()

        db_file_path = self.current_db_path  # Replace with your actual database file path
        db_file_size = os.path.getsize(db_file_path)
        db_file_size_mb = db_file_size / (1024 * 1024)  # Convert size to MB

        status_text = f"Entities: {entity_count}, DB Size: {db_file_size_mb:.2f} MB"
        self.databaseStatusLabel.setText(status_text)

    def execute_query_wrapper(self, query_text):
        self.results_window.show()
        self.results_window.set_query_and_execute(query_text)


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
                self.processing_thread.update_tree_signal.connect(self.updateTree)         
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
            unprocessed_files_log = f"{self.log_dir}_{current_timestamp}_unprocessed_files_log.csv"
            processed_files_log = f"{self.log_dir}_{current_timestamp}_processed_files_log.csv"

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

    def openLogDir(self):
        self.ui_helper.openFile(self.log_dir)

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

    def updateEntityRate(self, entity_rate, total_entities, file_rate, total_files_processed, estimated_time, data_rate_kibs):
        formatted_time = format_time(estimated_time)
        total_cpu_cores = multiprocessing.cpu_count()
        rate_text = (f"{entity_rate:.2f} entities/second, Total: {total_entities} // "
                    f"{file_rate:.2f} files/second, Total: {total_files_processed} // "
                    f"{data_rate_kibs:.2f} KiB/s // "
                    f"Estimated Completion: {formatted_time} // "
                    f"CPU Cores: {total_cpu_cores}")
        self.entityRateLabel.setText(rate_text)


    def openRegexLibrary(self):
        path_to_yaml = os.path.join(os.getcwd(), 'data', 'entities.yaml')
        if os.path.exists(path_to_yaml):
            self.ui_helper.openFile(path_to_yaml)  # Call openFile method on the UIHelper instance
        else:
            self.statusLabel.setText("   entities.yaml not found in the data directory.")



    def openGenerateReportWindow(self):
        if self.isProcessing():
            self.showProcessingWarning()
            return
        if not self.generate_report_window:
            self.generate_report_window = GenerateReportWindow(self.app)
        self.generate_report_window.show()

    def openGenerateWordlistWindow(self):
        if self.isProcessing():
            self.showProcessingWarning()
            return
        if not self.generate_wordlist_window:
            self.generate_wordlist_window = GenerateWordlistWindow(self.app)
        self.generate_wordlist_window.show()


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

