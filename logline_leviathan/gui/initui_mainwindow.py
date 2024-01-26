import os
from PyQt5.QtWidgets import (QGridLayout, QPushButton, QLabel, QHBoxLayout, QApplication,
                             QVBoxLayout, QProgressBar, QTableWidget, QTableWidgetItem,
                             QCheckBox, QListWidget, QGroupBox, QLineEdit)
from PyQt5.QtGui import  QColor, QPixmap #QPalette removed
from PyQt5.QtCore import Qt
import logline_leviathan.gui.versionvars as versionvars
from logline_leviathan.gui.presentation_mode import TerminalEasterEgg
from logline_leviathan.database.query import QueryLineEdit
from logline_leviathan.gui.generate_report import GenerateReportWindow
from logline_leviathan.gui.checkbox_panel import DatabasePanel

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)




def initialize_main_window(main_window, app):
        main_window.setWindowTitle('Logline Leviathan')
        main_window.mainLayout = QVBoxLayout(main_window)
        #main_window.extendedLayout = QHBoxLayout(main_window)
        main_window.db_session = None

        # Logo
        pixmap = QPixmap(os.path.join('logline_leviathan', 'gui', 'logo.png'))
        scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logoLabel = QLabel(main_window)
        logoLabel.setPixmap(scaled_pixmap)
        # Version label
        versionLabel = QLabel(versionvars.version_string, main_window)  # Replace X.X.X with your actual version number
        versionLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Horizontal layout
        hbox = QHBoxLayout()
        hbox.addWidget(versionLabel)  # Add version label to the left
        hbox.addStretch()  # Add stretchable space between the version label and logo
        hbox.addWidget(logoLabel, alignment=Qt.AlignRight)  # Add logo label to the right

        # Add horizontal layout to the main layout
        main_window.mainLayout.addLayout(hbox)

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
            min-width: 60px;
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

        main_window.setStyleSheet(stylesheet)


        
        # Data Ingestion Settings Label
        main_window.dataIngestionLabel = QLabel('   Welcome to the LogLineAnalyzer.\n   Start by using the Quick-Start Button, which allows the selection of Directories to analyze.\n   Immediately after Selection, the Analysis will start to recursively parse the files with properties set in the RegexLibrary.')
        main_window.dataIngestionLabel.setWordWrap(True)
        main_window.dataIngestionLabel.setMinimumHeight(60)
        main_window.dataIngestionLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")

        # Quick Start Button
        quickStartButton = QPushButton('Quick Start', main_window)
        quickStartButton.setStyleSheet(highlited_button_style)
        quickStartButton.setFixedSize(270, 55)
        quickStartButton.clicked.connect(main_window.quickStartWorkflow)  

        # Horizontal layout for label and button
        hBoxLayout = QHBoxLayout()
        hBoxLayout.addWidget(quickStartButton)
        hBoxLayout.addWidget(main_window.dataIngestionLabel)
        

        # Add horizontal layout to the main layout
        main_window.mainLayout.addLayout(hBoxLayout)


        # Grid Layout for Top Buttons
        topButtonGridLayout = QGridLayout()

        # Create Buttons
        main_window.openButton = QPushButton('Add Files to Selection', main_window)
        main_window.openButton.clicked.connect(main_window.openFileNameDialog)

        main_window.addDirButton = QPushButton('Add Directory and Subdirectories', main_window)
        main_window.addDirButton.clicked.connect(main_window.openDirNameDialog)

        main_window.clearSelectionButton = QPushButton('Clear all Files from Selection', main_window)
        main_window.clearSelectionButton.clicked.connect(lambda: main_window.clearFileSelection())

        main_window.createDbButton = QPushButton('Create empty local Database', main_window)
        main_window.createDbButton.clicked.connect(main_window.purgeDatabase)

        main_window.importDbButton = QPushButton('Select existing Database', main_window)
        main_window.importDbButton.clicked.connect(main_window.importDatabase)

        main_window.exportDBButton = QPushButton('Export existing Database', main_window)
        main_window.exportDBButton.clicked.connect(main_window.exportDatabase)

        main_window.inspectRegexButton = QPushButton('Inspect Regex Library (Restart if changed)', main_window)
        main_window.inspectRegexButton.clicked.connect(main_window.openRegexLibrary)

        main_window.processButton = QPushButton('Start/Resume File Analysis', main_window)
        main_window.processButton.setStyleSheet(highlited_button_style)
        main_window.processButton.clicked.connect(main_window.processFiles)

        main_window.abortAnalysisButton = QPushButton('Abort running Analysis', main_window)
        main_window.abortAnalysisButton.clicked.connect(main_window.abortAnalysis)

        # Create GroupBoxes
        fileSelectionGroup = QGroupBox("File Selection")
        databaseGroup = QGroupBox("Database Operations")
        analysisGroup = QGroupBox("Analysis Controls")

        # Create Layouts for each GroupBox
        fileSelectionLayout = QVBoxLayout()
        databaseLayout = QVBoxLayout()
        analysisLayout = QVBoxLayout()

        # Add Buttons to their respective Layout
        fileSelectionLayout.addWidget(main_window.openButton)
        fileSelectionLayout.addWidget(main_window.addDirButton)
        fileSelectionLayout.addWidget(main_window.clearSelectionButton)

        databaseLayout.addWidget(main_window.createDbButton)
        databaseLayout.addWidget(main_window.importDbButton)
        databaseLayout.addWidget(main_window.exportDBButton)

        analysisLayout.addWidget(main_window.inspectRegexButton)
        analysisLayout.addWidget(main_window.processButton)
        analysisLayout.addWidget(main_window.abortAnalysisButton)

        # Set Layouts to GroupBoxes
        fileSelectionGroup.setLayout(fileSelectionLayout)
        databaseGroup.setLayout(databaseLayout)
        analysisGroup.setLayout(analysisLayout)

        # Add GroupBoxes to Grid
        topButtonGridLayout.addWidget(fileSelectionGroup, 0, 0)
        topButtonGridLayout.addWidget(databaseGroup, 0, 1)
        topButtonGridLayout.addWidget(analysisGroup, 0, 2)

        # Set uniform spacing
        topButtonGridLayout.setHorizontalSpacing(20)
        topButtonGridLayout.setVerticalSpacing(10)

        # Add the Grid Layout to the Main Layout
        main_window.mainLayout.addLayout(topButtonGridLayout)

        # Progress Bar, Status Label, Entity Rate Label, File Count Label
        main_window.progressBar = QProgressBar(main_window)
        main_window.mainLayout.addWidget(main_window.progressBar)

        main_window.statusLabel = QLabel('   READY TO OPERATE // ANALYSIS NOT STARTED', main_window)
        main_window.statusLabel.setWordWrap(True)
        main_window.statusLabel.setMinimumHeight(40)
        main_window.statusLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        main_window.mainLayout.addWidget(main_window.statusLabel)

        main_window.entityRateLabel = QLabel('   READY TO OPERATE // ANALYSIS NOT STARTED', main_window)
        main_window.mainLayout.addWidget(main_window.entityRateLabel)

        main_window.fileCountLabel = QLabel('   0 FILES SELECTED', main_window)
        main_window.fileCountLabel.setMinimumHeight(40)
        main_window.fileCountLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        main_window.mainLayout.addWidget(main_window.fileCountLabel)

        # Create the new QGroupBox for Database Query
        databaseQueryGroupBox = QGroupBox("DATABASE QUERY", main_window)
        databaseQueryLayout = QVBoxLayout(databaseQueryGroupBox)
        databaseQueryLayout.setAlignment(Qt.AlignTop)

        # Create QLineEdit for text input
        databaseQueryLineEdit = QueryLineEdit(main_window)
        databaseQueryLineEdit.setPlaceholderText("   Enter search query...")
        databaseQueryLineEdit.setStyleSheet("""
            QLineEdit {
                background-color: #3C4043;
                color: white;
                min-height: 20px;
            }
        """)
        databaseQueryLineEdit.returnPressed.connect(lambda: main_window.execute_query_wrapper(databaseQueryLineEdit.text()))
        databaseQueryLabel = QLabel("   Query the database by any term. \n   The usage of standard search operators \n   +, - and '' is supported.", main_window)
        # Create QPushButton for executing the query
        executeQueryButton = QPushButton("Execute Query", main_window)
        executeQueryButton.clicked.connect(lambda: main_window.execute_query_wrapper(databaseQueryLineEdit.text()))
        main_window.databaseStatusLabel = QLabel("   Database not yet initialized.", main_window)
        # Add QLineEdit and QPushButton to the QVBoxLayout
        databaseQueryLayout.addWidget(databaseQueryLineEdit)
        databaseQueryLayout.addWidget(databaseQueryLabel)
        databaseQueryLayout.addWidget(executeQueryButton)
        databaseQueryLayout.addWidget(main_window.databaseStatusLabel)

        # Set the QVBoxLayout as the layout for the QGroupBox
        databaseQueryGroupBox.setLayout(databaseQueryLayout)
        
        databaseContentsGroupBox = QGroupBox("DATABASE CONTENTS", main_window)
        databaseContentsLayout = QHBoxLayout(databaseContentsGroupBox)
        databaseContentSwitchLayout = QVBoxLayout()

        expandAllButton = QPushButton("Expand All", main_window)
        expandAllButton.clicked.connect(lambda: main_window.databaseTree.expandAllTreeItems())

        collapseAllButton = QPushButton("Collapse All", main_window)
        collapseAllButton.clicked.connect(lambda: main_window.databaseTree.collapseAllTreeItems())
        databaseContentSwitchLayout.addWidget(expandAllButton)
        databaseContentSwitchLayout.addWidget(collapseAllButton)
        databaseContentSwitchLayout.setAlignment(Qt.AlignTop)
        databaseContentsLayout.addWidget(main_window.databaseTree)
        databaseContentsLayout.addLayout(databaseContentSwitchLayout)


        generationOptionsGroupBox = QGroupBox("GENERATION OPTIONS", main_window)
        generationOptionsLayout = QVBoxLayout(generationOptionsGroupBox)
        generationOptionsLayout.setAlignment(Qt.AlignTop)
        # Corrected button creation
        openGenerateReportWindowButton = QPushButton("Generate Report", main_window)
        openGenerateReportWindowButton.clicked.connect(main_window.openGenerateReportWindow)

        openGenerateWordlistButton = QPushButton("Generate Wordlist", main_window)
        openGenerateWordlistButton.clicked.connect(main_window.openGenerateWordlistWindow)

        generationOptionsLayout.addWidget(openGenerateReportWindowButton)
        generationOptionsLayout.addWidget(openGenerateWordlistButton)


        # Create a new QGridLayout for arranging QGroupBoxes
        groupBoxLayout = QGridLayout()

        databaseQueryGroupBox.setFixedWidth(300)
        databaseContentsGroupBox.setFixedWidth(500)
        generationOptionsGroupBox.setFixedWidth(300)
        # Add databaseQueryGroupBox to the grid layout
        groupBoxLayout.addWidget(databaseQueryGroupBox, 0, 0)
        groupBoxLayout.addWidget(databaseContentsGroupBox, 0, 1)
        groupBoxLayout.addWidget(generationOptionsGroupBox, 0, 2)



        # Link to GitHub Repo
        main_window.githubLink = QLabel(f'<a href="{versionvars.repo_link}">{versionvars.repo_link_text}</a>', main_window)
        main_window.githubLink.setOpenExternalLinks(True)

        main_window.openLogDirButton = QPushButton('Open Log Directory', main_window)
        main_window.openLogDirButton.clicked.connect(main_window.openLogDir)

        # Exit Button
        main_window.exitButton = QPushButton('Exit', main_window)
        main_window.exitButton.clicked.connect(main_window.close)

        groupBoxLayout.addWidget(main_window.githubLink, 1, 1)
        groupBoxLayout.addWidget(main_window.openLogDirButton, 1, 0)
        groupBoxLayout.addWidget(main_window.exitButton, 1, 2)

        # Add this grid layout to the main layout of the main window
        main_window.mainLayout.addLayout(groupBoxLayout)


        main_window.update()


