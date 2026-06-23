import json
import os
import shutil
import subprocess
from .effects import apply_zoom, add_caption

FFMPEG_EXE = shutil.which('ffmpeg') or r'D:\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe'
FFPROBE_EXE = shutil.which('ffprobe') or FFMPEG_EXE.replace('ffmpeg', 'ffprobe')
if not os.path.exists(FFMPEG_EXE):
    raise FileNotFoundError(
        'FFmpeg executable not found. Install ffmpeg and ensure it is available on the system PATH, '
        'or update pipeline/renderer.py with a valid FFMPEG_EXE path.'
    )
if not os.path.exists(FFPROBE_EXE):
    raise FileNotFoundError(
        'FFprobe executable not found. Install ffmpeg/ffprobe and ensure it is available on the PATH, '
        'or update pipeline/renderer.py with a valid FFPROBE_EXE path.'
    )

def get_crop_params(video_path: str) -> tuple:
    result = subprocess.run(
        [FFPROBE_EXE, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', video_path],
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f'ffprobe failed: {result.stderr.strip()}')

    probe = json.loads(result.stdout)
    streams = probe.get('streams', [])
    if not streams:
        raise RuntimeError('No video stream found in media file.')

    stream = streams[0]
    W, H = int(stream['width']), int(stream['height'])
    crop_w = int(H * 9 / 16)
    crop_h = H
    if crop_w > W:
        crop_w, crop_h = W, int(W * 16 / 9)
    crop_w = crop_w if crop_w % 2 == 0 else crop_w - 1
    crop_h = crop_h if crop_h % 2 == 0 else crop_h - 1
    return crop_w, crop_h, (W - crop_w) // 2, (H - crop_h) // 2

def render_clip(src, start, end, out, cw, ch, cx, cy):
    dur = end - start
    vf_filters = [
        f'crop={cw}:{ch}:{cx}:{cy}',
        'scale=1080:1920'
    ]

    # Apply caption as a drawtext filter
    drawtext = (
        "drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':"
        "text='Viral Clip':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.5:boxborderw=10:"
        "x=(w-text_w)/2:y=h*0.80"
    )
    vf_filters.append(drawtext)

    command = [
        FFMPEG_EXE,
        '-y',
        '-ss', str(start),
        '-t', str(dur),
        '-i', src,
        '-vf', ','.join(vf_filters),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        out
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'ffmpeg rendering failed: {result.stderr.strip()}')
