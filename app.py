from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
import os
import subprocess
import json
import numpy as np
import cv2  # OpenCVをインポート

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
            video_filename_with_extension = secure_filename(file.filename)
            video_filename, extension = os.path.splitext(video_filename_with_extension)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename_with_extension)
            file.save(video_path)

            # カレントディレクトリをOpenPoseのディレクトリに変更
            openpose_directory = r'C:\\openpose-1.7.0-binaries-win64-gpu-python3.7-flir-3d_recommended\\openpose'
            os.chdir(openpose_directory)

            # JSON出力の保存先を設定
            json_output_directory = os.path.join(app.config['JSON_OUTPUT_FOLDER'])
            if not os.path.exists(json_output_directory):
                os.makedirs(json_output_directory)

            # JSON出力ファイルのパスを設定
            json_output_path = os.path.join(json_output_directory)

            # OpenPoseの実行コマンド
            # openpose_command = f'bin\\OpenPoseDemo.exe --video "{video_path}" --write_json "{json_output_path}" --frame_step 3 .'
            openpose_command = f'bin\\OpenPoseDemo.exe --video "{video_path}" --write_json "{json_output_path}" .'


            # コマンドを実行
            print("Executing OpenPose command:", openpose_command)
            subprocess.run(openpose_command, shell=True)

            # カレントディレクトリを元のディレクトリに戻す
            os.chdir(app.root_path)

            # 動画の分割と新しい動画の作成
            start_frame = 10
            end_frame = 100
            new_video_filename = f"{video_filename}_output{extension}"
            new_video_path = os.path.join(app.config['VIDEO_OUTPUT_FOLDER'], new_video_filename)
            create_new_video(video_path, new_video_path, start_frame, end_frame)

            return redirect(url_for('result', video_filename=new_video_filename))



        else:
            flash('Invalid file type')
            return redirect(request.url)


def create_new_video(input_video_path, output_video_path, start_frame, end_frame):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 30, (frame_width, frame_height))
    
    frame_number = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_number += 1

        if frame_number >= start_frame and frame_number <= end_frame:
            out.write(frame)

    cap.release()
    out.release()
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_number += 1

        if frame_number >= start_frame and frame_number <= end_frame:
            out.write(frame)

    # 最後に out.release() で動画を閉じます
    out.release()

@app.route('/result')
def result():
    video_filename = request.args.get('video_filename', '')

    # 動画ファイルのパスを設定
    video_path = os.path.join(app.config['VIDEO_OUTPUT_FOLDER'], video_filename)

    if not os.path.exists(video_path):
        return "Video not found."

    # 動画ファイルの拡張子を取得
    video_extension = os.path.splitext(video_filename)[-1].lstrip('.')

    # video_urlを正しく生成
    video_url = url_for('static', filename=f'video_output/{video_filename}')

    # ログを出力
    print("Video URL:", video_url)
    print("Video Extension:", video_extension)
    
    return render_template('result.html', video_url=video_url, video_extension=video_extension)


if __name__ == '__main__':
    app.run(debug=True)

    