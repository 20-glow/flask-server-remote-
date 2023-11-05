import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import requests
import socket
import threading

class ScreenCapture(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Screen Capture')
        self.setGeometry(100, 100, 800, 600)

        self.sharing = False
        self.screenshot = QtGui.QPixmap()
        self.message_label = self.create_label('Ready to Share', alignment=QtCore.Qt.AlignCenter, y=660)

        self.start_button = self.create_button('Start Sharing', self.start_sharing)
        self.stop_button = self.create_button('Stop Sharing', self.stop_sharing)
        self.stop_button.setEnabled(False)

        self.server_url = "http://localhost:5000/start_sharing"  # For starting sharing

        self.update_timer = self.create_timer(self.update_screenshot)
        self.update_timer.start(100)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.message_label)
        self.setLayout(layout)

        self.show()

    def create_label(self, text, alignment, y):
        label = QtWidgets.QLabel(text)
        label.setAlignment(alignment)
        label.setGeometry(10, y, 780, 30)
        return label

    def create_button(self, text, callback):
        button = QtWidgets.QPushButton(text)
        button.clicked.connect(callback)
        return button

    def create_timer(self, callback):
        timer = QtCore.QTimer(self)
        timer.timeout.connect(callback)
        return timer

    def start_sharing(self):
        self.sharing = True
        self.message_label.setText('Sharing...')
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Start a new thread to handle the HTTP request
        t = threading.Thread(target=self.send_start_request)
        t.start()

    def send_start_request(self):
        # Send an HTTP POST request to the Flask server when starting sharing
        try:
            response = requests.post(self.server_url, data={'action': 'start_sharing'})
            if response.status_code == 200:
                print("Sharing started successfully.")
            else:
                print("Failed to start sharing.")
        except requests.exceptions.RequestException as e:
            print("Error sending request:", e)

    def stop_sharing(self):
        self.sharing = False
        self.message_label.setText('Not Sharing')
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        # Start a new thread to handle the HTTP request
        t = threading.Thread(target=self.send_stop_request)
        t.start()

    def send_stop_request(self):
        # Send an HTTP POST request to the Flask server when stopping sharing
        try:
            response = requests.post(self.server_url, data={'action': 'stop_sharing'})
            if response.status_code == 200:
                print("Sharing stopped successfully.")
            else:
                print("Failed to stop sharing.")
        except requests.exceptions.RequestException as e:
            print("Error sending request:", e)

    def update_screenshot(self):
        if self.sharing:
            screen = QtWidgets.QApplication.primaryScreen()
            screenshot = screen.grabWindow(0)
            screenshot = screenshot.scaled(self.size(), QtCore.Qt.KeepAspectRatio)
            self.screenshot = screenshot
            self.repaint()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.screenshot)

