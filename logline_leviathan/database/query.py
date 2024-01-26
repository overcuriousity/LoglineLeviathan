from sqlalchemy import or_, and_, not_, String
from PyQt5.QtWidgets import QProgressBar, QMainWindow, QTableWidget, QTableWidgetItem, QLineEdit, QStyledItemDelegate, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QStyle, QLabel
from logline_leviathan.database.database_manager import get_db_session, EntitiesTable, DistinctEntitiesTable, EntityTypesTable, ContextTable, FileMetadata, session_scope
from PyQt5.QtCore import pyqtSignal, Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextDocument, QTextOption
from fuzzywuzzy import fuzz
import re
import logging


class QueryThread(QThread):
    queryCompleted = pyqtSignal(list, list)  # Signal to indicate completion

    def __init__(self, db_query_instance, query_text):
        super(QueryThread, self).__init__()
        self.db_query_instance = db_query_instance
        self.query_text = query_text

    def run(self):
        base_query, search_terms = self.db_query_instance.prepare_query(self.query_text)
        query_lambda = self.db_query_instance.parse_query(self.query_text)
        
        # Pass the lambda function directly to filter
        results = base_query.filter(query_lambda).all()

        # Calculate scored results
        scored_results = [(result, self.db_query_instance.calculate_match_score(result, search_terms)) for result in results]
        self.queryCompleted.emit(scored_results, search_terms)

class DatabaseGUIQuery:
    def __init__(self):
        self.db_session = get_db_session()
        self.entity_types = EntityTypesTable
        self.entities = EntitiesTable
        self.distinct_entities = DistinctEntitiesTable
        self.context = ContextTable
        self.file_metadata = FileMetadata

    def parse_query(self, query):
        if not query.strip():
            return lambda _: False

        tokens = query.split()

        filters = []
        for token in tokens:
            is_exclude = token.startswith('-')
            is_include = token.startswith('+')
            token = token.lstrip('+-')  # Remove + or - if present

            if token.startswith('"') and token.endswith('"'):
                # Exact match without wildcards
                search_condition = token[1:-1]
            else:
                # Apply wildcard search by default
                search_condition = f'%{token.replace("*", "%")}%'

            condition = or_(
                self.distinct_entities.distinct_entity.like(search_condition),
                self.entity_types.entity_type.like(search_condition),
                self.entity_types.gui_name.like(search_condition),
                self.entity_types.gui_tooltip.like(search_condition),
                self.entity_types.script_parser.like(search_condition),
                self.file_metadata.file_name.like(search_condition),
                self.file_metadata.file_path.like(search_condition),
                self.file_metadata.file_mimetype.like(search_condition),
                self.entities.line_number.cast(String).like(search_condition),
                self.context.context_large.like(search_condition)
                # Add other fields as needed
                )
            if is_exclude:
                filters.append(not_(condition))
            elif is_include:
                filters.append(and_(condition))
            else:
                filters.append(condition)

        return lambda: or_(*filters)

    def parse_search_terms(self, query):
        tokens = query.split()
        search_terms = [token.lstrip('+-') for token in tokens if not token.startswith('-') and not token.startswith('+')]
        return search_terms

    def prepare_query(self, query):
        search_terms = self.parse_search_terms(query)

        # Construct the base query with proper joins
        base_query = self.db_session.query(
            self.distinct_entities.distinct_entity, 
            self.entity_types.gui_name,
            self.file_metadata.file_name, 
            self.entities.line_number, 
            self.entities.entry_timestamp, 
            self.context.context_large
        ).join(
            self.entities, self.distinct_entities.distinct_entities_id == self.entities.distinct_entities_id
        ).join(
            self.file_metadata, self.entities.file_id == self.file_metadata.file_id
        ).join(
            self.context, self.entities.entities_id == self.context.entities_id
        ).join(
            self.entity_types, self.entities.entity_types_id == self.entity_types.entity_type_id
        ).distinct()

        # Apply filters and return results
        return base_query, search_terms


    def display_results(self, results, search_terms):
        self.results_window = ResultsWindow(results, search_terms)
        self.results_window.show()


    def calculate_match_score(self, result, search_terms):
        # Adjusted weights and thresholds
        distinct_entity_weight = 6
        file_name_weight = 5
        timestamp_weight = 2
        line_number_weight = 1
        context_weight = 3
        multiple_term_weight = 2
        order_weight = 4
        fuzzy_match_weight = 0.5  # Reduced for less inclusiveness
        threshold_for_fuzzy = 85   # Increased threshold

        score = 0

        # Normalize search terms
        normalized_terms = [term.lower() for term in search_terms]

        # Check matches in various fields
        for term in normalized_terms:
            lower_distinct_entity = result.distinct_entity.lower()
            lower_file_name = result.file_name.lower()
            timestamp_str = str(result.entry_timestamp).lower()
            line_number_str = str(result.line_number).lower()

            if term in lower_distinct_entity:
                score += distinct_entity_weight
            if term in lower_file_name:
                score += file_name_weight
            if term in timestamp_str:
                score += timestamp_weight
            if term in line_number_str:
                score += line_number_weight

        # Context field handling
        words_in_context = result.context_large.lower().split()
        found_terms = set()
        for term in normalized_terms:
            if term in words_in_context:
                found_terms.add(term)
                score += context_weight

        # Additional weight for multiple different terms
        score += len(found_terms) * multiple_term_weight

        # Check for order of terms
        if ' '.join(normalized_terms) in ' '.join(words_in_context):
            score += order_weight

        # Fuzzy matching
        all_text = f"{result.distinct_entity} {result.file_name} {result.entry_timestamp} {result.line_number} {result.context_large}".lower()
        for term in normalized_terms:
            fuzzy_score = max(fuzz.partial_ratio(term, word) for word in all_text.split())
            if fuzzy_score > threshold_for_fuzzy:
                score += (fuzzy_score / 100) * fuzzy_match_weight

        return score

    
    def get_entity_types(self):
        with session_scope() as session:
            # Query to filter entity types that have either regex_pattern or script_parser
            return [entity_type.gui_name for entity_type in session.query(EntityTypesTable)
                    .filter(or_(EntityTypesTable.regex_pattern.isnot(None), 
                                EntityTypesTable.script_parser.isnot(None)))
                    .all()]




