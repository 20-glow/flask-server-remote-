import sys
import threading
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLineEdit
from PyQt5.QtCore import Qt
import requests
from functools import partial

class ProcessManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 800, 400)
        self.setWindowTitle("Process Manager")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create a QLineEdit for searching processes
        search_input = QLineEdit()
        search_input.setPlaceholderText("Search for processes...")
        layout.addWidget(search_input)

        # Create a QTableWidget to display the processes in a table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "CPU %", "Memory (MB)"])
        layout.addWidget(self.process_table)

        # Create a "List Processes" button
        list_button = QPushButton("List Processes")
        layout.addWidget(list_button)
        list_button.clicked.connect(self.list_processes)

        # Create a "Kill Process" button
        kill_button = QPushButton("Kill Process")
        layout.addWidget(kill_button)
        kill_button.clicked.connect(self.kill_selected_process)

        # Store a reference to the search input for later use
        self.search_input = search_input

        # Initialize the event loop
        self.loop = asyncio.get_event_loop()

    async def list_processes_async(self, search_query):
        try:
            # Make a GET request to the Flask server's list_processes route asynchronously
            list_processes_response = await asyncio.to_thread(requests.get, 'http://localhost:5000/list_processes')  # Update the URL
            if list_processes_response.status_code == 200:
                process_data = list_processes_response.json()
                self.update_table(process_data, search_query)
            else:
                print(f"Failed to fetch process list: {list_processes_response.status_code}")

        except Exception as e:
            print(f"An error occurred: {e}")

    def list_processes(self):
        search_query = self.search_input.text().strip().lower()
        self.loop.run_until_complete(self.list_processes_async(search_query))

    def update_table(self, process_data, search_query):
        self.process_table.setRowCount(0)

        for process_info in process_data:
            pid, name, cpu_percent, memory = process_info["PID"], process_info["Name"], process_info["CPU Percent"], process_info["Memory (MB)"]
            if search_query.lower() in name.lower() or not search_query:
                row_position = self.process_table.rowCount()
                self.process_table.insertRow(row_position)
                self.process_table.setItem(row_position, 0, QTableWidgetItem(str(pid)))  # Convert to str
                self.process_table.setItem(row_position, 1, QTableWidgetItem(name))
                self.process_table.setItem(row_position, 2, QTableWidgetItem(str(cpu_percent)))  # Convert to str
                self.process_table.setItem(row_position, 3, QTableWidgetItem(str(memory)))  # Convert to str

        # Set custom column sizes
        self.process_table.setColumnWidth(0, 100)  # Adjust the size of the first column
        self.process_table.setColumnWidth(1, 200)  # Adjust the size of the second column

    def kill_selected_process_async(self, pid, selected_row):
        try:
            kill_process_response = requests.post(f'http://localhost:5000/kill_process/{pid}')  # Update the URL
            if kill_process_response.status_code == 200:
                # Termination was successful
                self.process_table.removeRow(selected_row)
            else:
                print(f"Failed to terminate the process: {kill_process_response.status_code}")
        except (ValueError, Exception) as e:
            print(f"Error terminating the process: {e}")

    def kill_selected_process(self):
        selected_items = self.process_table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            pid = self.process_table.item(selected_row, 0).text()
            try:
                pid = int(pid)
                # Use a separate thread to perform process termination
                thread = threading.Thread(target=self.kill_selected_process_async, args=(pid, selected_row))
                thread.start()
            except (ValueError, Exception) as e:
                print(f"Error terminating the process: {e}")
