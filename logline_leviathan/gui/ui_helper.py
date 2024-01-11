from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
import os
import logging
import csv

class UIHelper():
    def __init__(self, main_window):
        self.main_window = main_window

    def openFileNameDialog(self):
        if self.main_window.isProcessing():
            self.main_window.showProcessingWarning()
            return
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self.main_window, "Select Files", "", ";All Files (*)", options=options)
        if files:
            for file in files:
                if file not in self.main_window.filePaths:
                    self.main_window.filePaths.append(file)
            self.main_window.fileCountLabel.setText(f"   {len(self.main_window.filePaths)} files selected for analysis.")

    def openDirNameDialog(self):
        if self.main_window.isProcessing():
            self.main_window.showProcessingWarning()
            return
        options = QFileDialog.Options()
        directory = QFileDialog.getExistingDirectory(self.main_window, "Select Directory", "", options=options)
        if directory:
            self.addAllFilesFromDirectory(directory)
            self.main_window.fileCountLabel.setText(f"   {len(self.main_window.filePaths)} files selected for analysis.")

    def addAllFilesFromDirectory(self, directory):
        for root, dirs, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                if file_path not in self.main_window.filePaths:
                    self.main_window.filePaths.append(file_path)


    def clearFileSelection(self):
        if self.main_window.isProcessing():
            self.main_window.showProcessingWarning()
            return
        self.main_window.filePaths.clear()
        self.main_window.fileCountLabel.setText('0 files selected.')

    def openOutputDir(self):
        outputDirPath = os.path.dirname(self.main_window.outputFilePath)
        if os.path.exists(outputDirPath):
            QDesktopServices.openUrl(QUrl.fromLocalFile(outputDirPath))
        else:
            logging.error(f"Directory does not exist: {outputDirPath}")

    def generate_files_log(self, file_path, files_list):
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                for file in files_list:
                    writer.writerow([file])
        except Exception as e:
            logging.error(f"Error generating log file {file_path}: {e}")

def format_time(seconds):
    if seconds != seconds or seconds == float('inf'):  # Check for NaN and inf
        return "N/A"

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes} min {seconds} sec"


