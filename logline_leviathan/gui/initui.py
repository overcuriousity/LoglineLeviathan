import os
from PyQt5.QtWidgets import (QGridLayout, QPushButton, QLabel, QHBoxLayout, QApplication,
                             QVBoxLayout, QProgressBar, 
                             QCheckBox, QListWidget, QGroupBox, QLineEdit)
from PyQt5.QtGui import QPalette, QColor, QPixmap
from PyQt5.QtCore import Qt

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)




def set_dark_mode(app):
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(63, 63, 73))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.black)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    button_style = "QPushButton { background-color: #353535; color: white; }"
    app.setStyleSheet(button_style)

def initialize_main_window(main_window, app):
        set_dark_mode(app)
        main_window.setWindowTitle('Logline Leviathan')
        main_window.setGeometry(800, 1000, 800, 1000)
        main_window.mainLayout = QVBoxLayout(main_window)
        main_window.db_session = None

        # Logo
        pixmap = QPixmap(os.path.join('logline_leviathan', 'gui', 'logo.png'))
        scaled_pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logoLabel = QLabel(main_window)
        #pixmap = QPixmap(os.path.join('logline_leviathan', 'gui', 'logo.png'))
        #logoLabel.setPixmap(pixmap.scaled(400, 1000, Qt.KeepAspectRatio))
        logoLabel.setPixmap(scaled_pixmap)
        main_window.mainLayout.addWidget(logoLabel, alignment=Qt.AlignTop | Qt.AlignRight)


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
        main_window.dataIngestionLabel = QLabel('   1. Start with adding the Files to import or specify a database.\n   2. Start File Analysis and populate Database.\n   3. Specify Export Options and Output Format, then Start Export.')
        main_window.dataIngestionLabel.setWordWrap(True)
        main_window.dataIngestionLabel.setMinimumHeight(60)
        main_window.dataIngestionLabel.setStyleSheet("QLabel { background-color: #333343; color: white; }")
        main_window.mainLayout.addWidget(main_window.dataIngestionLabel)


        # Grid Layout for Top Buttons
        topButtonGridLayout = QGridLayout()

        # Create Buttons
        main_window.openButton = QPushButton('Add Files to Selection', main_window)
        main_window.openButton.clicked.connect(main_window.openFileNameDialog)

        main_window.addDirButton = QPushButton('Add Directory and Subdirectories', main_window)
        main_window.addDirButton.clicked.connect(main_window.openDirNameDialog)

        main_window.clearSelectionButton = QPushButton('Clear all Files from Selection', main_window)
        main_window.clearSelectionButton.clicked.connect(lambda: main_window.clearFileSelection())

        main_window.createDbButton = QPushButton('Delete & Create Fresh Database', main_window)
        main_window.createDbButton.clicked.connect(main_window.purgeDatabase)

        main_window.importDbButton = QPushButton('Select existing Database', main_window)
        main_window.importDbButton.clicked.connect(main_window.importDatabase)

        main_window.exportDBButton = QPushButton('Export existing Database', main_window)
        main_window.exportDBButton.clicked.connect(main_window.exportDatabase)

        main_window.inspectRegexButton = QPushButton('Inspect Regex Library (Restart if changed)', main_window)
        main_window.inspectRegexButton.clicked.connect(main_window.openRegexLibrary)

        main_window.processButton = QPushButton('Start/Resume File Analysis', main_window)
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
        main_window.statusLabel.setStyleSheet("QLabel { background-color: #333343; color: white; }")
        main_window.mainLayout.addWidget(main_window.statusLabel)

        main_window.entityRateLabel = QLabel('0 Entities/Second', main_window)
        main_window.mainLayout.addWidget(main_window.entityRateLabel)

        main_window.fileCountLabel = QLabel('   0 FILES SELECTED', main_window)
        main_window.fileCountLabel.setMinimumHeight(40)
        main_window.fileCountLabel.setStyleSheet("QLabel { background-color: #333343; color: white; }")
        main_window.mainLayout.addWidget(main_window.fileCountLabel)

        # Export Layout
        exportLayout = QVBoxLayout()
        
        # Create a GroupBox for the CheckboxPanel
        exportOptionsGroupBox = QGroupBox("EXPORT OPTIONS", main_window)
        exportOptionsGroupBox.setStyleSheet("QGroupBox::title { color: white; }")  # Set title color to white
        exportOptionsLayout = QVBoxLayout(exportOptionsGroupBox)

        # Create a horizontal layout
        filterLayout = QHBoxLayout()

        # Create the label for the filter
        filterLabel = QLabel("Filter by checkboxes or shortcuts (ex. IPv4 Address or ipv4pu):")
        filterLayout.addWidget(filterLabel)  # Add label to the horizontal layout

        # Add Text Input for Filtering
        filterLineEdit = QLineEdit(main_window)
        filterLineEdit.setPlaceholderText("Filter checkboxes...")
        filterLineEdit.setStyleSheet("""
            QLineEdit {
                background-color: #232323; /* Background color */
                color: white; /* Text color */
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

        # Output Format
        outputFormatLabel = QLabel('OUTPUT FORMAT SELECTION')
        exportSettingsLayout.addWidget(outputFormatLabel, 0, 0)

        main_window.outputFormatList = QListWidget()
        main_window.outputFormatList.addItems(['HTML', 'Interactive HTML', 'XLSX'])
        main_window.outputFormatList.setCurrentRow(0)
        exportSettingsLayout.addWidget(main_window.outputFormatList, 1, 0)
        

        # Label to display current selection of output format
        main_window.outputFormatSelectionLabel = QLabel('')
        main_window.outputFormatSelectionLabel.setStyleSheet("QLabel { background-color: #333343; color: white; }")
        exportSettingsLayout.addWidget(main_window.outputFormatSelectionLabel, 2, 0)

        # Setup the output format and export context labels to accommodate multiline text
        main_window.outputFormatSelectionLabel.setWordWrap(True)
        main_window.outputFormatSelectionLabel.setMinimumHeight(80)  # Adjust height as needed for 3 lines

        # Export Context
        exportContextLabel = QLabel('PRESENTATION OF RESULTS:')
        exportSettingsLayout.addWidget(exportContextLabel, 0, 1)

        main_window.exportContextList = QListWidget()
        main_window.exportContextList.addItems(['Single-Line Context', 'Medium Context', 'Large Context', 'Compact Summary, no Context'])
        main_window.exportContextList.setCurrentRow(0)
        exportSettingsLayout.addWidget(main_window.exportContextList, 1, 1)
        

        # Label to display current selection of export context
        main_window.exportContextSelectionLabel = QLabel('')
        main_window.exportContextSelectionLabel.setStyleSheet("QLabel { background-color: #333343; color: white; }")
        exportSettingsLayout.addWidget(main_window.exportContextSelectionLabel, 2, 1)


        main_window.exportContextSelectionLabel.setWordWrap(True)
        main_window.exportContextSelectionLabel.setMinimumHeight(80)  # Adjust height as needed for 3 lines

        item_height = 20
        visible_items = 5
        stylesheet = """
        QListWidget::item:selected {
            background-color: #555555 !important; /* Adjust the color to your preference */
            color: white !important; /* Adjust the text color for better visibility if needed */
        }
        QListWidget::item:hover {
            background-color: #777777 !important; /* Optional: Different color for hover state */
        }
        """

        main_window.outputFormatList.setFixedHeight(item_height * visible_items)
        main_window.exportContextList.setFixedHeight(item_height * visible_items)
 
        main_window.outputFormatList.setStyleSheet(stylesheet)
        main_window.exportContextList.setStyleSheet(stylesheet)

                

        # Connect signal to the update function
        main_window.outputFormatList.currentItemChanged.connect(update_output_format_label)

        # Connect signal to the update function
        main_window.exportContextList.currentItemChanged.connect(update_export_context_label)

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
        exportSettingsLayout.addWidget(main_window.startExportButton, 5, 1) 


        main_window.openOutputFilepathButton = QPushButton('Open Output Directory', main_window)
        main_window.openOutputFilepathButton.clicked.connect(main_window.openOutputFilepath)
        exportSettingsLayout.addWidget(main_window.openOutputFilepathButton, 5, 0)

        exportLayout.addLayout(exportSettingsLayout)
        main_window.mainLayout.addLayout(exportLayout)

        # Exit Button Layout
        bottomLayout = QHBoxLayout()
        
        # Link to GitHub Repo
        main_window.githubLink = QLabel('<a href="https://c.mikoshi.de/apps/forms/s/JEioiy6WBpRTKJsDLEeRqN2E">Feedback-Link</a>', main_window)
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