COLUMN_WIDTHS = [200, 100, 250, 100, 120, 600, 80]  # Adjust these values as needed
COLUMN_NAMES = ['Distinct Entity', 'Entity Type', 'File Name', 'Line Number', 'Timestamp', 'Context', 'Match Score']
DEFAULT_ROW_HEIGHT = 120
FILTER_EDIT_WIDTH = 150

class ResultsWindow(QMainWindow):
    def __init__(self, db_query_instance, parent=None):
        super(ResultsWindow, self).__init__(parent)
        self.db_query_instance = db_query_instance
        self.loaded_data_count = 0
        self.total_data = []
        self.current_filters = {}
        self.setWindowTitle("Search Results")
        self.setGeometry(800, 600, 1500, 600)  # Adjust size as needed

        # Create central widget and set layout
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)

        queryFieldLayout = QHBoxLayout()

        self.databaseQueryLineEdit = QueryLineEdit(self)
        self.databaseQueryLineEdit.setPlaceholderText("   Enter query...")
        self.databaseQueryLineEdit.returnPressed.connect(self.execute_query_from_results_window)
        self.databaseQueryLineEdit.setStyleSheet("""
            QLineEdit {
                background-color: #3C4043;
                color: white;
                min-height: 20px;           
            }
        """)
        queryFieldLayout.addWidget(self.databaseQueryLineEdit)
        # Create a progress bar for query in progress
        self.queryProgressBar = QProgressBar(self)
        self.queryProgressBar.setRange(0, 1)  # Indeterminate mode
        self.queryProgressBar.setFixedWidth(100)  # Initially hidden
        queryFieldLayout.addWidget(self.queryProgressBar)
        executeQueryButton = QPushButton("Execute Query", self)
        executeQueryButton.clicked.connect(self.execute_query_from_results_window)
        queryFieldLayout.addWidget(executeQueryButton)

        mainLayout.addLayout(queryFieldLayout)

        # Create a horizontal layout for filter options
        filterLayout = QHBoxLayout()
        mainLayout.addLayout(filterLayout)

        # Add the table widget to the main layout
        self.tableWidget = QTableWidget()
        mainLayout.addWidget(self.tableWidget)

        # Updated stylesheet for the entire ResultsWindow
        stylesheet = """
        /* Styles for QTableWidget and headers */
        QTableWidget, QHeaderView::section {
            background-color: #2A2F35;
            color: white;
            border: 1px solid #4A4A4A;
        }

        /* Style for QLineEdit */
        QLineEdit {
            background-color: #3A3F44;
            color: white;
            border: 1px solid #4A4A4A;
        }

        /* Style for QPushButton */
        QPushButton {
            background-color: #4B5563;
            color: white;
            border-radius: 4px;
            padding: 5px;
            margin: 5px;
        }

        QPushButton:hover {
            background-color: #5C677D;
        }

        QPushButton:pressed {
            background-color: #2A2F35;
        }

        /* Style for empty rows and other areas */
        QWidget {
            background-color: #2A2F35;
            color: white;
        }
        """
        self.setStyleSheet(stylesheet)


        # Apply default row height after setting up the table
        self.tableWidget.verticalHeader().setDefaultSectionSize(DEFAULT_ROW_HEIGHT)
        
        self.clearAllButton = QPushButton("Clear All Filters", self)
        self.clearAllButton.clicked.connect(self.clear_all_filters)
        filterLayout.addWidget(self.clearAllButton)
        # Adding filter options after table setup
        self.entityTypeComboBox = QComboBox()
        filterLayout.addWidget(self.entityTypeComboBox)

        # Initialize filterWidgets before calling setup_table
        self.filterWidgets = []

        # Create and add QLineEdit widgets to the filter layout
        for i, column_name in enumerate(COLUMN_NAMES):
            # Skipping the filter creation for certain columns
            if column_name in ['Entity Type', 'Context']:
                continue

            filter_edit = QLineEdit(self)
            filter_edit.setFixedWidth(FILTER_EDIT_WIDTH)
            filter_edit.setPlaceholderText(f"Filter by {column_name}")
            filter_edit.textChanged.connect(lambda text, col=i: self.apply_filter(text, col))

            self.filterWidgets.append(filter_edit)
            filterLayout.addWidget(filter_edit)
        self.dataLoadTimer = QTimer(self)
        self.dataLoadTimer.timeout.connect(self.load_more_data)
        
        # Create and add the Dismiss button
        self.dismissButton = QPushButton("Dismiss", self)
        self.dismissButton.clicked.connect(self.dataLoadTimer.stop)
        self.dismissButton.clicked.connect(self.close)
        mainLayout.addWidget(self.dismissButton)

        self.populate_entity_type_combobox()

        # Adjust column widths and filter widgets' widths
        self.adjust_column_widths()

        #self.tableWidget.verticalScrollBar().valueChanged.connect(self.check_scroll)


    def populate_entity_type_combobox(self):
        entity_types = DatabaseGUIQuery().get_entity_types()
        self.entityTypeComboBox.addItem("All Entity Types", None)  # Default option
        for entity_type in entity_types:
            self.entityTypeComboBox.addItem(entity_type, entity_type)
        self.entityTypeComboBox.currentIndexChanged.connect(self.filter_by_entity_type)

    def clear_table(self):
        self.tableWidget.clear()  
        self.tableWidget.setRowCount(0)  
        self.tableWidget.setColumnCount(0)  

    def adjust_column_widths(self):
        for column, width in enumerate(COLUMN_WIDTHS):
            self.tableWidget.setColumnWidth(column, width)


    def execute_query_from_results_window(self):
        self.dataLoadTimer.start(2000) 
        query_text = self.databaseQueryLineEdit.text()
        if not query_text:
            return
        self.clear_table()
        self.queryProgressBar.setRange(0, 0)
        self.query_thread = QueryThread(self.db_query_instance, query_text)
        self.query_thread.queryCompleted.connect(self.on_query_completed)
        self.query_thread.start()

    def set_query_and_execute(self, query_text):
        self.databaseQueryLineEdit.setText(query_text)
        self.execute_query_from_results_window()


    def on_query_completed(self, results, search_terms):
        logging.debug(f"Query completed with {len(results)} results")  # Debug statementself.queryProgressBar.setRange(0, 1)
        self.total_data = results
        self.search_terms = search_terms
        self.loaded_data_count = 0
        self.setup_table(search_terms)
        self.apply_all_filters()


    def setup_table(self, search_terms=[]):
        # Set up the table columns and headers
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels(['Distinct Entity', 'Entity Type', 'File Name', 'Line Number', 'Timestamp', 'Context', 'Match Score'])
        highlight_delegate = HighlightDelegate(self, search_terms)
        self.tableWidget.setItemDelegateForColumn(0, highlight_delegate)
        self.tableWidget.setItemDelegateForColumn(1, highlight_delegate)
        self.tableWidget.setItemDelegateForColumn(3, highlight_delegate)
        # Apply column widths
        self.adjust_column_widths()
        # Disable sorting when initially populating data
        self.tableWidget.setSortingEnabled(False)
        # Load initial subset of data
        self.load_more_data()
        # Enable sorting by 'Match Score' after data is populated
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.sortItems(6, Qt.DescendingOrder)

    def add_table_row(self, row_index, result, score):
        self.tableWidget.insertRow(row_index)
        # Distinct Entity with highlighting
        distinct_entity_item = QTableWidgetItem(str(result[0]))
        self.tableWidget.setItem(row_index, 0, distinct_entity_item)
        # Entity Type
        entity_type_item = QTableWidgetItem(str(result[1]))
        self.tableWidget.setItem(row_index, 1, entity_type_item)
        # File Name - using CellWidget
        file_name_widget = CellWidget(str(result[2]), self.filterWidgets[1], self.search_terms)
        self.tableWidget.setCellWidget(row_index, 2, file_name_widget)
        # Line Number
        line_number_item = QTableWidgetItem(str(result[3]))
        self.tableWidget.setItem(row_index, 3, line_number_item)
        # Timestamp - using CellWidget
        timestamp_widget = CellWidget(str(result[4]), self.filterWidgets[3], self.search_terms)
        self.tableWidget.setCellWidget(row_index, 4, timestamp_widget)
        # Context - using ScrollableTextWidget
        scrollable_widget = ScrollableTextWidget(result[5], self.search_terms, str(result[0]))
        self.tableWidget.setCellWidget(row_index, 5, scrollable_widget)
        # Match Score
        match_score_item = NumericTableWidgetItem("{:.2f}".format(float(score)))
        self.tableWidget.setItem(row_index, 6, match_score_item)
        # Apply highlight delegate if needed
        highlight_delegate = HighlightDelegate(self, self.search_terms)
        self.tableWidget.setItemDelegateForRow(row_index, highlight_delegate)
        # Restore sorting, if it was enabled
        self.tableWidget.setSortingEnabled(True)

    def load_more_data(self):
        #logging.debug(f"Current Filters: {self.current_filters}")
        # Adjust logic to check for new data instead of relying on loaded_data_count
        if not self.is_new_data_available():
            return  # No new data available, just return

        start_index = self.loaded_data_count
        chunk_size = 50  # Adjust this number based on performance
        end_index = min(start_index + chunk_size, len(self.total_data))

        # Sort the chunk by match score in descending order
        sorted_chunk = sorted(self.total_data[start_index:end_index], key=lambda x: x[1], reverse=True)

        for index, row_data in enumerate(sorted_chunk):
            row_index = start_index + index
            if self.matches_current_filters(row_index, row_data):
                self.insert_row_in_sorted_order(row_data)

        # Reapply filters after loading new data
        self.apply_all_filters()
        # Update loaded_data_count or other mechanism to keep track of processed data
        self.update_data_tracking(end_index)

        self.tableWidget.update()  # Refresh the table

    def is_new_data_available(self):
        return self.loaded_data_count < len(self.total_data)


    def update_data_tracking(self, end_index):
        # Update loaded_data_count or implement other mechanism to keep track of processed data
        self.loaded_data_count = end_index

    def insert_row_in_sorted_order(self, row_data):
        row_index = 0
        score = row_data[1]
        # Find the correct position based on match score
        while row_index < self.tableWidget.rowCount():
            current_score_item = self.tableWidget.item(row_index, 6)  # Assuming column 6 is Match Score
            current_score = float(current_score_item.text()) if current_score_item else 0
            if score > current_score:
                break
            row_index += 1

        self.add_table_row(row_index, row_data[0], score)


    def matches_current_filters(self, row_index, row_data):
        for column, filter_text in self.current_filters.items():
            if not self.is_match(row_index, column, filter_text, row_data):
                return False
        return True

    def is_match(self, row_index, column, filter_text, row_data):
        # Extract text from the cell or widget
        widget = self.tableWidget.cellWidget(row_index, column)
        if isinstance(widget, CellWidget):
            # CellWidget contains a QLabel with HTML-formatted text
            document = QTextDocument()
            document.setHtml(widget.label.text())
            text = document.toPlainText()
        elif isinstance(widget, ScrollableTextWidget):
            # ScrollableTextWidget contains a QTextEdit with HTML-formatted text
            text = widget.text_edit.toPlainText()
        else:
            # Standard QTableWidgetItem
            item = self.tableWidget.item(row_index, column)
            text = item.text() if item else ""

        # Compare the extracted plain text with the filter text
        return filter_text.lower() in text.lower()


    def apply_filter(self, text, column):
        self.current_filters[column] = text.lower()
        self.apply_all_filters()


    def extract_row_data(self, row_index):
        # Construct row_data from the table content
        row_data = []
        for column in range(self.tableWidget.columnCount()):
            cell_data = self.get_cell_data(row_index, column)
            row_data.append(cell_data)
        return row_data

    def get_cell_data(self, row_index, column):
        widget = self.tableWidget.cellWidget(row_index, column)
        if isinstance(widget, CellWidget):
            document = QTextDocument()
            document.setHtml(widget.label.text())
            return document.toPlainText()
        elif isinstance(widget, ScrollableTextWidget):
            return widget.text_edit.toPlainText()
        else:
            item = self.tableWidget.item(row_index, column)
            return item.text() if item else ""

    def apply_all_filters(self):
        for row_index in range(self.tableWidget.rowCount()):
            row_data = self.extract_row_data(row_index)
            if self.matches_current_filters(row_index, row_data):
                self.tableWidget.showRow(row_index)
            else:
                self.tableWidget.hideRow(row_index)


    def filter_by_entity_type(self):
        selected_type = self.entityTypeComboBox.currentData()
        #logging.debug(f"Filtering by entity type: {selected_type}")

        # Update the current filters dictionary
        entity_type_column = COLUMN_NAMES.index('Entity Type')  # Assuming 'Entity Type' is one of the column names
        if selected_type is None:
            # Clear the filter for entity type if 'All Entity Types' is selected
            if entity_type_column in self.current_filters:
                del self.current_filters[entity_type_column]
        else:
            # Set the filter for entity type
            self.current_filters[entity_type_column] = selected_type.lower()

        # Reapply all filters including the entity type filter
        self.apply_all_filters()


    def on_filter_change(self):
        # Reapply all filters
        self.apply_all_filters()

    def clear_all_filters(self):
        for filter_widget in self.filterWidgets:
            filter_widget.clear()

        self.current_filters.clear()  # Clear all filters
        #logging.debug("All filters cleared")

        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.showRow(row)  # Show all rows

        # Optionally reapply entity type filter if it should be independent
        self.filter_by_entity_type()

    @staticmethod
    def strip_html_tags(text):
        return re.sub('<[^<]+?>', '', text)




