# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
import os
import cv2
import numpy as np
from openpose import pyopenpose as op

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# OpenPoseの設定
params = dict()
params["model_folder"] = "path_to_openpose/models"  # OpenPoseのモデルフォルダへのパス
params["net_resolution"] = "320x240"  # 解像度の設定

opWrapper = op.WrapperPython()
opWrapper.configure(params)
opWrapper.start()

def analyze_video(video_path):
    datum = op.Datum()

    # 動画を読み込み
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc, 30.0, (640, 480))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # OpenPoseでフレームを解析
        datum.cvInputData = frame
        opWrapper.emplaceAndPop([datum])

        # 解析結果を取得
        pose_keypoints = datum.poseKeypoints

        # 解析結果をフレームに描画（ここで解析結果をフレームに描画する処理を実装）

        # 動画にフレームを書き込み
        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], 'input_video.mp4')
        file.save(filename)
        analyze_video(filename)
        return render_template('result.html')

if __name__ == '__main__':
    app.run(debug=True)