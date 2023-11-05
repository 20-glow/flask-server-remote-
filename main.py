import json
import sys
import socket
import asyncio
import threading
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QComboBox,
    QListWidget, QListWidgetItem, QDesktopWidget, QTextEdit, QMainWindow, QTabWidget, QApplication, QMessageBox
)
import pyqtgraph as pg
import requests
import platform
import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer, pyqtSignal, QThread
import pyautogui
from PyQt5.QtGui import QPixmap
import socket
import requests
from PyQt5.QtWidgets import QMessageBox, QListWidget, QComboBox, QTextEdit, QListWidgetItem
import asyncio

from process_manager import ProcessManager
from capture import ScreenCapture
from run_process import ResourceOpener
from utils import scan_servers, connect_to_selected_server, check_port, show_error

class NetworkThread(QThread):
    data_received = pyqtSignal(dict)

    def __init__(self, selected_server):
        super().__init__()
        self.selected_server = selected_server

    def run(self):
        try:
            response = requests.get(f'http://{self.selected_server}:5000/system_info')
            response.raise_for_status()

            system_info = response.json()
            self.data_received.emit(system_info)
        except requests.exceptions.RequestException as e:
            self.data_received.emit({'error': f"Error fetching data from the server: {e}"})
        except Exception as e:
            self.data_received.emit({'error': f"An unexpected error occurred: {e}"})

