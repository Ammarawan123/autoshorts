import json
import os
import shutil
import subprocess
import cv2
from .effects import detect_face_center

# -----------------------------
# FFmpeg setup
# -----------------------------
FFMPEG_EXE = shutil.which('ffmpeg') or r'D:\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe'
FFPROBE_EXE = shutil.which('ffprobe') or FFMPEG_EXE.replace('ffmpeg', 'ffprobe')

if not os.path.exists(FFMPEG_EXE):
    raise FileNotFoundError("FFmpeg not found")
if not os.path.exists(FFPROBE_EXE):
    raise FileNotFoundError("FFprobe not found")


# -----------------------------
# Get video info
# -----------------------------
def get_crop_params(video_path: str):
    result = subprocess.run(
        [
            FFPROBE_EXE,
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json',
            video_path
        ],
        capture_output=True,
        text=True,
        check=False
    )

    probe = json.loads(result.stdout)
    stream = probe.get('streams', [None])[0]

    W, H = int(stream['width']), int(stream['height'])

    crop_w = int(H * 9 / 16)
    crop_h = H

    if crop_w > W:
        crop_w = W
        crop_h = int(W * 16 / 9)

    crop_w -= crop_w % 2
    crop_h -= crop_h % 2

    return crop_w, crop_h


# -----------------------------
# FACE CENTER (NEW SIMPLE VERSION)
# -----------------------------
def get_face_center_from_video(video_path):
    cap = cv2.VideoCapture(video_path)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None, None

    return detect_face_center(frame)


# -----------------------------
# RENDER CLIP (UPDATED)
# -----------------------------
def render_clip(src, start, end, out, cw, ch):

    # Get face center
    cx, cy = get_face_center_from_video(src)

    if cx is None:
        cx, cy = 0, 0

    duration = end - start

    command = [
        FFMPEG_EXE,
        '-y',
        '-i', src,
        '-ss', str(start),
        '-t', str(duration),

        '-vf',
        ",".join([
            f"crop={cw}:{ch}:{cx}:{cy}",
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':"
            "text='AutoShorts AI':fontcolor=white:fontsize=48:"
            "box=1:boxcolor=black@0.5:boxborderw=10:"
            "x=(w-text_w)/2:y=h*0.80"
        ]),

        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '20',

        '-c:a', 'aac',
        '-b:a', '128k',

        '-movflags', '+faststart',
        '-pix_fmt', 'yuv420p',

        out
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(result.stderr)
