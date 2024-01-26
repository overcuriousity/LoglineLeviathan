from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import QTimer
import random

class TerminalEasterEgg(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        self.terminal_widget = QTextEdit(self)
        self.terminal_widget.setStyleSheet("background-color: black; color: green;")
        self.terminal_widget.setReadOnly(True)
        layout.addWidget(self.terminal_widget)

        # Timer for fake prompts
        self.terminal_timer = QTimer(self)
        self.terminal_timer.timeout.connect(self.update_terminal)
        self.terminal_timer.start(1000)  # Update every second

    def update_terminal(self):
        fake_prompts = [
            "Decrypting data...",
            "Accessing secure server...",
            "Running diagnostics...",
            "Analyzing patterns...",
            "Compiling code...",
            "Scanning network...",
            # Add more fake prompts as desired
        ]
        self.terminal_widget.append(random.choice(fake_prompts))
