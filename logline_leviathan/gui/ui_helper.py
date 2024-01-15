from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
import os
import logging
import csv
import sys 
import subprocess

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
        options |= QFileDialog.DontUseNativeDialog
        fileDialog = QFileDialog(self.main_window, "Select Directories", "", options=options)
        fileDialog.setFileMode(QFileDialog.Directory)
        fileDialog.setOption(QFileDialog.ShowDirsOnly, True)
        fileDialog.setOption(QFileDialog.DontResolveSymlinks, True)
        
        # Store previously selected directories
        selected_directories = []

        while True:
            if fileDialog.exec_() == QFileDialog.Accepted:
                directory = fileDialog.selectedFiles()[0]
                if directory and directory not in selected_directories:
                    selected_directories.append(directory)
                    self.addAllFilesFromDirectory(directory)
            else:
                break  # Exit loop if user cancels

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
        self.main_window.fileCountLabel.setText('   0 files selected.')

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

    def openFile(self, file_path):
        if sys.platform == 'win32':
            os.startfile(file_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', file_path])
        else:  # Linux and other Unix-like systems
            subprocess.Popen(['xdg-open', file_path])

def format_time(seconds):
    if seconds != seconds or seconds == float('inf'):  # Check for NaN and inf
        return "N/A"

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes} min {seconds} sec"




