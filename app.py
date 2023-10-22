from flask import Flask, render_template, request, redirect, url_for, send_file, flash, send_file
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
import os
import subprocess
import json
import numpy as np
import cv2  # OpenCVをインポート
import shutil
import re

app = Flask(__name__)

# フォルダの設定
JSON_OUTPUT_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\json_output'
VIDEO_OUTPUT_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\static\\video_output'
OUTPUT_MOVIES_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\static\\output_movies'
ARM_CROSSED_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\static\\arm_crossed_folder'
HEAD_SCRATCHING_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\static\\head_scratching_folder'
HAND_CROSSED_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\static\\hand_crossed_folder'
NOT_LOOKING_AT_AUDIENCE_FOLDER = 'C:\\Users\\toshi\\OneDrive\\ドキュメント\\myjlab\\openpose_webapp\\static\\not_looking_at_audience_folder'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

app.config['JSON_OUTPUT_FOLDER'] = JSON_OUTPUT_FOLDER
app.config['VIDEO_OUTPUT_FOLDER'] = VIDEO_OUTPUT_FOLDER
app.config['OUTPUT_MOVIES_FOLDER'] = OUTPUT_MOVIES_FOLDER
app.config['ARM_CROSSED_FOLDER'] = ARM_CROSSED_FOLDER
app.config['HEAD_SCRATCHING_FOLDER'] = HEAD_SCRATCHING_FOLDER
app.config['HAND_CROSSED_FOLDER'] = HAND_CROSSED_FOLDER
app.config['NOT_LOOKING_AT_AUDIENCE_FOLDER'] = NOT_LOOKING_AT_AUDIENCE_FOLDER

# フォルダを作成
if not os.path.exists(app.config['JSON_OUTPUT_FOLDER']):
    os.makedirs(app.config['JSON_OUTPUT_FOLDER'])

if not os.path.exists(app.config['VIDEO_OUTPUT_FOLDER']):
    os.makedirs(app.config['VIDEO_OUTPUT_FOLDER'])

if not os.path.exists(app.config['OUTPUT_MOVIES_FOLDER']):
    os.makedirs(app.config['OUTPUT_MOVIES_FOLDER'])

if not os.path.exists(app.config['ARM_CROSSED_FOLDER']):
    os.makedirs(app.config['ARM_CROSSED_FOLDER'])

if not os.path.exists(app.config['HEAD_SCRATCHING_FOLDER']):
    os.makedirs(app.config['HEAD_SCRATCHING_FOLDER'])

if not os.path.exists(app.config['HAND_CROSSED_FOLDER']):
    os.makedirs(app.config['HAND_CROSSED_FOLDER'])