class ServerScan(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a tab widget to hold multiple tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.setWindowTitle('Client-Server Control')
     
        # Center the application window on the screen
        self.center()

        # Add a boolean variable to keep track of the scan process status
        self.scan_process_frozen = False

    def center(self):
        # Get the application's main screen
        screen = QDesktopWidget().screenGeometry()

        # Calculate the center position
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2

        # Move the application window to the center
        self.move(x, y)

        # Create the "Server Scan" tab
        self.server_scan_tab = QWidget()
        self.tabs.addTab(self.server_scan_tab, "Server Scan")
        self.create_server_scan_tab()

       
        # Hide the "Screen Sharing" tab initially
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.tabs.setTabEnabled(3, False)
        self.tabs.setTabEnabled(4, False)

        self.cpu_data = []
        self.memory_data = []
        self.disk_data = []
        self.time_data = []

        self.cpu_curve = pg.PlotWidget(title="CPU Usage")
        self.memory_curve = pg.PlotWidget(title="Memory Usage")
        self.disk_curve = pg.PlotWidget(title="Disk Usage")

        self.system_info_layout.addWidget(self.cpu_curve)
        self.system_info_layout.addWidget(self.memory_curve)
        self.system_info_layout.addWidget(self.disk_curve)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(1000)

        # Create the network thread
        self.network_thread = NetworkThread("")
        self.network_thread.data_received.connect(self.handle_network_data)

    def create_system_info_section(self):
        self.device_label = QLabel(f"Device Name: {platform.node()}", self)
        self.os_label = QLabel(f"Operating System: {platform.system()}", self)
        self.processor_label = QLabel(f"Processor: {platform.processor()}", self)
        self.release_label = QLabel(f"Release: {platform.release()}", self)
        self.version_label = QLabel(f"Version: {platform.version()}", self)
        self.architecture_label = QLabel(f"Architecture: {platform.architecture()[0]}", self)

        self.pie_chart = plt.figure(figsize=(6, 6))
        self.pie_axes = self.pie_chart.add_subplot(111)

        self.cpu_label = QLabel("CPU Usage: N/A", self)
        self.memory_label = QLabel("Memory Usage: N/A", self)
        self.disk_label = QLabel("Disk Usage: N/A", self)

        self.system_info_layout.addWidget(self.device_label)
        self.system_info_layout.addWidget(self.os_label)
        self.system_info_layout.addWidget(self.processor_label)
        self.system_info_layout.addWidget(self.release_label)
        self.system_info_layout.addWidget(self.version_label)
        self.system_info_layout.addWidget(self.architecture_label)
        self.system_info_layout.addWidget(self.pie_chart.canvas)
        self.system_info_layout.addWidget(self.cpu_label)
        self.system_info_layout.addWidget(self.memory_label)
        self.system_info_layout.addWidget(self.disk_label)

    def update_system_info(self):
        try:
            selected_server = self.server_combo.currentText()
            if not selected_server:
                return

            # Replace '{selected_server}' with the actual server address
            response = requests.get(f'http://{selected_server}:5000/system_info')
            response.raise_for_status()

            system_info = response.json()
            cpu_percent = system_info.get('CPU Percent', 'N/A')
            memory_percent = system_info.get('Memory Percent', 'N/A')
            disk_percent = system_info.get('Disk Percent', 'N/A')

            self.cpu_label.setText(f"CPU Usage: {cpu_percent}")
            self.memory_label.setText(f"Memory Usage: {memory_percent}")
            self.disk_label.setText(f"Disk Usage: {disk_percent}")

            if cpu_percent != 'N/A' and memory_percent != 'N/A':
                self.cpu_data.append(cpu_percent)
                self.memory_data.append(memory_percent)
                self.disk_data.append(disk_percent)
                self.time_data.append(len(self.time_data) + 1)

                self.cpu_curve.plot(self.time_data, self.cpu_data, pen='b')
                self.memory_curve.plot(self.time_data, self.memory_data, pen='g')
                self.disk_curve.plot(self.time_data, self.disk_data, pen='r')

                self.cpu_curve.setYRange(0, max(self.cpu_data) + 10)
                self.memory_curve.setYRange(0, max(self.memory_data) + 10)
                self.disk_curve.setYRange(0, max(self.disk_data) + 10)

                self.pie_axes.clear()
                usage_data = [cpu_percent, memory_percent]
                usage_labels = ['CPU', 'Memory']
                self.pie_axes.pie(usage_data, labels=usage_labels, autopct='%1.1f%%', startangle=140)
                self.pie_axes.axis('equal')
                self.pie_chart.canvas.draw()

                if len(self.time_data) > 60:
                    self.time_data.pop(0)
                    self.cpu_data.pop(0)
                    self.memory_data.pop(0)
                    self.disk_data.pop(0)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from the server: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

            
    def create_server_scan_tab(self):
        # Create a layout for the "Server Scan" tab
        layout = QVBoxLayout()

        # Add form layout
        form_layout = QFormLayout()

        self.start_ip_label = QLabel('Start IP:')
        self.start_ip_input = QLineEdit()
        form_layout.addRow(self.start_ip_label, self.start_ip_input)

        self.end_ip_label = QLabel('End IP:')
        self.end_ip_input = QLineEdit()
        form_layout.addRow(self.end_ip_label, self.end_ip_input)

        self.scan_btn = QPushButton('Scan Servers')
        self.scan_btn.clicked.connect(self.scan_servers)
        form_layout.addRow('', self.scan_btn)

        # Create a combo box to choose from available servers
        self.server_combo = QComboBox()
        form_layout.addRow('Select Server:', self.server_combo)

        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.connect_to_selected_server)
        form_layout.addRow('', self.connect_btn)

        # Create a "Freeze Scan" button and connect it to a function
        self.freeze_scan_btn = QPushButton('Freeze Scan')
        self.freeze_scan_btn.clicked.connect(self.freeze_scan_process)
        form_layout.addRow('', self.freeze_scan_btn)

        # Set form layout as the central layout for the widget
        layout.addLayout(form_layout)

        # Add result text box
        self.result_text = QListWidget()
        layout.addWidget(self.result_text)

        # Set the layout for the "Server Scan" tab
        self.server_scan_tab.setLayout(layout)
        
        # Create the "System Info" tab (hidden initially)
        self.system_info_tab = QWidget()
        self.system_info_layout = QVBoxLayout()
        self.system_info_text = QLabel()
        self.system_info_layout.addWidget(self.system_info_text)
        self.system_info_tab.setLayout(self.system_info_layout)
        self.tabs.addTab(self.system_info_tab, "System Info")
        self.create_system_info_section()
        # Create the "Screen Sharing" tab
        self.screen_sharing_tab = ScreenCapture()
        self.tabs.addTab(self.screen_sharing_tab, "Screen Sharing")

        # Create the "Process Manager" tab
        self.process_manager_tab = ProcessManager()
        self.tabs.addTab(self.process_manager_tab, "Process Manager")
       
        # Create the "Resource Opener" tab
        self.run_process_tab = ResourceOpener()
        self.tabs.addTab(self.run_process_tab, "Run Process")

    def handle_network_data(self, data):
        if 'error' in data:
            print(data['error'])  # Handle errors appropriately
        else:
            self.system_info_text.setText(json.dumps(data, indent=4))

    # Add the function to freeze the scan process
    def freeze_scan_process(self):
        self.scan_process_frozen = not self.scan_process_frozen

    def scan_servers(self):
        # Clear previous results
        self.result_text.clear()
        self.server_combo.clear()

        # Disable the "Scan Servers" button
        self.scan_btn.setEnabled(False)

        start_ip = self.start_ip_input.text()
        end_ip = self.end_ip_input.text()

        # Create a new thread for scanning servers
        thread = threading.Thread(target=self.perform_server_scan, args=(start_ip, end_ip))
        thread.start()

    def perform_server_scan(self, start_ip, end_ip):
        try:
            # Disable the "Connect" button before starting the scan
            self.connect_btn.setEnabled(False)

            # Display "Please wait..." in the IPs list
            item = QListWidgetItem("Please wait...")
            self.result_text.addItem(item)

            for ip in range(int(start_ip.split('.')[-1]), int(end_ip.split('.')[-1]) + 1):
                if self.scan_process_frozen:  # Check if the scan process is frozen
                    break

                current_ip = f"{start_ip.rsplit('.', 1)[0]}.{ip}"
                result = asyncio.run(scan_servers(current_ip, current_ip, self.check_port, self.result_text, self.server_combo))

            # Replace "Please wait..." with "Scan process completed"
            item.setText("Scan process completed:")

            # Re-enable the "Scan Servers" button when the scan is finished
            self.scan_btn.setEnabled(True)

            # Re-enable the "Connect" button when the scan is finished
            self.connect_btn.setEnabled(True)
        except ValueError:
            show_error('Invalid Input', 'Please enter valid IP addresses.')
        except socket.error as e:
            show_error('Socket Error', f'Socket error occurred: {e}')
        except Exception as e:
            show_error('Error', str(e))

    def check_port(self, ip, port):
        return check_port(ip, port)

    def connect_to_selected_server(self):
        selected_server = self.server_combo.currentText()
        if not selected_server:
            show_error('Error', 'No server selected.')
            return

        try:
            # Clear any previous text in the system_info_text
            self.system_info_text.clear()

            # Display "Please wait..." in the system_info_text
            self.system_info_text.setText("Please wait...")

            connect_to_selected_server(selected_server, self.system_info_text, self.tabs)

            # Replace "Please wait..." with "Connect process completed"
            self.system_info_text.setText(f'Connected to server: {selected_server} ')

            # Enable the "Screen Sharing" tab
            self.tabs.setTabEnabled(2, True)
            # Enable the "Process Manager" tab
            self.tabs.setTabEnabled(3, True)
            # Enable the "Resource Opener" tab
            self.tabs.setTabEnabled(4, True)
        except ConnectionRefusedError:
            show_error('Connection Refused', 'Connection was refused by the server.')
        except TimeoutError:
            show_error('Connection Timeout', 'Connection to the server timed out.')
        except Exception as e:
            show_error('Connection Error', f'Failed to connect to {selected_server}: {str(e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ServerScan()
    main_window.show()
    sys.exit(app.exec_())