class QueryLineEdit(QLineEdit):
    returnPressed = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.returnPressed.emit()
        else:
            super().keyPressEvent(event)


class HighlightDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, search_terms=None):
        super().__init__(parent)
        self.search_terms = search_terms or []

    def paint(self, painter, option, index):
        painter.save()

        # Set text color and other options
        options = QTextOption()
        options.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        document = QTextDocument()
        document.setDefaultTextOption(options)
        document.setDefaultFont(option.font)

        # Prepare highlighted text
        text = index.model().data(index)
        highlighted_text = self.get_highlighted_text(text)
        document.setHtml(highlighted_text)

        # Set the width of the document to the cell width
        document.setTextWidth(option.rect.width())

        # Draw the contents
        painter.translate(option.rect.topLeft())
        document.drawContents(painter)
        painter.restore()

    def get_highlighted_text(self, text):
        if text is None:
            text = ""

        # Rest of the method remains the same
        text_with_color = f"<span style='color: white;'>{text}</span>"
        for term in self.search_terms:
            if term.lower() in text.lower():
                highlighted_term = f"<span style='background-color: yellow; color: black;'>{term}</span>"
                text_with_color = text_with_color.replace(term, highlighted_term)

        return text_with_color.replace("\n", "<br>")

    
class ScrollableTextWidget(QWidget):
    def __init__(self, text, search_terms, distinct_entity, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.text_edit = CustomTextEdit(self)
        self.text_edit.setReadOnly(True)

        # Apply styles including scrollbar styles
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2A2F35; /* Dark blue-ish background */
                color: white; /* White text */
            }
            QTextEdit QScrollBar:vertical {
                border: none;
                background-color: #3A3F44; /* Dark scrollbar background */
                width: 8px; /* Width of the scrollbar */
            }
            QTextEdit QScrollBar::handle:vertical {
                background-color: #6E6E6E; /* Scroll handle color */
                border-radius: 4px; /* Rounded corners for the handle */
            }
            QTextEdit QScrollBar::add-line:vertical, QTextEdit QScrollBar::sub-line:vertical {
                background: none;
            }
        """)

        # Set the text with highlighting
        self.set_highlighted_text(text, search_terms, distinct_entity)
        layout.addWidget(self.text_edit)

        # Scroll to the distinct entity
        self.scroll_to_text(distinct_entity)

    def set_highlighted_text(self, text, search_terms, distinct_entity):
        if text is None:
            text = ""

        # Convert text to lowercase for case-insensitive comparison
        lower_text = text.lower()

        # Apply highlighting
        for term in search_terms:
            lower_term = term.lower()
            if lower_term in lower_text:
                highlighted_term = f"<span style='background-color: yellow; color: black;'>{term}</span>"
                # Replace all occurrences of the term (case-insensitive)
                text = re.sub(f'(?i){re.escape(term)}', highlighted_term, text)

        self.text_edit.setHtml(text.replace("\n", "<br>"))
        self.scroll_to_text(distinct_entity)

    def scroll_to_text(self, text):
        if text:
            cursor = self.text_edit.document().find(text)
            self.text_edit.setTextCursor(cursor)

class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Enable vertical scrollbar as needed

    def wheelEvent(self, event):
        # Always handle the wheel event within QTextEdit
        super().wheelEvent(event)

        # Stop propagation of the event to parent
        if self.verticalScrollBar().isVisible():
            event.accept()
        else:
            event.ignore()


class CellWidget(QWidget):
    def __init__(self, text, filter_edit, search_terms, parent=None):
        super(CellWidget, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.label = QLabel(text)
        self.setHighlightedText(text, search_terms)
        self.button = QPushButton()
        icon = self.button.style().standardIcon(QStyle.SP_CommandLink)  # Example of a standard icon
        self.button.setIcon(icon)
        self.button.setFixedSize(20, 20)  # Adjust size as needed
        self.button.clicked.connect(lambda: filter_edit.setText(text))
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    def setHighlightedText(self, text, search_terms):
        for term in search_terms:
            if term.lower() in text.lower():
                text = text.replace(term, f"<span style='background-color: yellow; color: black;'>{term}</span>")
        self.label.setText(text)

class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        return float(self.text()) < float(other.text())
