import os
import socket
import subprocess
import sys
import psutil
import requests
from flask import Flask, Response, render_template, request, jsonify, make_response, send_file
import socket

app = Flask(__name__)

@app.route('/system_info', methods=['GET'])
def get_system_info():
    # Get system information using psutil
    cpu_percent = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')

    system_info = {
        'CPU Percent': cpu_percent,
        'Memory Percent': memory_info.percent,
        'Disk Percent': disk_info.percent
    }

    return jsonify(system_info)

@app.route('/list_processes', methods=['GET'])
def list_processes():
    try:
        process_list = []
        for process in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_info"]):
            process_info = {
                "PID": process.info["pid"],
                "Name": process.info["name"],
                "CPU Percent": process.info["cpu_percent"],
                "Memory (MB)": process.info["memory_info"].rss / (1024 * 1024)  # Convert to MB
            }
            process_list.append(process_info)

        return jsonify(process_list)
    except Exception as e:
        return jsonify({"error": f"Error listing processes: {str(e)}"})

@app.route('/kill_process/<int:pid>', methods=['POST'])
def kill_process(pid):
    try:
        process = psutil.Process(pid)
        process.kill()
        return jsonify({"status": "Process terminated"})
    except psutil.NoSuchProcess:
        return jsonify({"error": f"Process with PID {pid} not found"})
    except Exception as e:
        return jsonify({"error": f"Error terminating the process: {str(e)}"})

screen_sharing = False
@app.route('/start_sharing', methods=['POST'])
def start_sharing():
    global screen_sharing
    if request.method == 'POST':
        if not screen_sharing:
            screen_sharing = True
            return "Screen sharing started", 200
        else:
            return "Screen sharing is already in progress", 400

@app.route('/stop_sharing', methods=['POST'])
def stop_sharing():
    global screen_sharing
    if request.method == 'POST':
        if screen_sharing:
            screen_sharing = False
            return "Screen sharing stopped", 200
        else:
            return "Screen sharing is not active", 400
        

@app.route('/open_resource', methods=['POST'])
def open_resource():
    data = request.get_json()
    resource = data.get('resource')
    try:
        subprocess.Popen(['start', resource], shell=True)
        return jsonify({'status': 'success', 'message': f'Opened resource: {resource}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {e}'})

@app.route('/shutdown', methods=['GET'])
def shutdown_server():
    try:
        if sys.platform == 'win32':
            os.system('shutdown /s /f /t 0')
        else:
            os.system('shutdown -h now')
        return jsonify({'status': 'success', 'message': 'Server is shutting down...'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {e}'})

@app.route('/restart', methods=['GET'])
def restart_server():
    try:
        if sys.platform == 'win32':
            os.system('shutdown /r /f /t 0')
        else:
            os.system('shutdown -r now')
        return jsonify({'status': 'success', 'message': 'Server is restarting...'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {e}'})
    
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search_servers", methods=["POST"])
def search_servers():
    port = 5000  # Port 5000
    server = f"Server at Port {port}"
    try:
        socket.create_connection(('localhost', port), timeout=1)
        server += " - Online"
    except ConnectionRefusedError:
        server += " - Offline"
    except Exception as e:
        server += f" - Error: {str(e)}"
    return jsonify({"server_status": server})

@app.route("/connect_to_server", methods=["POST"])
def connect_to_server():
    global screen_sharing
    try:
        socket.create_connection(('localhost', 5000), timeout=1)

        response = requests.get('http://{selected_server}:5000/system_info')
        response.raise_for_status()
        system_info = response.json()

        list_processes_response = requests.get('http://{selected_server}:5000/list_processes')
        list_processes_response.raise_for_status()
        list_processes_data = list_processes_response.json()

        kill_process_response = requests.post('http://{selected_server}:5000/kill_process/<int:pid>')
        kill_process_response.raise_for_status()
        kill_process_data = kill_process_response.json()

        # Include the run_process result in the response
        run_process_response = requests.post('http://{selected_server}:5000/open_resource')
        run_process_response.raise_for_status()
        run_process_data = run_process_response.json()

        shutdown_process_response = requests.get('http://{selected_server}:5000/shutdown')
        shutdown_process_response.raise_for_status()
        shutdown_process = shutdown_process_response.json()

        restart_process_response = requests.get('http://{selected_server}:5000/restart')
        restart_process_response.raise_for_status()
        restart_process = restart_process_response.json()


        # Check for the 'action' parameter in the request data
        if 'action' in request.form:
            action = request.form['action']

            if action == 'start_sharing':
                # Handle starting screen sharing
                if not screen_sharing:
                    screen_sharing = True
                    return jsonify({"status": "Screen Sharing Started"})
                else:
                    return jsonify({"status": "Error", "message": "Screen sharing is already in progress"})

            elif action == 'stop_sharing':
                # Handle stopping screen sharing
                if screen_sharing:
                    screen_sharing = False
                    return jsonify({"status": "Screen Sharing Stopped"})
                else:
                    return jsonify({"status": "Error", "message": "Screen sharing is not active"})

        return jsonify({
            "status": "Connected",
            "system_info": system_info,
            "list_processes_data": list_processes_data,
            "kill_process_data": kill_process_data,
            "run_process_data": run_process_data
        })
    except ConnectionRefusedError:
        return jsonify({"status": "Error", "message": "Server at port 5000 is offline"})
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "Error", "message": f"Failed to fetch data: {str(e)}"})
    except Exception as e:
        return jsonify({"status": "Error", "message": f"Error: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