if not os.path.exists(app.config['NOT_LOOKING_AT_AUDIENCE_FOLDER']):
    os.makedirs(app.config['NOT_LOOKING_AT_AUDIENCE_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_folder(folder_path):
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def find_arm_crossed_frames(json_data):
    arm_crossed_frames = []
    arm_crossing = False
    start_frame = 0

    # JSONデータを解析して腕を組んでいるフレームを検出
    for frame_index, person in enumerate(json_data['people']):
        keypoints_2d = person['pose_keypoints_2d']
        right_wrist_x = keypoints_2d[12]
        left_wrist_x = keypoints_2d[21]

        if right_wrist_x > left_wrist_x:
            # 右手首が左手首よりも左側にある場合、腕を組んでいると判断
            if not arm_crossing:
                # 腕を組んでいない状態から腕を組み始めた
                arm_crossing = True
                start_frame = frame_index  # 腕を組み始めたフレーム
        elif arm_crossing:
            # 腕を組んでいる状態で右手首が左手首を越えた
            end_frame = frame_index  # 腕を組み終わったフレーム
            arm_crossed_frames.append((start_frame, end_frame))
            arm_crossing = False  # リセット

    if arm_crossing:
        # 最後のフレームで腕を組んでいる場合を処理
        end_frame = frame_index
        arm_crossed_frames.append((start_frame, end_frame))

    return arm_crossed_frames

def find_head_scratching_frames(json_data):
    head_scratching_frames = []
    head_scratching = False
    start_frame = 0

    for frame_index, person in enumerate(json_data['people']):
        keypoints_2d = person['pose_keypoints_2d']
        right_wrist_x = keypoints_2d[12]
        right_wrist_y = keypoints_2d[13]
        left_wrist_x = keypoints_2d[21]
        left_wrist_y = keypoints_2d[22]
        right_ear_x = keypoints_2d[51]
        right_ear_y = keypoints_2d[52]
        left_ear_x = keypoints_2d[54]
        left_ear_y = keypoints_2d[55]

        # 右手首と右耳のx軸およびy軸、左手首と左耳のx軸およびy軸が20以内の場合、頭をかいていると判断
        if (abs(right_wrist_x - right_ear_x) < 20 and abs(right_wrist_y - right_ear_y) < 20) or (abs(left_wrist_x - left_ear_x) < 20 and abs(left_wrist_y - left_ear_y) < 20):
            if not head_scratching:
                head_scratching = True
                start_frame = frame_index
        elif head_scratching:
            end_frame = frame_index
            head_scratching_frames.append((start_frame, end_frame))
            head_scratching = False

    if head_scratching:
        end_frame = frame_index
        head_scratching_frames.append((start_frame, end_frame))

    return head_scratching_frames

def find_hand_crossed_frames(json_data):
    hand_crossed_frames = []
    hand_crossing = False
    start_frame = 0

    for frame_index, person in enumerate(json_data['people']):
        keypoints_2d = person['pose_keypoints_2d']
        right_wrist_x = keypoints_2d[12]
        right_wrist_y = keypoints_2d[13]
        left_wrist_x = keypoints_2d[21]
        left_wrist_y = keypoints_2d[22]

        # 右手首と左手首のx軸およびy軸が20以内の場合、手を組んでいると判断
        if abs(left_wrist_x - right_wrist_x) < 15 and abs(left_wrist_y - right_wrist_y) < 15:
            if not hand_crossing:
                hand_crossing = True
                start_frame = frame_index
        elif hand_crossing:
            end_frame = frame_index
            hand_crossed_frames.append((start_frame, end_frame))
            hand_crossing = False

    if hand_crossing:
        end_frame = frame_index
        hand_crossed_frames.append((start_frame, end_frame))

    return hand_crossed_frames

nose_to_neck_y_coords = []  # 首から鼻のy座標を格納するリスト

def find_not_looking_at_audience_frames(json_data):
    not_looking_frames = []
    not_looking = False
    start_frame = 0

    for frame_index, person in enumerate(json_data['people']):
        keypoints_2d = person['pose_keypoints_2d']
        left_eye_confidence = keypoints_2d[50]
        right_eye_confidence = keypoints_2d[47]
        nose_y_coord = keypoints_2d[1]
        neck_y_coord = keypoints_2d[4]

        # 目の特徴点の信頼度が 0.4 以下の場合、または首から鼻のy座標の差が平均の半分以下の距離になったら聴衆の方を向いていないと判断
        if left_eye_confidence <= 0.4 or right_eye_confidence <= 0.4 or abs(neck_y_coord - nose_y_coord) <= (np.mean(nose_to_neck_y_coords) * 0.75):
            if not not_looking:
                not_looking = True
                start_frame = frame_index
        elif not_looking:
            end_frame = frame_index
            not_looking_frames.append((start_frame, end_frame))
            not_looking = False
        if not (left_eye_confidence <= 0.4 or right_eye_confidence <= 0.4 or abs(neck_y_coord - nose_y_coord) <= (np.mean(nose_to_neck_y_coords) * 0.75)):
            nose_to_neck_y_coords.append(abs(nose_y_coord - neck_y_coord))

        # デバッグ用: リストの内容を確認
        print(f"Frame {frame_index}: len(nose_to_neck_y_coords) = {len(nose_to_neck_y_coords)}")
        print(f"Frame {frame_index}: np.mean(nose_to_neck_y_coords) = {np.mean(nose_to_neck_y_coords)}")

    if not_looking:
        end_frame = frame_index
        not_looking_frames.append((start_frame, end_frame))

    return not_looking_frames


def create_new_video(video_path, output_folder, start_frame, end_frame, json_filename, action_type, fps):
    video = VideoFileClip(video_path)
    video_duration = video.duration

    # start_frameとend_frameを秒数に変換
    start_time = start_frame / fps
    end_time = end_frame / fps

    # 前後に3秒追加
    start_time = max(0, start_time - 3)  # 0秒より小さくならないように
    end_time = min(video_duration, end_time + 3)  # 動画の長さを超えないように

    clip = video.subclip(start_time, end_time)

    # 出力ファイル名の作成
    minutes = int(start_time // 60)
    seconds = int(start_time % 60)
    if minutes > 0:
        filename_time = f"{minutes}m{seconds}s"
    else:
        filename_time = f"{seconds}s"

    # 動作の種類によってフォルダを選択
    if action_type == "arm_crossed":
        output_folder = app.config['ARM_CROSSED_FOLDER']
    elif action_type == "head_scratching":
        output_folder = app.config['HEAD_SCRATCHING_FOLDER']
    elif action_type == "hand_crossed":
        output_folder = app.config['HAND_CROSSED_FOLDER']
    elif action_type == "not_looking":
        output_folder = app.config['NOT_LOOKING_AT_AUDIENCE_FOLDER']

    output_movie_path = os.path.join(output_folder, f"{action_type}_{filename_time}.mp4")
    clip.write_videofile(output_movie_path)

def process_video_and_json(video_path, video_folder, output_folder):
    json_files = [f for f in os.listdir(video_folder) if f.endswith('_keypoints.json')]
    start_frame_arm_crossed = None
    end_frame_arm_crossed = None
    start_frame_head_scratching = None
    end_frame_head_scratching = None
    start_frame_hand_crossed = None
    end_frame_hand_crossed = None
    start_frame_not_looking = None
    end_frame_not_looking = None
    cap = VideoFileClip(video_path)
    fps = cap.fps

    # フォルダをクリア
    clear_folder(app.config['ARM_CROSSED_FOLDER'])
    clear_folder(app.config['HEAD_SCRATCHING_FOLDER'])
    clear_folder(app.config['HAND_CROSSED_FOLDER'])
    clear_folder(app.config['NOT_LOOKING_AT_AUDIENCE_FOLDER'])

    for json_filename in json_files:
        json_file_path = os.path.join(video_folder, json_filename)

        with open(json_file_path, 'r') as json_file:
            json_data = json.load(json_file)
            arm_crossed_frames = find_arm_crossed_frames(json_data)
            head_scratching_frames = find_head_scratching_frames(json_data)
            hand_crossed_frames = find_hand_crossed_frames(json_data)
            not_looking_frames = find_not_looking_at_audience_frames(json_data)

            if not arm_crossed_frames and not head_scratching_frames and not hand_crossed_frames and not not_looking_frames:
                # print(f"{json_filename} で腕または頭または手を組んでいるフレームが見つかりませんでした")
                continue

            match = re.search(r'_(\d+)_keypoints.json', json_filename)
            current_start_frame = int(match.group(1))
            current_end_frame = int(match.group(1))

            if arm_crossed_frames:
                if start_frame_arm_crossed is None:
                    start_frame_arm_crossed = current_start_frame
                    end_frame_arm_crossed = current_end_frame
                else:
                    if current_start_frame == end_frame_arm_crossed + 1:
                        end_frame_arm_crossed = current_end_frame
                    else:
                        if (end_frame_arm_crossed - start_frame_arm_crossed) / fps >= 5:
                            # 5秒以上の動作のみを含む動画を作成
                            create_new_video(video_path, output_folder, start_frame_arm_crossed, end_frame_arm_crossed, json_filename, "arm_crossed", fps)
                            # print(f"{json_filename} の腕を組んでいるフレーム: {start_frame_arm_crossed} - {end_frame_arm_crossed}")
                        start_frame_arm_crossed = current_start_frame
                        end_frame_arm_crossed = current_end_frame

            if head_scratching_frames:
                if start_frame_head_scratching is None:
                    start_frame_head_scratching = current_start_frame
                    end_frame_head_scratching = current_end_frame
                else:
                    if current_start_frame == end_frame_head_scratching + 1:
                        end_frame_head_scratching = current_end_frame
                    else:
                        if (end_frame_head_scratching - start_frame_head_scratching) / fps >= 5:
                            # 5秒以上の動作のみを含む動画を作成
                            create_new_video(video_path, output_folder, start_frame_head_scratching, end_frame_head_scratching, json_filename, "head_scratching", fps)
                            # print(f"{json_filename} の頭をかいているフレーム: {start_frame_head_scratching} - {end_frame_head_scratching}")
                        start_frame_head_scratching = current_start_frame
                        end_frame_head_scratching = current_end_frame

            if hand_crossed_frames:
                if start_frame_hand_crossed is None:
                    start_frame_hand_crossed = current_start_frame
                    end_frame_hand_crossed = current_end_frame
                else:
                    if current_start_frame == end_frame_hand_crossed + 1:
                        end_frame_hand_crossed = current_end_frame
                    else:
                        if (end_frame_hand_crossed - start_frame_hand_crossed) / fps >= 5:
                            # 5秒以上の動作のみを含む動画を作成
                            create_new_video(video_path, output_folder, start_frame_hand_crossed, end_frame_hand_crossed, json_filename, "hand_crossed", fps)
                            # print(f"{json_filename} の手を組んでいるフレーム: {start_frame_hand_crossed} - {end_frame_hand_crossed}")
                        start_frame_hand_crossed = current_start_frame
                        end_frame_hand_crossed = current_end_frame

            if not_looking_frames:
                if start_frame_not_looking is None:
                    start_frame_not_looking = current_start_frame
                    end_frame_not_looking = current_end_frame
                else:
                    if current_start_frame == end_frame_not_looking + 1:
                        end_frame_not_looking = current_end_frame
                    else:
                        if (end_frame_not_looking - start_frame_not_looking) / fps >= 5:
                            # 5秒以上の聴衆の方を向いていない動画を作成
                            create_new_video(video_path, output_folder, start_frame_not_looking, end_frame_not_looking, json_filename, "not_looking", fps)
                            # print(f"{json_filename} の聴衆の方を向いていないフレーム: {start_frame_not_looking} - {end_frame_not_looking}")
                        start_frame_not_looking = current_start_frame
                        end_frame_not_looking = current_end_frame

    if start_frame_arm_crossed is not None and end_frame_arm_crossed is not None:
        if (end_frame_arm_crossed - start_frame_arm_crossed) / fps >= 5:
            create_new_video(video_path, output_folder, start_frame_arm_crossed, end_frame_arm_crossed, json_filename, "arm_crossed", fps)
    if start_frame_head_scratching is not None and end_frame_head_scratching is not None:
        if (end_frame_head_scratching - start_frame_head_scratching) / fps >= 5:
            create_new_video(video_path, output_folder, start_frame_head_scratching, end_frame_head_scratching, json_filename, "head_scratching", fps)
    if start_frame_hand_crossed is not None and end_frame_hand_crossed is not None:
        if (end_frame_hand_crossed - start_frame_hand_crossed) / fps >= 5:
            create_new_video(video_path, output_folder, start_frame_hand_crossed, end_frame_hand_crossed, json_filename, "hand_crossed", fps)
    if start_frame_not_looking is not None and end_frame_not_looking is not None:
        if (end_frame_not_looking - start_frame_not_looking) / fps >= 5:
            create_new_video(video_path, output_folder, start_frame_not_looking, end_frame_not_looking, json_filename, "not_looking", fps)
    print("処理が完了しました。")




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
            clear_folder(app.config['VIDEO_OUTPUT_FOLDER'])
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
            # process_video_and_json(video_filename, video_path, extension)
            # 動画の分割と新しい動画の作成
            json_output_folder = app.config['JSON_OUTPUT_FOLDER']
            output_movies_folder = app.config['OUTPUT_MOVIES_FOLDER']

            process_video_and_json(video_path, json_output_folder, output_movies_folder)
            return redirect(url_for('result', video_filename=video_filename + extension))
            # return redirect(url_for('result', video_filename=video_filename_with_extension))

        else:
            flash('Invalid file type')
            return redirect(request.url)

@app.route('/result')
def result():
    uploaded_videos = os.listdir(app.config['VIDEO_OUTPUT_FOLDER'])
    arm_crossed_videos = os.listdir(app.config['ARM_CROSSED_FOLDER'])
    head_scratching_videos = os.listdir(app.config['HEAD_SCRATCHING_FOLDER'])
    hand_crossed_videos = os.listdir(app.config['HAND_CROSSED_FOLDER'])
    not_looking_at_audience_videos = os.listdir(app.config['NOT_LOOKING_AT_AUDIENCE_FOLDER'])


    return render_template('result.html', 
                            uploaded_videos=uploaded_videos, 
                            arm_crossed_videos=arm_crossed_videos,
                            head_scratching_videos=head_scratching_videos,
                            hand_crossed_videos=hand_crossed_videos,
                            not_looking_at_audience_videos=not_looking_at_audience_videos)


if __name__ == '__main__':
    app.run(debug=True)
