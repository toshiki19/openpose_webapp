from flask import Flask, render_template, request, redirect, url_for, send_file, flash, send_file
from werkzeug.utils import secure_filename
import os
import subprocess
import json
import numpy as np
import cv2  # OpenCVをインポート
import shutil

app = Flask(__name__)

UPLOAD_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\uploads'
JSON_OUTPUT_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\json_output'
VIDEO_OUTPUT_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\static\\video_output'
OUTPUT_MOVIES_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\static\\output_movies'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JSON_OUTPUT_FOLDER'] = JSON_OUTPUT_FOLDER
app.config['VIDEO_OUTPUT_FOLDER'] = VIDEO_OUTPUT_FOLDER
app.config['OUTPUT_MOVIES_FOLDER'] = OUTPUT_MOVIES_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['JSON_OUTPUT_FOLDER']):
    os.makedirs(app.config['JSON_OUTPUT_FOLDER'])

if not os.path.exists(app.config['VIDEO_OUTPUT_FOLDER']):
    os.makedirs(app.config['VIDEO_OUTPUT_FOLDER'])

if not os.path.exists(app.config['OUTPUT_MOVIES_FOLDER']):
    os.makedirs(app.config['OUTPUT_MOVIES_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# def create_new_video(input_video_path, output_video_path, start_frame, end_frame):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # H.264コーデックを指定して新しい動画を作成
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

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

def create_new_video(input_video_path, output_video_path, start_frame, end_frame):
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # FFmpegコマンドでVP9でエンコード
    ffmpeg_command = [
        'ffmpeg',
        '-i', input_video_path,
        '-c:v', 'libvpx-vp9',
        '-b:v', '1M',  # ビットレートを調整してください
        '-c:a', 'libvorbis',
        '-y',  # 存在する場合でも上書きする
        output_video_path
    ]
    
    subprocess.run(ffmpeg_command, shell=True)

    cap.release()

def process_video_and_json(video_filename, video_path, extension):
    # 動画をフレームに分割
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("total_frames:", total_frames)
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # 特定のJSONファイルを取得
    target_json_filename = f"{video_filename}_000000000050_keypoints.json"
    target_json_path = os.path.join(app.config['JSON_OUTPUT_FOLDER'], target_json_filename)
    print("target_json_path:", target_json_path)
    # JSONファイルが存在するか確認
    if os.path.exists(target_json_path):
        with open(target_json_path, 'r') as json_file:
            data = json.load(json_file)
            # ここでJSONデータを使用して必要な処理を行うことができます

        # 該当する動画のフレームを取得
        cap.set(cv2.CAP_PROP_POS_FRAMES, 50)  # 50フレーム目を取得
        ret, frame = cap.read()
        if ret:
            # 前後20フレームを取得
            start_frame = max(0, 50 - 50)
            end_frame = min(total_frames, 50 + 150)

            output_movie_path = os.path.join(app.config['OUTPUT_MOVIES_FOLDER'], f"{video_filename}_segment.mp4")
            create_new_video(video_path, output_movie_path, start_frame, end_frame)
            
        cap.release()

    else:
        print("JSON file not found.")

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
            video_path = os.path.join(app.config['VIDEO_OUTPUT_FOLDER'], video_filename_with_extension)
            file.save(video_path)

            # カレントディレクトリをOpenPoseのディレクトリに変更
            openpose_directory = r'C:\\openpose-1.7.0-binaries-win64-gpu-python3.7-flir-3d_recommended\\openpose'
            os.chdir(openpose_directory)

            # JSON出力の保存先を設定
            json_output_directory = os.path.join(app.config['JSON_OUTPUT_FOLDER'])
            
            # 既存のJSONファイルを削除（リセット）
            for json_file in os.listdir(json_output_directory):
                json_file_path = os.path.join(json_output_directory, json_file)
                if os.path.isfile(json_file_path):
                    os.remove(json_file_path)

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
            process_video_and_json(video_filename, video_path, extension)
            return redirect(url_for('result', video_filename=video_filename + extension))
            # return redirect(url_for('result', video_filename=video_filename_with_extension))

        else:
            flash('Invalid file type')
            return redirect(request.url)



@app.route('/result')
def result():
    video_filename_with_extension = request.args.get('video_filename', '')
    video_filename, extension = os.path.splitext(video_filename_with_extension)

    # 動画ファイルのパスを設定
    video_path = os.path.join(app.config['VIDEO_OUTPUT_FOLDER'], video_filename_with_extension)
    if not os.path.exists(video_path):
        return "Video not found."

    # video_urlを正しく生成
    video_url = url_for('static', filename=f'video_output/{video_filename_with_extension}')
    print("video_url:", video_url)
    segment_video_url = url_for('static', filename=f'output_movies/{video_filename}_segment.mp4')

    return render_template('result.html', video_url=video_url, video_extension=extension, segment_video_url=segment_video_url)


if __name__ == '__main__':
    app.run(debug=True)
