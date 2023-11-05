import socket
import requests
from PyQt5.QtWidgets import QMessageBox, QListWidget, QComboBox, QTextEdit, QListWidgetItem
from PyQt5.QtGui import QColor
import asyncio

from process_manager import ProcessManager
from capture import ScreenCapture
from run_process import ResourceOpener
async def check_port_function(ip, port):
    try:
        reader, writer = await asyncio.open_connection(ip, port)
        # If the connection was successful, the port is open
        writer.close()
        await writer.wait_closed()
        return True
    except (ConnectionRefusedError, asyncio.TimeoutError):
        # If the connection was refused or timed out, the port is closed
        return False
    except Exception as e:
        # Handle other exceptions as needed
        print(f"An error occurred while checking port {port} on {ip}: {str(e)}")
        return False
    
# Define function to scan servers takes 5 parameters.
async def scan_servers(start_ip, end_ip, check_port_function, result_text_widget, server_combo_widget):
    try:
        # Split start_ip and end_ip from strings into lists of integers
        start_ip_parts = list(map(int, start_ip.split('.')))
        end_ip_parts = list(map(int, end_ip.split('.')))

        async def check_and_add(ip):
            status = await check_port_function(ip, 5000)
            item = QListWidgetItem(f"IP:{ip} - {'Alive' if status else 'Dead'}")
            
            # Set text color based on status
            color = QColor("green" if status else "red")
            item.setForeground(color)

            result_text_widget.addItem(item)
            if status:
                server_combo_widget.addItem(ip)

        async def scan_ip_range(start_i, end_i, start_j, end_j):
            for i in range(start_i, end_i + 1):
                for j in range(start_j if i == start_i else 0, end_j + 1 if i == end_i else 255 + 1):
                    ip = f"{start_ip_parts[0]}.{start_ip_parts[1]}.{i}.{j}"
                    await check_and_add(ip)

        # Determine the ranges for the third and fourth parts of the IP address
        start_i = start_ip_parts[2]
        end_i = end_ip_parts[2]
        start_j = start_ip_parts[3]
        end_j = end_ip_parts[3]

        # Scan the specified IP range
        await scan_ip_range(start_i, end_i, start_j, end_j)

    except Exception as e:
        # Handle exceptions here
        print(f"An error occurred: {str(e)}")


# Create function to check the port and IP address
async def check_port(ip, port):
    try:
        # TCP connections
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = await asyncio.to_thread(sock.connect_ex, (ip, port))
        sock.close()
        # If the connection of ip and port is successful using connect_ex method return 0
        return result == 0
    except Exception:
        return False

# Create function to select IP server and connect with and enable system info tab.
def connect_to_selected_server(selected_server, system_info_text_widget, tabs_widget):
    try:
        # Clear any previous text in the system_info_text_widget
        system_info_text_widget.clear()

        # Create a socket and connect to the selected server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((selected_server, 5000))
        sock.close()

        QMessageBox.information(None, 'Connection Status', f'Connected to {selected_server}')
        
        # Fetch and display system information in the "System Info" tab
        response = requests.get(f'http://{selected_server}:5000/system_info')
        response.raise_for_status()  # Check for HTTP error
        system_info = response.text
        system_info_text_widget.setText(system_info)

        # Enable the "System Info" tab
        tabs_widget.setTabEnabled(1, True)
        tabs_widget.setCurrentIndex(1)

        capture = ScreenCapture(selected_server)
        start_sharing_url = (f'http://{selected_server}:5000/start_sharing')
        start_sharing_response = requests.post(start_sharing_url)
        start_sharing_response.raise_for_status()
        # Handle the response from the start sharing request
        if start_sharing_response.status_code == 200:
            QMessageBox.information(None, 'Screen Sharing', 'Screen sharing started successfully')
        else:
            QMessageBox.critical(None, 'Screen Sharing Error', 'Failed to start screen sharing')
       
        stop_sharing_url = (f'http://{selected_server}:5000/stop_sharing')
        stop_sharing_response = requests.post(stop_sharing_url)
        stop_sharing_response.raise_for_status()
        if stop_sharing_response.status_code == 200:
            QMessageBox.information(None, 'Screen Sharing', 'Screen sharing stopped successfully')
        else:
            QMessageBox.critical(None, 'Screen Sharing Error', 'Failed to stop screen sharing')

        # Create a ProcessManager instance
        process_manager = ProcessManager(selected_server)
        # Fetch and display the list of processes
        list_processes_url = (f'http://{selected_server}:5000/list_processes')
        list_processes_response = requests.get(list_processes_url)
        list_processes_response.raise_for_status()
        # Update the process table with the fetched data
        process_manager.update_table(list_processes_response.json())

        kill_process_url = (f'http://{selected_server}:5000/kill_process/<int:pid>')
        kill_process_response = requests.post(kill_process_url) 
        kill_process_response.raise_for_status()
        process_manager.removeRow(kill_process_response.json())
        
        run_process = ResourceOpener(selected_server)
        run_process_url = ('http://{selected_server}:5000/open_resource')
        run_process_response = requests.post(run_process_url)
        run_process_response.raise_for_status()
    
        shutdown_process_url = ('http://{selected_server}:5000/shutdown')
        shutdown_process_response = requests.get(shutdown_process_url)
        shutdown_process_response.raise_for_status()

        restart_process_url = ('http://{selected_server}:5000/restart')
        restart_process_response = requests.get(restart_process_url)
        restart_process_response.raise_for_status()

    except Exception as e:
        # Handle exceptions here
        print(f"An error occurred: {str(e)}")


def show_error(title, message):
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setWindowTitle(title)
    error_dialog.setText(message)
    error_dialog.exec_()
