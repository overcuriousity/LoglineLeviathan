import os
from PyQt5.QtWidgets import (QGridLayout, QPushButton, QLabel, QHBoxLayout, QApplication,
                             QVBoxLayout, QProgressBar, 
                             QCheckBox, QListWidget, QGroupBox, QLineEdit)
from PyQt5.QtGui import  QColor, QPixmap #QPalette removed
from PyQt5.QtCore import Qt

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)







def initialize_main_window(main_window, app):
        #set_dark_mode(app)
        main_window.setWindowTitle('Logline Leviathan')
        main_window.setGeometry(800, 1000, 800, 1000)
        main_window.mainLayout = QVBoxLayout(main_window)
        main_window.db_session = None

        # Logo
        pixmap = QPixmap(os.path.join('logline_leviathan', 'gui', 'logo.png'))
        scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logoLabel = QLabel(main_window)
        logoLabel.setPixmap(scaled_pixmap)

        # Version label
        versionLabel = QLabel("LoglineLeviathan v0.1.0", main_window)  # Replace X.X.X with your actual version number
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
            min-height: 20px;
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
            min-width: 60px;
            min-height: 20px;
        }

        QPushButton:hover {
            background-color: #7EC0EE; /* Even lighter blue on hover */
        }

        QPushButton:pressed {
            background-color: #4A86E8; /* Slightly darker blue when pressed */
        }
        """

        main_window.setStyleSheet(stylesheet)

        # Update function for output format selection label with custom text and line breaks
        def update_output_format_label(current):
            if current is not None:
                format_text = current.text()
                format_descriptions = {
                    'HTML': "   HTML\n   Outputs a Single-Line Context, clearly readable HTML File.\n   Can be easily viewed on any browser.\n   Suitable for quick overviews if the analyzed data is not too large.",
                    'Interactive HTML': "   Interactive HTML\n   Generates an interactive HTML file which can be viewed in the browser.\n   Includes sorting, filtering, and search capabilities.\n   Ideal for detailed analysis, but requires JavaScript and Internet access.",
                    'XLSX': "   XLSX\n   Exports data to an Excel file.\n   Multiple sheets for different data types. Does not support Context\n   highlighting!\n   Good for comprehensive data handling and further external analysis."
                }
                main_window.outputFormatSelectionLabel.setText(format_descriptions.get(format_text, ""))


        def update_export_context_label(current):
            if current is not None:
                context_text = current.text()  # Get the text of the current item
                context_descriptions = {
                    "Single-Line Context": "   Single-Line Context\n   Generates a new line for each single line where an entity was\n   found.\n   Small context of 1 line is provided.\n",
                    "Medium Context": "   Medium Context\n   Generates a new line for each single line where an entity was\n   found.\n   A context of 5 lines is displayed.\n",
                    "Large Context": "   Large Context\n   Generates a new line for each single line where an entity was\n   found.\n   Large context of 10 lines is displayed.\n",
                    "Compact Summary, no Context": "   Compact Summary\n   Generates a summary where one line for each distinct entity\n   discovered.\n   The sources and timestamps are summarized.\n   No context is provided."
                }
                main_window.exportContextSelectionLabel.setText(context_descriptions.get(context_text, ""))


        
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

        main_window.statusLabel = QLabel('   READY TO OPERATE // START PROCESSING', main_window)
        main_window.statusLabel.setWordWrap(True)
        main_window.statusLabel.setMinimumHeight(40)
        main_window.statusLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        main_window.mainLayout.addWidget(main_window.statusLabel)

        main_window.entityRateLabel = QLabel('0 Entities/Second', main_window)
        main_window.mainLayout.addWidget(main_window.entityRateLabel)

        main_window.fileCountLabel = QLabel('   0 FILES SELECTED', main_window)
        main_window.fileCountLabel.setMinimumHeight(40)
        main_window.fileCountLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        main_window.mainLayout.addWidget(main_window.fileCountLabel)

        # Export Layout
        exportLayout = QVBoxLayout()
        
        # Create a GroupBox for the CheckboxPanel
        exportOptionsGroupBox = QGroupBox("EXPORT OPTIONS", main_window)
        #exportOptionsGroupBox.setStyleSheet("QGroupBox::title { color: white; }")  # Set title color to white
        exportOptionsLayout = QVBoxLayout(exportOptionsGroupBox)

        # Create a horizontal layout
        filterLayout = QHBoxLayout()

        # Create the "Check All" button
        checkAllButton = QPushButton("Check All", main_window)
        checkAllButton.clicked.connect(lambda: main_window.checkboxPanel.checkAllVisible())

        # Create the "Uncheck All" button
        uncheckAllButton = QPushButton("Uncheck All", main_window)
        uncheckAllButton.clicked.connect(lambda: main_window.checkboxPanel.uncheckAllVisible())

        expandAllButton = QPushButton("Expand All", main_window)
        expandAllButton.clicked.connect(lambda: main_window.checkboxPanel.expandAllTreeItems())

        collapseAllButton = QPushButton("Collapse All", main_window)
        collapseAllButton.clicked.connect(lambda: main_window.checkboxPanel.collapseAllTreeItems())

        # Add buttons to the filter layout, to the left of the filter label
        filterLayout.addWidget(checkAllButton)
        filterLayout.addWidget(uncheckAllButton)
        filterLayout.addWidget(expandAllButton)
        filterLayout.addWidget(collapseAllButton)
        
        # Create the label for the filter
        filterLabel = QLabel("Filter options:")
        filterLayout.addWidget(filterLabel)  # Add label to the horizontal layout

        # Add Text Input for Filtering
        filterLineEdit = QLineEdit(main_window)
        filterLineEdit.setPlaceholderText("   enter shortcuts, tooltips, or entity types")
        filterLineEdit.setStyleSheet("""
            QLineEdit {
                background-color: #3C4043; /* Background color */
                color: white; /* Text color */
                min-height: 20px;
            }
        """)
        filterLayout.addWidget(filterLineEdit)  # Add line edit to the horizontal layout

        exportOptionsLayout.addLayout(filterLayout)  # Add the horizontal layout to the export options layout


        # Add CheckboxPanel to the GroupBox's Layout
        exportOptionsLayout.addWidget(main_window.checkboxPanel)


        # Connect the textChanged signal of QLineEdit to a new method
        filterLineEdit.textChanged.connect(main_window.checkboxPanel.filterCheckboxes)

        # Add the Export Options GroupBox to the Export Layout
        exportLayout.addWidget(exportOptionsGroupBox)

        
        # Export Settings as a Grid Layout
        exportSettingsLayout = QGridLayout()
        item_height = 20
        visible_items = 3

        # Set a fixed width for both QListWidgets (adjust the width as needed)
        list_widget_width = 400
        outputFormatGroupBox = QGroupBox("OUTPUT FORMAT SELECTION", main_window)
        outputFormatLayout = QVBoxLayout(outputFormatGroupBox)

        main_window.outputFormatList = QListWidget()
        main_window.outputFormatList.addItems(['HTML', 'Interactive HTML', 'XLSX'])
        main_window.outputFormatList.setCurrentRow(0)
        main_window.outputFormatList.setFixedHeight(item_height * visible_items)
        outputFormatLayout.addWidget(main_window.outputFormatList)

        # Label to display current selection of output format
        main_window.outputFormatSelectionLabel = QLabel('')
        main_window.outputFormatSelectionLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        main_window.outputFormatSelectionLabel.setWordWrap(True)
        main_window.outputFormatSelectionLabel.setMinimumHeight(80)
        outputFormatLayout.addWidget(main_window.outputFormatSelectionLabel)

        exportSettingsLayout.addWidget(outputFormatGroupBox, 0, 0)

        # Export Context Group Box
        exportContextGroupBox = QGroupBox("PRESENTATION OF RESULTS", main_window)
        exportContextLayout = QVBoxLayout(exportContextGroupBox)

        main_window.exportContextList = QListWidget()
        main_window.exportContextList.addItems(['Single-Line Context', 'Medium Context', 'Large Context', 'Compact Summary, no Context'])
        main_window.exportContextList.setCurrentRow(0)
        main_window.exportContextList.setFixedHeight(item_height * visible_items)
        exportContextLayout.addWidget(main_window.exportContextList)

        # Label to display current selection of export context
        main_window.exportContextSelectionLabel = QLabel('')
        main_window.exportContextSelectionLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        main_window.exportContextSelectionLabel.setWordWrap(True)
        main_window.exportContextSelectionLabel.setMinimumHeight(80)
        exportContextLayout.addWidget(main_window.exportContextSelectionLabel)

        exportSettingsLayout.addWidget(exportContextGroupBox, 0, 1)

        # Connect signals to the update functions
        main_window.outputFormatList.currentItemChanged.connect(update_output_format_label)
        main_window.exportContextList.currentItemChanged.connect(update_export_context_label)

        # Initially update the labels
        update_output_format_label(main_window.outputFormatList.currentItem())
        update_export_context_label(main_window.exportContextList.currentItem())



        # Initially update the label
        update_output_format_label(main_window.outputFormatList.currentItem())

        # Initially update the label
        update_export_context_label(main_window.exportContextList.currentItem())


        # Add a checkbox for Crossmatches
        main_window.crossmatchesCheckbox = QCheckBox('Include Only Crossmatches (Select only one SubType for export)')
        exportSettingsLayout.addWidget(main_window.crossmatchesCheckbox, 4, 1)

        # Output File Path Label 
        main_window.outputFilePathLabel = QLabel('', main_window)
        main_window.updateOutputFilePathLabel()  # Call this method to set the initial text
        exportSettingsLayout.addWidget(main_window.outputFilePathLabel, 4, 0)


        # Start Export Button
        main_window.startExportButton = QPushButton('Start Export', main_window)
        main_window.startExportButton.clicked.connect(main_window.start_export_process)
        main_window.startExportButton.setStyleSheet(highlited_button_style)
        exportSettingsLayout.addWidget(main_window.startExportButton, 5, 1) 


        main_window.openOutputFilepathButton = QPushButton('Open Output Directory', main_window)
        main_window.openOutputFilepathButton.clicked.connect(main_window.openOutputFilepath)
        exportSettingsLayout.addWidget(main_window.openOutputFilepathButton, 5, 0)

        exportLayout.addLayout(exportSettingsLayout)
        main_window.mainLayout.addLayout(exportLayout)

        # Exit Button Layout
        bottomLayout = QHBoxLayout()
        
        # Link to GitHub Repo
        main_window.githubLink = QLabel('<a href="https://github.com/overcuriousity/LoglineLeviathan">GitHub</a>', main_window)
        main_window.githubLink.setOpenExternalLinks(True)
        bottomLayout.addWidget(main_window.githubLink)

        # Output File Directory
        main_window.selectOutputFileButton = QPushButton('Specify Output File', main_window)
        main_window.selectOutputFileButton.clicked.connect(main_window.selectOutputFile)
        bottomLayout.addWidget(main_window.selectOutputFileButton)

        # Exit Button
        main_window.exitButton = QPushButton('Exit', main_window)
        main_window.exitButton.clicked.connect(main_window.close)
        bottomLayout.addWidget(main_window.exitButton)

        main_window.mainLayout.addLayout(bottomLayout)

        main_window.setLayout(main_window.mainLayout)

        #main_window.refreshApplicationState()


        main_window.update()


