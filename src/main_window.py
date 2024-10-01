import os
import sqlite3
import pandas as pd
from collections import deque
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QApplication, 
                             QListWidget, QPushButton, QComboBox, QDesktopWidget, QFileDialog,
                             QLineEdit, QLabel, QGroupBox, QSplitter, QTableWidget, QSizePolicy, QShortcut,
                             QRadioButton, QAbstractItemView, QFileDialog, QMessageBox, QTableWidgetItem, QCheckBox)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QKeySequence, QFont, QColor, QIcon, QIntValidator, QDoubleValidator, QPalette
from PyQt5.QtCore import Qt, QTimer, QLocale



class ResponsiveMainWindow(QMainWindow):
    def __init__(self):
        super(ResponsiveMainWindow, self).__init__()

        self.countdown_running = False
        self.new_row_index = None  # To store the index of the newly added row
        self.is_edit_mode = False  # Initial edit mode state

        # Set up window title
        self.setWindowTitle("CORE PHOTO VIEWER")

        # Set a timer to handle dynamic resizing
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.handle_resize_event)

        # Initialize the file explorer functionality
        self.current_directory = None
        self.connection = None
        self.suppress_img_warning = False
        self.setup_ui()
        self.setup_file_explorer()
        self.setup_validators()

        # Add keyboard shortcuts for Previous (F2) and Next (F3) image
        self.shortcut_previous = QShortcut(QKeySequence(Qt.Key_F2), self)
        self.shortcut_next = QShortcut(QKeySequence(Qt.Key_F3), self)

        # Connect shortcuts to the appropriate methods
        self.shortcut_previous.activated.connect(self.show_previous_image)
        self.shortcut_next.activated.connect(self.show_next_image)

        self.is_edit_mode = False  # Track whether the table is in edit mode


    def setup_ui(self):
        # Set central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Create a QSplitter for the file explorer and center layout
        splitter = QSplitter(Qt.Horizontal)

        self.countdown_timer = QTimer()
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.update_countdown)

        # Create a QGroupBox for the file explorer and list widget
        self.file_explorer_group = QGroupBox("File Explorer")
        file_explorer_layout = QVBoxLayout()

        # Create the QComboBox and QListWidget
        self.file_explorer_combo = QComboBox()
        self.list_widget = QListWidget()

        #Refresh button to manually refresh the QListWidget
        self.refresh_list = QPushButton("Refresh")
        self.refresh_list.clicked.connect(self.refresh_list_widget)

        self.db_buttons_group = QGroupBox()
        self.db_buttons_layout = QHBoxLayout()

        #Create a database
        self.create_db_button = QPushButton("Create DB")
        self.create_db_button.clicked.connect(self.create_database)
        
        #Open a database
        self.open_db_button = QPushButton("Open DB")
        self.open_db_button.clicked.connect(self.open_database)

        #Export data from database
        self.export_db_button = QPushButton("Export DB")
        self.export_db_button.clicked.connect(self.export_database)

        #displays the Current database connection
        self.current_db_connection_lbl = QLabel("Database: None")
        self.current_db_connection_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))

        self.db_buttons_layout.addWidget(self.create_db_button)
        self.db_buttons_layout.addWidget(self.open_db_button)
        self.db_buttons_layout.addWidget(self.export_db_button)
        self.db_buttons_group.setLayout(self.db_buttons_layout)


        # Add them to the layout inside the QGroupBox
        file_explorer_layout.addWidget(self.file_explorer_combo)
        file_explorer_layout.addWidget(self.list_widget)
        file_explorer_layout.addWidget(self.refresh_list)
        self.file_explorer_group.setLayout(file_explorer_layout)

        # Create widgets for the center
        self.hole_id_edit = QLineEdit()
        self.hole_id_edit.setPlaceholderText("Enter Hole ID")
        self.hole_id_edit.setAlignment(Qt.AlignCenter)  # Center text entered by the user

        self.image_viewer = QLabel()
        self.image_viewer.setAlignment(Qt.AlignCenter)
        self.image_viewer.setStyleSheet("background-color: lightgray;")
        self.image_viewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create QGroupBox for interval input
        self.interval_group = QGroupBox("Interval Details")
        interval_layout = QHBoxLayout()
        interval_layout.setContentsMargins(5, 20, 10, 0)

        self.input_from_length = QLineEdit()
        self.input_from_length.setPlaceholderText("From Length")
        
        self.input_to_length = QLineEdit()
        self.input_to_length.setPlaceholderText("To Length")
        
        self.box_id = QLineEdit()
        self.box_id.setPlaceholderText("Box ID")
        
        self.add_box_btn = QPushButton("Add Box")
        self.add_box_btn.setDefault(True)
        self.add_box_btn.clicked.connect(self.add_box_data)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_process)
        self.cancel_btn.setVisible(False)# Initially hidden


        self.is_countdown_active = False
        self.countdown_seconds = 5
        
        self.task_queue = deque()
        self.current_task = None

        # Add widgets to the QHBoxLayout
        interval_layout.addWidget(self.input_from_length)
        interval_layout.addWidget(self.input_to_length)
        interval_layout.addWidget(self.box_id)
        interval_layout.addWidget(self.add_box_btn)
        interval_layout.addWidget(self.cancel_btn)

        # Set the layout for the QGroupBox
        self.interval_group.setLayout(interval_layout)

        # Create new QGroupBox for core size and hole ID
        self.core_size_hole_id_group = QGroupBox()
        self.core_size_hole_id_group.setStyleSheet("QGroupBox { border: none; }")  # Hide the border
        core_size_layout = QVBoxLayout()
        
        # Add the self.hole_id_edit to the layout
        core_size_layout.addWidget(self.hole_id_edit)

        # Create a QHBoxLayout for the radio buttons
        radio_button_layout = QHBoxLayout()

        # Create radio buttons
        self.radio_half_core = QRadioButton("Half Core")
        self.radio_whole_core = QRadioButton("Whole Core")

        # Add radio buttons to the layout
        radio_button_layout.addWidget(self.radio_half_core)
        radio_button_layout.addWidget(self.radio_whole_core)

        # Set alignment for radio buttons (centered below the hole_id_edit)
        radio_button_layout.setAlignment(Qt.AlignCenter)

        # Add the radio button layout to the main group layout
        core_size_layout.addLayout(radio_button_layout)

        # Set the final layout for the group box
        self.core_size_hole_id_group.setLayout(core_size_layout)

        # Set up layouts
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.current_db_connection_lbl)
        left_layout.addWidget(self.file_explorer_group)
        left_layout.addWidget(self.db_buttons_group)

        center_layout = QVBoxLayout()
        center_layout.addWidget(self.core_size_hole_id_group)  # Add the new QGroupBox
        center_layout.addWidget(self.image_viewer)
        center_layout.addWidget(self.interval_group, alignment=Qt.AlignBottom | Qt.AlignCenter)

        # Create a widget for the left part and set the left layout
        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        # Create a widget for the center part and set the center layout
        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        # Right Side: QComboBox and QTableWidget in a vertical layout
        right_layout = QVBoxLayout()

        # QComboBox for Hole ID items
        self.hole_id_items = QComboBox()
        # Connect the QComboBox signal to the filtering function
        self.hole_id_items.currentIndexChanged.connect(self.filter_core_photo_records_by_hole_id)


        # QTableWidget for core photo records
        self.core_photo_records_tbl = QTableWidget()
        self.core_photo_records_tbl.setColumnCount(6)
        self.core_photo_records_tbl.setRowCount(100)
        self.core_photo_records_tbl.setHorizontalHeaderLabels(['HOLE ID', 'FROM', 'TO', 'LENGTH', 'BOX #', 'CORE PHOTO TYPE'])
        self.core_photo_records_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.core_photo_records_tbl.itemClicked.connect(self.on_item_clicked)




        self.core_photo_records_tbl.setSelectionBehavior(QTableWidget.SelectRows)#highlight the entire row when selected
        self.core_photo_records_tbl.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: gold;      /* Highlight the selected row with gold */
                color: black;                /* Set text color of the selected cell to white */
            }
            QTableWidget::item {
                color: black;                /* Set the default text color to black */
            }
        """)

        self.misc_buttons_group = QGroupBox()

        misc_buttons_layout = QHBoxLayout()
        misc_buttons_layout.setSpacing(10)

        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.toggle_edit_mode)
        #self.edit_button.setStyleSheet("padding-left: 2px; padding-right: 2px; padding-top: 2px; padding-bottom: 2px;")
        self.add_rows_button = QPushButton("Add Row")
        self.add_rows_button.clicked.connect(self.add_row)
        #self.add_rows_button.setStyleSheet("margin-left: 5px; margin-right: 5px;")
        self.delete_row = QPushButton("Delete Row")
        self.delete_row.clicked.connect(self.delete_selected_row)

        #Adding ctlr+enter key to skip the countdown
        ctrl_enter_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        ctrl_enter_shortcut.activated.connect(self.skip_countdown_and_rename)

        misc_buttons_layout.addWidget(self.edit_button)
        misc_buttons_layout.addWidget(self.add_rows_button)
        misc_buttons_layout.addWidget(self.delete_row)
        self.misc_buttons_group.setLayout(misc_buttons_layout)

        # Add widgets to the right layout
        right_layout.addWidget(self.hole_id_items)
        right_layout.addWidget(self.core_photo_records_tbl)
        right_layout.addWidget(self.misc_buttons_group)

        # Create a widget for the right part
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Add both widgets to the splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(center_widget)
        splitter.addWidget(right_widget)

        # Set the splitter to allow resizing
        splitter.setStretchFactor(0, 1)  # Left part resizable
        splitter.setStretchFactor(1, 2)  # Center part resizable
        splitter.setStretchFactor(2, 1)  # Right part resizable

        # Add the splitter to the main layout
        layout.addWidget(splitter)

        # Set the layout for the central widget
        central_widget.setLayout(layout)

        # Set the central widget to the main window
        self.setCentralWidget(central_widget)

        # Connect the QComboBox selection change signal
        self.file_explorer_combo.currentIndexChanged.connect(self.on_combobox_selection_changed)
        # Connect the QListWidget item selection change signal
        self.list_widget.currentItemChanged.connect(self.on_list_widget_item_changed)

        # Dynamically fit to screen
        self.resize_window()


    def show_previous_image(self):
        """
        Show the previous image in the list.
        """
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            previous_item = self.list_widget.item(current_row - 1)
            self.list_widget.setCurrentItem(previous_item)
            self.on_list_widget_item_changed(previous_item, None)

    def show_next_image(self):
        """
        Show the next image in the list.
        """
        current_row = self.list_widget.currentRow()
        if current_row < self.list_widget.count() - 1:
            next_item = self.list_widget.item(current_row + 1)
            self.list_widget.setCurrentItem(next_item)
            self.on_list_widget_item_changed(next_item, None)

    def toggle_edit_mode(self):
        if self.new_row_index is not None:  # Check if a new row has been added
            # Prompt the user with a message box when toggling edit mode off
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Save Changes?")
            msg_box.setText("Do you want to save the changes to the new row?")
            msg_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Save)

            reply = msg_box.exec_()

            if reply == QMessageBox.Save:
                # Handle Save: Collect data from the new row and save to the database
                hole_id = self.core_photo_records_tbl.item(self.new_row_index, 0).text()
                top_length = float(self.core_photo_records_tbl.item(self.new_row_index, 1).text())
                bottom_length = float(self.core_photo_records_tbl.item(self.new_row_index, 2).text())
                total_length = bottom_length - top_length
                box_id = self.core_photo_records_tbl.item(self.new_row_index, 4).text()
                core_size = self.core_photo_records_tbl.item(self.new_row_index, 5).text()

                # Save data to database
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO core_data (hole_id, top_length, bottom_length, total_length, box_id, core_size)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (hole_id, top_length, bottom_length, total_length, box_id, core_size))
                self.connection.commit()

                # Reset the new row tracker
                self.new_row_index = None

            elif reply == QMessageBox.Discard:
                # Handle Discard: Remove the newly added row
                self.core_photo_records_tbl.removeRow(self.new_row_index)
                self.new_row_index = None

            elif reply == QMessageBox.Cancel:
                # Handle Cancel: Do nothing and return to edit mode
                return  # Exit the function without disabling edit mode

        # Toggle edit mode
        self.is_edit_mode = not self.is_edit_mode  # Toggle edit mode state
        if self.is_edit_mode:
            self.core_photo_records_tbl.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
            self.edit_button.setText("Disable Edit Mode")
        else:
            self.core_photo_records_tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.edit_button.setText("Edit")
    

    
    def on_item_clicked(self, item):
        if self.is_edit_mode:
            self.core_photo_records_tbl.editItem(item)  # Start editing the clicked item

    def add_row(self):
        # Add a new row at the end of the table
        row_position = self.core_photo_records_tbl.rowCount()
        self.core_photo_records_tbl.insertRow(row_position)

        # Store the newly added row index to track it
        self.new_row_index = row_position

        # Optionally, make sure this row is highlighted or visible for the user
        self.core_photo_records_tbl.scrollToItem(self.core_photo_records_tbl.item(row_position, 0))


    
    def delete_selected_row(self):
        if self.is_edit_mode:  # Ensure it's in edit mode
            current_row = self.core_photo_records_tbl.currentRow()
            if current_row >= 0:  # Ensure a row is selected
                # Get data from the selected row to identify the record in the database
                hole_id = self.core_photo_records_tbl.item(current_row, 0).text()  # Assuming 'HOLE ID' is in column 0
                top_length = self.core_photo_records_tbl.item(current_row, 1).text()  # Assuming 'FROM' is in column 1

                # Confirm deletion from the user
                reply = QMessageBox.question(
                    self, "Confirm Delete", 
                    f"Are you sure you want to delete the record for Hole ID: {hole_id} and Top Length: {top_length}?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    try:
                        # Delete the row from the database
                        cursor = self.connection.cursor()
                        cursor.execute("""
                            DELETE FROM core_data 
                            WHERE hole_id = ? AND top_length = ?
                        """, (hole_id, top_length))
                        self.connection.commit()

                        # Remove the row from the table
                        self.core_photo_records_tbl.removeRow(current_row)
                        QMessageBox.information(self, "Deleted", "Record successfully deleted.")
                        
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to delete record from database: {str(e)}")
                else:
                    return
                
    #Validators

    def setup_validators(self):
        """
        Sets validators for input fields to allow only numbers.
        """
        # Validator for decimal numbers (for lengths)
        double_validator = QDoubleValidator(0.0, 999999.99, 2)  # Range (0, 999999.99) with 2 decimal places
        double_validator.setNotation(QDoubleValidator.StandardNotation)  # Standard decimal notation
        double_validator.setLocale(QLocale(QLocale.English))  # Ensures '.' is used as the decimal separator

        # Validator for integer numbers (for box_id)
        int_validator = QIntValidator(0, 999999)  # Adjust the range based on your box_id limits

        # Apply validators to input fields
        self.input_from_length.setValidator(double_validator)  # Only decimal numbers
        self.input_to_length.setValidator(double_validator)    # Reuse the same validator for both fields
        self.box_id.setValidator(int_validator)                # Only integers


    def setup_file_explorer(self):
        """
        Populate the QComboBox with initial items.
        """
        self.file_explorer_combo.addItem("Select a directory or file")
        self.file_explorer_combo.addItem("Open File Explorer...")

    def on_combobox_selection_changed(self, index):
        """
        Handle the QComboBox selection change.
        """
        selected_item = self.file_explorer_combo.currentText()

        if selected_item == "Open File Explorer...":
            # Open file dialog to select a directory
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.Directory)
            file_dialog.setOption(QFileDialog.ShowDirsOnly)
            file_dialog.setViewMode(QFileDialog.List)

            if file_dialog.exec_():
                selected_directory = file_dialog.selectedFiles()[0]
                self.current_directory = selected_directory
                self.file_explorer_combo.addItem(selected_directory)  # Add to combo box
                self.file_explorer_combo.setCurrentText(selected_directory)  # Set the current text
                self.populate_combobox_with_directory(selected_directory)
                self.display_directory_contents(selected_directory)
        elif os.path.isdir(selected_item):
            self.current_directory = selected_item
            self.display_directory_contents(selected_item)
        elif os.path.isfile(selected_item):
            self.display_file_contents(selected_item)

    def populate_combobox_with_directory(self, directory):
        """
        Populate the QComboBox with files and directories from the selected directory.
        """
        self.file_explorer_combo.blockSignals(True)  # Block signals to prevent triggering events
        self.file_explorer_combo.clear()
        self.file_explorer_combo.addItem("Select a directory or file")
        self.file_explorer_combo.addItem("Open File Explorer...")

        try:
            for item in os.listdir(directory):
                full_path = os.path.join(directory, item)
                self.file_explorer_combo.addItem(full_path)
        except PermissionError:
            self.file_explorer_combo.addItem("Cannot access directory")  # Display error if directory cannot be accessed
        self.file_explorer_combo.blockSignals(False)  # Unblock signals

    def display_directory_contents(self, directory):
        """
        Display the contents of the selected directory in the QListWidget.
        """
        self.list_widget.clear()
        try:
            for item in os.listdir(directory):
                self.list_widget.addItem(item)
        except PermissionError:
            self.list_widget.addItem("Cannot access directory")

    def display_file_contents(self, file_path):
        """
        Display the contents of the selected file in the QListWidget.
        If it's a directory, list the directory contents.
        """
        self.list_widget.clear()

        # Check if the path is a directory
        if os.path.isdir(file_path):
            try:
                # List contents of the directory
                for item in os.listdir(file_path):
                    item_path = os.path.join(file_path, item)
                    self.list_widget.addItem(item)

            except Exception as e:
                self.list_widget.addItem(f"Error reading directory: {e}")

        elif os.path.isfile(file_path):
            try:
                # Display file contents
                with open(file_path, 'r') as file:
                    contents = file.readlines()
                    self.list_widget.addItems(contents)

            except Exception as e:
                self.list_widget.addItem(f"Error reading file: {e}")

            # Check if it's an image file and load it in the image viewer
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                pixmap = QPixmap(file_path)
                self.image_viewer.setPixmap(pixmap.scaled(self.image_viewer.size(), Qt.KeepAspectRatio))
            else:
                self.image_viewer.clear()
        else:
            self.list_widget.addItem("Invalid file or directory.")

    def on_list_widget_item_changed(self, current, previous):
        """
        Handle the selection change in the QListWidget.
        """
        if current:
            selected_item = current.text()
            if self.current_directory:
                file_path = os.path.join(self.current_directory, selected_item)
                if os.path.isfile(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Store the full file path in the item data
                    current.setData(Qt.UserRole, file_path)

                    # Display the image
                    pixmap = QPixmap(file_path)
                    self.image_viewer.setPixmap(pixmap.scaled(self.image_viewer.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
    def populate_hole_id_combobox(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT DISTINCT hole_id FROM core_data")
            hole_ids = cursor.fetchall()

            # Clear the QComboBox before populating
            self.hole_id_items.clear()
            self.hole_id_items.addItem("All")  # Add an 'All' option to display all records

            # Populate the QComboBox with distinct hole_ids
            for hole_id in hole_ids:
                self.hole_id_items.addItem(hole_id[0])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to populate hole_id: {str(e)}")
    

    def filter_core_photo_records_by_hole_id(self):
        try:
            # Get the selected hole_id from the combo box
            selected_hole_id = self.hole_id_items.currentText()

            # Clear the table before populating with new data
            self.core_photo_records_tbl.setRowCount(0)

            # SQL query to fetch data based on the selected hole_id
            query = "SELECT hole_id, top_length, bottom_length, total_length, box_id, core_size FROM core_data"
            
            if selected_hole_id != "All":
                query += " WHERE hole_id = ?"
                data = self.connection.cursor().execute(query, (selected_hole_id,))
            else:
                # If "All" is selected, retrieve all records
                data = self.connection.cursor().execute(query)

            # Fetch data and populate the table
            records = data.fetchall()
            for row_number, row_data in enumerate(records):
                self.core_photo_records_tbl.insertRow(row_number)
                for column_number, cell_data in enumerate(row_data):
                    # Format total_length (index 3) to 2 decimal places
                    if column_number == 3:  # total_length column
                        formatted_value = f"{float(cell_data):.2f}"
                        self.core_photo_records_tbl.setItem(row_number, column_number, QTableWidgetItem(formatted_value))
                    else:
                        self.core_photo_records_tbl.setItem(row_number, column_number, QTableWidgetItem(str(cell_data)))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to filter records by hole_id: {str(e)}")




    def create_database(self):
        # Open a file dialog to get the file path for the database
        options = QFileDialog.Options()
        db_file, _ = QFileDialog.getSaveFileName(self, "Save Database File", "", "SQLite Database (*.db);;All Files (*)", options=options)
        
        if db_file:
            # Ensure the file has the .db extension
            if not db_file.endswith(".db"):
                db_file += ".db"

            # Create the database and the table if it doesn't exist
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS core_data (
                        id INTEGER PRIMARY KEY,
                        hole_id TEXT NOT NULL,
                        top_length DECIMAL(7,2),
                        bottom_length DECIMAL(7,2),
                        total_length DECIMAL(7,2),
                        box_id DECIMAL(7,2),
                        core_size TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Success", "Database created successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create database: {str(e)}")
    
    def open_database(self):
        # Open a file dialog to select the database file
        options = QFileDialog.Options()
        db_file, _ = QFileDialog.getOpenFileName(self, "Open Database File", "", "SQLite Database (*.db);;All Files (*)", options=options)
        
        if db_file:
            try:
                # Connect to the selected database and store the connection
                self.connection = sqlite3.connect(db_file)
                cursor = self.connection.cursor()

                # Clear the current contents of the table
                self.core_photo_records_tbl.setRowCount(0)

                self.populate_hole_id_combobox()

                # Query to select all records from the core_data table
                cursor.execute("SELECT hole_id, top_length, bottom_length, total_length, box_id FROM core_data")
                records = cursor.fetchall()

                # Populate the table with the fetched records
                for row in records:
                    row_position = self.core_photo_records_tbl.rowCount()
                    self.core_photo_records_tbl.insertRow(row_position)
                    for column, data in enumerate(row):
                        self.core_photo_records_tbl.setItem(row_position, column, QTableWidgetItem(str(data)))

                # Update the database name label
                self.current_db_connection_lbl.setText(f"Database: {db_file.split('/')[-1]}")  # Get only the file name
                QMessageBox.information(self, "Success", "Database opened and records populated.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open database: {str(e)}")


    def export_database(self):
        if self.connection is None:
            QMessageBox.warning(self, "No Database", "Please open a database first.")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Excel Files (*.xlsx);;CSV Files (*.csv)", options=options)

        if file_name:
            if file_name.endswith('.xlsx'):
                self.export_to_excel(file_name)
            elif file_name.endswith('.csv'):
                self.export_to_csv(file_name)
            else:
                QMessageBox.warning(self, "Invalid Format", "Please select a valid file format (.xlsx or .csv).")

    
    def export_to_excel(self, file_name):
        # Query data from the database
        query = "SELECT hole_id, top_length, bottom_length, total_length, box_id, core_size FROM core_data"
        data = pd.read_sql_query(query, self.connection)  # Assuming self.connection is your database connection
        data.columns = ['HOLE ID', 'FROM', 'TO', 'LENGTH', 'BOX NUMBER', 'CORE PHOTO TYPE']  # Rename columns
        data.to_excel(file_name, index=False)  # Export to Excel
        QMessageBox.information(self, "Export Successful", "Data exported to Excel successfully.")
    
    def export_to_csv(self, file_name):
        # Query data from the database
        query = "SELECT hole_id, top_length, bottom_length, total_length, box_id, core_size FROM core_data"
        data = pd.read_sql_query(query, self.connection)  # Assuming self.connection is your database connection
        data.columns = ['HOLE ID', 'FROM', 'TO', 'LENGTH', 'BOX NUMBER', 'CORE PHOTO TYPE']  # Rename columns
        data.to_csv(file_name, index=False)  # Export to CSV
        QMessageBox.information(self, "Export Successful", "Data exported to CSV successfully.")

    def add_box_data(self):
        if self.is_duplicate_entry():
            QMessageBox.warning(self, "Duplicate Entry", "This entry already exists.")
            return

        # Get current selected file data
        current_file_data = self.list_widget.currentItem().data(Qt.UserRole)
        
        # Queue the current file and its associated data
        task = {
            "hole_id": self.hole_id_edit.text(),
            "top_length": float(self.input_from_length.text()),
            "bottom_length": float(self.input_to_length.text()),
            "box_id": self.box_id.text(),
            "current_file_data": current_file_data
        }
        self.task_queue.append(task)

        # Start the countdown if it's not already active
        if not self.is_countdown_active:
            self.start_countdown()
    
    def start_countdown(self):
        # Start countdown for the first task in the queue
        if self.task_queue:
            self.is_countdown_active = True
            self.countdown_seconds = 5  # Reset countdown
            self.current_task = self.task_queue.popleft()  # Fetch the next task
            self.cancel_btn.setVisible(True)
            self.countdown_timer.start()

    def update_countdown(self):
        if self.countdown_seconds > 0:
            self.cancel_btn.setText(f"Cancel ({self.countdown_seconds})")
            self.countdown_seconds -= 1
        else:
            self.countdown_timer.stop()
            self.cancel_btn.setVisible(False)
            self.is_countdown_active = False
            self.perform_add_box_data()  # Process the current task

            # If there are more tasks in the queue, continue with the next
            if self.task_queue:
                self.start_countdown()

    def cancel_process(self):
        self.countdown_timer.stop()
        self.cancel_btn.setVisible(False)
        self.is_countdown_active = False
        self.current_task = None  # Clear current task without processing it
        self.cancel_btn.setText("Cancel")  # Reset button text

        # If there are more tasks in the queue, start the next task
        if self.task_queue:
            self.start_countdown()
    
        
    def perform_add_box_data(self):
        try:
            if not self.current_task:
                return  # No task to process

            # Extract the data from the current task
            hole_id = self.current_task["hole_id"]
            top_length = self.current_task["top_length"]
            bottom_length = self.current_task["bottom_length"]
            box_id = self.current_task["box_id"]
            current_file_data = self.current_task["current_file_data"]

            # Get core size from radio buttons
            core_size = "Half Core" if self.radio_half_core.isChecked() else "Whole Core"

            # Calculate total length
            total_length = bottom_length - top_length

            # Insert into the database
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO core_data (hole_id, top_length, bottom_length, total_length, box_id, core_size)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (hole_id, top_length, bottom_length, total_length, box_id, core_size))
            self.connection.commit()

            # Update the QListWidget or any other UI component
            self.rename_selected_list_item(hole_id, top_length, bottom_length, current_file_data)

            # Automatically focus on the last row of the table after inserting data
            row_count = self.core_photo_records_tbl.rowCount()

            # Insert a new row into the table (if needed, based on your implementation)
            self.core_photo_records_tbl.insertRow(row_count)

            # Set the data for the newly added row (modify this based on what data you show)
            self.core_photo_records_tbl.setItem(row_count, 0, QTableWidgetItem(str(hole_id)))
            self.core_photo_records_tbl.setItem(row_count, 1, QTableWidgetItem(str(top_length)))
            self.core_photo_records_tbl.setItem(row_count, 2, QTableWidgetItem(str(bottom_length)))
            self.core_photo_records_tbl.setItem(row_count, 3, QTableWidgetItem(str(total_length)))
            self.core_photo_records_tbl.setItem(row_count, 4, QTableWidgetItem(str(box_id)))
            self.core_photo_records_tbl.setItem(row_count, 5, QTableWidgetItem(core_size))

            # Clear input fields after the data is committed and table is updated
            self.clear_input_fields()

            # Highlight the newly added row in gold for 5 seconds
            self.highlight_row(row_count)

            # Scroll to the last row and set it as the current selection
            self.core_photo_records_tbl.scrollToItem(self.core_photo_records_tbl.item(row_count, 0))
            self.core_photo_records_tbl.setCurrentCell(row_count, 0)

            # Optionally jump to the first item containing "IMG_" if needed
            self.jump_to_img_placeholder()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add data to the database: {str(e)}")

        finally:
            self.current_task = None  # Clear the current task

    
    def refresh_list_widget(self):
        """
        Refresh the list_widget while preserving the current selection.
        """
        # Get the currently selected item text before refreshing
        current_item = self.list_widget.currentItem()
        current_text = current_item.text() if current_item else None

        # Repopulate the list (using the directory content display method)
        self.display_directory_contents(self.current_directory)

        # If there was a selection, try to restore it
        if current_text:
            items = self.list_widget.findItems(current_text, Qt.MatchExactly)
            if items:
                self.list_widget.setCurrentItem(items[0])  # Restore the previous selection
    
    def rename_and_refresh(self, hole_id, top_length, bottom_length):
        current_item = self.list_widget.currentItem()  # Get current selected item
        next_index = self.list_widget.row(current_item) + 1  # Track next item (F3 or "Next")

        # Perform renaming and refresh
        self.rename_selected_list_item(hole_id, top_length, bottom_length)
        self.refresh_list_widget()

        # After refreshing, re-select the next item in the list (if it exists)
        if next_index < self.list_widget.count():
            self.list_widget.setCurrentRow(next_index)  # Move to the next item
        else:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)  # Stay at the last item
    
    
    def jump_to_img_placeholder(self):
        """
        Jump to the first item in the list_widget that contains 'IMG_'.
        If no such item exists, show a message box with a suppressible warning.
        """
        # Try to find the first item containing "IMG_"
        found = False
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if "IMG_" in item.text():
                self.list_widget.setCurrentRow(i)  # Select the first "IMG_" item
                found = True
                break

        # If no item with "IMG_" was found
        if not found and not self.suppress_img_warning:
            self.show_no_img_placeholder_warning()
        
    def show_no_img_placeholder_warning(self):
        """
        Show a warning message box when no IMG_ item is found, with an option to suppress future warnings.
        """
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText("No IMG_ placeholder found in the list.")
        msg_box.setWindowTitle("Warning")
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # Add a checkbox to suppress future warnings
        checkbox = QCheckBox("Don't show this message again")
        msg_box.setCheckBox(checkbox)

        # Show the message box and wait for user interaction
        if msg_box.exec() == QMessageBox.Ok and checkbox.isChecked():
            self.suppress_img_warning = True  # Suppress future warnings
    

    #Auto-Refresh table
    def refresh_core_photo_records_tbl(self):
        try:
            # Clear the current contents of the table
            self.core_photo_records_tbl.setRowCount(0)

            # Query to select all records from the core_data table
            cursor = self.connection.cursor()
            cursor.execute("SELECT hole_id, top_length, bottom_length, total_length, box_id, core_size FROM core_data")
            records = cursor.fetchall()

            # Populate the table with the fetched records
            for row in records:
                row_position = self.core_photo_records_tbl.rowCount()
                self.core_photo_records_tbl.insertRow(row_position)
                for column, data in enumerate(row):
                    self.core_photo_records_tbl.setItem(row_position, column, QTableWidgetItem(str(data)))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh table: {str(e)}")
    
    def clear_input_fields(self):
        self.input_from_length.clear()
        self.input_to_length.clear()
        self.box_id.clear()

    def rename_selected_list_item(self, hole_id, top_length, bottom_length, current_file_data):
        new_name = f"{hole_id}_{top_length:.2f}-{bottom_length:.2f}.jpg"
        
        # Check if the file exists
        if not os.path.exists(current_file_data):
            QMessageBox.critical(self, "Error", f"File does not exist: {current_file_data}")
            return

        # Construct the new file path
        new_file_path = os.path.join(os.path.dirname(current_file_data), new_name)

        try:
            # Rename the file
            os.rename(current_file_data, new_file_path)

            # Update the list widget item to display the new name
            current_item = self.list_widget.currentItem()
            current_item.setText(new_name)
            current_item.setData(Qt.UserRole, new_file_path)  # Update the stored path

            # Set a green checkmark icon to indicate success
            check_icon = QIcon(QPixmap("../resources/icons/check.png"))
            current_item.setIcon(check_icon)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to rename file: {str(e)}")
        
    
    def is_duplicate_entry(self):
        hole_id = self.hole_id_edit.text()
        top_length = self.input_from_length.text()
        bottom_length = self.input_to_length.text()
        box_id = self.box_id.text()

        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM core_data WHERE hole_id=? AND top_length=? AND bottom_length=? AND box_id=?", 
                       (hole_id, top_length, bottom_length, box_id))
        
        count = cursor.fetchone()[0]
        return count > 0  # Return True if there's a duplicate


    def keyPressEvent(self, event):
        """
        Override keyPressEvent to handle custom key bindings.
        """
        # Check if Delete key is pressed
        if event.key() == Qt.Key_Delete:
            self.delete_selected_row()  # Trigger the delete function

        # Check if Enter or Numpad Enter is pressed
        elif (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter):
            # If the countdown is already active, skip it
            if self.is_countdown_active:
                self.skip_countdown_and_rename()  # Skip countdown and process task immediately
            else:
                self.start_countdown()  # Start countdown if it's not active

        # We no longer need the Ctrl + Enter check here as it's handled by the QShortcut
        else:
            super().keyPressEvent(event)





    def skip_countdown_and_rename(self):
        """
        Skip the countdown and immediately process the current task.
        """
        if self.is_countdown_active:
            self.countdown_timer.stop()  # Stop the countdown
            self.cancel_btn.setVisible(False)  # Hide the cancel button
            self.is_countdown_active = False  # Reset countdown flag
            self.perform_add_box_data()  # Immediately perform the task


    def highlight_row(self, row_index):
        # Set the row's background color to gold
        for column in range(self.core_photo_records_tbl.columnCount()):
            item = self.core_photo_records_tbl.item(row_index, column)
            if item:
                item.setBackground(QColor('gold'))

        # Revert the background color to default after 5 seconds
        QTimer.singleShot(5000, lambda: self.revert_row_color(row_index))

    def revert_row_color(self, row_index):
        """
        Reverts the background color of the specified row to the default color or
        handles alternating row colors (if applicable).
        """
        # Get the system's default background color for the table
        default_color = self.core_photo_records_tbl.palette().color(QPalette.Base)

        # Handle alternating row colors (striped effect) if needed
        if row_index % 2 == 1:
            default_color = self.core_photo_records_tbl.palette().color(QPalette.AlternateBase)

        # Revert each item in the row to the appropriate default color
        for column in range(self.core_photo_records_tbl.columnCount()):
            item = self.core_photo_records_tbl.item(row_index, column)
            if item:
                item.setBackground(default_color)


    
    # Method for loading images in image viewer with dynamic size
    def load_image(self, image_path):
        # Load the image
        image = QImage(image_path)
        if image.isNull():
            self.image_viewer.setText("Failed to load image")
            return
        
        # Scale the image to fit within the QLabel
        pixmap = QPixmap.fromImage(image).scaled(self.image_viewer.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_viewer.setPixmap(pixmap)

    def resize_window(self):
        """Resize the window to fit the user's screen, with padding."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        width = int(screen_geometry.width() * 0.8)  # 80% of the screen width
        height = int(screen_geometry.height() * 0.8)  # 80% of the screen height
        self.setGeometry(0, 0, width, height)

        # Move the window to the center
        self.center_window()

    def center_window(self):
        """Centers the window on the screen."""
        frame_geometry = self.frameGeometry()
        screen_center = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def resizeEvent(self, event):
        """
        Capture the resize event and trigger custom handling.
        """
        # Trigger a timer to avoid resizing too often in large applications
        self.resize_timer.start(250)  # 250ms delay before handling the resize

        # Call the parent class resizeEvent
        super(ResponsiveMainWindow, self).resizeEvent(event)

    def handle_resize_event(self):
        """
        Custom method to handle actions when the window is resized.
        """
        self.image_viewer.setFixedSize(self.hole_id_edit.width(), 800)  # Example of dynamic resizing


if __name__ == "__main__":
    app = QApplication([])
    window = ResponsiveMainWindow()
    window.show()
    app.exec_()
