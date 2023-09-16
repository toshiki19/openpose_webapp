from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
import os
import subprocess
import json

app = Flask(__name__)

UPLOAD_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\uploads'
JSON_OUTPUT_FOLDER = 'json_output'
VIDEO_OUTPUT_FOLDER = 'video_output'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_OUTPUT_FOLDER'] = JSON_OUTPUT_FOLDER
app.config['VIDEO_OUTPUT_FOLDER'] = VIDEO_OUTPUT_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['JSON_OUTPUT_FOLDER']):
    os.makedirs(app.config['JSON_OUTPUT_FOLDER'])

if not os.path.exists(app.config['VIDEO_OUTPUT_FOLDER']):
    os.makedirs(app.config['VIDEO_OUTPUT_FOLDER'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file:
        if allowed_file(file.filename):
            # アップロードされた動画を保存
            video_filename = secure_filename(file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
            file.save(video_path)

        # 以降の処理で video_path を使用できます

        else:
            flash('Invalid file type')
            return redirect(request.url)
        
        # video_path = "C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\uploads\\video.avi" # ここで video_path を定義す

            # カレントディレクトリをOpenPoseのディレクトリに変更
        openpose_directory = r'C:\\openpose-1.7.0-binaries-win64-gpu-python3.7-flir-3d_recommended\\openpose'
        os.chdir(openpose_directory)


        # JSON出力の保存先を設定
        json_output_directory = os.path.join(app.config['JSON_OUTPUT_FOLDER'], 'output')
        if not os.path.exists(json_output_directory):
            os.makedirs(json_output_directory)
        
        # JSON出力ファイルのパスを設定
        json_output_path = os.path.join(json_output_directory, 'output.json')
    
        # OpenPoseの実行コマンド
        openpose_command = f'bin\\OpenPoseDemo.exe --video "{video_path}" --write_json "{json_output_directory}" .'
    
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
    
        # 動画ファイルのパスを設定
    video_path = os.path.join(app.config['VIDEO_OUTPUT_FOLDER'], video_filename)

    return render_template('result.html', video_filename=video_filename, json_data=json_data)

if __name__ == '__main__':
    app.run(debug=True)
