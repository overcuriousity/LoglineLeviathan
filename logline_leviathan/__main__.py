"""
You're welcome! I'm glad you like the name "Logline Leviathan". It's a fitting name for a program that can delve into the depths of unstructured text data like a leviathan, extracting valuable insights from the chaotic ocean of information. I hope your program is successful in its mission to help investigators navigate the dark, digital realm of cyberpunk."""

import sys
from PyQt5.QtWidgets import QApplication
from pathlib import Path
import argparse

# Add the parent directory of 'logline_leviathan' to sys.path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from logline_leviathan.gui.mainwindow import MainWindow
from logline_leviathan.database.database_manager import create_database

def initialize_database():
    create_database()


def main():
    parser = argparse.ArgumentParser(description='Analyze Export')
    parser.add_argument('directory', nargs='?', default='', help='Directory to analyze')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    main_window = MainWindow(app, initialize_database, args.directory)  # Pass the function as an argument
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
