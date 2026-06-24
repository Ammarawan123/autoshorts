import json
import os
import shutil
import subprocess
from .effects import apply_zoom, add_caption  # kept for future use

# -----------------------------
# FFmpeg setup
# -----------------------------
FFMPEG_EXE = shutil.which('ffmpeg') or r'D:\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe'
FFPROBE_EXE = shutil.which('ffprobe') or FFMPEG_EXE.replace('ffmpeg', 'ffprobe')

if not os.path.exists(FFMPEG_EXE):
    raise FileNotFoundError(
        'FFmpeg executable not found. Install ffmpeg or fix PATH.'
    )

if not os.path.exists(FFPROBE_EXE):
    raise FileNotFoundError(
        'FFprobe executable not found. Install ffmpeg or fix PATH.'
    )

# -----------------------------
# Get crop parameters
# -----------------------------
def get_crop_params(video_path: str) -> tuple:
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

    if result.returncode != 0:
        raise RuntimeError(f'ffprobe failed: {result.stderr.strip()}')

    probe = json.loads(result.stdout)
    stream = probe.get('streams', [None])[0]

    if not stream:
        raise RuntimeError('No video stream found.')

    W, H = int(stream['width']), int(stream['height'])

    # 9:16 crop calculation
    crop_w = int(H * 9 / 16)
    crop_h = H

    if crop_w > W:
        crop_w = W
        crop_h = int(W * 16 / 9)

    crop_w -= crop_w % 2
    crop_h -= crop_h % 2

    cx = (W - crop_w) // 2
    cy = (H - crop_h) // 2

    return crop_w, crop_h, cx, cy


# -----------------------------
# Render optimized clip
# -----------------------------
def render_clip(src, start, end, out, cw, ch, cx, cy):

    duration = end - start

    command = [
        FFMPEG_EXE,
        '-y',

        # FAST SEEKING
        '-i', src,
        '-ss', str(start),
        '-t', str(duration),

        # VIDEO FILTER PIPELINE
        '-vf',
        ",".join([
            f'crop={cw}:{ch}:{cx}:{cy}',
            'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
            "drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':"
            "text='AutoShorts AI':fontcolor=white:fontsize=48:"
            "box=1:boxcolor=black@0.5:boxborderw=10:"
            "x=(w-text_w)/2:y=h*0.80"
        ]),

        # ENCODING (OPTIMIZED)
        '-c:v', 'libx264',
        '-preset', 'veryfast',
        '-crf', '20',

        # AUDIO
        '-c:a', 'aac',
        '-b:a', '128k',

        # WEB OPTIMIZATION
        '-movflags', '+faststart',
        '-pix_fmt', 'yuv420p',

        out
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f'FFmpeg rendering failed:\n{result.stderr.strip()}')
