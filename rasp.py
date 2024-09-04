import os
import logging
import time
from flask import Flask, request, jsonify, render_template_string
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = '/home/pi2/Desktop/pptx_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def terminate_existing_processes():
    # Terminate any existing LibreOffice and VLC instances
    subprocess.call(['pkill', '-f', 'libreoffice'])
    subprocess.call(['pkill', '-f', 'vlc'])
    subprocess.call(['pkill', '-f', 'feh'])

def start_slideshow(file_path):
    try:
        # Terminate any existing instances
        terminate_existing_processes()
        # Start LibreOffice Impress in fullscreen mode with the given file
        subprocess.Popen(['libreoffice', '--impress', '--show', '--norestore', file_path])
    except Exception as e:
        logging.error(f"Failed to start slideshow: {e}")

def play_image(file_path):
    try:
        # Terminate any existing instances
        terminate_existing_processes()
        # Display image using feh
        subprocess.Popen(['feh', '--fullscreen', file_path])
    except Exception as e:
        logging.error(f"Failed to display image: {e}")

def play_video(file_path):
    try:
        # Terminate any existing instances
        terminate_existing_processes()
        # Play video using VLC
        subprocess.Popen(['cvlc', '--fullscreen', '--loop', file_path])
    except Exception as e:
        logging.error(f"Failed to play video: {e}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    # Delete existing files
    for existing_file in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, existing_file))
    file.save(file_path)

    # Call the appropriate function based on file type
    if file.filename.endswith('.pptx'):
        start_slideshow(file_path)
    elif file.filename.endswith(('.jpg', '.jpeg', '.png')):
        play_image(file_path)
    elif file.filename.endswith(('.mp4', '.avi')):
        play_video(file_path)

    return jsonify({'message': 'File uploaded and displayed successfully'}), 200

@app.route('/tv_status', methods=['GET'])
def tv_status():
    try:
        result = os.popen("echo 'pow 0' | cec-client -s -d 1").read()
        if "power status: on" in result.lower():
            status = "on"
        elif "power status: standby" in result.lower() or "power status: off" in result.lower():
            status = "off"
        else:
            status = "unknown"
        return jsonify({'status': status}), 200
    except Exception as e:
        logging.error(f"Error getting TV status: {e}")
        return jsonify({'status': 'unknown'}), 500

@app.route('/current_file', methods=['GET'])
def current_file():
    try:
        files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(('.pptx', '.jpg', '.jpeg', '.png', '.mp4', '.avi'))]
        if files:
            return jsonify({'current_file': files[0]}), 200
        else:
            return jsonify({'current_file': 'None'}), 200
    except Exception as e:
        logging.error(f"Error getting current file: {e}")
        return jsonify({'current_file': 'unknown'}), 500

@app.route('/tv_on', methods=['POST'])
def tv_on():
    try:
        os.system("echo 'on 0.0.0.0' | cec-client -s -d 1")
        time.sleep(1)
        os.system("echo 'as' | cec-client -s -d 1")
        return jsonify({'message': 'TV turned on successfully'}), 200
    except Exception as e:
        logging.error(f"Error turning on TV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/tv_off', methods=['POST'])
def tv_off():
    try:
        os.system("echo 'standby 0' | cec-client -s -d 1")
        return jsonify({'message': 'TV turned off successfully'}), 200
    except Exception as e:
        logging.error(f"Error turning off TV: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/change_hdmi_input', methods=['POST'])
def change_hdmi_input_route():
    data = request.get_json()
    input_number = data.get('input_number')
    try:
        command = f"echo 'tx 4F:82:{input_number:02}' | cec-client -s"
        result = os.system(command)
        if result == 0:
            return jsonify({'message': 'HDMI input changed successfully'}), 200
        else:
            return jsonify({'error': 'Failed to change HDMI input'}), 500
    except Exception as e:
        logging.error(f"Error changing HDMI input: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/delete_remote_file', methods=['POST'])
def delete_remote_file():
    data = request.get_json()
    file_name = data.get('file_name')
    try:
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        os.remove(file_path)
        return jsonify({'message': 'Remote file deleted successfully'}), 200
    except Exception as e:
        logging.error(f"Error deleting remote file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/emergency', methods=['POST'])
def emergency():
    data = request.get_json()
    message = data.get('message')
    try:
        terminate_existing_processes()
        for existing_file in os.listdir(UPLOAD_FOLDER):
            os.remove(os.path.join(UPLOAD_FOLDER, existing_file))

        # Define HTML template within Python code
        html_template = '''
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Emergency Alert</title>
            <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@700&family=Roboto:wght@700&display=swap" rel="stylesheet">
            <style>
                body {
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                    margin: 0;
                    font-family: 'Roboto', 'Noto Sans KR', sans-serif;
                    font-weight: bold;
                    overflow: hidden;
                }
                .top-section {
                    background-color: red;
                    color: white;
                    text-align: center;
                    flex: 65%;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    padding-top: 20px;
                    box-sizing: border-box;
                }
                .bottom-section {
                    background-color: yellow;
                    color: black;
                    text-align: center;
                    flex: 35%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    box-sizing: border-box;
                }
                .icon {
                    width: 30vmin;
                    height: 30vmin;
                }
                .emergency {
                    font-size: 10vmin;
                    margin-top: 10px;
                }
                .message {
                    font-size: 5vmin;
                }
            </style>
        </head>
        <body>
            <div class="top-section">
                <img src="https://static.vecteezy.com/system/resources/previews/016/314/775/non_2x/transparent-warning-free-png.png" alt="Warning Icon" class="icon">
                <div class="emergency">EMERGENCY</div>
            </div>
            <div class="bottom-section">
                <div class="message">{{ message }}</div>
            </div>
        </body>
        </html>
        '''

        # Save HTML to a file
        html_content = render_template_string(html_template, message=message)
        html_file_path = os.path.join(UPLOAD_FOLDER, 'emergency.html')
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Convert HTML file to an image
        image_file_path = os.path.join(UPLOAD_FOLDER, 'emergency.png')
        subprocess.run([
            'wkhtmltoimage', 
            '--width', '1920',  # Set to desired resolution
            '--height', '1080', # Set to desired resolution
            html_file_path, 
            image_file_path
        ])

        # Asynchronously display the image file on the display
        subprocess.Popen(['feh', '--fullscreen', image_file_path])
        return jsonify({'message': 'Emergency message displayed successfully'}), 200
    except Exception as e:
        logging.error(f"Error displaying emergency message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/reboot', methods=['POST'])
def reboot():
    try:
        os.system("sudo reboot")
        return jsonify({'message': 'System rebooting...'}), 200
    except Exception as e:
        logging.error(f"Error rebooting system: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/shutdown', methods=['POST'])
def shutdown():
    try:
        os.system("sudo shutdown -h now")
        return jsonify({'message': 'System shutting down...'}), 200
    except Exception as e:
        logging.error(f"Error shutting down system: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
