from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
import os
import subprocess
import json

app = Flask(__name__)

UPLOAD_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\uploads'
JSON_OUTPUT_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\json_output'
VIDEO_OUTPUT_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\video_output'
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
            openpose_command = f'bin\\OpenPoseDemo.exe --video "{video_path}" --write_json "{json_output_directory}" --frame_step 3 .'

            # コマンドを実行
            print("Executing OpenPose command:", openpose_command)
            subprocess.run(openpose_command, shell=True)

            # カレントディレクトリを元のディレクトリに戻す
            os.chdir(app.root_path)

            return redirect(url_for('result', json_filename='output.json'))

        else:
            flash('Invalid file type')
            return redirect(request.url)


@app.route('/result')
def result():
    json_filename = request.args.get('json_filename', '')

    # JSONデータのパス
    json_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], json_filename)

    return render_template('result.html', json_path=json_path)

if __name__ == '__main__':
    app.run(debug=True)
