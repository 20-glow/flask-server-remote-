import sys
import requests
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFileDialog, QLabel, QLineEdit, QPushButton, QWidget, QTextBrowser, QMessageBox

class ResourceOpener(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Resource Opener')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        label = QLabel('Type the name of a program, folder, document, or internet resource, and Windows will open it for you.')
        self.input_box = QLineEdit()
        self.browse_button = QPushButton('Browse')
        self.open_button = QPushButton('Open')
        self.result_display = QTextBrowser()

        layout.addWidget(label)
        layout.addWidget(self.input_box)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.open_button)
        layout.addWidget(self.result_display)

        self.browse_button.clicked.connect(self.browse_folder)
        self.open_button.clicked.connect(self.open_resource)

        self.shutdown_button = QPushButton('Shutdown Server')
        self.restart_button = QPushButton('Restart Server')

        layout.addWidget(self.shutdown_button)
        layout.addWidget(self.restart_button)

        self.shutdown_button.clicked.connect(self.threaded_shutdown_server)
        self.restart_button.clicked.connect(self.threaded_restart_server)

        central_widget.setLayout(layout)

    def browse_folder(self):
        folder_dialog = QFileDialog()
        selected_folder = folder_dialog.getExistingDirectory(self, 'Select a folder')
        if selected_folder:
            self.input_box.setText(selected_folder)

    def open_resource(self):
        resource = self.input_box.text()
        self.result_display.clear()

        if not resource:
            # Show an error message if the input is empty
            self.display_error_message("Please type or select a resource.")
            return

        def open_resource_async():
            server_url = 'http://localhost:5000/open_resource'  # Replace with your server URL
            try:
                response = requests.post(server_url, json={'resource': resource})
                if response.status_code == 200:
                    self.result_display.append(response.json()['message'])
                else:
                    self.result_display.append(f"Server returned an error: {response.status_code}")
            except Exception as e:
                self.result_display.append(f"Error: {e}")

        # Run the resource opening function in a separate thread
        thread = threading.Thread(target=open_resource_async)
        thread.start()

    def display_error_message(self, message):
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setText(message)
        error_msg.setWindowTitle("Error")
        error_msg.exec_()

    def handle_shutdown_response(self, response):
        if response.status_code == 200:
            self.result_display.append(response.text)
        else:
            self.display_error_message(f"Server returned an error: {response.status_code}")

    def handle_restart_response(self, response):
        if response.status_code == 200:
            self.result_display.append(response.text)
        else:
            self.display_error_message(f"Server returned an error: {response.status_code}")

    def threaded_shutdown_server(self):
        server_url = 'http://localhost:5000/shutdown'  # Replace with your server's actual URL
        self.result_display.clear()

        def perform_shutdown():
            try:
                response = requests.get(server_url)
                self.handle_shutdown_response(response)
            except requests.exceptions.RequestException as e:
                self.display_error_message(f"Request Error: {e}")

        threading.Thread(target=perform_shutdown).start()

    def threaded_restart_server(self):
        server_url = 'http://localhost:5000/restart'  # Replace with your server's actual URL
        self.result_display.clear()

        def perform_restart():
            try:
                response = requests.get(server_url)
                self.handle_restart_response(response)
            except requests.exceptions.RequestException as e:
                self.display_error_message(f"Request Error: {e}")

        threading.Thread(target=perform_restart).start()  
