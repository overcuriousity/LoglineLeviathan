from PyQt5.QtWidgets import QVBoxLayout, QCheckBox, QHBoxLayout, QGroupBox, QPushButton, QLineEdit, QGridLayout, QLabel, QListWidget, QGridLayout
import logline_leviathan.gui.versionvars as versionvars
from logline_leviathan.gui.checkbox_panel import *



def initialize_generate_report_window(generate_report_window, app):
        generate_report_window.setWindowTitle('Logline Leviathan')
        generate_report_window.mainLayout = QVBoxLayout(generate_report_window)
        #generate_report_window.extendedLayout = QHBoxLayout(generate_report_window)
        generate_report_window.db_session = None
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
            min-width: 50px;
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

        # Update function for output format selection label with custom text and line breaks
        def update_output_format_label(current):
            if current is not None:
                format_text = current.text()
                format_descriptions = {
                    'HTML': "   HTML\n   Outputs a Single-Line Context, clearly readable HTML File.\n   Can be easily viewed on any browser.\n   Suitable for quick overviews if the analyzed data is not too large.",
                    'Interactive HTML': "   Interactive HTML\n   Generates an interactive HTML file which can be viewed in the browser.\n   Includes sorting, filtering, and search capabilities.\n   Ideal for detailed analysis, but requires JavaScript and Internet access.",
                    'XLSX': "   XLSX\n   Exports data to an Excel file.\n   Multiple sheets for different data types. Does not support Context\n   highlighting!\n   Good for comprehensive data handling and further external analysis."
                }
                generate_report_window.outputFormatSelectionLabel.setText(format_descriptions.get(format_text, ""))


        def update_export_context_label(current):
            if current is not None:
                context_text = current.text()  # Get the text of the current item
                context_descriptions = {
                    "Single-Line Context": "   Single-Line Context\n   Generates a new line for each single line where an entity was\n   found.\n   Small context of 1 line is provided.\n",
                    "Medium Context": "   Medium Context\n   Generates a new line for each single line where an entity was\n   found.\n   A context of 5 lines is displayed.\n",
                    "Large Context": "   Large Context\n   Generates a new line for each single line where an entity was\n   found.\n   Large context of 10 lines is displayed.\n",
                    "Compact Summary, no Context": "   Compact Summary\n   Generates a summary where one line for each distinct entity\n   discovered.\n   The sources and timestamps are summarized.\n   No context is provided."
                }
                generate_report_window.exportContextSelectionLabel.setText(context_descriptions.get(context_text, ""))


        generate_report_window.setStyleSheet(stylesheet)
        generate_report_window.statusLabel = QLabel('   Awaiting Selection for which Entities to include.', generate_report_window)
        generate_report_window.statusLabel.setWordWrap(True)
        generate_report_window.statusLabel.setMinimumHeight(40)
        generate_report_window.statusLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        generate_report_window.mainLayout.addWidget(generate_report_window.statusLabel)
        # Create a GroupBox for the CheckboxPanel
        exportOptionsGroupBox = QGroupBox("EXPORT OPTIONS", generate_report_window)
        exportOptionsLayout = QVBoxLayout(exportOptionsGroupBox)
        generate_report_window.checkboxPanel = CheckboxPanel()
        # Create a horizontal layout
        filterLayout = QHBoxLayout()

        # Create the "Check All" button
        checkAllButton = QPushButton("Check All", generate_report_window)
        checkAllButton.clicked.connect(lambda: generate_report_window.checkboxPanel.checkAllVisible())

        # Create the "Uncheck All" button
        uncheckAllButton = QPushButton("Uncheck All", generate_report_window)
        uncheckAllButton.clicked.connect(lambda: generate_report_window.checkboxPanel.uncheckAllVisible())

        expandAllButton = QPushButton("Expand All", generate_report_window)
        expandAllButton.clicked.connect(lambda: generate_report_window.checkboxPanel.expandAllTreeItems())

        collapseAllButton = QPushButton("Collapse All", generate_report_window)
        collapseAllButton.clicked.connect(lambda: generate_report_window.checkboxPanel.collapseAllTreeItems())

        # Add buttons to the filter layout, to the left of the filter label
        filterLayout.addWidget(checkAllButton)
        filterLayout.addWidget(uncheckAllButton)
        filterLayout.addWidget(expandAllButton)
        filterLayout.addWidget(collapseAllButton)
        
        # Create the label for the filter
        filterLabel = QLabel("Filter options:")
        filterLayout.addWidget(filterLabel)  # Add label to the horizontal layout

        # Add Text Input for Filtering
        filterLineEdit = QLineEdit(generate_report_window)
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
        exportOptionsLayout.addWidget(generate_report_window.checkboxPanel)


        # Connect the textChanged signal of QLineEdit to a new method
        filterLineEdit.textChanged.connect(generate_report_window.checkboxPanel.filterCheckboxes)

    # First Horizontal Layout for Database Query and Export Options
        topHBoxLayout = QHBoxLayout()
        topHBoxLayout.addWidget(exportOptionsGroupBox)
        generate_report_window.mainLayout.addLayout(topHBoxLayout)
                # Export Settings as a Grid Layout
        exportSettingsLayout = QGridLayout()
        item_height = 20
        visible_items = 3

        # Set a fixed width for both QListWidgets (adjust the width as needed)
        outputFormatGroupBox = QGroupBox("OUTPUT FORMAT SELECTION", generate_report_window)
        outputFormatGroupBox.setFixedHeight(200)
        outputFormatLayout = QVBoxLayout(outputFormatGroupBox)

        generate_report_window.outputFormatList = QListWidget()
        generate_report_window.outputFormatList.addItems(['HTML', 'Interactive HTML', 'XLSX'])
        generate_report_window.outputFormatList.setCurrentRow(0)
        generate_report_window.outputFormatList.setFixedHeight(item_height * visible_items)
        outputFormatLayout.addWidget(generate_report_window.outputFormatList)

        # Label to display current selection of output format
        generate_report_window.outputFormatSelectionLabel = QLabel('')
        generate_report_window.outputFormatSelectionLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        generate_report_window.outputFormatSelectionLabel.setWordWrap(True)
        generate_report_window.outputFormatSelectionLabel.setFixedHeight(80)
        outputFormatLayout.addWidget(generate_report_window.outputFormatSelectionLabel)

        exportSettingsLayout.addWidget(outputFormatGroupBox, 0, 0)

        # Export Context Group Box
        exportContextGroupBox = QGroupBox("PRESENTATION OF RESULTS", generate_report_window)
        exportContextGroupBox.setFixedHeight(200)
        exportContextLayout = QVBoxLayout(exportContextGroupBox)

        generate_report_window.exportContextList = QListWidget()
        generate_report_window.exportContextList.addItems(['Single-Line Context', 'Medium Context', 'Large Context', 'Compact Summary, no Context'])
        generate_report_window.exportContextList.setCurrentRow(0)
        generate_report_window.exportContextList.setFixedHeight(item_height * visible_items)
        exportContextLayout.addWidget(generate_report_window.exportContextList)

        # Label to display current selection of export context
        generate_report_window.exportContextSelectionLabel = QLabel('')
        generate_report_window.exportContextSelectionLabel.setStyleSheet("QLabel { background-color: #3C4043; color: white; }")
        generate_report_window.exportContextSelectionLabel.setWordWrap(True)
        generate_report_window.exportContextSelectionLabel.setFixedHeight(80)
        exportContextLayout.addWidget(generate_report_window.exportContextSelectionLabel)

        exportSettingsLayout.addWidget(exportContextGroupBox, 0, 1)

        # Connect signals to the update functions
        generate_report_window.outputFormatList.currentItemChanged.connect(update_output_format_label)
        generate_report_window.exportContextList.currentItemChanged.connect(update_export_context_label)

        # Initially update the labels
        update_output_format_label(generate_report_window.outputFormatList.currentItem())
        update_export_context_label(generate_report_window.exportContextList.currentItem())



        # Initially update the label
        update_output_format_label(generate_report_window.outputFormatList.currentItem())

        # Initially update the label
        update_export_context_label(generate_report_window.exportContextList.currentItem())


        # Add a checkbox for Crossmatches
        generate_report_window.crossmatchesCheckbox = QCheckBox('Include Only Crossmatches (Entities, which show up in multiple analyzed files)', generate_report_window)
        exportSettingsLayout.addWidget(generate_report_window.crossmatchesCheckbox, 4, 1)

        # Output File Path Label 
        generate_report_window.outputFilePathLabel = QLabel('', generate_report_window)
        generate_report_window.updateOutputFilePathLabel()  # Call this method to set the initial text
        exportSettingsLayout.addWidget(generate_report_window.outputFilePathLabel, 4, 0)

        #exportLayout.addLayout(exportSettingsLayout)
        generate_report_window.mainLayout.addLayout(exportSettingsLayout)

        # Exit Button Layout
        bottomLayout = QGridLayout()

        generate_report_window.customizeResultsButton = QPushButton('Customize Results (WiP)', generate_report_window)
        generate_report_window.customizeResultsButton.setDisabled(True)
        generate_report_window.customizeResultsButton.clicked.connect(generate_report_window.openCustomizeResultsDialog)
        bottomLayout.addWidget(generate_report_window.customizeResultsButton, 0, 0)

        generate_report_window.openOutputFilepathButton = QPushButton('Open Output Directory', generate_report_window)
        generate_report_window.openOutputFilepathButton.clicked.connect(generate_report_window.openOutputFilepath)
        bottomLayout.addWidget(generate_report_window.openOutputFilepathButton, 0, 1)

        # Start Export Button
        generate_report_window.startExportButton = QPushButton('Start Export', generate_report_window)
        generate_report_window.startExportButton.clicked.connect(generate_report_window.start_export_process)
        generate_report_window.startExportButton.setStyleSheet(highlited_button_style)
        bottomLayout.addWidget(generate_report_window.startExportButton, 0, 2) 
        
        # Link to GitHub Repo
        generate_report_window.githubLink = QLabel(f'<a href="{versionvars.repo_link}">{versionvars.repo_link_text}</a>', generate_report_window)
        generate_report_window.githubLink.setOpenExternalLinks(True)
        bottomLayout.addWidget(generate_report_window.githubLink, 1, 0)

        # Output File Directory
        generate_report_window.selectOutputFileButton = QPushButton('Specify Output File', generate_report_window)
        generate_report_window.selectOutputFileButton.clicked.connect(generate_report_window.selectOutputFile)
        bottomLayout.addWidget(generate_report_window.selectOutputFileButton, 1, 1)

        # Exit Button
        generate_report_window.exitButton = QPushButton('Exit', generate_report_window)
        generate_report_window.exitButton.clicked.connect(generate_report_window.close)
        bottomLayout.addWidget(generate_report_window.exitButton, 1, 2)

        generate_report_window.mainLayout.addLayout(bottomLayout)

        #Easteregg
        #generate_report_window.extendedLayout.addLayout(generate_report_window.mainLayout)
        #generate_report_window.terminalEasterEgg = TerminalEasterEgg(generate_report_window)
        #generate_report_window.terminalEasterEgg.hide()
        #logoLabel.clicked.connect(generate_report_window.terminalEasterEgg.show)


        generate_report_window.setLayout(generate_report_window.mainLayout)