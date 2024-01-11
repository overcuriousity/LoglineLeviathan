import time
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from logline_leviathan.database.database_manager import session_scope
from .text_processor import process_text_file
from .xlsx_processor import process_xlsx_file
from .pdf_processor import process_pdf_file
import magic
import logging


class FileProcessorThread(QThread):
    update_progress = pyqtSignal(int)
    update_status = pyqtSignal(str)
    update_rate = pyqtSignal(float, int, float, int, float)
    last_update_time = 0

    def __init__(self, file_paths): 
        super().__init__()
        self.file_paths = file_paths  # Variable initialized here
        self.start_time = time.time()
        self.total_entities_count = 0
        self.total_entities_count_lock = QMutex()
        self.abort_mutex = QMutex()

        self.abort_flag = False
        self.file_paths = file_paths
        self.unsupported_files_count = 0
        self.processed_files_count = 0
        self.unsupported_files_list = []
        self.all_unsupported_files = []

    @property
    def abort_flag(self):
        self.abort_mutex.lock()
        flag = self._abort_flag
        self.abort_mutex.unlock()
        return flag

    @abort_flag.setter
    def abort_flag(self, value):
        self.abort_mutex.lock()
        self._abort_flag = value
        self.abort_mutex.unlock()
    
    def classify_file_type(self, file_path):
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        return file_type

    def run(self):
        try:
            for index, file_path in enumerate(self.file_paths):
                if self.abort_flag:
                    self.update_status.emit("Processing aborted.")
                    return

                file_type = self.classify_file_type(file_path)
                logging.info(f"Processing {file_type} file: {file_path}")

                with session_scope() as session:
                    if 'text/' in file_type:
                        process_text_file(file_path, file_type, self, session, lambda: self.abort_flag)
                    elif file_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                        process_xlsx_file(file_path, file_type, self, session, lambda: self.abort_flag)
                    elif 'application/pdf' in file_type:
                        process_pdf_file(file_path, file_type, self, session, lambda: self.abort_flag)
                    else:
                        logging.info(f"Skipping unsupported file type: {file_type}")
                        self.all_unsupported_files.append(file_path)
                        self.unsupported_files_count += 1
                        if len(self.unsupported_files_list) < 20:
                            self.unsupported_files_list.append(f"{file_path} (Type: {file_type})")
                        continue
                self.processed_files_count = index + 1 
                self.update_progress.emit(index + 1)

            self.update_status.emit(f"   Processing complete. A Total of {index + 1 - self.unsupported_files_count} of {len(self.file_paths)} files processed.")
        except Exception as e:
            logging.error(f"Error processing files: {e}")
            self.update_status.emit(f"Error processing files: {e}")

    def calculate_and_emit_rate(self):
        current_time = time.time()
        if current_time - self.last_update_time >= 1:  # Check if 1 second has passed
            entity_rate = self.calculate_rate()
            file_rate = self.calculate_file_rate()
            estimated_time = self.calculate_estimated_time_to_completion()
            self.update_rate.emit(entity_rate, self.total_entities_count, file_rate, self.processed_files_count, estimated_time)
            self.last_update_time = current_time

    def calculate_estimated_time_to_completion(self):
        total_files_to_process = len(self.file_paths)
        remaining_files = total_files_to_process - self.processed_files_count
        file_rate = self.calculate_file_rate()

        if file_rate > 0:
            estimated_time = remaining_files / file_rate
        else:
            estimated_time = float('inf')  # Indefinite time if rate is zero

        return estimated_time



    def calculate_file_rate(self):
        elapsed_time = time.time() - self.start_time
        return self.processed_files_count / elapsed_time if elapsed_time > 0 else 0


    def calculate_rate(self):
        elapsed_time = time.time() - self.start_time
        rate = self.total_entities_count / elapsed_time if elapsed_time > 0 else 0
        return rate

    def abort(self):
        self.abort_flag = True

    def getUnsupportedFilesCount(self):
        return self.unsupported_files_count
    
    def getUnsupportedFilesList(self):
        return self.unsupported_files_list

