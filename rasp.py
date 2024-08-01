import os
import logging
import time
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import subprocess


app = Flask(__name__)
UPLOAD_FOLDER = '/home/pi1/Desktop/pptx_files'
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
  # 기존 파일 삭제
  for existing_file in os.listdir(UPLOAD_FOLDER):
      os.remove(os.path.join(UPLOAD_FOLDER, existing_file))
  file.save(file_path)


  # 파일 유형에 따라 적절한 함수를 호출
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
      # 기존 파일 삭제
      for existing_file in os.listdir(UPLOAD_FOLDER):
          os.remove(os.path.join(UPLOAD_FOLDER, existing_file))
      # 이미지 파일 생성
      emergency_file_path = os.path.join(UPLOAD_FOLDER, 'emergency.png')
      img = Image.new('RGB', (1920, 1080), color=(255, 0, 0))
      d = ImageDraw.Draw(img)
      font_size = 100
      font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
      font = ImageFont.truetype(font_path, font_size)
      text = f"Emergency: {message}"
      text_width, text_height = d.textsize(text, font=font)
      position = ((img.width - text_width) / 2, (img.height - text_height) / 2)
      d.text(position, text, fill=(255, 255, 255), font=font)
      img.save(emergency_file_path)
      # 이미지 파일을 디스플레이에 표시
      subprocess.Popen(['feh', '--fullscreen', emergency_file_path])
      return jsonify({'message': 'Emergency message displayed successfully'}), 200
  except Exception as e:
      logging.error(f"Error displaying emergency message: {e}")
      return jsonify({'error': str(e)}), 500


@app.route('/reboot', methods=['POST'])
def reboot():
  try:
      os.system("sudo reboot")
      return jsonify({'message': 'Reboot initiated successfully'}), 200
  except Exception as e:
      logging.error(f"Error initiating reboot: {e}")
      return jsonify({'error': str(e)}), 500


@app.route('/shutdown', methods=['POST'])
def shutdown():
  try:
      os.system("sudo shutdown now")
      return jsonify({'message': 'Shutdown initiated successfully'}), 200
  except Exception as e:
      logging.error(f"Error initiating shutdown: {e}")
      return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
  ## LEt's test it out ! 
  ## Let's test morder!
  ## HELo check this out ! 
  ## Hello !
  ## dddd...
  ##????
  ## let's hope it works
  # plz ! 
  #  plz! ! 
  # plz ! 
  # FKUNHEE HWANG
  # This is actually fun ! 
  # Fuck you Thunder ! 
  
  app.run(debug=True, host='0.0.0.0', port=5001)