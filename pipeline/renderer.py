import json
import os
import shutil
import subprocess
import cv2
from .effects import detect_face_center

# -----------------------------
# FFmpeg setup
# -----------------------------
FFMPEG_EXE = shutil.which("ffmpeg")
FFPROBE_EXE = shutil.which("ffprobe")

# Windows fallback
if FFMPEG_EXE is None:
    paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg-8.1.2-essentials_build\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe",
    ]

    for p in paths:
        if os.path.exists(p):
            FFMPEG_EXE = p
            break

if FFPROBE_EXE is None:
    paths = [
        r"C:\ffmpeg\bin\ffprobe.exe",
        r"C:\ffmpeg-8.1.2-essentials_build\ffmpeg-8.1.2-essentials_build\bin\ffprobe.exe",
    ]

    for p in paths:
        if os.path.exists(p):
            FFPROBE_EXE = p
            break

if FFMPEG_EXE is None:
    raise FileNotFoundError("FFmpeg not found")

if FFPROBE_EXE is None:
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
