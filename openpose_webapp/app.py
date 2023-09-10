from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import subprocess
import json

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
JSON_OUTPUT_FOLDER = 'json_output'
VIDEO_OUTPUT_FOLDER = 'video_output'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_OUTPUT_FOLDER'] = JSON_OUTPUT_FOLDER
app.config['VIDEO_OUTPUT_FOLDER'] = VIDEO_OUTPUT_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    #if 'video' not in request.files:
        #return redirect(request.url)
    
    #video_file = request.files['video']
    #if video_file.filename == '':
        #return redirect(request.url)
    
    #if video_file and allowed_file(video_file.filename):
        # アップロードされた動画を保存
        # video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
        # video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'video.avi')
        video_path = "C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\uploads\\video.avi" # ここで video_path を定義する
        #video_file.save(video_path)

        output_directory = os.path.join(app.config['JSON_OUTPUT_FOLDER'], 'output')
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
    
        json_output_path = os.path.join(output_directory, 'output.json')
        video_output_path = os.path.join(app.config['VIDEO_OUTPUT_FOLDER'], 'output.mp4')

        # カレントディレクトリをOpenPoseのディレクトリに変更
        openpose_directory = r'C:\\openpose-1.7.0-binaries-win64-gpu-python3.7-flir-3d_recommended\\openpose'
        os.chdir(openpose_directory)
        
        # OpenPoseの実行コマンド（パスはエスケープ文字を含む）
        #openpose_command = f'bin\\OpenPoseDemo.exe --video "{video_path}" --write_json "{json_output_path}" --write_video "{video_output_path}" .'
        openpose_command = f'bin\\OpenPoseDemo.exe --video "{video_path}" --write_json "{output_directory}" .'
        
        # コマンドを実行
        print("Executing OpenPose command:", openpose_command)
        subprocess.run(openpose_command, shell=True)
        
        return redirect(url_for('result', video_filename='output.mp4', json_filename='output.json'))
    
@app.route('/result')
def result():
    video_filename = request.args.get('video_filename', '')
    json_filename = request.args.get('json_filename', '')
    
    # JSONデータを読み込む
    json_data = {}
    json_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], json_filename)
    if os.path.exists(json_path):
        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file)
    
    return render_template('result.html', video_filename=video_filename, json_data=json_data)

if __name__ == '__main__':
    app.run(debug=True)
