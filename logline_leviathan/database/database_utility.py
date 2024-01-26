import shutil
import logging
import time
import os
from PyQt5.QtWidgets import QFileDialog
from sqlalchemy.exc import SQLAlchemyError
from logline_leviathan.database.database_manager import get_db_session

class DatabaseUtility():
    def __init__(self, main_window):
        self.main_window = main_window

    def purgeDatabase(self):
        if self.main_window.isProcessing():
            self.main_window.showProcessingWarning()
            return

        try:
            db_session = get_db_session()
            # Close and dispose of any existing database session
            if db_session:
                db_session.close()
                db_session.bind.dispose()

            # Attempt to delete the database file with retries
            retries = 3
            for attempt in range(retries):
                try:
                    if os.path.exists('entities.db'):
                        os.remove('entities.db')
                    break
                except OSError as e:
                    if attempt < retries - 1:
                        time.sleep(0.1)
                    else:
                        raise e

            # Reinitialize the database
            self.main_window.db_init_func()
            self.main_window.statusLabel.setText("   Empty Database created. Process files now.")
            logging.debug("Database created.")
            self.main_window.refreshApplicationState()
        except SQLAlchemyError as e:
            logging.error(f"Error creating database: {e}")
        except Exception as e:
            logging.error(f"General error: {e}")

    def importDatabase(self):
        if self.main_window.isProcessing():
            self.main_window.showProcessingWarning()
            return
        options = QFileDialog.Options()
        db_file, _ = QFileDialog.getOpenFileName(self.main_window, "Select External Database", "", "Database Files (*.db);;All Files (*)", options=options)
        if db_file and db_file.endswith(".db"):
            try:
                shutil.copy(db_file, 'entities.db')
                self.main_window.current_db_path = db_file
                self.main_window.statusLabel.setText("   External database selected for this session.")
                self.main_window.refreshApplicationState()
            except Exception as e:
                logging.error(f"Error selecting external database: {e}")
                self.main_window.statusLabel.setText(f"   Error selecting external database: {e}")
        else:
            self.main_window.statusLabel.setText("   No valid database selected.")

    def exportDatabase(self):
        if self.main_window.isProcessing():
            self.main_window.showProcessingWarning()
            return
        options = QFileDialog.Options()
        default_filename = "entities_" + time.strftime('%Y%m%d_%H%M%S') + ".db"
        save_path, _ = QFileDialog.getSaveFileName(self.main_window, "Save Database File", default_filename, "Database Files (*.db);;All Files (*)", options=options)
        if save_path:
            try:
                shutil.copy('entities.db', save_path)
                self.main_window.statusLabel.setText(f"   Database exported successfully to {save_path}")
            except Exception as e:
                logging.error(f"Error exporting database: {e}")
                self.main_window.statusLabel.setText(f"   Error exporting database: {e}")


